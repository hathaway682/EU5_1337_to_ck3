# -*- coding: utf-8 -*-
import json, io, os, csv
GEN = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_two_counties.out")
pol = json.load(io.open(os.path.join(GEN, "eu5_politics.json"), encoding="utf-8"))
pe = json.load(io.open(os.path.join(GEN, "eu5_peoples.json"), encoding="utf-8"))
L = []
for c in ("c_tashir", "c_meskheti"):
    L.append("%s -> counties=%s  culture=%s  religion=%s" % (
        c, pol["counties"].get(c), pe["county_culture"].get(c), pe["county_religion"].get(c)))

# school map 里这两个县有没有记录
rows = [r for r in csv.DictReader(io.open(os.path.join(GEN, "_eu5_school_map.csv"), encoding="utf-8-sig"))
        if r["county"] in ("c_tashir", "c_meskheti")]
L.append("school_map 里这两个县的行数: %d" % len(rows))
for r in rows[:10]:
    L.append("   %s" % r)
io.open(OUT, "w", encoding="utf-8-sig", newline="\n").write("\n".join(L))
