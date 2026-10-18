# -*- coding: utf-8 -*-
"""Attach vanilla COAs to merged houses, disambiguating duplicate family names by characters.

Rules (user-confirmed):
  - Houses stay houses (支系). Only inherit the vanilla COA of the SAME family.
  - vanilla treats the family as an independent dynasty (B2) -> keep house, take that COA.
  - Ashikaga: only if 源氏足利 (house_minamoto_shimotsuke) exists; else leave untouched.
  - No same-name vanilla family with a COA -> leave untouched (no parent fallback).
  - Duplicate family names -> decide by comparing character given names.

Two-hop resolution:
    our house -> v4 match (vanilla house key / dynasty id) -> family name key
              -> all vanilla entities with that name key that actually carry a COA
              -> character-name overlap picks the right one.

Default dry run; pass --apply to write.
"""
import json, os, re, sys, unicodedata, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

VAN = 'E:/SteamLibrary/steamapps/common/Crusader Kings III/game'
APPLY = '--apply' in sys.argv
OUT = 'common/coat_of_arms/coat_of_arms/zz_eu5_house_coas.txt'

ROMAN = re.compile(r'^[ivxlc]+$')


def norm_name(raw):
    """Given-name normalizer: strip loc prefix, drop roman numerals/digits, deaccent."""
    s = raw.strip().strip('"')
    if s.startswith('name_eu5_'):
        s = s[len('name_eu5_'):]
    elif s.startswith('name_'):
        s = s[len('name_'):]
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = s.replace('_', ' ').lower()
    for tok in re.findall(r"[a-z']+", s):
        tok = tok.strip("'")
        if not tok or ROMAN.match(tok) or len(tok) < 2:
            continue
        return tok
    return ''


def iter_blocks(path):
    """Yield (key, body_lines) for top-level `key = { ... }` blocks."""
    try:
        with open(path, 'rb') as f:
            lines = f.read().decode('utf-8-sig', 'ignore').splitlines()
    except FileNotFoundError:
        return
    depth, cur, buf = 0, None, []
    for ln in lines:
        s = ln.strip()
        if depth == 0:
            m = re.match(r'^([A-Za-z0-9_.\-]+)\s*=\s*\{', s)
            if m:
                cur, buf, depth = m.group(1), [], 1
                continue
            continue
        depth += s.count('{') - s.count('}')
        if depth <= 0:
            if cur is not None:
                yield cur, buf
            depth, cur, buf = 0, None, []
        else:
            buf.append(s)


# ------------------------------------------------------------------ vanilla defs
def parse_defs(folder):
    out = {}
    for f in os.listdir(folder):
        if not f.endswith('.txt'):
            continue
        for key, body in iter_blocks(os.path.join(folder, f)):
            for s in body:
                m = re.match(r'^name\s*=\s*"([^"]*)"', s)
                if m:
                    out[key] = m.group(1)
                    break
    return out


van_dyn = parse_defs(os.path.join(VAN, 'common/dynasties'))
van_house = parse_defs(os.path.join(VAN, 'common/dynasty_houses'))
print('vanilla dynasties: %d, houses: %d' % (len(van_dyn), len(van_house)))


def coa_top_keys(path):
    keys, depth = set(), 0
    try:
        with open(path, 'rb') as f:
            lines = f.read().decode('utf-8-sig', 'ignore').splitlines()
    except FileNotFoundError:
        return keys
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith('#'):
            continue
        if depth == 0:
            m = re.match(r'^([A-Za-z0-9_.\-]+)\s*=\s*(\{|[A-Za-z0-9_.\-]+)\s*(#.*)?$', s)
            if m:
                keys.add(m.group(1))
                if m.group(2) == '{':
                    depth = 1
            continue
        depth += s.count('{') - s.count('}')
        if depth < 0:
            depth = 0
    return keys


coa_dir = os.path.join(VAN, 'common/coat_of_arms/coat_of_arms')
van_coa = set()
for f in os.listdir(coa_dir):
    if f.endswith('.txt'):
        van_coa |= coa_top_keys(os.path.join(coa_dir, f))
print('vanilla COA keys: %d' % len(van_coa))


