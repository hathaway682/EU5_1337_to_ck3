# -*- coding: utf-8 -*-
"""只读：_cu_barony_detail.csv 里印度教省份的 CU 数据覆盖与分布"""
import io, os, csv, collections

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
D = os.path.join(MOD, "gen_debug", "_cu_barony_detail.csv")
SRC = os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt")

out = io.open(os.path.join(MOD, "gen_debug", "_hindu_cu_probe2.out"), "w", encoding="utf-8")
def w(s=""):
    out.write(str(s) + "\n")

rows = list(csv.DictReader(io.open(D, encoding="utf-8-sig")))
w("_cu_barony_detail 行数: %d" % len(rows))
w("列: %s" % list(rows[0].keys()))

HINDU = {"vaishnava_faith", "shaiva_faith", "shakta_faith", "smartism"}
h = [r for r in rows if r["our_faith"] in HINDU]
w("\n其中 our_faith 是印度教系: %d" % len(h))

w("\n==== cu_rite 分布（印度教系行）====")
for k, v in collections.Counter(r["cu_rite"] or "(空)" for r in h).most_common(30):
    w("  %-28s %d" % (k, v))

w("\n==== 按 eu5_religion ====")
for k, v in collections.Counter(r["eu5_religion"] for r in h).most_common(20):
    w("  %-28s %d" % (k, v))

w("\n==== 按 region ====")
for k, v in collections.Counter(r["region"] for r in h).most_common(30):
    w("  %-28s %d" % (k, v))

w("\n==== eu5_religion == hindu 且 cu_rite 是印度教的 ====")
CUH = {"vaishnavism", "krishnaism", "shaivism", "srikula_shaktism",
       "kalikula_shaktism", "smartism"}
n = 0
for r in h:
    if r["eu5_religion"] == "hindu" and r["cu_rite"] in CUH:
        n += 1
w("  %d 行" % n)

w("\n==== eu5_religion 分布（全部行，看 hindu 有多少 barony）====")
allh = [r for r in rows if r["eu5_religion"] == "hindu"]
w("  eu5_religion==hindu 的 barony 行: %d" % len(allh))
w("  其中 cu_rite 有值: %d" % len([r for r in allh if r["cu_rite"]]))
for k, v in collections.Counter(r["cu_rite"] or "(空)" for r in allh).most_common(20):
    w("    %-24s %d" % (k, v))

w("\n==== 当前 shaiva_faith 的 68 个省在哪 ====")
txt = io.open(SRC, encoding="utf-8-sig", errors="ignore").read()
prov = {}
for m in re.finditer(r"(?m)^(\d+) = \{(.*?)\n\}", txt, re.S):
    f = re.search(r"(?m)^\s*faith = (\S+)", m.group(2))
    prov[int(m.group(1))] = f.group(1) if f else None
p2c = {int(r["province"]): r for r in rows}
c = collections.Counter()
for p, f in prov.items():
    if f == "shaiva_faith":
        r = p2c.get(p)
        c[(r["region"] if r else "?", r["eu5_religion"] if r else "?")] += 1
for k, v in c.most_common(20):
    w("  %-30s %d" % (str(k), v))

out.close()
print("done")
