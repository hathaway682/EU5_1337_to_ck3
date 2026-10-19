# -*- coding: utf-8 -*-
"""只读：在旧备份里找 faith=sunni 但没有 rite 的省份（会回落到 sunni.main_rite=hanafi）"""
import io, re, os, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLD = os.path.join(ROOT, "history", "provinces", "00_generated_provinces.txt.bak_faithrestore_20261019_191647")
CUR = os.path.join(ROOT, "history", "provinces", "00_generated_provinces.txt")
LT = os.path.join(ROOT, "common", "landed_titles", "00_landed_titles.txt")
LOC = os.path.join(ROOT, "localization", "simp_chinese")

out = io.open(os.path.join(ROOT, "gen_debug", "_nubia_sidamo4.out"), "w", encoding="utf-8")
def w(s=""):
    out.write(str(s) + "\n")

def parse(path):
    txt = io.open(path, encoding="utf-8-sig", errors="ignore").read()
    d = {}
    for m in re.finditer(r"(?m)^(\d+) = \{(.*?)\n\}", txt, re.S):
        pid = int(m.group(1)); body = m.group(2)
        f = re.search(r"(?m)^\s*faith = (\S+)", body)
        r = re.search(r"(?m)^\s*rite = (\S+)", body)
        d[pid] = (f.group(1) if f else None, r.group(1) if r else None)
    return d

old = parse(OLD)
cur = parse(CUR)
w("old blocks=%d  cur blocks=%d" % (len(old), len(cur)))

lt = io.open(LT, encoding="utf-8-sig", errors="ignore").read().replace("\r\n", "\n")
county = collections.OrderedDict()
stack = []; cur_c = None
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
            cur_c = key
            county[key] = {"baronies": [], "duchy": dd[-1] if dd else None,
                           "kingdom": kk[-1] if kk else None}
        continue
    mp = re.match(r"\s*province\s*=\s*(\d+)", line)
    if mp and cur_c:
        bb = [s[1] for s in stack if s[1].startswith("b_")]
        if bb:
            county[cur_c]["baronies"].append((bb[-1], int(mp.group(1))))

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

pid2 = {}
for c, info in county.items():
    for bn, pid in info["baronies"]:
        pid2[pid] = (c, info["duchy"], info["kingdom"], bn)

w("\n==== 旧文件里 sunni 无 rite（= 显示哈乃斐）的省份 ====")
n = 0
by_kg = collections.Counter()
rows = []
for pid, (f, r) in sorted(old.items()):
    if f == "sunni" and not r:
        n += 1
        c, du, kg, bn = pid2.get(pid, ("?", "?", "?", "?"))
        by_kg[kg] += 1
        rows.append((pid, c, du, kg, bn))
w("总数 %d" % n)
for pid, c, du, kg, bn in rows:
    cf, cr = cur.get(pid, (None, None))
    w("  p%-6d %-24s %-12s duchy=%-20s kingdom=%-14s  现在 faith=%-8s rite=%s" %
      (pid, bn, loc.get(c, ""), du, kg, cf, cr))
w("\n按 kingdom 聚合: %s" % dict(by_kg.most_common()))

w("\n==== 旧文件里所有 sunni 无 rite 的 county 汇总 ====")
cc = collections.Counter()
for pid, c, du, kg, bn in rows:
    cc[c] += 1
for c, k in cc.most_common(40):
    w("  %-24s %-12s %d" % (c, loc.get(c, ""), k))

out.close()
print("done")
