# -*- coding: utf-8 -*-
"""只读：搜 mapping.json 里 levant / egypt / china / huaxi / syria / sichuan 相关层级键。"""
import json, io, os, re
from collections import Counter

GEN = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_geo_search.out")
L = []

m = json.load(io.open(os.path.join(GEN, "mapping.json"), encoding="utf-8"))
locs = m["locations"]

L.append("=== 全部 kingdom ===")
kv = Counter(l.get("kingdom") for l in locs if l.get("kingdom"))
L.append("  " + ", ".join(sorted(kv)))

for pat in ("levant", "egypt", "syria", "huaxi", "sichuan", "china", "anatol", "rum", "sham", "misr"):
    L.append("")
    L.append("=== 含 '%s' 的层级键 ===" % pat)
    hits = {}
    for key in ("hegemony", "empire", "kingdom", "duchy", "province"):
        vs = {l.get(key) for l in locs if l.get(key) and pat in str(l.get(key))}
        if vs:
            hits[key] = sorted(vs)
    for k, v in hits.items():
        L.append("  %-10s %s" % (k, v))

# 埃及 / 黎凡特 大概在哪个 kingdom
L.append("")
L.append("=== 按 location 名反查（cairo / alexandria / jerusalem / damascus / antioch）===")
for nm in ("cairo", "alexandria", "jerusalem", "damascus", "aleppo", "antioch", "tripoli", "gaza"):
    for l in locs:
        if l.get("name") == nm:
            L.append("  %-12s kingdom=%-12s duchy=%-16s province=%s"
                     % (nm, l.get("kingdom"), l.get("duchy"), l.get("province")))
            break

io.open(OUT, "w", encoding="utf-8-sig", newline="\n").write("\n".join(L))
