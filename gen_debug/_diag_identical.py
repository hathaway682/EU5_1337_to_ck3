# -*- coding: utf-8 -*-
"""Break down identical en/zh entries by kind. ASCII output."""
import json, re, os, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

def load(p):
    with open(p, 'rb') as f:
        t = f.read().decode('utf-8-sig')
    d = {}
    for ln in t.splitlines()[1:]:
        m = re.match(r'^\s*([A-Za-z0-9_.\-]+):\d*\s+"(.*)"\s*$', ln)
        if m:
            d[m.group(1)] = m.group(2)
    return d

en = load('localization/english/zz_eu5_names_l_english.yml')
zh = load('localization/simp_chinese/zz_eu5_names_l_simp_chinese.yml')

mapping = json.load(open('gen_debug/name_loc_mapping.json', encoding='utf-8'))
# mapping: {orig_key: {key, en, zh, kind}}
kind_of = {}
for v in mapping.values():
    kind_of[v['key']] = v.get('kind', '?')

same = [k for k in en if zh.get(k) == en[k]]
cnt = collections.Counter(kind_of.get(k, 'unknown') for k in same)
print('identical en==zh total: %d' % len(same))
for k, n in cnt.most_common():
    print('  kind=%-10s %d' % (k, n))
print()
print('non-regent identical examples:')
shown = 0
for k in same:
    if kind_of.get(k) != 'regent':
        print('  %-40s %s' % (k, en[k]))
        shown += 1
        if shown >= 30:
            break

# also: how many zh values are pure ASCII (i.e. no CJK at all)
cjk = re.compile(r'[\u4e00-\u9fff]')
no_cjk = [k for k in zh if not cjk.search(zh[k])]
print()
print('zh values with no CJK at all: %d / %d' % (len(no_cjk), len(zh)))
print('  examples: %s' % [zh[k] for k in no_cjk[:12]])
