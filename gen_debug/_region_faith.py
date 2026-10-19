# -*- coding: utf-8 -*-
"""只读：安纳托利亚/黎凡特/埃及/华西 的县宗教分布 + 实际 province faith 分布。"""
import io, os, re, json
from collections import Counter, defaultdict

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
GEN = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_region_faith.out")
L = []

mp = json.load(io.open(os.path.join(GEN, "mapping.json"), encoding="utf-8"))
locs = mp["locations"]
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

REGIONS = [
    ("kingdom", "anatolia",   "安纳托利亚"),
    ("duchy",   "levant",     "黎凡特"),
    ("kingdom", "egypt",      "埃及"),
    ("kingdom", "west_china", "华西"),
]

for key, val, label in REGIONS:
    cs = {"c_" + l["county"] for l in locs if l.get("kind") == "land" and l.get(key) == val}
    L.append("== %s (%s=%s): %d 个县" % (label, key, val, len(cs)))
    L.append("   县宗教分布: %s" % dict(Counter(cr.get(c) for c in cs).most_common(8)))
    pf = Counter()
    rite = Counter()
    for c in cs:
        for p in c2ps.get(c, ()):
            pf[prov.get(p, (None, None))[0]] += 1
            rite[prov.get(p, (None, None))[1]] += 1
    L.append("   province faith 分布: %s" % dict(pf.most_common(8)))
    L.append("   现有 rite 分布: %s" % dict(rite.most_common(6)))
    L.append("")

io.open(OUT, "w", encoding="utf-8-sig", newline="\n").write("\n".join(L))
