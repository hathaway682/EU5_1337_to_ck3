# -*- coding: utf-8 -*-
"""只读：伊斯兰各派还有多少省没有 rite。"""
import io, os, re
from collections import Counter
MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_islamic_gap.out")
L = []
hist = io.open(os.path.join(MOD, "history/provinces/00_generated_provinces.txt"),
               encoding="utf-8-sig").read()
prov = {}
for mm in re.finditer(r"(?m)^(\d+) = \{(.*?)\n\}", hist, re.S):
    f = re.search(r"(?m)^\s*faith\s*=\s*(\S+)", mm.group(2))
    r = re.search(r"(?m)^\s*rite\s*=\s*(\S+)", mm.group(2))
    prov[int(mm.group(1))] = (f.group(1) if f else None, r.group(1) if r else None)
for tgt in ("sunni", "shia", "kharijite"):
    ps = [p for p, (f, r) in prov.items() if f == tgt]
    no = [p for p in ps if not prov[p][1]]
    L.append("%-10s %4d 省，无 rite %3d" % (tgt, len(ps), len(no)))
io.open(OUT, "w", encoding="utf-8-sig", newline="\n").write("\n".join(L))
