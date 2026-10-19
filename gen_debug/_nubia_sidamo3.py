# -*- coding: utf-8 -*-
"""只读诊断：sunni 无 rite 的省份 -> 回落到 sunni.main_rite = hanafi"""
import io, re, os, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROV = os.path.join(ROOT, "history", "provinces", "00_generated_provinces.txt")
LT = os.path.join(ROOT, "common", "landed_titles", "00_landed_titles.txt")
LOC = os.path.join(ROOT, "localization", "simp_chinese")

out = io.open(os.path.join(ROOT, "gen_debug", "_nubia_sidamo3.out"), "w", encoding="utf-8")
def w(s=""):
    out.write(str(s) + "\n")

txt = io.open(PROV, encoding="utf-8-sig", errors="ignore").read()
prov = {}
for m in re.finditer(r"(?m)^(\d+) = \{(.*?)\n\}", txt, re.S):
    pid = int(m.group(1)); body = m.group(2)
    f = re.search(r"(?m)^\s*faith = (\S+)", body)
    r = re.search(r"(?m)^\s*rite = (\S+)", body)
    prov[pid] = (f.group(1) if f else None, r.group(1) if r else None)

lt = io.open(LT, encoding="utf-8-sig", errors="ignore").read().replace("\r\n", "\n")
county = collections.OrderedDict()
stack = []
cur = None
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

def load_loc():
    d = {}
    for fn in os.listdir(LOC):
        if not fn.endswith(".yml"):
            continue
        try:
            t = io.open(os.path.join(LOC, fn), encoding="utf-8-sig", errors="ignore").read()
        except Exception:
            continue
        for m in re.finditer(r'(?m)^\s*([A-Za-z0-9_.\-]+):\d*\s*"([^"]*)"', t):
            d.setdefault(m.group(1), m.group(2))
    return d
loc = load_loc()

# 全图统计：faith=sunni 但无 rite
w("==== 全图：faith=sunni 且无 rite 的省份 ====")
no_rite_sunni = [(pid, f) for pid, (f, r) in prov.items() if f == "sunni" and not r]
w("总数: %d" % len(no_rite_sunni))
by_faith = collections.Counter(f for pid, (f, r) in prov.items() if not r)
w("全图无 rite 的 faith 分布前 25: %s" % dict(by_faith.most_common(25)))

pid2 = {}
for c, info in county.items():
    for bn, pid in info["baronies"]:
        pid2[pid] = (c, info["duchy"], info["kingdom"], bn)

# 目标区域：kingdom 名含 nubia/ethiopia/somalia 或 duchy 名含相关
KEY_K = ("k_nubia", "k_ethiopia", "k_somalia", "k_alodia", "k_makuria", "k_beja", "k_adal")
w("\n==== 目标王国里 faith=sunni 且无 rite 的省份 ====")
tot = 0
for pid, f in sorted(no_rite_sunni):
    c, du, kg, bn = pid2.get(pid, ("?", "?", "?", "?"))
    if kg in KEY_K:
        tot += 1
        w("   p%-6d %-22s %-26s %-12s duchy=%-22s" % (pid, bn, c, loc.get(c, ""), du))
w("目标王国小计: %d" % tot)

# 目标区域：所有 sunni 省份，看有/无 rite
w("\n==== 目标王国 sunni 省份全量（faith=sunni）====")
for pid, (f, r) in sorted(prov.items()):
    if f != "sunni":
        continue
    c, du, kg, bn = pid2.get(pid, ("?", "?", "?", "?"))
    if kg in KEY_K:
        w("   p%-6d %-22s %-26s rite=%-10s %s" % (pid, bn, c, r, "<<< 无 rite→显示 hanafi" if not r else ""))

# 每个目标 county 的汇总
w("\n==== 目标 county 汇总（按 county 聚合 rite）====")
for c, info in sorted(county.items()):
    if info["kingdom"] not in KEY_K:
        continue
    cc = collections.Counter()
    for bn, pid in info["baronies"]:
        f, r = prov.get(pid, (None, None))
        cc[(f, r if r else "∅")] += 1
    w("%-24s %-12s %-22s %s" % (c, loc.get(c, ""), info["duchy"], dict(cc)))

out.close()
print("done")
