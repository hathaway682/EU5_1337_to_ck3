# -*- coding: utf-8 -*-
"""按 EU5 province 的人口多数，给该 province 下所有男爵领写同一个 culture。

用户 2026-10-27 定：
  旧：按 EU5 location 的 culture 各自填到对应男爵领 → 同一伯爵领内五花八门。
  新：按 **EU5 province 的人口多数**（不是 location 个数）判断，同一个 province 填一个数据。

数据源（全部读游戏安装目录，只读）：
  * 06_pops.txt            location -> {culture: size}  人口，按 size 累加
  * definitions.txt        province -> [location]       （栈/正则解析 xxx_province = { ... }）
  * 00_landed_titles.txt   county -> [barony 名]         barony 名去掉 b_ 即 location 名
  * _culture_classification.csv  EU5 culture -> CK3 culture（cat1-cat9，跳过 NEW:）

口径：
  1. province 内所有 location 的 pop 按 culture 累加，取 size 最大的 culture。
  2. 该 province 对应的 CK3 county 下所有男爵领写这同一个 culture。
  3. province 查不到（94 个）/ 该 province 无 pop 数据时，退回「该 county 当前各男爵领的多数」。

默认 dry run，--apply 才写。BOM / CRLF 原样保留，只动 culture 值。
"""
import argparse
import collections
import csv
import io
import os
import re
import sys

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
GAME = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"

POPS = os.path.join(GAME, "main_menu", "setup", "start", "06_pops.txt")
DEFS = os.path.join(GAME, "in_game", "map_data", "definitions.txt")
LANDED = os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt")
PROV = os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt")
CLASSIF = os.path.join(MOD, "gen_debug", "_culture_classification.csv")

INSIDE_CATS = set("123456789")

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true")
ap.add_argument("--pops", default=POPS)
ap.add_argument("--defs", default=DEFS)
ap.add_argument("--landed", default=LANDED)
ap.add_argument("--provinces", default=PROV)
ap.add_argument("--classif", default=CLASSIF)
# 可选过滤：默认只跑图内（cat 1-9）。美洲/大洋洲图外批次需要 --cats 10,11
ap.add_argument("--cats", default="123456789",
                help="逗号分隔的 category 白名单，默认 123456789（图内）")
ap.add_argument("--continents", default="",
                help="逗号分隔的 continent 白名单，空=全部")
ap.add_argument("--only-selected", action="store_true",
                help="只改写 EU5 主体文化落在 --cats/--continents 白名单内的县，其余县一律不碰")
args = ap.parse_args()

CATS = set(x.strip() for x in args.cats.split(",") if x.strip())
CONT = set(x.strip() for x in args.continents.split(",") if x.strip())

# ---------- 1) location -> {culture: size} ----------
RE_LOC = re.compile(r"^\s*([a-z0-9_]+)\s*=\s*\{\s*$")
RE_POP = re.compile(r"define_pop\s*=\s*\{[^}]*?size\s*=\s*([0-9.]+)[^}]*?culture\s*=\s*([a-z0-9_]+)")
loc_cult = collections.defaultdict(collections.Counter)
cur = None
for line in io.open(args.pops, encoding="utf-8-sig", errors="ignore"):
    m = RE_LOC.match(line.rstrip("\n"))
    if m:
        cur = m.group(1)
        continue
    if "define_pop" in line:
        mm = RE_POP.search(line)
        if mm and cur:
            loc_cult[cur][mm.group(2)] += float(mm.group(1))
print("pops: %d locations" % len(loc_cult))

# ---------- 2) province -> [location] ----------
defs_txt = io.open(args.defs, encoding="utf-8-sig", errors="ignore").read()
prov_locs = {}
for m in re.finditer(r"(?m)^\s*([a-z0-9_]+)_province\s*=\s*\{([^}]*)\}", defs_txt):
    prov_locs[m.group(1)] = [x for x in m.group(2).split() if not x.startswith("#")]
