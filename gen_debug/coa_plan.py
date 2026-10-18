# -*- coding: utf-8 -*-
"""Build a COA assignment plan for the 168 merged houses. READ ONLY - writes nothing to game files.

Rule (per user):
  - House keeps its house structure (支系).
  - It inherits the vanilla COA of its matched vanilla counterpart.
  - If vanilla considers it an independent dynasty (downgrade / B2), we still keep the house
    and just take that dynasty's COA.
  - No vanilla counterpart -> fall back to the parent dynasty's COA.
  - Ashikaga is special-cased.
"""
import json, os, re, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

VAN = 'E:/SteamLibrary/steamapps/common/Crusader Kings III/game'
COA_FILES = [
    VAN + '/common/coat_of_arms/coat_of_arms/90_dynasties.txt',
    VAN + '/common/coat_of_arms/coat_of_arms/01_landed_titles.txt',
    VAN + '/common/coat_of_arms/coat_of_arms/default.txt',
    VAN + '/common/coat_of_arms/coat_of_arms/99_historical_character_coa.txt',
]


def coa_keys(path):
    """Top-level keys defined in a COA file."""
    keys = set()
    try:
        with open(path, 'rb') as f:
            t = f.read().decode('utf-8-sig', 'ignore')
    except FileNotFoundError:
        return keys
    for ln in t.splitlines():
        m = re.match(r'^([A-Za-z0-9_.\-]+)\s*=\s*(\{|[A-Za-z0-9_.\-]+)\s*(#.*)?$', ln)
        if m:
            keys.add(m.group(1))
    return keys


vanilla_coa = set()
for p in COA_FILES:
    vanilla_coa |= coa_keys(p)
print('vanilla COA keys parsed: %d' % len(vanilla_coa))

# ---- our houses ----
with open('common/dynasty_houses/zz_eu5_merged_houses.txt', 'rb') as f:
    txt = f.read().decode('utf-8-sig')
blocks = re.findall(r'^(house_[A-Za-z0-9_]+)\s*=\s*\{(.*?)^\}', txt, re.M | re.S)
houses = {}
for key, body in blocks:
    m = re.search(r'^\s*dynasty\s*=\s*([A-Za-z0-9_]+)', body, re.M)
    n = re.search(r'^\s*name\s*=\s*"([^"]*)"', body, re.M)
    houses[key] = {'parent': m.group(1) if m else None,
                   'name': n.group(1) if n else None}
print('houses parsed: %d' % len(houses))

# ---- v4 analysis ----
v4 = json.load(open('gen_debug/house_confidence_v4.json', encoding='utf-8'))
by_short = {c['short']: c for c in v4['children']}

# ---- special cases ----
# house_ashikaga: vanilla has two Ashikaga houses. Ours sits under seiwa_genji (清和源氏),
# so the matching one is 源氏足利 = house_minamoto_shimotsuke (足利二つ引).
SPECIAL = {
    'house_ashikaga': ('house_minamoto_shimotsuke',
                       'vanilla 有两家足利；本家挂在清和源氏 -> 源氏足利(下野源氏)=house_minamoto_shimotsuke'),
}

plan = []
stats = collections.Counter()
unresolved = []

for key in sorted(houses):
    short = key[len('house_'):]
    rec = by_short.get(short)
    parent = houses[key]['parent']
    entry = {'house': key, 'parent': parent, 'grade': None, 'vanilla_coa': None,
             'source': None, 'note': ''}

    if key in SPECIAL:
        coa, note = SPECIAL[key]
        entry.update(vanilla_coa=coa, source='special', note=note)
        stats['special'] += 1
        plan.append(entry)
        continue

    if not rec:
        entry['note'] = 'no v4 record'
        unresolved.append(entry)
        stats['no_record'] += 1
        plan.append(entry)
        continue

    entry['grade'] = rec['grade']

    cand, src = None, None
    if rec.get('downgrade') and rec.get('named'):
        # vanilla treats it as an independent dynasty -> take that dynasty's COA
        cand, src = rec['named'][0], 'vanilla_dynasty(B2)'
    elif rec.get('house') and rec.get('aligned'):
        cand, src = rec['house'], 'vanilla_house(A1)'
    elif rec.get('house') and rec.get('mismatch'):
        cand, src = rec['house'], 'vanilla_house(B1-name-match)'
    elif rec.get('parent_anchored') and rec.get('parent_keys'):
        cand, src = rec['parent_keys'][0], 'parent_dynasty(%s)' % rec['grade']
    elif rec.get('named'):
        cand, src = rec['named'][0], 'vanilla_dynasty(name-match)'

    if cand and cand == key:
        # self reference -> vanilla COA already applies by key match
        entry.update(source='already_applies', note='house key == vanilla house key')
        stats['already_applies'] += 1
        plan.append(entry)
        continue

    if cand and cand in vanilla_coa:
        entry.update(vanilla_coa=cand, source=src)
        stats[src.split('(')[0]] += 1
    else:
        entry['note'] = 'candidate %r not found in vanilla COA' % cand if cand else 'no candidate'
        unresolved.append(entry)
        stats['unresolved'] += 1
    plan.append(entry)

# ---- report ----
lines = []
lines.append('houses total: %d' % len(houses))
lines.append('')
lines.append('=== by source ===')
for k, n in stats.most_common():
    lines.append('  %-28s %d' % (k, n))
lines.append('')
lines.append('=== unresolved (%d) ===' % len(unresolved))
for e in unresolved:
    lines.append('  %-34s parent=%-26s grade=%s  %s' % (e['house'], e['parent'], e['grade'], e['note']))

# grade x source crosstab
ct = collections.Counter((e['grade'], e['source']) for e in plan)
lines.append('')
lines.append('=== grade x source ===')
for (g, s), n in sorted(ct.items(), key=lambda x: (str(x[0][0]), str(x[0][1]))):
    lines.append('  %-6s %-30s %d' % (g, s, n))

out = '\n'.join(lines)
with open('gen_debug/coa_plan_report.txt', 'w', encoding='utf-8') as f:
    f.write(out + '\n')
json.dump(plan, open('gen_debug/coa_plan.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# ascii console summary
print(out.replace('\u2192', '->'))
