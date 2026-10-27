# -*- coding: utf-8 -*-
"""对「完全对不上」的 mod 高等级头衔，在原版 e_/k_ 名字里找近似候选（子串包含）"""
import os, re, csv, collections

CK3 = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"
MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"

LOC_RE = re.compile(r'^\s*([A-Za-z0-9_.\-]+)\s*:\s*(?:\d+\s*)?"(.*)"\s*$')

def load(root):
    d = {}
    for dp, _, fns in os.walk(root):
        for fn in fns:
            if not fn.endswith('.yml'):
                continue
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
            m = re.match(r'^\s*([ek]_[A-Za-z0-9_]+)\s*=\s*\{', line)
            if m:
                keys.add(m.group(1))
names = collections.defaultdict(list)
for k in keys:
    v = loc.get(k)
    if v:
        names[v].append(k)

rows = list(csv.DictReader(open(os.path.join(MOD, 'gen_debug', '_mod_high_titles_vs_vanilla.csv'), encoding='utf-8-sig')))
none = [r for r in rows if r['status'] == 'none']
print('待查:', len(none))
for r in none:
    n = r['name']
    cands = []
    for v, ks in names.items():
        if n == v:
            continue
        if n in v or v in n:
            cands.append('%s=%s' % (v, '/'.join(ks)))
    print('%-14s %-12s %s' % (n, r['mod_title'], ' | '.join(cands) if cands else '—'))