print("provinces: %d" % len(prov_locs))

# ---------- 3) province -> 人口多数 culture ----------
prov_cult = {}
for pv, locs in prov_locs.items():
    tot = collections.Counter()
    for l in locs:
        for c, sz in loc_cult.get(l, {}).items():
            tot[c] += sz
    if tot:
        prov_cult[pv] = min(tot.items(), key=lambda kv: (-kv[1], kv[0]))[0]
print("provinces with pop majority: %d" % len(prov_cult))

# ---------- 4) EU5 culture -> CK3 culture ----------
# cmap：白名单内的行（默认图内 cat 1-9）一定进；--only-selected 时把白名单本身也并进来。
# sel ：--only-selected 下允许改写的 EU5 culture 集合。
cmap = {}
sel = set()
for r in csv.DictReader(io.open(args.classif, encoding="utf-8-sig")):
    c, t = r["culture"], r["target"]
    if not t or t.startswith("NEW:") or t == c:
        continue
    in_cat = r["category"] in (INSIDE_CATS | CATS)
    in_cont = (not CONT) or r.get("continent", "") in CONT
    if in_cat:
        cmap[c] = t
    if r["category"] in CATS and in_cont:
        sel.add(c)
        cmap[c] = t
print("culture map: %d | 本次可改写 %d" % (len(cmap), len(sel) if args.only_selected else len(cmap)))

# ---------- 5) county -> [barony 名] ----------
county_bar = collections.defaultdict(list)
cur = None
stack = []
for line in io.open(args.landed, encoding="utf-8-sig", errors="ignore"):
    s = line.strip()
    if not s or s.startswith("#"):
        continue
    m = re.match(r"^(c_[a-z0-9_]+)\s*=\s*\{", s)
    if m:
        cur = m.group(1)
        stack.append("c")
        continue
    m = re.match(r"^(b_[a-z0-9_]+)\s*=\s*\{", s)
    if m and cur:
        county_bar[cur].append(m.group(1)[2:])
        stack.append("b")
        continue
    if s == "}":
        if stack:
            stack.pop()
        if not any(x == "c" for x in stack):
            cur = None
print("counties: %d" % len(county_bar))

# ---------- 6) 读 provinces ----------
RE_BLOCK = re.compile(r"^(\d+) = \{$")
RE_CULT = re.compile(r'^([ \t]*)culture([ \t]*=[ \t]*)"?([A-Za-z0-9_]+)"?([ \t]*)(\r?)$')

raw = io.open(args.provinces, encoding="utf-8-sig", newline="").read()
lines = raw.split("\n")
cur_id = None
cult_line = {}
cult_now = {}
for i, line in enumerate(lines):
    s = line.rstrip("\r")
    m = RE_BLOCK.match(s)
    if m:
        cur_id = int(m.group(1))
        continue
    if s == "}":
        cur_id = None
        continue
    m = RE_CULT.match(s)
    if m and cur_id is not None:
        cult_line[cur_id] = i
        cult_now[cur_id] = m.group(3)
print("provinces file: %d culture lines" % len(cult_now))

# province id -> barony 名（用于反查 EU5 province）
# definition.csv 的 id 与 CK3 province id 不同，改用 barony 名反查
bar_prov = {}
for pv, locs in prov_locs.items():
    for l in locs:
        bar_prov[l] = pv

# ---------- 7) county -> 男爵领 province id（写盘用） ----------
county_pids = collections.defaultdict(list)
cur = None
stack = []
for line in io.open(args.landed, encoding="utf-8-sig", errors="ignore"):
    s = line.strip()
    if not s or s.startswith("#"):
        continue
    m = re.match(r"^(c_[a-z0-9_]+)\s*=\s*\{", s)
    if m:
        cur = m.group(1)
        stack.append("c")
        continue
    m = re.match(r"^(b_[a-z0-9_]+)\s*=\s*\{", s)
    if m:
        stack.append("b")
        continue
    m = re.match(r"^province\s*=\s*(\d+)", s)
    if m and "b" in stack and cur:
        county_pids[cur].append(int(m.group(1)))
    if s == "}":
        if stack:
            stack.pop()
        if not any(x == "c" for x in stack):
            cur = None

