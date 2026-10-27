# -*- coding: utf-8 -*-
"""只读：现在 15 个 ismaili 省分别是哪些县 / 谁的 / EU5 县宗教是什么。"""
import io, os, re, json
from collections import Counter

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
GEN = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_ismaili_detail.out")
L = []

pol = json.load(io.open(os.path.join(GEN, "eu5_politics.json"), encoding="utf-8"))
pe = json.load(io.open(os.path.join(GEN, "eu5_peoples.json"), encoding="utf-8"))
cr = pe["county_religion"]

c2ps = {}
for fn in os.listdir(os.path.join(MOD, "common/landed_titles")):
    if not fn.endswith(".txt"):
        continue
    stack = []
    for line in io.open(os.path.join(MOD, "common/landed_titles", fn),
                        encoding="utf-8-sig", errors="ignore"):
        m = re.match(r"^\t*([cedkb]_[A-Za-z0-9_\-]+)\s*=\s*\{", line)
        if m:
            ind = len(line) - len(line.lstrip("\t"))
            stack = [k for k in stack if k[1] < ind]
            stack.append((m.group(1), ind))
            continue
        pm = re.match(r"^\s*province\s*=\s*(\d+)", line)
        if pm and stack and stack[-1][0].startswith("b_"):
            cc = [k for k, _ in stack if k.startswith("c_")]
            if cc:
                c2ps.setdefault(cc[-1], set()).add(int(pm.group(1)))

hist = io.open(os.path.join(MOD, "history/provinces/00_generated_provinces.txt"),
               encoding="utf-8-sig").read()
prov = {}
for mm in re.finditer(r"(?m)^(\d+) = \{(.*?)\n\}", hist, re.S):
    f = re.search(r"(?m)^\s*faith\s*=\s*(\S+)", mm.group(2))
    r = re.search(r"(?m)^\s*rite\s*=\s*(\S+)", mm.group(2))
    prov[int(mm.group(1))] = (f.group(1) if f else None, r.group(1) if r else None)

p2c = {}
for c, ps in c2ps.items():
    for p in ps:
        p2c[p] = c

L.append("全部 ismaili 省：")
for p, (f, r) in sorted(prov.items()):
    if r == "ismaili":
        c = p2c.get(p, "?")
        L.append("   p%-6d %-20s faith=%-6s owner=%-5s eu5_religion=%s"
                 % (p, c, f, pol["counties"].get(c, {}).get("owner"), cr.get(c)))

L.append("")
L.append("EU5 县宗教里出现的伊斯兰类取值:")
L.append("   %s" % dict(Counter(v for v in cr.values()
                                if v in ("sunni", "shia", "ibadi", "ismaili", "zaidi",
                                         "alawi", "alevi", "druze", "kharijite", "mutazila")).most_common()))

io.open(OUT, "w", encoding="utf-8-sig", newline="\n").write("\n".join(L))
