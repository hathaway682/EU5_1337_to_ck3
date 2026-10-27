# -*- coding: utf-8 -*-
"""只读：马达加斯加 / 拉克沙群岛 为什么没拿到礼"""
import io, re, os, json, collections

GEN = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
SRC = os.path.join(MOD, "history/provinces/00_generated_provinces.txt")
LT = os.path.join(MOD, "common/landed_titles/00_landed_titles.txt")
LOC = os.path.join(MOD, "localization/simp_chinese")
ADJ = os.path.join(GEN, "_ck3_province_adjacency.json")
MAP = os.path.join(GEN, "mapping.json")

out = io.open(os.path.join(MOD, "gen_debug", "_madagascar_gap.out"), "w", encoding="utf-8")
def w(s=""):
    out.write(str(s) + "\n")

# province faith/rite
txt = io.open(SRC, encoding="utf-8-sig", errors="ignore").read()
prov = {}
for m in re.finditer(r"(?m)^(\d+) = \{(.*?)\n\}", txt, re.S):
    pid = int(m.group(1)); body = m.group(2)
    f = re.search(r"(?m)^\s*faith = (\S+)", body)
    r = re.search(r"(?m)^\s*rite = (\S+)", body)
    prov[pid] = (f.group(1) if f else None, r.group(1) if r else None)

# titles
lt = io.open(LT, encoding="utf-8-sig", errors="ignore").read().replace("\r\n", "\n")
county = collections.OrderedDict(); stack = []; cur = None
for line in lt.split("\n"):
    if not line.strip() or line.lstrip().startswith("#"):
        continue
    depth = len(line) - len(line.lstrip("\t"))
    m = re.match(r"\s*([a-z]_[A-Za-z0-9_]+)\s*=\s*\{", line)
    if m:
        key = m.group(1)
        while stack and stack[-1][0] >= depth:
            stack.pop()
        stack.append((depth, key))
        if key.startswith("c_"):
            kk = [s[1] for s in stack if s[1].startswith("k_")]
            dd = [s[1] for s in stack if s[1].startswith("d_")]
            cur = key
            county[key] = {"baronies": [], "duchy": dd[-1] if dd else None,
                           "kingdom": kk[-1] if kk else None}
        continue
    mp = re.match(r"\s*province\s*=\s*(\d+)", line)
    if mp and cur:
        bb = [s[1] for s in stack if s[1].startswith("b_")]
        if bb:
            county[cur]["baronies"].append((bb[-1], int(mp.group(1))))

loc = {}
for fn in os.listdir(LOC):
    if not fn.endswith(".yml"):
        continue
    try:
        t = io.open(os.path.join(LOC, fn), encoding="utf-8-sig", errors="ignore").read()
    except Exception:
        continue
    for m in re.finditer(r'(?m)^\s*([A-Za-z0-9_.\-]+):\d*\s*"([^"]*)"', t):
        loc.setdefault(m.group(1), m.group(2))

adj = json.load(open(ADJ, encoding="utf-8"))
w("adjacency keys=%d" % len(adj))

TARGET_PIDS = [12243, 14381, 14386, 14388, 14427, 14435]

w("\n==== 目标省现状 + 接壤 ====")
for pid in TARGET_PIDS:
    f, r = prov.get(pid, (None, None))
    nb = adj.get(str(pid), [])
    w("\np%d  faith=%s  rite=%s" % (pid, f, r))
    w("   adj(%d): %s" % (len(nb), nb))
    for n in nb:
        n = int(n)
        nf, nr = prov.get(n, (None, None))
        w("      p%-6d faith=%-20s rite=%s" % (n, nf, nr))

w("\n==== k_madagascar 全部省份 ====")
for c, info in sorted(county.items()):
    if info["kingdom"] != "k_madagascar":
        continue
    w("\n-- %-24s %-12s duchy=%s" % (c, loc.get(c, ""), info["duchy"]))
    for bn, pid in info["baronies"]:
        f, r = prov.get(pid, (None, None))
        nb = len(adj.get(str(pid), []))
        w("   %-22s p%-6d faith=%-20s rite=%-10s adj=%d" % (bn, pid, f, r, nb))

w("\n==== c_laccadive ====")
info = county.get("c_laccadive")
if info:
    for bn, pid in info["baronies"]:
        f, r = prov.get(pid, (None, None))
        nb = adj.get(str(pid), [])
        w("   %-22s p%-6d faith=%-20s rite=%-10s adj=%s" % (bn, pid, f, r, nb))

# mapping.json 里这些 county 的 religion
w("\n==== mapping.json 里马达加斯加/拉克沙 locations ====")
mp = json.load(open(MAP, encoding="utf-8"))
locs = mp["locations"]
for l in locs:
    if l.get("kingdom") == "k_madagascar" or l.get("county") in ("laccadive",):
        w("   %-24s kind=%-6s county=%-24s kingdom=%-14s religion=%s" %
          (l.get("name"), l.get("kind"), l.get("county"), l.get("kingdom"), l.get("religion")))

out.close()
print("done")