# ---------- 8) 每个 county 定目标 ----------
target = {}
src = collections.Counter()
for cty, bars in county_bar.items():
    # barony 名 -> EU5 province
    pvs = {bar_prov[b] for b in bars if b in bar_prov}
    pvs.discard(None)
    eu5 = None
    if len(pvs) == 1:
        pv = pvs.pop()
        if pv in prov_cult:
            eu5 = prov_cult[pv]
            src["pop"] += 1
    if eu5:
        if args.only_selected and eu5 not in sel:
            src["skip_not_selected"] += 1
            continue
        target[cty] = cmap.get(eu5, eu5)
        continue
    if args.only_selected:
        src["skip_not_selected"] += 1
        continue
    # fallback：该 county 当前各男爵领的多数，保证同县仍统一
    vals = [cult_now[p] for p in county_pids.get(cty, []) if p in cult_now]
    if vals:
        target[cty] = min(collections.Counter(vals).items(), key=lambda kv: (-kv[1], kv[0]))[0]
        src["fallback_unified"] += 1

print("county 目标：人口多数 %d | fallback（同县多数）%d | 跳过 %d | 总计 %d"
      % (src["pop"], src["fallback_unified"], src["skip_not_selected"], len(target)))

# ---------- 9) 生成改动 ----------
changes = []
prov_target = {}
for cty, tgt in target.items():
    for p in county_pids.get(cty, []):
        if p in cult_now:
            prov_target[p] = tgt
            if cult_now[p] != tgt:
                changes.append((p, cty, cult_now[p], tgt))

print("需改写 %d 行（%d 个 province）" % (len(changes), len({c[0] for c in changes})))

# 一致性检查
mixed_before = mixed_after = tot = 0
for cty, pids in county_pids.items():
    vals = [cult_now[p] for p in pids if p in cult_now]
    if len(vals) < 2:
        continue
    tot += 1
    if len(set(vals)) > 1:
        mixed_before += 1
    vals2 = [prov_target.get(p, cult_now[p]) for p in pids if p in cult_now]
    if len(set(vals2)) > 1:
        mixed_after += 1
print("county 内不一致：改前 %d/%d → 改后 %d/%d" % (mixed_before, tot, mixed_after, tot))

top = collections.Counter(c[3] for c in changes)
print("目标 culture top15:", top.most_common(15))

# 预演：种类变化
_new = dict(cult_now)
for p, cty, old, tgt in changes:
    _new[p] = tgt
_o = collections.Counter(cult_now.values())
_n = collections.Counter(_new.values())
_gone = sorted(((k, _o[k]) for k in set(_o) - set(_n)), key=lambda x: -x[1])
print("文化种类：%d → %d | 消失 %d 个（%d 省）"
      % (len(_o), len(_n), len(_gone), sum(v for _, v in _gone)))
_big = [(k, v) for k, v in _gone if v >= 5]
if _big:
    print("  其中 >=5 省的 %d 个：%s" % (len(_big), _big[:12]))

if not args.apply:
    print("\nDRY RUN：未写入。加 --apply 执行。")
    sys.exit(0)

for p, cty, old, new in changes:
    i = cult_line[p]
    line = lines[i]
    cr = "\r" if line.endswith("\r") else ""
    body = line.rstrip("\r")
    m = RE_CULT.match(body)
    ind, mid, tail = m.group(1), m.group(2), m.group(4)
    quote = '"' if '"' in body.split("=", 1)[1] else ""
    lines[i] = "%s%s%s%s%s%s%s" % (ind, "culture", mid, quote, new, quote, tail) + cr

io.open(args.provinces, "w", encoding="utf-8-sig", newline="").write("\n".join(lines))
print("已写入 %s" % args.provinces)
