# -*- coding: utf-8 -*-
"""把「同名直接对应」的宗教映射投到地图上（改写省份 faith）。

输入：
  _same_name_religion_map.csv        eu5_religion -> ck3_faith（42 条）
  common/landed_titles/00_landed_titles.txt   男爵领 b_<location> -> province id
  EU5 main_menu/setup/start/06_pops.txt       location -> religion -> size
  history/provinces/00_generated_provinces.txt  当前 faith

口径：
  每个男爵领取它对应 EU5 location 的人口多数宗教；
  该宗教若在映射表里，就把它改写为映射到的 CK3 faith；不在表里的省份不动。

用法：
  python _apply_same_name_religions.py            # 只出计划，不写
  python _apply_same_name_religions.py --apply    # 备份后写入
"""
import io, os, re, csv, sys, shutil, datetime, collections

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"
GD = os.path.join(MOD, "gen_debug")
MAP = os.path.join(GD, "_same_name_religion_map.csv")
SRC = os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt")
PLAN = os.path.join(GD, "_religion_map_projection.csv")

APPLY = "--apply" in sys.argv


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


# ---------- 1) 映射表 ----------
fmap = {}
for r in csv.DictReader(io.open(MAP, encoding="utf-8-sig")):
    fmap[r["eu5_religion"]] = r["ck3_faith"]
print("映射表 %d 条" % len(fmap))

# ---------- 2) 男爵领 -> province id ----------
barony_prov, stack = {}, []
for line in read(os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt")).split("\n"):
    if "{" in line and "}" in line:
        continue
    m = re.match(r"^\s*([A-Za-z0-9_]+)\s*=\s*\{", line)
    if m:
        stack.append(m.group(1))
        continue
    if re.match(r"^\s*\}", line):
        if stack:
            stack.pop()
        continue
    mp = re.search(r"\bprovince\s*=\s*(\d+)", line)
    if mp and stack and stack[-1].startswith("b_"):
        barony_prov[stack[-1][2:]] = int(mp.group(1))
print("男爵领 -> province: %d" % len(barony_prov))

# ---------- 3) pops: location -> religion -> size ----------
pop_rel = collections.defaultdict(collections.Counter)
pt = read(os.path.join(EU5, "main_menu", "setup", "start", "06_pops.txt"))
for m in re.finditer(r"(?ms)^[ \t]*([a-z0-9_']+)[ \t]*=[ \t]*\{\n(.*?)^[ \t]*\}", pt):
    loc = m.group(1)
    for pm in re.finditer(r"define_pop\s*=\s*\{([^}]*)\}", m.group(2)):
        pb = pm.group(1)
        sz = re.search(r"\bsize\s*=\s*([0-9.]+)", pb)
        rl = re.search(r"\breligion\s*=\s*([a-z0-9_]+)", pb)
        if sz and rl:
            pop_rel[loc][rl.group(1)] += float(sz.group(1))
print("有 pops 的 location: %d" % len(pop_rel))

# ---------- 4) 读省份当前 faith ----------
raw = read(SRC)
cur = {}
for m in re.finditer(r"(?m)^(\d+)\s*=\s*\{", raw):
    pid = int(m.group(1))
    body = raw[m.end() - 1:]
    d = 0
    for j, ch in enumerate(body):
        if ch == "{":
            d += 1
        elif ch == "}":
            d -= 1
            if d == 0:
                body = body[:j + 1]
                break
    f = re.search(r"(?m)^\s*faith\s*=\s*(\S+)", body)
    cur[pid] = f.group(1) if f else None
print("省份 %d" % len(cur))

# ---------- 5) 生成计划 ----------
plan, stat = {}, collections.Counter()
hit_rel = collections.Counter()
for loc, pid in barony_prov.items():
    rels = pop_rel.get(loc)
    if not rels:
        stat["无人口数据"] += 1
        continue
    eu5rel, _ = min(rels.items(), key=lambda kv: (-kv[1], kv[0]))
    if eu5rel not in fmap:
        stat["EU5宗教不在映射表"] += 1
        continue
    new = fmap[eu5rel]
    old = cur.get(pid)
    hit_rel[eu5rel] += 1
    if old == new:
        stat["已经是目标 faith"] += 1
    else:
        stat["需改写"] += 1
        plan[pid] = (old, new, eu5rel)

print()
for k, v in stat.most_common():
    print("  %-22s %d" % (k, v))
print("  命中映射的省份合计 %d" % sum(hit_rel.values()))
print()
print("== 命中映射的 EU5 宗教（按省份数）==")
for r, n in hit_rel.most_common():
    print("  %-28s -> %-24s %4d" % (r, fmap[r], n))

with io.open(PLAN, "w", encoding="utf-8-sig", newline="") as fp:
    w = csv.DictWriter(fp, fieldnames=["province", "old_faith", "new_faith", "eu5_religion"],
                       lineterminator="\n")
    w.writeheader()
    for pid, (o, n, r) in sorted(plan.items()):
        w.writerow({"province": pid, "old_faith": o, "new_faith": n, "eu5_religion": r})
print("\n计划写出 %s（%d 行）" % (PLAN, len(plan)))

if not APPLY:
    print("（未写入，加 --apply 才改省份文件）")
    sys.exit(0)

# ---------- 6) 落盘 ----------
bak = SRC + ".bak_relmap_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy2(SRC, bak)
out = raw
n = 0
for pid, (old, new, rel) in plan.items():
    pat = re.compile(r"(?m)^(%d\s*=\s*\{)(.*?)(^\})" % pid, re.S)
    m = pat.search(out)
    if not m:
        continue
    body = m.group(2)
    nb = re.sub(r"(?m)^(\s*faith\s*=\s*)\S+", r"\g<1>" + new, body, count=1)
    if nb != body:
        out = out[:m.start(2)] + nb + out[m.end(2):]
        n += 1
io.open(SRC, "w", encoding="utf-8-sig", newline="").write(out)
print("已写入 %d 处，备份 %s" % (n, os.path.basename(bak)))
