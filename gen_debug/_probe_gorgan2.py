# -*- coding: utf-8 -*-
"""只读探查：c_gorgan 的男爵领顺序 / 首府 / 各 province 的 faith+rite。"""
import io, os, re, json
from collections import Counter

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
GEN = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_gorgan_probe2.out")

L = []

# 1) landed_titles 里 c_gorgan 块（按出现顺序取 barony -> province）
bars = []          # [(barony, province)]
cur_c = None
depth = 0
for fn in sorted(os.listdir(os.path.join(MOD, "common/landed_titles"))):
    if not fn.endswith(".txt"):
        continue
    for line in io.open(os.path.join(MOD, "common/landed_titles", fn),
                        encoding="utf-8-sig", errors="ignore"):
        m = re.match(r"^(\t*)(c_[A-Za-z0-9_\-]+)\s*=\s*\{", line)
        if m:
            cur_c = m.group(2)
            continue
        m = re.match(r"^(\t*)(b_[A-Za-z0-9_\-]+)\s*=\s*\{", line)
        if m:
            cur_b = m.group(2)
            continue
        pm = re.match(r"^\s*province\s*=\s*(\d+)", line)
        if pm and cur_c == "c_gorgan" and "cur_b" in dir():
            bars.append((cur_b, int(pm.group(1))))

L.append("c_gorgan 的 barony 顺序（landed_titles 里出现的顺序，第一个通常就是首府）:")
for i, (b, p) in enumerate(bars):
    L.append("   %d) %-24s p%d" % (i + 1, b, p))

# 2) 省份 history
hist = io.open(os.path.join(MOD, "history/provinces/00_generated_provinces.txt"),
               encoding="utf-8-sig").read()
prov = {}
for mm in re.finditer(r"(?m)^(\d+) = \{(.*?)\n\}", hist, re.S):
    body = mm.group(2)
    f = re.search(r"(?m)^\s*faith\s*=\s*(\S+)", body)
    r = re.search(r"(?m)^\s*rite\s*=\s*(\S+)", body)
    prov[int(mm.group(1))] = (f.group(1) if f else None, r.group(1) if r else None)

L.append("")
L.append("各 province 现状:")
for b, p in bars:
    L.append("   %-24s p%-6d faith=%-12s rite=%s" % (b, p, prov.get(p, (None, None))[0], prov.get(p, (None, None))[1]))

# 3) EU5 侧：戈尔甘 location 的宗教人口
pe = json.load(io.open(os.path.join(GEN, "eu5_peoples.json"), encoding="utf-8"))
L.append("")
L.append("eu5_peoples.json 的 county_religion[c_gorgan] = %s" % pe["county_religion"].get("c_gorgan"))
for k in pe:
    if k != "county_religion" and isinstance(pe[k], dict) and "c_gorgan" in pe[k]:
        L.append("   %s[c_gorgan] = %s" % (k, pe[k]["c_gorgan"]))

# 4) 首府判定：CK3 里 c_ 块的第一个 b_ 就是首府
if bars:
    cap_b, cap_p = bars[0]
    L.append("")
    L.append("首府 barony = %s (p%d)，faith = %s" % (cap_b, cap_p, prov.get(cap_p, (None, None))[0]))

io.open(OUT, "w", encoding="utf-8-sig", newline="\n").write("\n".join(L))
