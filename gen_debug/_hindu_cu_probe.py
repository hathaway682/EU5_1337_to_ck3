# -*- coding: utf-8 -*-
"""只读：CU 数据里印度教相关 barony 的 rite 分布，以及与本 mod 现状的对照"""
import io, os, re, csv, json, collections

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
CSV = os.path.join(MOD, "gen_debug", "_cu_vs_ours.csv")
SRC = os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt")
LT = os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt")

out = io.open(os.path.join(MOD, "gen_debug", "_hindu_cu_probe.out"), "w", encoding="utf-8")
def w(s=""):
    out.write(str(s) + "\n")

# 我们的 province faith
txt = io.open(SRC, encoding="utf-8-sig", errors="ignore").read()
prov = {}
for m in re.finditer(r"(?m)^(\d+) = \{(.*?)\n\}", txt, re.S):
    f = re.search(r"(?m)^\s*faith = (\S+)", m.group(2))
    prov[int(m.group(1))] = f.group(1) if f else None

HINDU = {"vaishnava_faith", "shaiva_faith", "shakta_faith", "smartism"}
hindu_pids = {p for p, f in prov.items() if f in HINDU}
w("本 mod 印度教系 province: %d" % len(hindu_pids))

rows = list(csv.DictReader(io.open(CSV, encoding="utf-8-sig")))
w("CU csv 行数: %d" % len(rows))

# 只看印度教 province 的 barony
sub = [r for r in rows if int(r["our_province"]) in hindu_pids]
w("匹配到印度教 province 的 CU 行: %d" % len(sub))

w("\n==== CU 给出的 rite 分布（印度教 province 上）====")
c = collections.Counter(r["cu_rite"] or "(空)" for r in sub)
for k, v in c.most_common(30):
    w("  %-28s %d" % (k, v))

w("\n==== 这些 barony 我们当前的 faith 分布 ====")
c2 = collections.Counter(prov[int(r["our_province"])] for r in sub)
for k, v in c2.most_common():
    w("  %-20s %d" % (k, v))

w("\n==== 样例：CU 有印度教 rite 的 barony（前 60）====")
HINDU_CU = {"vaishnavism", "krishnaism", "shaivism", "srikula_shaktism",
            "kalikula_shaktism", "smartism"}
n = 0
for r in sub:
    if r["cu_rite"] in HINDU_CU:
        n += 1
        if n <= 60:
            w("  %-24s p%-6d county=%-18s 我们=%-16s CU=%s" %
              (r["barony"], int(r["our_province"]), r["our_county"], r["our_faith"], r["cu_rite"]))
w("  ... 合计 CU 印度教 rite 行: %d" % n)

w("\n==== CU 为空 / 非印度教的样例（前 40）====")
n = 0
for r in sub:
    if r["cu_rite"] not in HINDU_CU:
        n += 1
        if n <= 40:
            w("  %-24s p%-6d county=%-18s 我们=%-16s CU=%s" %
              (r["barony"], int(r["our_province"]), r["our_county"], r["our_faith"],
               r["cu_rite"] or "(空)"))
w("  ... 合计非印度教/空: %d" % n)

# 覆盖：有多少印度教 province 根本没进 csv
in_csv = {int(r["our_province"]) for r in rows}
missing = sorted(hindu_pids - in_csv)
w("\n==== 印度教 province 但不在 CU csv 里（按 barony 名对不上）: %d ====" % len(missing))
w("  %s%s" % (missing[:40], " ..." if len(missing) > 40 else ""))

out.close()
print("done")
