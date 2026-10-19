# -*- coding: utf-8 -*-
"""只读：当前所有 ismaili 省 + 新疆/上印度河一带的 shia 省"""
import io, re, os, collections

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
SRC = os.path.join(MOD, "history/provinces/00_generated_provinces.txt")
LT = os.path.join(MOD, "common/landed_titles/00_landed_titles.txt")
LOC = os.path.join(MOD, "localization/simp_chinese")

out = io.open(os.path.join(MOD, "gen_debug", "_ismaili_now.out"), "w", encoding="utf-8")
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

pid2 = {}
for c, info in county.items():
    for bn, pid in info["baronies"]:
        pid2[pid] = (c, info["duchy"], info["kingdom"], bn)

w("==== 当前全部 ismaili 省 ====")
n = 0
for pid in sorted(prov):
    f, r = prov[pid]
    if r == "ismaili":
        n += 1
        c, du, kg, bn = pid2.get(pid, ("?", "?", "?", "?"))
        w("  p%-6d %-24s %-14s duchy=%-18s kingdom=%s" % (pid, bn, loc.get(c, ""), du, kg))
w("合计 %d" % n)

w("\n==== k_xinjiang / d_upper_indus / d_tarim 的 shia 省 ====")
for pid in sorted(prov):
    f, r = prov[pid]
    if f != "shia":
        continue
    c, du, kg, bn = pid2.get(pid, ("?", "?", "?", "?"))
    if kg in ("k_xinjiang", "k_hindustan") or du in ("d_tarim", "d_upper_indus"):
        w("  p%-6d %-24s %-14s duchy=%-18s kingdom=%-14s rite=%s" % (pid, bn, loc.get(c, ""), du, kg, r))

out.close()
print("done")
