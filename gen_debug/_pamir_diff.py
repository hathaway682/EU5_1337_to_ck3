# -*- coding: utf-8 -*-
"""只读：对比运行前后的 rite 变化（参数：旧文件路径）"""
import io, re, os, sys, collections

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
NEW = os.path.join(MOD, "history/provinces/00_generated_provinces.txt")
OLD = sys.argv[1] if len(sys.argv) > 1 else os.path.join(MOD, "gen_debug", "_before_pamir.txt")
LT = os.path.join(MOD, "common/landed_titles/00_landed_titles.txt")
LOC = os.path.join(MOD, "localization/simp_chinese")

out = io.open(os.path.join(MOD, "gen_debug", "_pamir_diff.out"), "w", encoding="utf-8")
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

new = parse(NEW); old = parse(OLD)

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

w("blocks old=%d new=%d" % (len(old), len(new)))
fdiff = [(p, old[p][0], new[p][0]) for p in old if p in new and old[p][0] != new[p][0]]
w("faith 变化: %d" % len(fdiff))

rdiff = [(p, old[p][1], new[p][1]) for p in old if p in new and old[p][1] != new[p][1]]
w("\n==== rite 变化 %d 处 ====" % len(rdiff))
for p, a, b in rdiff:
    c, du, kg, bn = pid2.get(p, ("?", "?", "?", "?"))
    w("  p%-6d %-24s %-14s duchy=%-18s %s -> %s" % (p, bn, loc.get(c, ""), du, a, b))

w("\n==== rite 计数 ====")
co = collections.Counter(v[1] for v in old.values())
cn = collections.Counter(v[1] for v in new.values())
for k in sorted(set(co) | set(cn), key=lambda x: -cn.get(x, 0)):
    a, b = co.get(k, 0), cn.get(k, 0)
    if a != b:
        w("  %-22s %5d -> %5d  %+d" % (str(k), a, b, b - a))
w("总 rite 行: %d -> %d" % (sum(v for k, v in co.items() if k), sum(v for k, v in cn.items() if k)))

out.close()
print("done")
