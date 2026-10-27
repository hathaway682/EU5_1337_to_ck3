#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只读诊断：比对「我们生成的公国头衔」(d_eu5_*) 与「地图上 de jure 公国」(00_landed_titles.txt 的 d_*)
是否存在同名（中文名 / 英文名）。"""
import re, os, sys, collections

MOD = r"D:/Documents/Paradox Interactive/Crusader Kings III/mod/EU5_Modern_Borders_noshape"

def read(p):
    with open(p, "rb") as f:
        return f.read().decode("utf-8-sig", errors="replace")

def loc_map(path):
    """解析 yml:  key:0 "value"  -> {key: value}"""
    d = {}
    for line in read(path).splitlines():
        m = re.match(r'\s*([A-Za-z0-9_.\-]+):\d*\s+"(.*)"\s*$', line)
        if m:
            d[m.group(1)] = m.group(2)
    return d

def titles_in(path, prefix):
    txt = read(path)
    keys = []
    for m in re.finditer(r'^\s*(' + prefix + r'[A-Za-z0-9_]+)\s*=\s*\{', txt, re.M):
        keys.append(m.group(1))
    return keys

dejure = titles_in(os.path.join(MOD, "common/landed_titles/00_landed_titles.txt"), "d_")
gen    = titles_in(os.path.join(MOD, "common/landed_titles/zz_eu5_titular.txt"), "d_eu5_")
dejure = [k for k in dejure if not k.startswith("d_eu5_")]

zh_titles = loc_map(os.path.join(MOD, "localization/simp_chinese/eu5_titles_l_simp_chinese.yml"))
en_titles = loc_map(os.path.join(MOD, "localization/english/eu5_titles_l_english.yml"))
en_titles.update(loc_map(os.path.join(MOD, "localization/english/gen_titles_l_english.yml")))
zh_pol = loc_map(os.path.join(MOD, "localization/simp_chinese/zz_eu5_politics_l_simp_chinese.yml"))
en_pol = loc_map(os.path.join(MOD, "localization/english/zz_eu5_politics_l_english.yml"))

print(f"地图 de jure 公国: {len(dejure)}   生成公国 d_eu5_*: {len(gen)}")

def name_of(key, zh, en):
    return zh.get(key, ""), en.get(key, "")

# 建索引
by_zh = collections.defaultdict(list)
by_en = collections.defaultdict(list)
miss = []
for k in dejure:
    z, e = name_of(k, zh_titles, en_titles)
    if not z and not e:
        miss.append(k)
        continue
    if z: by_zh[z].append(k)
    if e: by_en[e.lower()].append(k)

print(f"地图公国缺名: {len(miss)} {miss[:5]}")

rows = []
gmiss = []
for k in gen:
    z, e = name_of(k, zh_pol, en_pol)
    if not z and not e:
        gmiss.append(k)
        continue
    hits_zh = [x for x in by_zh.get(z, []) if x != k]
    hits_en = [x for x in by_en.get(e.lower(), []) if x != k]
    if hits_zh or hits_en:
        rows.append((k, z, e, sorted(set(hits_zh + hits_en))))

print(f"生成公国缺名: {len(gmiss)} {gmiss[:5]}")
print(f"\n=== 与地图公国同名: {len(rows)} / {len(gen)} ===\n")
for k, z, e, hits in rows:
    hz = " | ".join(f"{h}({zh_titles.get(h,'')})" for h in hits)
    print(f"{k:20s} {z:10s} {e:28s} -> {hz}")

# 反向：地图公国内部也有重名
dup = {z: v for z, v in by_zh.items() if len(v) > 1}
print(f"\n地图公国内部同名(中文) {len(dup)} 组")
for z, v in list(dup.items())[:15]:
    print("  ", z, v)
