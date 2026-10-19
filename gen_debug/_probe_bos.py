# -*- coding: utf-8 -*-
"""只读探查：BOS 县的当前 faith（christian_rites 会无条件改 faith=bosnian_church）。"""
import json, io, os, re
from collections import Counter

GEN = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_bos_probe.out")

pol = json.load(io.open(os.path.join(GEN, "eu5_politics.json"), encoding="utf-8"))
counties = pol["counties"]

hist = io.open(os.path.join(MOD, "history/provinces/00_generated_provinces.txt"),
               encoding="utf-8-sig").read()
prov = {}
for mm in re.finditer(r"(?m)^(\d+) = \{(.*?)\n\}", hist, re.S):
    f = re.search(r"(?m)^\s*faith\s*=\s*(\S+)", mm.group(2))
    prov[int(mm.group(1))] = f.group(1) if f else None

c2ps = {}
for fn in os.listdir(os.path.join(MOD, "common/landed_titles")):
    stack = []
    for line in io.open(os.path.join(MOD, "common/landed_titles", fn), encoding="utf-8-sig", errors="ignore"):
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
                c2ps.setdefault(cc[-1], set()).add(int(pm.group(1)))

L = []
bos = [c for c, i in counties.items() if i.get("owner") == "BOS"]
L.append("BOS 县: %s" % bos)
cnt = Counter()
for c in bos:
    for p in sorted(c2ps.get(c, ())):
        cnt[prov.get(p)] += 1
L.append("BOS 县下 province 的 faith 分布: %s" % dict(cnt))
L.append("全图 faith=bosnian_church 的 province: %d" % sum(1 for v in prov.values() if v == "bosnian_church"))

# 重复 title 检查
L.append("")
for c in ("c_gorgan", "c_antakya"):
    L.append("%s 的 province 数（去重后）: %d" % (c, len(c2ps.get(c, ()))))

io.open(OUT, "w", encoding="utf-8-sig", newline="\n").write("\n".join(L))
