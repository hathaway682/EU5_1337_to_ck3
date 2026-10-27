# -*- coding: utf-8 -*-
"""对 mod 高等级头衔中「原版 e_/k_ 无同名」的，在原版所有层级里找同名，标注层级"""
import os, re, csv, collections

CK3 = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"
MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
LOC_RE = re.compile(r'^\s*([A-Za-z0-9_.\-]+)\s*:\s*(?:\d+\s*)?"(.*)"\s*$')

def load(root):
    d = {}
    for dp, _, fns in os.walk(root):
        for fn in fns:
            if fn.endswith('.yml'):
                raw = open(os.path.join(dp, fn), 'rb').read()
                if raw.startswith(b'\xef\xbb\xbf'):
                    raw = raw[3:]
                for line in raw.decode('utf-8', 'replace').splitlines():
                    m = LOC_RE.match(line)
                    if m:
                        d[m.group(1)] = m.group(2)
    return d

loc = load(os.path.join(CK3, 'localization', 'simp_chinese'))
keys = set()
root = os.path.join(CK3, 'common', 'landed_titles')
for fn in os.listdir(root):
    if fn.endswith('.txt'):
        for line in open(os.path.join(root, fn), 'rb').read().decode('utf-8', 'replace').splitlines():
            m = re.match(r'^\s*([ekdcb]_[A-Za-z0-9_]+)\s*=\s*\{', line)
            if m:
                keys.add(m.group(1))

byname = collections.defaultdict(list)
for k in keys:
    v = loc.get(k)
    if v:
        byname[v].append(k)

rows = list(csv.DictReader(open(os.path.join(MOD, 'gen_debug', '_mod_high_titles_vs_vanilla.csv'), encoding='utf-8-sig')))
none = [r for r in rows if r['status'] == 'none']

print('%-16s %-12s %s' % ('名字', 'mod key', '原版同名（全部层级）'))
for r in sorted(none, key=lambda x: x['name']):
    n = r['name']
    hits = byname.get(n, [])
    print('%-16s %-12s %s' % (n, r['mod_title'], '、'.join(sorted(hits)) if hits else '—— 无'))
