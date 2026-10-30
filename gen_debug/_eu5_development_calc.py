# -*- coding: utf-8 -*-
"""按 EU5 14_development.txt 的公式，静态算出每个 location 的 development。

development = base
            + coastal(5 * natural_harbor_suitability)
            + river(0.5 * river_size)      <- 静态数据不可得，跳过
            + road(2)
            + rank(city 5 / town 2)
            + vegetation / climate / topography
            + region / area / province 修正
            + unique location 修正

只读，输出 gen_debug/_eu5_development.csv
"""
import os, re, csv, collections

EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"
SETUP = os.path.join(EU5, "main_menu", "setup", "1337")
ROOT = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
OUT = os.path.join(ROOT, "gen_debug", "_eu5_development.csv")


def read(p):
    with open(p, encoding="utf-8-sig", errors="replace") as f:
        return f.read()


# ---------- 1. 修正表 ----------
devtxt = read(os.path.join(SETUP, "14_development.txt"))
mods = {}
for ln in devtxt.splitlines():
    s = ln.split("#")[0].strip()
    m = re.match(r"^([A-Za-z0-9_]+)\s*=\s*(-?[0-9.]+)$", s)
    if m:
        mods[m.group(1)] = float(m.group(2))

# ---------- 2. definitions.txt 层级 ----------
deftxt = read(os.path.join(EU5, "in_game", "map_data", "definitions.txt"))
loc2prov, loc2area, loc2region = {}, {}, {}
stack = []


def assign(names, extra=None):
    # province 是 area 的直接子块；有些 province 名不带 _province 后缀（swat / hazara / balor）
    if extra:
        prov = extra
    elif stack and not stack[-1].endswith(("_area", "_region")):
        prov = stack[-1]
    else:
        prov = None
    area = next((x for x in reversed(stack) if x.endswith("_area")), None)
    region = next((x for x in reversed(stack) if x.endswith("_region")), None)
    for n in names:
        loc2prov[n] = prov
        loc2area[n] = area
        loc2region[n] = region


for ln in deftxt.splitlines():
    s = ln.split("#")[0].strip()
    if not s:
        continue
    opens, closes = s.count("{"), s.count("}")
    if opens and not closes:                      # 打开一个块
        m = re.match(r"^([A-Za-z0-9_-]+)\s*=\s*\{", s)
        stack.append(m.group(1) if m else "")
        continue
    if opens and closes:                          # 单行闭合：name = { loc ... }
        m = re.match(r"^([A-Za-z0-9_-]+)\s*=\s*\{(.*)\}\s*$", s)
        if m:
            assign(re.findall(r"[A-Za-z0-9_-]+", m.group(2)), extra=m.group(1))
        continue
    if closes and not opens:                      # 闭合
        # 关键：location 列表可能和 } 写在同一行，例如
        #   ganjam_garjats = { #5
        #       ganjam asika ... kulada }
        # 先处理 } 之前的内容，再出栈，否则这些 location 会全部丢失
        body = s.split("}")[0].strip()
        if body:
            assign(re.findall(r"[A-Za-z0-9_-]+", body))
        if stack:
            stack.pop()
        continue
    assign(re.findall(r"[A-Za-z0-9_-]+", s))      # 叶子行

# ---------- 3. location_templates: 地形/植被/气候/港口 ----------
ltxt = read(os.path.join(EU5, "in_game", "map_data", "location_templates.txt"))
topo, veg, clim, harbor = {}, {}, {}, {}
for m in re.finditer(r"^([A-Za-z0-9_]+)\s*=\s*\{([^}]*)\}", ltxt, re.M):
    name, body = m.group(1), m.group(2)
    for key, store in (("topography", topo), ("vegetation", veg), ("climate", clim)):
        mm = re.search(rf"\b{key}\s*=\s*([A-Za-z0-9_]+)", body)
        if mm:
            store[name] = mm.group(1)
    mm = re.search(r"natural_harbor_suitability\s*=\s*(-?[0-9.]+)", body)
    if mm:
        harbor[name] = float(mm.group(1))

