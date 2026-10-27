# -*- coding: utf-8 -*-
"""
mod 的 EU5 王国以上头衔（e_eu5_* / k_eu5_*）与原版 CK3 头衔的对应情况
原版侧分三档：h_/e_/k_（王国以上）、d_（公国）、c_/b_（更低）
"""
import os, re, collections

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

VAR_RE = re.compile(r'\$([A-Za-z0-9_]+)\$')
FMT_RE = re.compile(r'#[A-Za-z0-9_!]*')
def clean(n, t, d=0):
    if not n:
        return None
    if d < 4:
        n = VAR_RE.sub(lambda m: t.get(m.group(1), m.group(0)), n)
    return FMT_RE.sub('', n).replace('\\"', '"').strip()

loc = load(os.path.join(CK3, 'localization', 'simp_chinese'))
tiers = collections.defaultdict(lambda: collections.defaultdict(list))
root = os.path.join(CK3, 'common', 'landed_titles')
for fn in os.listdir(root):
    if not fn.endswith('.txt'):
        continue
    for line in open(os.path.join(root, fn), 'rb').read().decode('utf-8', 'replace').splitlines():
        m = re.match(r'^\s*([hekdcb]_[A-Za-z0-9_]+)\s*=\s*\{', line)
        if not m:
            continue
        k = m.group(1)
        v = loc.get(k)
        if not v:
            continue
        v = clean(v, loc)
        if not v:
            continue
        g = 'high' if k[0] in 'hek' else ('d' if k[0] == 'd' else 'low')
        tiers[g][v].append(k)

# mod 侧
modloc = {}
for fn in os.listdir(os.path.join(MOD, 'localization', 'simp_chinese')):
    if fn.endswith('.yml'):
        raw = open(os.path.join(MOD, 'localization', 'simp_chinese', fn), 'rb').read()
        if raw.startswith(b'\xef\xbb\xbf'):
            raw = raw[3:]
        for line in raw.decode('utf-8', 'replace').splitlines():
            m = LOC_RE.match(line)
            if m:
                modloc[m.group(1)] = m.group(2)

keys = []
for line in open(os.path.join(MOD, 'common', 'landed_titles', 'zz_eu5_titular.txt'), 'rb').read().decode('utf-8-sig', 'replace').splitlines():
    m = re.match(r'^([ek])_eu5_([a-z0-9_]+)\s*=\s*\{', line)
    if m:
        keys.append('%s_eu5_%s' % (m.group(1), m.group(2)))

A, B, C, D, E = [], [], [], [], []   # 严格同名 / 仅差后缀(手工) / 仅公国 / 仅更低 / 完全没有
SUFFIX = {
    'e_eu5_byz': ('拜占庭', 'e_byzantium「拜占庭帝国」'),
    'e_eu5_ogk': ('神圣罗马', 'e_hre「神圣罗马帝国」'),
    'e_eu5_yua': ('元', 'e_great_yuan「大元帝国」'),
    'k_eu5_val': ('巴伦西亚', 'k_valencia「瓦伦西亚」'),
    'k_eu5_jmb': ('末罗瑜', 'k_malayadvipa「末罗瑜洲」'),
    'e_eu5_eth': ('埃塞俄比亚', 'e_abyssinia「阿比西尼亚」'),
    'k_eu5_mor': ('摩洛哥', 'k_maghreb「马格里布」'),
    'k_eu5_kor': ('高丽', 'e_goryeo「三韩」'),
    'e_eu5_ymt': ('大和', 'k_yamato「大和」（原版是王国级）'),
    'e_eu5_khm': ('高棉', 'e_kambuja「甘孛智」'),
}
for k in keys:
    n = clean(modloc.get(k), modloc)
    if not n:
        print('缺本地化', k)
        continue
    if n in tiers['high']:
        A.append((n, k, '、'.join(sorted(tiers['high'][n]))))
    elif k in SUFFIX:
        B.append((n, k, SUFFIX[k][1]))
    elif n in tiers['d']:
        C.append((n, k, '、'.join(sorted(tiers['d'][n]))))
    elif n in tiers['low']:
        D.append((n, k, '、'.join(sorted(tiers['low'][n]))))
    else:
        E.append((n, k, ''))

print('EU5 王国以上头衔:', len(keys))
print('A 原版同名(h/e/k):', len(A))
print('B 同实体但名字不同(人工):', len(B))
print('C 仅公国级同名:', len(C))
print('D 仅伯爵/男爵级同名:', len(D))
print('E 原版完全没有:', len(E))
print()
for label, arr in [('B 同实体但名字不同', B), ('C 仅公国级', C), ('D 仅伯爵/男爵级', D), ('E 完全没有', E)]:
    print('===== %s (%d) =====' % (label, len(arr)))
    for n, k, v in sorted(arr):
        print('%-14s %-12s %s' % (n, k, v))
    print()

import csv
out = os.path.join(MOD, 'gen_debug', '_mod_eu5_high_titles_coverage.csv')
with open(out, 'w', encoding='utf-8-sig', newline='\r\n') as f:
    f.write('status,name,mod_title,vanilla\n')
    for tag, arr in [('same', A), ('renamed', B), ('only_duchy', C), ('only_lower', D), ('none', E)]:
        for n, k, v in sorted(arr):
            f.write('%s,%s,%s,%s\n' % (tag, n, k, v))
print('写出:', out)
