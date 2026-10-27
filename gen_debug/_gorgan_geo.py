# -*- coding: utf-8 -*-
import io, os, json
GEN = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_gorgan_geo.out")
mp = json.load(io.open(os.path.join(GEN, "mapping.json"), encoding="utf-8"))
L = []
for l in mp["locations"]:
    if l.get("kind") == "land" and l.get("county") == "gorgan":
        L.append("%-14s kingdom=%-10s duchy=%-12s province=%s"
                 % (l.get("name"), l.get("kingdom"), l.get("duchy"), l.get("province")))
io.open(OUT, "w", encoding="utf-8-sig", newline="\n").write("\n".join(L))
