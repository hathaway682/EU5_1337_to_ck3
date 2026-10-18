# -*- coding: utf-8 -*-
"""
补齐人名本地化 —— dry run

坏键 1382 个：
  · 1300 个 "X Regent"（摄政占位角色，名字应为地名）
  · 82 个亲属/家族描述（如 byz apokauka、jap ashikaga takayoshi no musume）

做法：生成 name_eu5_<slug> 新 key，改角色 name 字段，补英中本地化。
中文来源：vanilla + mod 的 titles 本地化（英文地名 -> 中文地名）
"""
import os, re, json, unicodedata
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(BASE)
VAN = r"E:/SteamLibrary/steamapps/common/Crusader Kings III/game/localization"

def load_dir(d):
    out = {}
    if not os.path.isdir(d):
        return out
    for root, _, fs in os.walk(d):
        for fn in fs:
            if not fn.endswith('.yml'):
                continue
            try:
                t = open(os.path.join(root, fn), 'r', encoding='utf-8-sig').read()
            except Exception:
                continue
            for m in re.finditer(r'^\s*([A-Za-z0-9_\.\-]+):\d*\s*"([^"]*)"', t, re.M):
                out.setdefault(m.group(1), m.group(2))
    return out

en = load_dir(os.path.join(VAN, 'english'))
en.update(load_dir(os.path.join(MOD, 'localization', 'english')))
zh = load_dir(os.path.join(VAN, 'simp_chinese'))
zh.update(load_dir(os.path.join(MOD, 'localization', 'simp_chinese')))

# 英文名 -> 中文名（只用 titles 类，避免人名/事件名干扰）
en2zh = {}
for k, v in en.items():
    if k in zh and v:
        en2zh.setdefault(v.strip().lower(), zh[k])

# 也用 b_<slug> 直接查
def zh_by_slug(slug):
    for pref in ('b_', 'c_', 'd_', 'k_', 'e_'):
        k = pref + slug
        if k in zh and k in en:
            return zh[k]
    return ''

def strip_acc(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def slugify(s):
    s = strip_acc(s).lower()
    s = re.sub(r"[^a-z0-9]+", '_', s).strip('_')
    return s or 'x'

FILES = ['history/characters/zz_eu5_characters.txt',
         'history/characters/zz_eu5_regents.txt']

bad = {}
for f in FILES:
    p = os.path.join(MOD, f)
    if not os.path.exists(p):
        continue
    s = open(p, 'r', encoding='utf-8-sig').read()
    for n in re.findall(r'^\s*name\s*=\s*"([^"]*)"', s, re.M):
        if n not in en:
            bad.setdefault(n, []).append(f)

print(f"唯一坏键: {len(bad)}")
reg = {k: v for k, v in bad.items() if k.lower().endswith(' regent')}
oth = {k: v for k, v in bad.items() if not k.lower().endswith(' regent')}
print(f"  Regent 类: {len(reg)}")
print(f"  其他    : {len(oth)}")

# 生成映射
mapping = {}
slug_used = {}
conflict = []
for k in sorted(bad):
    if k.lower().endswith(' regent'):
        place = k[:-len(' Regent')].strip()
        sl = slugify(place)
        key = 'name_eu5_' + sl
        zhv = en2zh.get(place.strip().lower(), '') or zh_by_slug(sl)
        mapping[k] = {'key': key, 'en': place, 'zh': zhv or place, 'kind': 'regent'}
    else:
        sl = slugify(k)
        key = 'name_eu5_' + sl
        mapping[k] = {'key': key, 'en': k, 'zh': '', 'kind': 'other'}
    if key in slug_used and slug_used[key] != k:
        conflict.append((key, slug_used[key], k))
    slug_used[key] = k

print(f"\n生成 key: {len(mapping)}  冲突: {len(conflict)}")
for c in conflict[:10]:
    print('  冲突:', c)

# 统计
reg_m = [v for v in mapping.values() if v['kind'] == 'regent']
zh_hit = sum(1 for v in reg_m if v['zh'] != v['en'])
print(f"\nRegent 中文命中: {zh_hit}/{len(reg_m)}  未命中 {len(reg_m)-zh_hit}")
print("\n=== Regent 样例 ===")
for v in reg_m[:8]:
    print(f"  {v['key']:<32} en={v['en']:<22} zh={v['zh']}")
print("\n=== 未命中样例 ===")
miss = [v for v in reg_m if v['zh'] == v['en']]
for v in miss[:15]:
    print(f"  {v['key']:<32} {v['en']}")

json.dump(mapping, open(os.path.join(BASE, 'name_loc_mapping.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print(f"\n写入 name_loc_mapping.json")
