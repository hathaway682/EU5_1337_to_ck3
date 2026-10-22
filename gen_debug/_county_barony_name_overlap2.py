#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统计「伯爵领名 与 非首府男爵领名 同名/被包含」的县。

CK3 规则: 伯爵领块内第一个 b_ 是首府。
名字来源: 原版 localization + mod localization(simp_chinese / english)。
输出 gen_debug/_county_barony_name_overlap2.json（喂给 ck3-mapviz 的 spec 用）。
"""
import os, re, json

MOD = r"D:/Documents/Paradox Interactive/Crusader Kings III/mod/EU5_Modern_Borders_noshape"
VAN = r"E:/SteamLibrary/steamapps/common/Crusader Kings III/game/localization"
LT_DIR = os.path.join(MOD, "common", "landed_titles")

TITLE_RE = re.compile(r'^\s*([bdkec])_([a-z0-9_]+)\s*=\s*\{')

# 1. county -> 有序 barony 列表 + 祖先链
counties = {}
stack = []
for fn in sorted(os.listdir(LT_DIR)):
    if '.bak_' in fn:
        continue
    path = os.path.join(LT_DIR, fn)
    if not os.path.isfile(path):
        continue
    for line in open(path, 'r', encoding='utf-8-sig', errors='replace'):
        m = TITLE_RE.match(line)
        if m:
            tier, full = m.group(1), f"{m.group(1)}_{m.group(2)}"
            stack.append((tier, full))
            if tier == 'c':
                counties[full] = {"baronies": [], "ancestors": [k for t, k in stack[:-1]]}
            elif tier == 'b' and len(stack) >= 2 and stack[-2][0] == 'c':
                counties[stack[-2][1]]["baronies"].append(full)
            continue
        if stack and line.strip() == '}':
            stack.pop()

# 2. 本地化
def load_loc(path):
    out = {}
    for line in open(path, 'r', encoding='utf-8-sig', errors='replace'):
        m = re.match(r'^\s*([a-z]+_[A-Za-z0-9_]+):\d*\s*"(.*)"\s*$', line)
        if m:
            out[m.group(1)] = m.group(2)
    return out

loc = {"simp_chinese": {}, "english": {}}
for lang, f in (("simp_chinese", "titles_l_simp_chinese.yml"),
                ("english", "titles_l_english.yml")):
    p = os.path.join(VAN, lang, f)
    if os.path.exists(p):
        loc[lang].update(load_loc(p))
for lang, f in (("simp_chinese", "eu5_titles_l_simp_chinese.yml"),
                ("english", "eu5_titles_l_english.yml")):
    p = os.path.join(MOD, "localization", lang, f)
    if os.path.exists(p):
        loc[lang].update(load_loc(p))

def nm(key, lang):
    return loc[lang].get(key)

# 3. 匹配（中文名优先，英文名作对照）
MIN_LEN = 2
rows = []
for ck, info in counties.items():
    bs = info["baronies"]
    if not bs:
        continue
    cap = bs[0]
    czh, cen = nm(ck, "simp_chinese"), nm(ck, "english")
    for b in bs[1:]:
        bzh, ben = nm(b, "simp_chinese"), nm(b, "english")
        base, bb = czh or cen, bzh or ben
        hit_zh = None
        if base and bb:
            if base == bb:
                hit_zh = "same"
            elif len(bb) >= MIN_LEN and bb in base:
                hit_zh = "contains"
        hit_en = None
        if cen and ben:
            if cen == ben:
                hit_en = "same"
            elif len(ben) >= 3 and ben in cen:
                hit_en = "contains"
        if hit_zh or hit_en:
            anc = info["ancestors"]
            rows.append({
                "county": ck, "county_zh": czh or "", "county_en": cen or "",
                "barony": b, "barony_zh": bzh or "", "barony_en": ben or "",
                "capital": cap,
                "capital_zh": nm(cap, "simp_chinese") or "",
                "capital_en": nm(cap, "english") or "",
                "kingdom": next((k for k in anc if k.startswith("k_")), ""),
                "empire": next((k for k in anc if k.startswith("e_")), ""),
                "duchy": anc[-1] if anc else "",
                "hit_zh": hit_zh, "hit_en": hit_en,
                "n_baronies": len(bs),
            })

zh = [r for r in rows if r["hit_zh"]]
print("counties:", len(counties), "with baronies:", sum(1 for v in counties.values() if v["baronies"]))
print("zh hits:", len(zh), " (same", sum(1 for r in zh if r["hit_zh"] == "same"),
      "/ contains", sum(1 for r in zh if r["hit_zh"] == "contains"),
      ") distinct counties:", len({r["county"] for r in zh}))
print("en-only extra:", len([r for r in rows if not r["hit_zh"] and r["hit_en"]]))

out = os.path.join(MOD, "gen_debug", "_county_barony_name_overlap2.json")
json.dump({"rows": rows}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print("written:", out)
