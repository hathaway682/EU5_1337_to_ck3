# -*- coding: utf-8 -*-
"""修复后的完整静态验证"""
import os, re, json

BASE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(BASE)

def read(p):
    return open(p, 'r', encoding='utf-8-sig').read()

houses_txt = read(os.path.join(MOD, 'common', 'dynasty_houses', 'zz_eu5_merged_houses.txt'))
dyn_txt = read(os.path.join(MOD, 'common', 'dynasties', 'zz_eu5_dynasties.txt'))
char_txt = read(os.path.join(MOD, 'history', 'characters', 'zz_eu5_characters.txt'))

print("=" * 70)
print("修复后静态验证")
print("=" * 70)

# 1. 非法语法
bad = [l for l in houses_txt.split('\n') if l.strip().startswith('l_')]
print(f"\n1. house 文件非法 l_ 行: {len(bad)}  {'OK' if not bad else bad}")

# 2. house 定义
houses = {}
for m in re.finditer(r'^(house_\w+)\s*=\s*\{([^}]*)\}', houses_txt, re.M):
    body = m.group(2)
    nm = re.search(r'name\s*=\s*"([^"]+)"', body)
    dy = re.search(r'dynasty\s*=\s*(\w+)', body)
    houses[m.group(1)] = {'name': nm.group(1) if nm else '', 'parent': dy.group(1) if dy else ''}
print(f"\n2. house 定义数: {len(houses)}  {'OK' if len(houses)==168 else 'EXPECT 168'}")

# 3. 有效 dynasty（未注释）
active_dyn = set(re.findall(r'^(\w+_dynasty)\s*=\s*\{', dyn_txt, re.M))
print(f"\n3. active dynasty 数: {len(active_dyn)}")

# 4. house parent 是否有效
bad_parent = [(h, d['parent']) for h, d in houses.items() if d['parent'] not in active_dyn]
print(f"\n4. house 的 parent 无效: {len(bad_parent)}")
for h, p in bad_parent[:10]:
    print(f"   {h} -> {p}")

# 5. 角色 dynasty_house 引用
dh_refs = re.findall(r'dynasty_house\s*=\s*(\w+)', char_txt)
dh_set = set(dh_refs)
print(f"\n5. 角色 dynasty_house 引用: {len(dh_refs)} 次 / {len(dh_set)} 个唯一")
undef = dh_set - set(houses)
print(f"   引用未定义的 house: {len(undef)}  {'OK' if not undef else sorted(undef)[:10]}")
unused = set(houses) - dh_set
print(f"   定义了但没角色用的 house: {len(unused)}  {sorted(unused)[:10] if unused else ''}")

# 6. 角色 dynasty 引用
d_refs = re.findall(r'(?<!_)dynasty\s*=\s*(\w+)', char_txt)
d_refs = [d for d in d_refs if not d.startswith('house_')]
d_set = set(d_refs)
print(f"\n6. 角色 dynasty 引用: {len(d_refs)} 次 / {len(d_set)} 个唯一")
undef_d = d_set - active_dyn
print(f"   引用未定义的 dynasty: {len(undef_d)}")
if undef_d:
    print(f"   {sorted(undef_d)[:10]}")

# 7. 旧的错误写法残留
old = len(re.findall(r'(?<!_)dynasty\s*=\s*house_', char_txt))
print(f"\n7. 残留 dynasty = house_ 旧写法: {old}  {'OK' if old==0 else 'ERROR'}")

# 8. 花括号
print(f"\n8. house 文件花括号: {{ {houses_txt.count('{')} }} {houses_txt.count('}')}  "
      f"{'OK' if houses_txt.count('{')==houses_txt.count('}') else 'MISMATCH'}")

# 9. BOM / 编码
for f, p in [('houses', os.path.join(MOD,'common','dynasty_houses','zz_eu5_merged_houses.txt')),
             ('chars', os.path.join(MOD,'history','characters','zz_eu5_characters.txt'))]:
    raw = open(p,'rb').read()
    print(f"\n9.{f} BOM={raw[:3]==b'\\xef\\xbb\\xbf'}  CRLF={raw.count(b'\\r\\n')}  LF={raw.count(b'\\n')}")

print("\n" + "=" * 70)
ok = (not bad) and len(houses)==168 and not bad_parent and not undef and old==0
print("RESULT:", "ALL OK" if ok else "HAS ISSUES")
print("=" * 70)
