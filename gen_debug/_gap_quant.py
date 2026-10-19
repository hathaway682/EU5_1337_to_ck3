# -*- coding: utf-8 -*-
"""只读：量化 christian 层漏写的规模 + HLL/LCK 的 zayidi 残留。"""
import io, os, re, json
from collections import Counter, defaultdict

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
GEN = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_gap_quant.out")
L = []

pol = json.load(io.open(os.path.join(GEN, "eu5_politics.json"), encoding="utf-8"))
cty = pol["counties"]
pe = json.load(io.open(os.path.join(GEN, "eu5_peoples.json"), encoding="utf-8"))
cr = pe["county_religion"]
owners = {}
import csv
with io.open(os.path.join(GEN, "eu5_county_owners.csv"), encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        owners[r["county"]] = r["owner"]

# province -> county
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
                c2ps.setdefault(cc[-1], []).append(int(pm.group(1)))

hist = io.open(os.path.join(MOD, "history/provinces/00_generated_provinces.txt"),
               encoding="utf-8-sig").read()
prov = {}
for mm in re.finditer(r"(?m)^(\d+) = \{(.*?)\n\}", hist, re.S):
    body = mm.group(2)
    f = re.search(r"(?m)^\s*faith\s*=\s*(\S+)", body)
    r = re.search(r"(?m)^\s*rite\s*=\s*(\S+)", body)
    prov[int(mm.group(1))] = (f.group(1) if f else None, r.group(1) if r else None)

# 1) orthodox / miaphysitism 无 rite 的省
for tgt in ("orthodox", "miaphysitism"):
    ps = [p for p, (f, r) in prov.items() if f == tgt]
    no = [p for p in ps if not prov[p][1]]
    L.append("%s province %d，无 rite %d" % (tgt, len(ps), len(no)))

# 2) 无 rite 的 orthodox 省，按 (EU5 县宗教, owner) 归类
cnt = Counter()
sample = defaultdict(list)
p2c = {}
for c, ps in c2ps.items():
    for p in set(ps):
        p2c[p] = c
for p, (f, r) in prov.items():
    if f == "orthodox" and not r:
        c = p2c.get(p, "?")
        cnt[(cr.get(c), owners.get(c))] += 1
        if len(sample[(cr.get(c), owners.get(c))]) < 4:
            sample[(cr.get(c), owners.get(c))].append(c)
L.append("")
L.append("无 rite 的 orthodox 省，按 (EU5 县宗教, owner) 分组:")
for k, n in cnt.most_common(25):
    L.append("   %-30s %4d   例: %s" % (str(k), n, ",".join(sample[k])))

# 3) HLL / LCK 的 province
L.append("")
L.append("HLL / LCK 名下的县:")
for c, info in sorted(cty.items()):
    o = info.get("owner")
    if o in ("HLL", "LCK"):
        ps = sorted(set(c2ps.get(c, [])))
        L.append("   %-22s owner=%-4s eu5rel=%-8s %s" % (
            c, o, cr.get(c),
            " ".join("%s/%s" % (prov.get(p, (None, None))[0], prov.get(p, (None, None))[1]) for p in ps)))

# 4) 全图 zayidi 分布
L.append("")
z = [p for p, (f, r) in prov.items() if r == "zayidi"]
L.append("zayidi province %d，按 owner 分组:" % len(z))
L.append("   %s" % dict(Counter(owners.get(p2c.get(p, "?"), "?") for p in z).most_common()))

io.open(OUT, "w", encoding="utf-8-sig", newline="\n").write("\n".join(L))
