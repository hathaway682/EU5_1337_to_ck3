#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只读：导出「生成的公国头衔 vs 地图 de jure 公国」同名清单 CSV。"""
import re, os, collections, csv

MOD = r"D:/Documents/Paradox Interactive/Crusader Kings III/mod/EU5_Modern_Borders_noshape"

def read(p):
    return open(p, "rb").read().decode("utf-8-sig", errors="replace")

def loc_map(path):
    d = {}
    for line in read(path).splitlines():
        m = re.match(r'\s*([A-Za-z0-9_.\-]+):\d*\s+"(.*)"\s*$', line)
        if m:
            d[m.group(1)] = m.group(2)
    return d

txt = read(os.path.join(MOD, "common/landed_titles/00_landed_titles.txt"))
stack, county_duchy, duchy_counties = [], {}, collections.defaultdict(list)
for line in txt.splitlines():
    s = line.strip()
    m = re.match(r'^([a-z]_[A-Za-z0-9_]+)\s*=\s*\{', s)
    if m:
        stack.append((len(stack), m.group(1)[0], m.group(1)))
        continue
    if s.startswith("}"):
        if stack: stack.pop()
        continue
    c = [x for x in stack if x[1] == "c"]
    dd = [x for x in stack if x[1] == "d"]
    if c and dd:
        county_duchy[c[-1][2]] = dd[-1][2]
        if c[-1][2] not in duchy_counties[dd[-1][2]]:
            duchy_counties[dd[-1][2]].append(c[-1][2])

gen_txt = read(os.path.join(MOD, "common/landed_titles/zz_eu5_titular.txt"))
gen = {}
for m in re.finditer(r'^(d_eu5_[A-Za-z0-9_]+)\s*=\s*\{(.*?)^\}', gen_txt, re.M | re.S):
    cap = re.search(r'capital\s*=\s*(c_[A-Za-z0-9_]+)', m.group(2))
    gen[m.group(1)] = cap.group(1) if cap else ""

zh_t = loc_map(os.path.join(MOD, "localization/simp_chinese/eu5_titles_l_simp_chinese.yml"))
en_t = loc_map(os.path.join(MOD, "localization/english/eu5_titles_l_english.yml"))
en_t.update(loc_map(os.path.join(MOD, "localization/english/gen_titles_l_english.yml")))
zh_p = loc_map(os.path.join(MOD, "localization/simp_chinese/zz_eu5_politics_l_simp_chinese.yml"))
en_p = loc_map(os.path.join(MOD, "localization/english/zz_eu5_politics_l_english.yml"))
held = set(m.group(1) for m in re.finditer(r'^(d_eu5_[a-z0-9_]+)\s*=\s*\{',
                                           read(os.path.join(MOD, "history/titles/zz_eu5_titles.txt")), re.M))

by_zh, by_en = collections.defaultdict(list), collections.defaultdict(list)
for k in duchy_counties:
    z, e = zh_t.get(k, ""), en_t.get(k, "")
    if z: by_zh[z].append(k)
    if e: by_en[e.lower()].append(k)

out = os.path.join(MOD, "gen_debug/duchy_name_clash.csv")
rows = []
for k, cap in sorted(gen.items()):
    z, e = zh_p.get(k, ""), en_p.get(k, "")
    hits = []
    for x in by_zh.get(z, []):
        hits.append((x, "中文同名"))
    for x in by_en.get(e.lower(), []):
        if not any(h[0] == x for h in hits):
            hits.append((x, "英文同名"))
    for x, why in hits:
        cd = county_duchy.get(cap)
        rel = "capital 就在该公国内" if cd == x else (f"capital 属 {cd}({zh_t.get(cd,'')})" if cd else "capital 不在任何公国")
        rows.append([k, z, e, cap, x, zh_t.get(x, ""), en_t.get(x, ""), why, rel,
                     "有" if k in held else "无", len(duchy_counties[x])])

with open(out, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["生成公国key", "中文名", "英文名", "capital", "同名地图公国", "地图公国中文名",
                "地图公国英文名", "匹配依据", "capital 归属", "生成公国开局有holder", "地图公国县数"])
    w.writerows(rows)
print(f"写出 {out}  {len(rows)} 行")
