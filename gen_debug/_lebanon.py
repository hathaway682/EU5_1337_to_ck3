# -*- coding: utf-8 -*-
import io, os, re, json
MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
GEN = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lebanon.out")
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
L.append("c_lebanon owner=%s eu5rel=%s" % (pol["counties"].get("c_lebanon", {}).get("owner"),
                                           pe["county_religion"].get("c_lebanon")))
for b, p in c2b.get("c_lebanon", []):
    L.append("   %-18s p%-6d faith=%-14s rite=%s" % (b, p, prov.get(p, (None, None))[0], prov.get(p, (None, None))[1]))
io.open(OUT, "w", encoding="utf-8-sig", newline="\n").write("\n".join(L))