def norm_nk(nk):
    if not nk:
        return None
    s = nk.lower()
    for p in ('dynn_', 'dynnp_'):
        if s.startswith(p):
            s = s[len(p):]
    return re.sub(r'[^a-z0-9]', '', s)


# family name key -> COA-bearing entities
by_name = collections.defaultdict(list)
for k, nk in van_house.items():
    n = norm_nk(nk)
    if n and k in van_coa:
        by_name[n].append(('house', k))
for k, nk in van_dyn.items():
    n = norm_nk(nk)
    if n and k in van_coa:
        by_name[n].append(('dynasty', k))

# ------------------------------------------------------------------ characters
def char_index(paths):
    """entity key -> Counter of normalized given names."""
    idx = collections.defaultdict(collections.Counter)
    for p in paths:
        for key, body in iter_blocks(p):
            name, ent = None, None
            for s in body:
                if name is None:
                    m = re.match(r'^name\s*=\s*"([^"]*)"', s)
                    if m:
                        name = m.group(1)
                        continue
                if ent is None:
                    m = re.match(r'^dynasty_house\s*=\s*([A-Za-z0-9_\-]+)', s)
                    if m:
                        ent = m.group(1)
                        continue
                    m = re.match(r'^dynasty\s*=\s*([A-Za-z0-9_\-]+)', s)
                    if m:
                        ent = m.group(1)
            if name and ent:
                n = norm_name(name)
                if n:
                    idx[ent][n] += 1
    return idx


van_chars = char_index([os.path.join(VAN, 'history/characters', f)
                        for f in os.listdir(os.path.join(VAN, 'history/characters'))
                        if f.endswith('.txt')])
print('vanilla characters indexed for %d families' % len(van_chars))

our_chars = char_index(['history/characters/zz_eu5_characters.txt',
                        'history/characters/zz_eu5_regents.txt'])
print('our characters indexed for %d houses' % len(our_chars))

# ------------------------------------------------------------------ our houses
with open('common/dynasty_houses/zz_eu5_merged_houses.txt', 'rb') as f:
    htxt = f.read().decode('utf-8-sig')
houses = {}
for key, body in re.findall(r'^(house_[A-Za-z0-9_]+)\s*=\s*\{(.*?)^\}', htxt, re.M | re.S):
    m = re.search(r'^\s*dynasty\s*=\s*([A-Za-z0-9_]+)', body, re.M)
    houses[key] = m.group(1) if m else None

v4 = json.load(open('gen_debug/house_confidence_v4.json', encoding='utf-8'))
by_short = {c['short']: c for c in v4['children']}

ASHIKAGA = 'house_minamoto_shimotsuke'

result, stats, lines = [], collections.Counter(), []

