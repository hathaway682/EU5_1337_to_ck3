# -*- coding: utf-8 -*-
"""
只读检查：mod 生成的王国级以上头衔（e_eu5_* / k_eu5_*）
        在 CK3 原版里是否有同名（中文）的王国/帝国头衔。
"""
import os, re, collections

CK3 = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"
MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"

LOC_RE = re.compile(r'^\s*([A-Za-z0-9_.\-]+)\s*:\s*(?:\d+\s*)?"(.*)"\s*$')

def parse_yml(path, out):
    raw = open(path, 'rb').read()
    if raw.startswith(b'\xef\xbb\xbf'):
        raw = raw[3:]
    for line in raw.decode('utf-8', 'replace').splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        m = LOC_RE.match(line)
        if m:
            out[m.group(1)] = m.group(2)

VAR_RE = re.compile(r'\$([A-Za-z0-9_]+)\$')
FMT_RE = re.compile(r'#[A-Za-z0-9_!]*')
def clean(n, table, d=0):
    if not n:
        return None
    if d < 4:
        n = VAR_RE.sub(lambda m: table.get(m.group(1), m.group(0)), n)
    return FMT_RE.sub('', n).replace('\\"', '"').strip()

# mod 头衔 key
TITLE_DEF = re.compile(r'^([ek])_eu5_([a-z0-9_]+)\s*=\s*\{')
mod_keys = []
for line in open(os.path.join(MOD, 'common', 'landed_titles', 'zz_eu5_titular.txt'), 'rb').read().decode('utf-8-sig', 'replace').splitlines():
    m = TITLE_DEF.match(line)
    if m:
        mod_keys.append((m.group(1), m.group(2), '%s_eu5_%s' % (m.group(1), m.group(2))))

# mod 本地化
mod_loc = {}
for fn in os.listdir(os.path.join(MOD, 'localization', 'simp_chinese')):
    if fn.endswith('.yml') and ('politics' in fn or 'eu5_titles' in fn):
        parse_yml(os.path.join(MOD, 'localization', 'simp_chinese', fn), mod_loc)

# CK3 原版 e_/k_ 头衔
ck3_keys = set()
root = os.path.join(CK3, 'common', 'landed_titles')
for fn in os.listdir(root):
    if fn.endswith('.txt'):
        for line in open(os.path.join(root, fn), 'rb').read().decode('utf-8', 'replace').splitlines():
            m = re.match(r'^\s*([ek]_[A-Za-z0-9_]+)\s*=\s*\{', line)
            if m:
                ck3_keys.add(m.group(1))

ck3_loc = {}
for dp, _, fns in os.walk(os.path.join(CK3, 'localization', 'simp_chinese')):
    for fn in fns:
        if fn.endswith('.yml'):
            parse_yml(os.path.join(dp, fn), ck3_loc)

ck3_name = {}
for k in ck3_keys:
    if k in ck3_loc:
        v = clean(ck3_loc[k], ck3_loc)
        if v:
            ck3_name.setdefault(v, []).append(k)

# 同时准备 d_ 级，用于标注「只对得上公国」
ck3_d = {}
root = os.path.join(CK3, 'common', 'landed_titles')
for fn in os.listdir(root):
    if fn.endswith('.txt'):
        for line in open(os.path.join(root, fn), 'rb').read().decode('utf-8', 'replace').splitlines():
            m = re.match(r'^\s*(d_[A-Za-z0-9_]+)\s*=\s*\{', line)
            if m and m.group(1) in ck3_loc:
                v = clean(ck3_loc[m.group(1)], ck3_loc)
                if v:
                    ck3_d.setdefault(v, []).append(m.group(1))

print('mod 王国以上头衔:', len(mod_keys))
print('  e_:', sum(1 for t in mod_keys if t[0] == 'e'), ' k_:', sum(1 for t in mod_keys if t[0] == 'k'))
print('CK3 原版 e_/k_ 头衔:', len(ck3_keys), ' 有中文名:', len(ck3_name))

no_loc = []
ok, only_d, none = [], [], []
for tier, tag, key in mod_keys:
    name = mod_loc.get(key)
    if name:
        name = clean(name, mod_loc)
    if not name:
        no_loc.append((tier, tag, key))
        continue
    if name in ck3_name:
        ok.append((tier, tag, key, name, ck3_name[name]))
    elif name in ck3_d:
        only_d.append((tier, tag, key, name, ck3_d[name]))
    else:
        none.append((tier, tag, key, name))

print('\n有原版同名 e_/k_ 头衔:', len(ok))
print('只对得上原版 d_（公国）:', len(only_d))
print('完全对不上:', len(none))
print('缺本地化:', len(no_loc))

print('\n===== 完全对不上 =====')
for tier, tag, key, name in sorted(none):
    print('%s\t%s\t%s' % (name, key, tier))

print('\n===== 只对得上公国级 =====')
for tier, tag, key, name, ds in sorted(only_d):
    print('%s\t%s\t%s\t%s' % (name, key, tier, '、'.join(ds)))

out = os.path.join(MOD, 'gen_debug', '_mod_high_titles_vs_vanilla.csv')
with open(out, 'w', encoding='utf-8-sig', newline='\r\n') as f:
    f.write('status,name,mod_title,tier,vanilla_titles\n')
    for tier, tag, key, name, vs in sorted(ok):
        f.write('ok,%s,%s,%s,%s\n' % (name, key, tier, '、'.join(sorted(vs))))
    for tier, tag, key, name, vs in sorted(only_d):
        f.write('only_duchy,%s,%s,%s,%s\n' % (name, key, tier, '、'.join(sorted(vs))))
    for tier, tag, key, name in sorted(none):
        f.write('none,%s,%s,%s,\n' % (name, key, tier))
    for tier, tag, key in sorted(no_loc):
        f.write('no_loc,,%s,%s,\n' % (key, tier))
print('\n写出:', out)
