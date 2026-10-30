# -*- coding: utf-8 -*-
"""把 EU5 location 的 development 聚合到 CK3 county（取所属 EU5 province 的最高值）。

只读，输出 gen_debug/_county_development.csv
"""
import os, csv, collections

ROOT = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
DEV = os.path.join(ROOT, "gen_debug", "_eu5_development.csv")
PROVMAP = os.path.join(ROOT, "gen_debug", "_tier_province_map.csv")
OUT = os.path.join(ROOT, "gen_debug", "_county_development.csv")

# location -> development
locdev = {}
with open(DEV, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        locdev[r["location"]] = (float(r["development"]), r["province"])

# EU5 province -> 最高 development 的 location
prov_best = {}
for loc, (d, prov) in locdev.items():
    if not prov:
        continue
    cur = prov_best.get(prov)
    if cur is None or d > cur[0]:
        prov_best[prov] = (d, loc)

# province id -> barony / county
prov_barony, prov_county = {}, {}
with open(PROVMAP, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        if r["class"] != "land":
            continue
        prov_barony[int(r["province"])] = r["barony"]
        prov_county[int(r["province"])] = r["county"]

# county -> 所属 EU5 province 集合
county_provs = collections.defaultdict(set)
county_prov_ids = collections.defaultdict(list)
miss_barony = []
for pid, bar in prov_barony.items():
    loc = bar[2:] if bar.startswith("b_") else bar
    if loc not in locdev:
        miss_barony.append((pid, bar, loc))
        continue
    prov = locdev[loc][1]
    c = prov_county[pid]
    county_prov_ids[c].append(pid)
    if prov:
        county_provs[c].add(prov)

rows = []
no_prov = []
for c, pids in sorted(county_prov_ids.items()):
    best = None
    for prov in county_provs[c]:
        cand = prov_best.get(prov)
        if cand and (best is None or cand[0] > best[0]):
            best = cand
    if best is None:
        # 兜底：这些 barony 的 location 在 EU5 里没有 province（沙漠/雨林/无人区），
        # 直接用 location 自身的 development
        own = []
        for pid in pids:
            bar = prov_barony[pid]
            loc = bar[2:] if bar.startswith("b_") else bar
            if loc in locdev:
                own.append((locdev[loc][0], loc))
        if own:
            best = max(own)
        else:
            no_prov.append(c)
            rows.append((c, "", "", "", len(pids)))
            continue
    rows.append((c, round(best[0], 2), best[1], ",".join(sorted(county_provs[c])), len(pids)))

with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    w = csv.writer(f)
    w.writerow(["county", "development", "best_location", "eu5_provinces", "n_provinces"])
    w.writerows(rows)

vals = sorted(float(r[1]) for r in rows if r[1] != "")
n = len(vals)
print(f"counties: {len(county_prov_ids)}  mapped: {n}  unmapped: {len(no_prov)}")
if n:
    print(f"dev min {vals[0]}  p10 {vals[n//10]}  p25 {vals[n//4]}  median {vals[n//2]}  "
          f"p75 {vals[3*n//4]}  p90 {vals[9*n//10]}  max {vals[-1]}")
    print(f"negative counties: {sum(1 for v in vals if v < 0)}")
print(f"barony 未在 EU5 location 里: {len(miss_barony)}")
for x in miss_barony[:10]:
    print("   ", x)
print(f"没有可用 EU5 province 的 county: {len(no_prov)}")
for x in no_prov[:15]:
    print("   ", x)
