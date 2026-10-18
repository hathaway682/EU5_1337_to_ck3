# -*- coding: utf-8 -*-
"""Build the missing-part vocabulary for the 154 compound ruler-name keys.

Sources consulted, in order:
  1. `name_*`  keys in zz_eu5_politics_l_<lang>.yml  (EU5 person names)
  2. `cul_*`   keys in gen_cultures_l_<lang>.yml      (EU5 culture/name-list names)
Only unfound parts need hand translation.
"""
import re, os, json, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

LANGS = ['braz_por', 'english', 'french', 'german', 'japanese', 'korean',
         'polish', 'russian', 'simp_chinese', 'spanish', 'turkish']


def load(path):
    d = {}
    try:
        with open(path, 'rb') as f:
            lines = f.read().decode('utf-8-sig').splitlines()
    except FileNotFoundError:
        return d
    for ln in lines:
        m = re.match(r'^\s*([A-Za-z0-9_.\-]+):\d*\s+"(.*)"\s*$', ln)
        if m:
            d.setdefault(m.group(1), m.group(2))
    return d


locs = {}
for l in LANGS:
    d = load('localization/%s/zz_eu5_politics_l_%s.yml' % (l, l))
    d.update(load('localization/%s/gen_cultures_l_%s.yml' % (l, l)))
    locs[l] = d


def find(lang, part):
    """name_mongke -> try name_mongke, then cul_mongke."""
    if part in locs[lang]:
        return locs[lang][part]
    if part.startswith('name_'):
        alt = 'cul_' + part[len('name_'):]
        if alt in locs[lang]:
            return locs[lang][alt]
    return None

en = locs['english']
zh = locs['simp_chinese']

compound = sorted(k for k in en if '.' in k and k.startswith('name_'))
print('compound keys: %d' % len(compound))

missing = collections.defaultdict(list)   # lang -> [part keys]
for k in compound:
    for p in k.split('.'):
        for lang in LANGS:
            if find(lang, p) is None:
                missing[lang].append(p)

for lang in LANGS:
    mp = sorted(set(missing[lang]))
    print('%-13s missing parts: %3d' % (lang, len(mp)))
    if lang in ('english', 'simp_chinese'):
        for p in mp:
            print('      %s' % p)

json.dump({l: sorted(set(v)) for l, v in missing.items()},
          open('gen_debug/compound_missing_parts.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
json.dump(compound, open('gen_debug/compound_keys.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
