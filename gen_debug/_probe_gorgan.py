# -*- coding: utf-8 -*-
"""只读探查：戈尔甘 province 的县 / 宗教 / 当前 faith。"""
import json, io, os, re
from collections import Counter

GEN = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_gorgan_probe.out")

m = json.load(io.open(os.path.join(GEN, "mapping.json"), encoding="utf-8"))
locs = m["locations"]
pe = json.load(io.open(os.path.join(GEN, "eu5_peoples.json"), encoding="utf-8"))
cr = pe["county_religion"]
pol = json.load(io.open(os.path.join(GEN, "eu5_politics.json"), encoding="utf-8"))
counties = pol["counties"]

L = []
gor = [l for l in locs if l.get("province") == "gorgan_province" and l.get("kind") == "land"]
L.append("gorgan_province 的 land location 数: %d" % len(gor))
cs = sorted({"c_" + l["county"] for l in gor})
L.append("涉及县 (%d): %s" % (len(cs), ", ".join(cs)))
for c in cs:
    L.append("   %-22s county_religion=%-10s owner=%s"
             % (c, cr.get(c), counties.get(c, {}).get("owner")))

# 当前 province history 里的 faith / rite
hist = io.open(os.path.join(MOD, "history/provinces/00_generated_provinces.txt"),
               encoding="utf-8-sig").read()
prov = {}
for mm in re.finditer(r"(?m)^(\d+) = \{(.*?)\n\}", hist, re.S):
    body = mm.group(2)
    f = re.search(r"(?m)^\s*faith\s*=\s*(\S+)", body)
    r = re.search(r"(?m)^\s*rite\s*=\s*(\S+)", body)
    prov[int(mm.group(1))] = (f.group(1) if f else None, r.group(1) if r else None)

# county -> province
c2ps = {}
lt = os.path.join(MOD, "common/landed_titles")
for fn in os.listdir(lt):
    stack = []
    for line in io.open(os.path.join(lt, fn), encoding="utf-8-sig", errors="ignore"):
        mm = re.match(r"^\t*([cedkb]_[A-Za-z0-9_\-]+)\s*=\s*\{", line)
        if mm:
            ind = len(line) - len(line.lstrip("\t"))
            stack = [k for k in stack if k[1] < ind]
            stack.append((mm.group(1), ind))
            continue
        pm = re.match(r"^\s*province\s*=\s*(\d+)", line)
        if pm and stack and stack[-1][0].startswith("b_"):
            cc = [k for k, _ in stack if k.startswith("c_")]
            if cc:
                c2ps.setdefault(cc[-1], []).append(int(pm.group(1)))

L.append("")
L.append("戈尔甘各县当前 province 状态:")
for c in cs:
    for p in c2ps.get(c, []):
        L.append("   %-22s p%-6d faith=%-14s rite=%s" % (c, p, prov.get(p, (None, None))[0], prov.get(p, (None, None))[1]))

# 全局 ismaili 分布
L.append("")
L.append("当前 ismaili province 数: %d" % sum(1 for v in prov.values() if v[1] == "ismaili"))
for c in sorted({k for k in c2ps}):
    ps = c2ps[c]
    if any(prov.get(p, (0, 0))[1] == "ismaili" for p in ps):
        L.append("   ismaili 县: %-24s faith=%s" % (c, prov.get(ps[0], (None, None))[0]))

# 呼罗珊 / quhestan 规模
kh = {"c_" + l["county"] for l in locs if l.get("kind") == "land" and l.get("kingdom") == "khorasan"}
qu = {"c_" + l["county"] for l in locs if l.get("kind") == "land" and l.get("duchy") == "quhestan"}
L.append("")
L.append("khorasan 县 %d 个（其中 shia %d）" % (len(kh), sum(1 for c in kh if cr.get(c) == "shia")))
L.append("quhestan 县 %d 个（其中 shia %d）" % (len(qu), sum(1 for c in qu if cr.get(c) == "shia")))
L.append("gorgan 县 %d 个（其中 shia %d）" % (len(cs), sum(1 for c in cs if cr.get(c) == "shia")))

io.open(OUT, "w", encoding="utf-8-sig", newline="\n").write("\n".join(L))
