# -*- coding: utf-8 -*-
"""只读：mapping.json 的 location 字段结构 + 可用地理层级键。"""
import json, io, os
from collections import Counter

GEN = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_geo_fields.out")
L = []

m = json.load(io.open(os.path.join(GEN, "mapping.json"), encoding="utf-8"))
locs = m["locations"]
L.append("顶层键: %s" % list(m.keys()))
L.append("locations: %d" % len(locs))
L.append("单个 location 的字段: %s" % list(locs[0].keys()))
L.append("")
for k, v in locs[0].items():
    L.append("   %-12s = %s" % (k, str(v)[:120]))

# 各层级取值样例
for key in ("region", "area", "kingdom", "duchy", "province"):
    vals = Counter(l.get(key) for l in locs if l.get(key))
    L.append("")
    L.append("%s: %d 种" % (key, len(vals)))
    for v, n in vals.most_common(40):
        L.append("   %-34s %d" % (v, n))

io.open(OUT, "w", encoding="utf-8-sig", newline="\n").write("\n".join(L))
