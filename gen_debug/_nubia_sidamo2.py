# -*- coding: utf-8 -*-
"""只读诊断：努比亚/埃塞俄比亚一带为什么出现 hanafi"""
import io, re, os, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROV = os.path.join(ROOT, "history", "provinces", "00_generated_provinces.txt")
LT = os.path.join(ROOT, "common", "landed_titles", "00_landed_titles.txt")
LOC = os.path.join(ROOT, "localization", "simp_chinese")

out = io.open(os.path.join(ROOT, "gen_debug", "_nubia_sidamo2.out"), "w", encoding="utf-8")
def w(s=""):
    out.write(str(s) + "\n")

# ---- 1. province faith / rite ----
txt = io.open(PROV, encoding="utf-8-sig", errors="ignore").read()
prov = {}
for m in re.finditer(r"(?m)^(\d+) = \{(.*?)\n\}", txt, re.S):
    pid = int(m.group(1)); body = m.group(2)
    f = re.search(r"(?m)^\s*faith = (\S+)", body)
    r = re.search(r"(?m)^\s*rite = (\S+)", body)
    prov[pid] = (f.group(1) if f else None, r.group(1) if r else None)
w("province blocks: %d" % len(prov))

# ---- 2. 按 tab 深度解析 titles ----
lt = io.open(LT, encoding="utf-8-sig", errors="ignore").read().replace("\r\n", "\n")
county = collections.OrderedDict()   # c_key -> {"baronies":[(b,pid)], "duchy":d, "kingdom":k}
duchy_kingdom = {}
stack = []          # [(depth, key)]
cur_county = None
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
            cur_county = key
            county[key] = {"baronies": [], "duchy": dd[-1] if dd else None,
                           "kingdom": kk[-1] if kk else None}
            if dd:
                duchy_kingdom[dd[-1]] = kk[-1] if kk else None
        continue
    mp = re.match(r"\s*province\s*=\s*(\d+)", line)
    if mp and cur_county:
        # 找到最近的 b_
        bb = [s[1] for s in stack if s[1].startswith("b_")]
        if bb:
            county[cur_county]["baronies"].append((bb[-1], int(mp.group(1))))
w("counties: %d" % len(county))

# ---- 3. localization ----
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
w("loc keys: %d" % len(loc))

# ---- 4. 名字匹配 ----
TARGETS = ["锡达莫", "锡达马", "努比", "努贝", "埃塞", "绍阿", "阿姆哈拉", "提格雷",
           "戈贾姆", "沃莱", "哈拉尔", "巴莱", "达莫特", "卡法", "哈迪亚", "伊法特",
           "阿达尔", "马库里亚", "阿勒瓦", "阿尔瓦", "贝贾", "森纳尔", "科尔多凡"]
w("\n==== 名字匹配的 county ====")
hit = []
for c in county:
    n = loc.get(c, "")
    if n and any(t in n for t in TARGETS):
        hit.append((c, n))
for c, n in sorted(hit, key=lambda x: x[1]):
    info = county[c]
    w("%-30s %-12s duchy=%-24s kingdom=%s" % (c, n, info["duchy"], info["kingdom"]))

# ---- 5. 详情 ----
w("\n==== 目标 county 详情 ====")
for c, n in sorted(hit, key=lambda x: x[1]):
    info = county[c]
    w("\n-- %s  %s   duchy=%s kingdom=%s" % (c, n, info["duchy"], info["kingdom"]))
    for bn, pid in info["baronies"]:
        f, r = prov.get(pid, (None, None))
        flag = "  <<< HANAFI" if r == "hanafi" else ""
        w("   %-26s p%-6d faith=%-22s rite=%s%s" % (bn, pid, f, r, flag))

# ---- 6. hanafi 全图按 duchy 聚合 ----
pid2 = {}
for c, info in county.items():
    for bn, pid in info["baronies"]:
        pid2[pid] = (c, info["duchy"], info["kingdom"])
cnt = collections.Counter()
det = collections.defaultdict(list)
for pid, (f, r) in prov.items():
    if r == "hanafi":
        c, du, kg = pid2.get(pid, ("?", "?", "?"))
        cnt[(du, kg)] += 1
        det[(du, kg)].append((pid, c, f))
w("\n==== 全图 hanafi 按 duchy 聚合（前 50）====")
for (du, kg), k in cnt.most_common(50):
    w("%-26s k=%-24s %4d  %s" % (du, kg, k, loc.get(du, "")))

# ---- 7. 东非/尼罗河相关 ----
w("\n==== 东非/尼罗河上游 duchy 的 hanafi 明细 ====")
KEY = ["nubia", "sudan", "alwa", "alodia", "makuria", "dotawo", "beja", "sennar", "kordofan",
       "ethiopia", "sidamo", "shoa", "amhara", "gondar", "gojjam", "wollo", "harar",
       "bale", "damot", "welega", "kefa", "hadya", "ifat", "adal", "dawaro", "fatejar",
       "majeerteen", "mudug", "hobyo", "warsangali", "ogaden"]
for (du, kg), lst in sorted(det.items(), key=lambda x: -len(x[1])):
    if du and any(k in du for k in KEY):
        w("\n-- %s / %s   %s" % (du, kg, loc.get(du, "")))
        for pid, c, f in sorted(lst):
            w("   p%-6d %-26s %-12s faith=%-20s rite=hanafi" % (pid, c, loc.get(c, ""), f))

# ---- 8. 全图所有 shafii/hanafi 在埃塞的分布对比 ----
w("\n==== 埃塞一带（kingdom ethiopia / nubia）各 rite 统计 ====")
for kg in ["k_ethiopia", "k_nubia", "k_alodia", "k_makuria", "k_beja", "k_adal", "k_ifat"]:
    cc = collections.Counter()
    for c, info in county.items():
        if info["kingdom"] == kg:
            for bn, pid in info["baronies"]:
                r = prov.get(pid, (None, None))[1]
                cc[r] += 1
    if cc:
        w("%-14s %s" % (kg, dict(cc.most_common())))

out.close()
print("done")