for key in sorted(houses):
    short = key[len('house_'):]
    rec = by_short.get(short) or {}
    ent = {'house': key, 'parent': houses[key], 'grade': rec.get('grade'),
           'coa': None, 'via': None, 'overlap': None, 'cands': [], 'note': ''}

    if key == 'house_ashikaga':
        if ASHIKAGA in van_coa:
            ent.update(coa=ASHIKAGA, via='special:源氏足利(house_minamoto_shimotsuke)')
            stats['special'] += 1
        else:
            ent['note'] = '源氏足利 不存在 -> 不动'
            stats['ashikaga_skip'] += 1
        result.append(ent)
        continue

    # vanilla already defines a COA under this exact key -> it applies by itself, never shadow it
    if key in van_coa:
        ent['note'] = 'vanilla 已有同名 house 的 COA，自动生效'
        stats['auto_applies'] += 1
        result.append(ent)
        continue

    # collect candidate entities via v4
    cands = []
    if rec.get('house'):
        cands.append(('house', rec['house']))
    for n in rec.get('named') or []:
        cands.append(('house' if n.startswith('house_') else 'dynasty', n))

    name_keys = []
    for kind, ck in cands:
        nk = (van_house if kind == 'house' else van_dyn).get(ck)
        n = norm_nk(nk)
        if n and n not in name_keys:
            name_keys.append(n)

    pool = []
    for n in name_keys:
        for item in by_name.get(n, []):
            if item not in pool:
                pool.append(item)

    if not pool:
        if key in van_coa:
            ent['note'] = 'vanilla 已有同名 house，COA 自动生效'
            stats['auto_applies'] += 1
        else:
            ent['note'] = 'vanilla 无同名且带 COA 的家族'
            stats['no_counterpart'] += 1
        result.append(ent)
        continue

    mine = our_chars.get(key, collections.Counter())
    mynames = set(mine)
    scored = []
    for kind, ck in pool:
        theirs = set(van_chars.get(ck, {}))
        ov = mynames & theirs
        scored.append((len(ov), kind, ck, sorted(ov)[:4], len(theirs)))
    scored.sort(key=lambda x: (-x[0], 0 if x[1] == 'house' else 1, x[2]))

    ent['cands'] = [{'key': c[2], 'kind': c[1], 'overlap': c[0], 'names': c[3], 'their_n': c[4]}
                    for c in scored]
    best = scored[0]
    if best[2] == key:
        # vanilla already has a house with this exact key -> its COA applies by itself.
        # Writing `house_x = house_x` would be a self reference.
        ent['note'] = 'vanilla 已有同名 house，COA 自动生效'
        ent['overlap'] = best[0]
        stats['auto_applies'] += 1
        result.append(ent)
        continue
    ent.update(coa=best[2], via='%s:%s' % (best[1], '/'.join(name_keys)),
               overlap=best[0])
    if len(scored) > 1 and scored[0][0] == scored[1][0]:
        ent['note'] = '重名且人物无区分证据，取默认'
        stats['attached_ambiguous'] += 1
    else:
        stats['attached_' + best[1]] += 1
    result.append(ent)

# ------------------------------------------------------------------ report
lines.append('houses total: %d' % len(houses))
lines.append('')
lines.append('=== 结果分布 ===')
for k, n in stats.most_common():
    lines.append('  %-24s %d' % (k, n))

attached = [e for e in result if e['coa']]
lines.append('')
lines.append('=== 写入 %d 条 ===' % len(attached))
for e in attached:
    extra = ''
    if len(e['cands']) > 1:
        extra = '  [重名: ' + ', '.join('%s(ov=%d,n=%d)' % (c['key'], c['overlap'], c['their_n'])
                                       for c in e['cands']) + ']'
    lines.append('  %-30s -> %-30s ov=%-2s %s%s' % (
        e['house'], e['coa'], e['overlap'], e['via'], extra))
    if e['cands'] and e['cands'][0]['names']:
        lines.append('        %s' % ('  共同人物: ' + ', '.join(e['cands'][0]['names'])))

skipped = [e for e in result if not e['coa']]
lines.append('')
lines.append('=== 未写入 %d 条 ===' % len(skipped))
for e in skipped:
    lines.append('  %-30s %-4s %s' % (e['house'], str(e['grade']), e['note']))

report = '\n'.join(lines)
open('gen_debug/coa_plan_report.txt', 'w', encoding='utf-8').write(report + '\n')
json.dump(result, open('gen_debug/coa_plan.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(report)

# ------------------------------------------------------------------ write
if APPLY:
    if not attached:
        print('nothing to write')
        sys.exit(0)
    body = [
        '# =========================================================',
        '# 支系纹章：继承 vanilla 同名家族的 COA',
        '# 由 gen_debug/coa_attach.py 生成；只挂 vanilla 里确实存在且带 COA 的同名家族',
        '# 重名家族按人物（given name）重合度裁决',
        '# =========================================================',
        '',
    ]
    for e in attached:
        body.append('%s = %s' % (e['house'], e['coa']))
    text = '\n'.join(body) + '\n'
    if os.path.exists(OUT):
        with open(OUT, 'rb') as f:
            if f.read().decode('utf-8-sig') == text:
                print('no change, file untouched')
                sys.exit(0)
        import datetime
        bak = OUT + '.bak_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        os.rename(OUT, bak)
        print('backup -> %s' % bak)
    with open(OUT, 'wb') as f:
        f.write(b'\xef\xbb\xbf' + text.encode('utf-8'))
    print('WROTE %s (%d entries)' % (OUT, len(attached)))