# ---------- 4. rank ----------
ctxt = read(os.path.join(SETUP, "07_cities_and_buildings.txt"))
rank = {}
for m in re.finditer(r"^[ \t]*([A-Za-z0-9_]+)\s*=\s*\{[ \t]*rank[ \t]*=[ \t]*([a-z]+)", ctxt, re.M):
    rank[m.group(1)] = m.group(2)

# ---------- 5. coastal ----------
coastal = set()
for ln in read(os.path.join(EU5, "in_game", "map_data", "ports.csv")).splitlines():
    p = ln.split(";")
    if len(p) > 1 and p[0] and p[0] not in ("LandProvince",):
        coastal.add(p[0])

# ---------- 6. road ----------
road = set()
rtxt = read(os.path.join(SETUP, "09_roads.txt"))
for m in re.finditer(r"^[ \t]*([A-Za-z0-9_]+)\s*=\s*([A-Za-z0-9_]+)\s*$", rtxt, re.M):
    a, b = m.group(1), m.group(2)
    if a in ("road_network",):
        continue
    road.add(a); road.add(b)

# ---------- 6b. river size（从 rivers.png 像素取的） ----------
river_size = {}
rp = os.path.join(ROOT, "gen_debug", "_eu5_river_size.csv")
if os.path.exists(rp):
    with open(rp, encoding="utf-8") as f:
        next(f)
        for ln in f:
            k, v = ln.strip().split(",")
            river_size[k] = int(v)

# ---------- 7. 计算 ----------
all_locs = sorted(set(list(loc2prov) + list(topo) + list(rank)))
rows = []
for n in all_locs:
    d = mods.get("base", 0.0)
    if n in coastal:
        d += mods.get("coastal", 0.0) * harbor.get(n, 0.0)
    if n in river_size:
        d += mods.get("river", 0.0) * river_size[n]
    # road 修正不计入：用游戏内实测值反推，加 road 会让所有有路的 location 统一偏高 2
    # （君士坦丁堡 31→29、伦敦 37.5→35.5、德里 41.5→39.5、巴格达 18.5→16.5 才对齐）
    # 09_roads.txt 的连接图不等于 location 的 road 属性，road=2 的触发条件未知
    r = rank.get(n)
    if r in mods:
        d += mods[r]
    if veg.get(n) in mods:
        d += mods[veg[n]]
    if clim.get(n) in mods:
        d += mods[clim[n]]
    if topo.get(n) in mods:
        d += mods[topo[n]]
    if loc2region.get(n) in mods:
        d += mods[loc2region[n]]
    if loc2area.get(n) in mods:
        d += mods[loc2area[n]]
    if loc2prov.get(n) in mods:
        d += mods[loc2prov[n]]
    if n in mods:  # unique location
        d += mods[n]
    rows.append((n, loc2prov.get(n, ""), loc2area.get(n, ""), loc2region.get(n, ""),
                 rank.get(n, ""), veg.get(n, ""), clim.get(n, ""), topo.get(n, ""),
                 "1" if n in coastal else "", "1" if n in road else "",
             river_size.get(n, 0), round(d, 2)))

with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    w = csv.writer(f)
    w.writerow(["location", "province", "area", "region", "rank", "vegetation",
                "climate", "topography", "coastal", "road", "river", "development"])
    w.writerows(rows)

vals = [r[-1] for r in rows]
vals_sorted = sorted(vals)
n = len(vals_sorted)
print(f"locations: {n}")
print(f"min {vals_sorted[0]}  p10 {vals_sorted[n//10]}  p25 {vals_sorted[n//4]}  "
      f"median {vals_sorted[n//2]}  p75 {vals_sorted[3*n//4]}  p90 {vals_sorted[9*n//10]}  max {vals_sorted[-1]}")
print(f"no province assigned: {sum(1 for r in rows if not r[1])}")
print(f"rank counts: {collections.Counter(r[4] for r in rows)}")
print(f"coastal {len(coastal)}  road {len(road)}")
print("\ntop 15:")
for r in sorted(rows, key=lambda x: -x[-1])[:15]:
    print("  ", r)
print("\nbottom 10:")
for r in sorted(rows, key=lambda x: x[-1])[:10]:
    print("  ", r)
