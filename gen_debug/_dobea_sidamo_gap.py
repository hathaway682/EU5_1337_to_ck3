# -*- coding: utf-8 -*-
"""只读：多贝亚 / 锡达莫 的 4 个省为什么在旧版拿不到礼（县级判定跳过的原因）"""
import io, re, os, json, collections

GEN = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
SRC = os.path.join(MOD, "history/provinces/00_generated_provinces.txt")
OLD = os.path.join(MOD, "history/provinces/00_generated_provinces.txt.bak_faithrestore_20261019_191647")
LT = os.path.join(MOD, "common/landed_titles/00_landed_titles.txt")
LOC = os.path.join(MOD, "localization/simp_chinese")
ADJ = os.path.join(GEN, "_ck3_province_adjacency.json")
MAP = os.path.join(GEN, "mapping.json")

out = io.open(os.path.join(MOD, "gen_debug", "_dobea_sidamo_gap.out"), "w", encoding="utf-8")
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

cur = parse(SRC); old = parse(OLD)
adj = json.load(open(ADJ, encoding="utf-8"))
mp = json.load(open(MAP, encoding="utf-8"))
locs = mp["locations"]

# EU5 县宗教
county_rel = {}
for l in locs:
    if l.get("kind") == "land":
        county_rel.setdefault(l.get("county"), collections.Counter())[l.get("religion")] += 1

TARGETS = {"dobea": [13866, 13867], "sidamo": [13942, 13943]}
w("==== 两个县的 EU5 县宗教（mapping.json）====")
for c in TARGETS:
    w("  %-12s %s" % (c, dict(county_rel.get(c, {}))))

w("\n==== 4 个目标省：新旧对比 + 邻居 ====")
for c, pids in TARGETS.items():
    for pid in pids:
        of, orr = old.get(pid, (None, None))
        cf, cr = cur.get(pid, (None, None))
        w("\n-- %s  p%d" % (c, pid))
        w("   旧: faith=%-16s rite=%s" % (of, orr))
        w("   新: faith=%-16s rite=%s" % (cf, cr))
        nb = adj.get(str(pid), [])
        w("   邻居 %d 个:" % len(nb))
        for n in nb:
            n = int(n)
            nf, nr = cur.get(n, (None, None))
            mark = ""
            if nf == "sunni" and nr:
                mark = "  <<< 同父信仰的已知源（" + nr + "）"
            w("      p%-6d faith=%-18s rite=%-10s%s" % (n, nf, nr, mark))

# 多贝亚/锡达莫所在县在 EU5 里的 owner
w("\n==== 这两个县在 EU5 的 owner / 宗教 ====")
for l in locs:
    if l.get("county") in TARGETS and l.get("kind") == "land":
        w("  %-22s county=%-10s owner=%-6s religion=%-14s kingdom=%s" %
          (l.get("name"), l.get("county"), l.get("owner"), l.get("religion"), l.get("kingdom")))

out.close()
print("done")
