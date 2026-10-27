# -*- coding: utf-8 -*-
"""只读：巴达赫尚（d_badakhshan）的什叶省现状 + 呼罗珊覆盖命中范围"""
import io, re, os, json, collections

GEN = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
SRC = os.path.join(MOD, "history/provinces/00_generated_provinces.txt")
LT = os.path.join(MOD, "common/landed_titles/00_landed_titles.txt")
LOC = os.path.join(MOD, "localization/simp_chinese")
MAP = os.path.join(GEN, "mapping.json")

out = io.open(os.path.join(MOD, "gen_debug", "_badakhshan.out"), "w", encoding="utf-8")
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

# mapping.json 的县 -> duchy / kingdom
mp = json.load(open(MAP, encoding="utf-8"))
c2duchy = {}
for l in mp["locations"]:
    if l.get("kind") == "land":
        c2duchy.setdefault("c_" + l["county"], (l.get("duchy"), l.get("kingdom")))

# eu5 县宗教
pe = json.load(open(os.path.join(GEN, "eu5_peoples.json"), encoding="utf-8"))
cr = pe["county_religion"]

w("==== d_badakhshan 全部县 / 省 ====")
for c, info in sorted(county.items()):
    if info["duchy"] != "d_badakhshan":
        continue
    w("\n-- %-24s %-12s duchy=%s kingdom=%s  EU5县宗教=%s" %
      (c, loc.get(c, ""), info["duchy"], info["kingdom"], cr.get(c)))
    for bn, pid in info["baronies"]:
        f, r = prov.get(pid, (None, None))
        flag = "  <<< shia" if f == "shia" else ""
        w("   %-24s p%-6d faith=%-16s rite=%-10s%s" % (bn, pid, f, r, flag))

w("\n==== 呼罗珊(kingdom) 里所有 shia 省，按 duchy 聚合 ====")
cnt = collections.Counter()
det = collections.defaultdict(list)
for pid, (f, r) in prov.items():
    if f != "shia":
        continue
    for c, info in county.items():
        if any(pp == pid for _, pp in info["baronies"]):
            du = info["duchy"]; kg = info["kingdom"]
            if kg == "k_khorasan":
                cnt[du] += 1
                det[du].append((pid, c, r))
            break
for du, k in cnt.most_common():
    w("%-24s %4d   %s" % (du, k, loc.get(du, "")))
    for pid, c, r in det[du][:12]:
        w("      p%-6d %-22s %-12s rite=%s" % (pid, c, loc.get(c, ""), r))

out.close()
print("done")
