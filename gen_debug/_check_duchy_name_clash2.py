#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只读诊断：36 个同名公国，逐个看生成公国的 capital 县是否落在同名 de jure 公国领地内。"""
import re, os, collections

MOD = r"D:/Documents/Paradox Interactive/Crusader Kings III/mod/EU5_Modern_Borders_noshape"

def read(p):
    with open(p, "rb") as f:
        return f.read().decode("utf-8-sig", errors="replace")

def loc_map(path):
    d = {}
    for line in read(path).splitlines():
        m = re.match(r'\s*([A-Za-z0-9_.\-]+):\d*\s+"(.*)"\s*$', line)
        if m:
            d[m.group(1)] = m.group(2)
    return d

# ---- 解析 00_landed_titles.txt 层级：d_ -> [c_...]，并记录 c_ -> d_ ----
txt = read(os.path.join(MOD, "common/landed_titles/00_landed_titles.txt"))
stack = []           # [(depth, kind, key)]
duchy_counties = collections.defaultdict(list)
county_duchy = {}
for line in txt.splitlines():
    s = line.strip()
    m = re.match(r'^([a-z]_[A-Za-z0-9_]+)\s*=\s*\{', s)
    if m:
        key = m.group(1)
        depth = len(stack)
        stack.append((depth, key[0], key))
        continue
    if s.startswith("}"):
        if stack:
            stack.pop()
        continue
    if not stack:
        continue
    cur = [x for x in stack if x[1] == "c"]
    curd = [x for x in stack if x[1] == "d"]
    if cur and curd:
        county_duchy[cur[-1][2]] = curd[-1][2]
        if cur[-1][2] not in duchy_counties[curd[-1][2]]:
            duchy_counties[curd[-1][2]].append(cur[-1][2])

# ---- 生成公国 ----
gen_txt = read(os.path.join(MOD, "common/landed_titles/zz_eu5_titular.txt"))
gen = {}
for m in re.finditer(r'^(d_eu5_[A-Za-z0-9_]+)\s*=\s*\{(.*?)^\}', gen_txt, re.M | re.S):
    cap = re.search(r'capital\s*=\s*(c_[A-Za-z0-9_]+)', m.group(2))
    gen[m.group(1)] = cap.group(1) if cap else None

zh_t = loc_map(os.path.join(MOD, "localization/simp_chinese/eu5_titles_l_simp_chinese.yml"))
en_t = loc_map(os.path.join(MOD, "localization/english/eu5_titles_l_english.yml"))
en_t.update(loc_map(os.path.join(MOD, "localization/english/gen_titles_l_english.yml")))
zh_p = loc_map(os.path.join(MOD, "localization/simp_chinese/zz_eu5_politics_l_simp_chinese.yml"))
en_p = loc_map(os.path.join(MOD, "localization/english/zz_eu5_politics_l_english.yml"))
zh_c = loc_map(os.path.join(MOD, "localization/simp_chinese/eu5_titles_l_simp_chinese.yml"))

by_zh, by_en = collections.defaultdict(list), collections.defaultdict(list)
for k in duchy_counties:
    z, e = zh_t.get(k, ""), en_t.get(k, "")
    if z: by_zh[z].append(k)
    if e: by_en[e.lower()].append(k)

print(f"{'生成公国':22s} {'中文名':12s} {'capital':24s} {'同名地图公国':22s} 关系")
print("-" * 120)
n_same, n_diff = 0, 0
for k, cap in sorted(gen.items()):
    z, e = zh_p.get(k, ""), en_p.get(k, "")
    hit = []
    for x in by_zh.get(z, []):
        hit.append((x, "zh"))
    for x in by_en.get(e.lower(), []):
        if (x, "zh") not in hit:
            hit.append((x, "en"))
    if not hit:
        continue
    for x, why in hit:
        cd = county_duchy.get(cap)
        if cd == x:
            rel = "★ 同县：capital 就在该公国内"
            n_same += 1
        elif cd:
            rel = f"capital 属 {cd}({zh_t.get(cd,'')})"
            n_diff += 1
        else:
            rel = "capital 不在任何公国"
            n_diff += 1
        print(f"{k:22s} {z:12s} {str(cap):24s} {x:22s} [{why}] {rel}")

print(f"\ncapital 落在同名公国内: {n_same} ；落在别的公国: {n_diff}")
