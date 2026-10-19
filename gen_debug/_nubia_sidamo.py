# -*- coding: utf-8 -*-
"""只读：c_sidamo 与努比亚一带的 faith/rite。"""
import io, os, re, json
from collections import Counter

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
GEN = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_nubia_sidamo.out")
L = []

c2b = {}
for fn in sorted(os.listdir(os.path.join(MOD, "common/landed_titles"))):
    if not fn.endswith(".txt"):
        continue
    cur_c = cur_b = None
    for line in io.open(os.path.join(MOD, "common/landed_titles", fn), encoding="utf-8-sig", errors="ignore"):
        m = re.match(r"^(\t*)(c_[A-Za-z0-9_\-]+)\s*=\s*\{", line)
        if m:
            cur_c = m.group(2); cur_b = None; continue
        m = re.match(r"^(\t*)(b_[A-Za-z0-9_\-]+)\s*=\s*\{", line)
        if m:
            cur_b = m.group(2); continue
        pm = re.match(r"^\s*province\s*=\s*(\d+)", line)
        if pm and cur_c and cur_b:
            c2b.setdefault(cur_c, []).append((cur_b, int(pm.group(1)))); cur_b = None

hist = io.open(os.path.join(MOD, "history/provinces/00_generated_provinces.txt"), encoding="utf-8-sig").read()
prov = {}
for mm in re.finditer(r"(?m)^(\d+) = \{(.*?)\n\}", hist, re.S):
    f = re.search(r"(?m)^\s*faith\s*=\s*(\S+)", mm.group(2))
    r = re.search(r"(?m)^\s*rite\s*=\s*(\S+)", mm.group(2))
    prov[int(mm.group(1))] = (f.group(1) if f else None, r.group(1) if r else None)

pol = json.load(io.open(os.path.join(GEN, "eu5_politics.json"), encoding="utf-8"))
pe = json.load(io.open(os.path.join(GEN, "eu5_peoples.json"), encoding="utf-8"))
cr = pe["county_religion"]

mp = json.load(io.open(os.path.join(GEN, "mapping.json"), encoding="utf-8"))
# 努比亚王国 / 锡达莫 所属县
nub = {"c_" + l["county"] for l in mp["locations"]
       if l.get("kind") == "land" and l.get("kingdom") == "nubia"}

targets = ["c_sidamo"] + sorted(nub)
for c in targets:
    ps = c2b.get(c, [])
    if not ps:
        continue
    L.append("== %-22s owner=%-5s eu5rel=%-12s" % (c, pol["counties"].get(c, {}).get("owner"), cr.get(c)))
    for b, p in ps:
        L.append("   %-20s p%-6d faith=%-16s rite=%s" % (b, p, prov.get(p, (None, None))[0], prov.get(p, (None, None))[1]))
    L.append("   faith: %s | rite: %s" % (
        dict(Counter(prov.get(p, (None, None))[0] for _, p in ps)),
        dict(Counter(prov.get(p, (None, None))[1] for _, p in ps))))

io.open(OUT, "w", encoding="utf-8-sig", newline="\n").write("\n".join(L))
