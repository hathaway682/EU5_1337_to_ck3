# -*- coding: utf-8 -*-
"""只读：汇总 _culture_by_pops_diff.csv，看这 442 处 faith 变化都是什么组合。"""
import csv, io, os
from collections import Counter

p = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape\gen_debug\_culture_by_pops_diff.csv"
rows = list(csv.DictReader(io.open(p, encoding="utf-8-sig")))
out = ["diff 行数: %d" % len(rows)]
out.append("cur_faith -> new_faith:")
for k, v in Counter((r["cur_faith"], r["new_faith"]) for r in rows).most_common(40):
    out.append("   %-30s -> %-26s %d" % (k[0], k[1], v))
out.append("")
out.append("culture 变化行数: %d" % sum(1 for r in rows if r["cur_culture"] != r["new_culture"]))
out.append("")
out.append("=== new_faith=pagan 的省，按 EU5 religion 分组 ===")
pg = Counter(r["eu5_religion"] for r in rows if r["new_faith"] == "pagan")
out.append("EU5 religion 种数: %d，省数 %d" % (len(pg), sum(pg.values())))
for k, v in pg.most_common(50):
    out.append("   %-30s %d" % (k, v))
io.open(os.path.join(os.path.dirname(p), "_popsrebuild_summary.out"), "w", encoding="utf-8").write("\n".join(out))
print("done")
