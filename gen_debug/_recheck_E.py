# -*- coding: utf-8 -*-
"""复核 E 类：这些名字在 CK3 全部本地化里是否有对应 key（含文化名 cn_*）"""
import os, re, csv, collections

CK3 = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"
MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
LOC_RE = re.compile(r'^\s*([A-Za-z0-9_.\-]+)\s*:\s*(?:\d+\s*)?"(.*)"\s*$')

# 1. 加载本地化
val2key = collections.defaultdict(list)
for dp, _, fns in os.walk(os.path.join(CK3, 'localization', 'simp_chinese')):
    for fn in fns:
        if not fn.endswith('.yml'):
            continue
        raw = open(os.path.join(dp, fn), 'rb').read()
        if raw.startswith(b'\xef\xbb\xbf'):
            raw = raw[3:]
        for line in raw.decode('utf-8', 'replace').splitlines():
            m = LOC_RE.match(line)
            if m:
                val2key[m.group(2).strip()].append(m.group(1))

# 2. 头衔定义行 + cn_ 绑定
title_lines = []   # (lineno, key, indent)
cn_bind = {}       # cn_key -> [(title_key)]
root = os.path.join(CK3, 'common', 'landed_titles')
for fn in os.listdir(root):
    if not fn.endswith('.txt'):
        continue
    lines = open(os.path.join(root, fn), 'rb').read().decode('utf-8', 'replace').splitlines()
    stack = []
    for i, line in enumerate(lines):
        m = re.match(r'^(\s*)([hekdcb]_[A-Za-z0-9_]+)\s*=\s*\{', line)
        if m:
            stack.append((len(m.group(1)), m.group(2)))
            continue
        m2 = re.search(r'name_list_\w+\s*=\s*(cn_[A-Za-z0-9_]+)', line)
        if m2 and stack:
            cn_bind.setdefault(m2.group(1), []).append(stack[-1][1])

# 3. E 类名字
rows = list(csv.DictReader(open(os.path.join(MOD, 'gen_debug', '_mod_eu5_high_titles_coverage_1337.csv'), encoding='utf-8-sig')))
E = [r for r in rows if r['status'] == 'none']

print('%-14s %-12s %s' % ('名字', 'mod', 'CK3 本地化命中'))
for r in sorted(E, key=lambda x: x['name']):
    n = r['name']
    ks = val2key.get(n, [])
    info = []
    for k in ks:
        if k.startswith('cn_'):
            t = cn_bind.get(k, [])
            info.append('%s(文化名→%s)' % (k, '/'.join(sorted(set(t))) or '未绑定'))
        else:
            info.append(k)
    print('%-14s %-12s %s' % (n, r['mod_title'], '、'.join(info) if info else '——'))
