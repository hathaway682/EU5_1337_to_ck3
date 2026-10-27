# -*- coding: utf-8 -*-
"""只读：diff 里 442 个省，有没有带 rite 行的？"""
import csv, io, os, re

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
SRC = os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt")
CSVP = os.path.join(MOD, "gen_debug", "_culture_by_pops_diff.csv")

pids = [int(r["province"]) for r in csv.DictReader(io.open(CSVP, encoding="utf-8-sig"))]
t = io.open(SRC, encoding="utf-8-sig", errors="ignore").read()
has = {}
for pid, body in re.findall(r"(?m)^(\d+) = \{(.*?)\n\}", t, re.S):
    p = int(pid)
    if p in set(pids):
        has[p] = re.findall(r"(?m)^\s*rite = (\S+)", body)

with_rite = {p: v for p, v in has.items() if v}
out = ["diff 省数: %d" % len(pids),
       "带 rite 行的: %d" % len(with_rite)]
for p, v in sorted(with_rite.items()):
    out.append("   p%d rite=%s" % (p, v))

# 顺便：全部 21046 个省里 faith 改变后是否会造成「rite 与父信仰不匹配」
out.append("")
out.append("=== 全部省 faith 分布（改后，即 dry-run 的目标值） ===")
plan = {}
for r in csv.DictReader(io.open(CSVP, encoding="utf-8-sig")):
    plan[int(r["province"])] = r["new_faith"]
from collections import Counter
cur = {}
for pid, body in re.findall(r"(?m)^(\d+) = \{(.*?)\n\}", t, re.S):
    m = re.search(r"(?m)^\s*faith = (\S+)", body)
    cur[int(pid)] = m.group(1) if m else None
after = dict(cur)
after.update(plan)
out.append(str(dict(Counter(after.values()).most_common())))
io.open(os.path.join(MOD, "gen_debug", "_popsrebuild_ritecheck.out"), "w",
        encoding="utf-8").write("\n".join(out))
print("done")
