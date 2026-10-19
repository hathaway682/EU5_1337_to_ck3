# -*- coding: utf-8 -*-
"""只读：b_sarikol 萨雷阔勒 的位置与信仰"""
import io, re, os, json, collections

GEN = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
SRC = os.path.join(MOD, "history/provinces/00_generated_provinces.txt")
LT = os.path.join(MOD, "common/landed_titles/00_landed_titles.txt")
LOC = os.path.join(MOD, "localization/simp_chinese")
ADJ = os.path.join(GEN, "_ck3_province_adjacency.json")
MAP = os.path.join(GEN, "mapping.json")

out = io.open(os.path.join(MOD, "gen_debug", "_sarikol.out"), "w", encoding="utf-8")
def w(s=""):
    out.write(str(s) + "\n")

txt = io.open(SRC, encoding="utf-8-sig", errors="ignore").read()
prov = {}
for m in re.finditer(r"(?m)^(\d+) = \{(.*?)\n\}", txt, re.S):
    pid = int(m.group(1)); body = m.group(2)
    f = re.search(r"(?m)^\s*faith = (\S+)", body)
    r = re.search(r"(?m)^\s*rite = (\S+)", body)
    prov[pid] = (f.group(1) if f else None, r.group(1) if r else None)

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
mp = json.load(open(MAP, encoding="utf-8"))
c2d = {}
for l in mp["locations"]:
    if l.get("kind") == "land":
        c2d.setdefault("c_" + l["county"], (l.get("duchy"), l.get("kingdom")))
pe = json.load(open(os.path.join(GEN, "eu5_peoples.json"), encoding="utf-8"))
cr = pe["county_religion"]

# 找 b_sarikol
target = None
for c, info in county.items():
    for bn, pid in info["baronies"]:
        if bn == "b_sarikol":
            target = (c, pid, info)
            break
    if target:
        break
if not target:
    w("b_sarikol 未找到")
else:
    c, pid, info = target
    w("b_sarikol -> p%d   county=%s (%s)  duchy=%s kingdom=%s  EU5县宗教=%s" %
      (pid, c, loc.get(c, ""), info["duchy"], info["kingdom"], cr.get(c)))
    w("  mapping: %s" % (c2d.get(c),))
    f, r = prov.get(pid, (None, None))
    w("  faith=%s  rite=%s" % (f, r))

    w("\n==== 该县全部省 ====")
    for bn, pp in info["baronies"]:
        ff, rr = prov.get(pp, (None, None))
        w("   %-24s p%-6d faith=%-14s rite=%s" % (bn, pp, ff, rr))

    w("\n==== p%d 的邻居 ====" % pid)
    for n in adj.get(str(pid), []):
        n = int(n)
        nf, nr = prov.get(n, (None, None))
        nc = None
        for cc, inf in county.items():
            if any(pp == n for _, pp in inf["baronies"]):
                nc = cc; break
        w("   p%-6d %-22s %-12s faith=%-14s rite=%-10s duchy=%s" %
          (n, "", loc.get(nc, ""), nf, nr, county.get(nc, {}).get("duchy")))

    w("\n==== 同县/同 duchy 里所有 shia 省 ====")
    for cc, inf in county.items():
        if inf["duchy"] != info["duchy"]:
            continue
        for bn, pp in inf["baronies"]:
            ff, rr = prov.get(pp, (None, None))
            if ff == "shia":
                w("   %-22s p%-6d %-22s %-12s rite=%s" % (cc, pp, bn, loc.get(cc, ""), rr))

out.close()
print("done")
