# -*- coding: utf-8 -*-
"""Resolve the 154 compound `name_X.name_Y` placeholders out of the EU5 loc single keys.

The EU5->CK3 converter slugged two-part ruler names into `name_a.name_b` and emitted
placeholder values ("name a.name b") instead of the real name. Each half usually exists
as its own single key in the same file, so the real EU5 name is composable mechanically.

Dry run only: writes a proposal file, changes nothing.
"""
import re, os, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

LANGS = ['braz_por', 'english', 'french', 'german', 'japanese', 'korean',
         'polish', 'russian', 'simp_chinese', 'spanish', 'turkish']

BASE = 'localization/%s/zz_eu5_politics_l_%s.yml'


def load(lang):
    p = BASE % (lang, lang)
    d = {}
    with open(p, 'rb') as f:
        lines = f.read().decode('utf-8-sig').splitlines()
    for ln in lines:
        m = re.match(r'^\s*([A-Za-z0-9_.\-]+):\d*\s+"(.*)"\s*$', ln)
        if m:
            d[m.group(1)] = m.group(2)
    return d


def split_parts(key):
    """name_ala.name_al_din.name_muhammad -> ['name_ala','name_al_din','name_muhammad']"""
    return [p for p in key.split('.') if p]


locs = {l: load(l) for l in LANGS}
en = locs['english']
zh = locs['simp_chinese']

compound = [k for k in en if '.' in k and k.count('.') >= 1 and k.startswith('name_')]
compound.sort()
print('compound name keys in english loc: %d' % len(compound))

rows = []
bad = 0
for k in compound:
    parts = split_parts(k)
    rec = {'key': k, 'parts': parts, 'en': None, 'zh': None,
           'missing_en': [], 'missing_zh': [], 'n_parts': len(parts)}
    vals = {}
    for lang, miss_field in (('english', 'missing_en'), ('simp_chinese', 'missing_zh')):
        got = []
        for p in parts:
            if p in locs[lang]:
                got.append(locs[lang][p])
            else:
                rec[miss_field].append(p)
                got.append(None)
        vals[lang] = got
    rec['en'] = ' '.join(g for g in vals['english'] if g)
    rec['zh'] = ' '.join(g for g in vals['simp_chinese'] if g)
    if rec['missing_en'] or rec['missing_zh']:
        bad += 1
    rows.append(rec)

print('fully composable (en+zh): %d / %d' % (len(rows) - bad, len(rows)))
print()
print('=== 无法完整拼出的条目 ===')
for r in rows:
    if r['missing_en'] or r['missing_zh']:
        print('  %-46s' % r['key'])
        if r['missing_en']:
            print('        EN 缺: %s' % ', '.join(r['missing_en']))
        if r['missing_zh']:
            print('        ZH 缺: %s' % ', '.join(r['missing_zh']))
print()
print('=== 三个及以上部分 ===')
for r in rows:
    if r['n_parts'] > 2:
        print('  %-46s -> %s / %s' % (r['key'], r['en'], r['zh']))

print()
print('=== 前 40 条示例 ===')
for r in rows[:40]:
    print('  %-44s %-32s %s' % (r['key'], r['en'], r['zh']))

import json
json.dump(rows, open('gen_debug/compound_name_proposal.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

# characters that still reference these keys
with open('history/characters/zz_eu5_characters.txt', 'rb') as f:
    t = f.read().decode('utf-8-sig')
keys = set(r['key'] for r in rows)
used = collections.Counter()
for m in re.finditer(r'^\s*name\s*=\s*"([^"]*)"', t, re.M):
    v = m.group(1)
    if v in keys:
        used[v] += 1
print()
print('referenced by zz_eu5_characters.txt: %d distinct, %d occurrences' % (len(used), sum(used.values())))
unused = keys - set(used)
print('not referenced (dead keys): %d' % len(unused))
