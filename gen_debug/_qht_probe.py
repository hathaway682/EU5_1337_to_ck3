# -*- coding: utf-8 -*-
"""只读：QHT/YAM 名下县是否都在 north_yemen，以及 c_balor/c_hunza/c_qusiyya 的地理归属。"""
import io, os, json
from collections import Counter
GEN = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_qht_probe.out")
L = []
mp = json.load(io.open(os.path.join(GEN, "mapping.json"), encoding="utf-8"))
locs = mp["locations"]
pol = json.load(io.open(os.path.join(GEN, "eu5_politics.json"), encoding="utf-8"))
pe = json.load(io.open(os.path.join(GEN, "eu5_peoples.json"), encoding="utf-8"))
cr = pe["county_religion"]

# county -> 它落在哪些 duchy
c_duchy = {}
for l in locs:
    if l.get("kind") == "land":
        c_duchy.setdefault("c_" + l["county"], set()).add(l.get("duchy"))

for tag in ("QHT", "YAM"):
    cs = [c for c, i in pol["counties"].items() if i.get("owner") == tag]
    L.append("%s 名下 %d 个县:" % (tag, len(cs)))
    for c in sorted(cs):
        L.append("   %-20s eu5rel=%-8s duchy=%s" % (c, cr.get(c), ",".join(sorted(x for x in c_duchy.get(c, ()) if x))))

L.append("")
for c in ("c_balor", "c_hunza", "c_qusiyya"):
    L.append("%-12s owner=%-4s eu5rel=%-8s duchy=%s" % (
        c, pol["counties"].get(c, {}).get("owner"), cr.get(c),
        ",".join(sorted(x for x in c_duchy.get(c, ()) if x))))
io.open(OUT, "w", encoding="utf-8-sig", newline="\n").write("\n".join(L))
