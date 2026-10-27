# -*- coding: utf-8 -*-
"""给「无地块」文化按 EU5 人口分布定大洲。

分类 CSV 里的大洲是按**主导王国**判的，而 0 男爵领的文化没有王国，只能标「无地块」。
这类文化大多是散居/少数民族（犹太社群、汉语方言岛、小部族），人口是有的，
只是没占到任何一个男爵领的多数。所以改用 EU5 pops 找他们的主要人口落在哪。

流程：
  1. landed_titles/00_landed_titles.txt  男爵领 b_<location> → 所属王国 k_xxx
  2. EU5 main_menu/setup/start/06_pops.txt   location → culture → size
  3. 按王国汇总每个文化的 pops，取人口最多的王国

输出 _culture_pop_continent.csv（culture / pops_total / top_kingdom / top_share / pop_by_kingdom），
王国→大洲的映射仍由 _classify_cultures.py 里的 CONTINENT 负责，这里不重复定义。
"""
import io, os, re, sys, csv, collections

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"
GD = os.path.join(MOD, "gen_debug")
OUT = os.path.join(GD, "_culture_pop_continent.csv")


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


# ---------- 1) 男爵领 → 王国 ----------
barony_kingdom = {}
stack = []
for line in read(os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt")).split("\n"):
    if "{" in line and "}" in line:
        continue                      # 单行块，如 color = {1 2 3}
    m = re.match(r"^\s*([A-Za-z0-9_]+)\s*=\s*\{", line)
    if m:
        stack.append(m.group(1))
        continue
    if re.match(r"^\s*\}", line):
        if stack:
            stack.pop()
        continue
    if re.search(r"\bprovince\s*=\s*\d+", line) and stack and stack[-1].startswith("b_"):
        k = next((x for x in reversed(stack) if x.startswith("k_")), None)
        if k:
            barony_kingdom[stack[-1][2:]] = k[2:]
print("男爵领→王国: %d" % len(barony_kingdom))

# ---------- 2) pops: location → culture → size ----------
pop_cult = collections.defaultdict(collections.Counter)
pt = read(os.path.join(EU5, "main_menu", "setup", "start", "06_pops.txt"))
for m in re.finditer(r"(?ms)^[ \t]*([a-z0-9_']+)[ \t]*=[ \t]*\{\n(.*?)^[ \t]*\}", pt):
    loc = m.group(1)
    for pm in re.finditer(r"define_pop\s*=\s*\{([^}]*)\}", m.group(2)):
        pb = pm.group(1)
        sz = re.search(r"\bsize\s*=\s*([0-9.]+)", pb)
        cu = re.search(r"\bculture\s*=\s*([a-z0-9_]+)", pb)
        if sz and cu:
            pop_cult[loc][cu.group(1)] += float(sz.group(1))
print("有 pops 的 location: %d / 涉及文化 %d 种"
      % (len(pop_cult), len({c for v in pop_cult.values() for c in v})))

# ---------- 3) 按王国汇总 ----------
by_cult = collections.defaultdict(collections.Counter)
no_loc = collections.Counter()
for loc, cults in pop_cult.items():
    k = barony_kingdom.get(loc)
    for c, v in cults.items():
        if k:
            by_cult[c][k] += v
        else:
            no_loc[c] += v

rows = []
for c, ctr in by_cult.items():
    tot = sum(ctr.values()) + no_loc.get(c, 0)
    k, v = ctr.most_common(1)[0]
    rows.append({
        "culture": c,
        "pops_total": round(tot, 1),
        "top_kingdom": k,
        "top_share": round(100.0 * v / tot, 1) if tot else 0,
        "pop_by_kingdom": ";".join("%s:%d" % (kk, vv) for kk, vv in ctr.most_common(6)),
        "pops_unmapped": round(no_loc.get(c, 0), 1),
    })
rows.sort(key=lambda r: -r["pops_total"])

with io.open(OUT, "w", encoding="utf-8-sig", newline="") as fp:
    w = csv.DictWriter(fp, fieldnames=["culture", "pops_total", "top_kingdom", "top_share",
                                       "pop_by_kingdom", "pops_unmapped"], lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
print("写出 %s（%d 个文化）" % (OUT, len(rows)))
