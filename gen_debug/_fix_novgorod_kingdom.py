# -*- coding: utf-8 -*-
"""NOV 诺夫哥罗德改挂 k_novgorod，并从莫斯科（k_opolye）独立。

依据（用户 2026-11-14 下令）：
- EU5 setup: NOV country_rank = rank_duchy, type = republic, 首都圈 own_control_core 含 novgorod 等
- k_novgorod 已存在于 common/landed_titles/00_landed_titles.txt（e_russia 下，de jure 含 d_east_novgorod）
- e_russia 在 history/titles 里无人持有 -> k_novgorod 归 NOV 后自然独立

改动四处：
1. history/titles/zz_eu5_titles.txt
   - 新建 k_novgorod 块（1337.4.1 holder = eu5_rep_nov, republic_government）
   - 删掉 d_east_novgorod 块内的 "1337.1.1 = { liege = k_opolye }"
     （同一 ruler 同时持有 k_novgorod 与 d_east_novgorod，不能再写 liege 指向旧宗主）
2. gen_debug/eu5_ck3_title_map.csv 的 country,NOV 行：d_east_novgorod/d -> k_novgorod/k，liege 清空
3. gen_debug/_title_overrides.csv 的 country,NOV 行同步
4. NOV 全部属地（holder 尾部是 eu5_rep_nov 的块）清掉 "1337.1.1 = { liege = k_opolye }"：
   29 个县 + d_karelia / d_pomorye / d_totma / d_west_novgorod 四个公国。
   依据：这些块 holder 就是 eu5_rep_nov，与莫斯科系（c_moscow 等）同构——同一 ruler
   持有 k_novgorod 与属地时不写 liege，写了反而仍算 k_opolye 的封臣。

幂等：已有 k_novgorod 块 / liege 段已删 / 行已改，重复执行无副作用。
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P_TITLES = os.path.join(ROOT, "history", "titles", "zz_eu5_titles.txt")
P_CSV = os.path.join(ROOT, "gen_debug", "eu5_ck3_title_map.csv")
P_OVR = os.path.join(ROOT, "gen_debug", "_title_overrides.csv")

NEW_BLOCK = (
    "k_novgorod = {\r\n"
    "\t1337.4.1 = {\r\n"
    "\t\tholder = eu5_rep_nov\r\n"
    "\t\tgovernment = republic_government\r\n"
    "\t}\r\n"
    "}\r\n\r\n"
)
LIEge_SEG = "\t1337.1.1 = {\r\n\t\tliege = k_opolye\r\n\t}\r\n"

OLD_ROW = ('country,NOV,d,Velikiy Novgorod,大诺夫哥罗德,,,d_east_novgorod,d,'
           'East Novgorod,东诺夫哥罗德,eu5_rep_nov,eu5_rep_nov,k_opolye,'
           'republic_government,yes,"consul,vassal,consul-holds"')
NEW_ROW = ('country,NOV,d,Velikiy Novgorod,大诺夫哥罗德,,,k_novgorod,k,'
           'Novgorod,诺夫哥罗德,eu5_rep_nov,eu5_rep_nov,,'
           'republic_government,yes,"consul,vassal,consul-holds,independent-of-MOS"')

OLD_OVR = "country,NOV,title_key,d_east_novgorod,首都所在公国，改绑（原 d_eu5_nov）"
NEW_OVR = "country,NOV,title_key,k_novgorod,升为王国 k_novgorod 并独立于莫斯科（原 d_eu5_nov → d_east_novgorod）"

changed = []

# ---------- 1. history/titles ----------
t = io.open(P_TITLES, encoding="utf-8-sig", newline="").read()
orig = t

start = t.find("d_east_novgorod = {")
if start < 0:
    sys.exit("找不到 d_east_novgorod 块")
nxt = t.find("\r\nk_novgorod = {", start)
# 找 d_east_novgorod 块后第一个顶层键
import re
m = re.compile(r"\r\n([a-z0-9_]+) = \{").search(t, start + len("d_east_novgorod = {"))
if not m:
    sys.exit("找不到 d_east_novgorod 块的结束位置")
block = t[start:m.start()]
if LIEge_SEG in block:
    t = t[:start] + block.replace(LIEge_SEG, "", 1) + t[m.start():]
    changed.append("titles: 删除 d_east_novgorod 的 liege = k_opolye")
else:
    changed.append("titles: d_east_novgorod 已无 liege = k_opolye（跳过）")

if "\r\nk_novgorod = {" in t or t.startswith("k_novgorod = {"):
    changed.append("titles: k_novgorod 块已存在（跳过插入）")
else:
    i = t.find("\r\nk_opolye = {")
    if i < 0:
        sys.exit("找不到 k_opolye 锚点")
    t = t[:i + 2] + NEW_BLOCK + t[i + 2:]
    changed.append("titles: 插入 k_novgorod 块（holder=eu5_rep_nov, republic_government）")

if t != orig:
    io.open(P_TITLES, "w", encoding="utf-8-sig", newline="").write(t)

# ---------- 2. title_map csv ----------
c = io.open(P_CSV, encoding="utf-8-sig", newline="").read()
if OLD_ROW + "\r\n" in c:
    c = c.replace(OLD_ROW + "\r\n", NEW_ROW + "\r\n", 1)
    io.open(P_CSV, "w", encoding="utf-8-sig", newline="").write(c)
    changed.append("csv: country,NOV 行改为 k_novgorod/k，liege 清空")
elif NEW_ROW + "\r\n" in c:
    changed.append("csv: country,NOV 行已是新值（跳过）")
else:
    sys.exit("csv: country,NOV 行未匹配，请人工检查")

# ---------- 3. overrides ----------
o = io.open(P_OVR, encoding="utf-8-sig", newline="").read()
if OLD_OVR + "\r\n" in o:
    o = o.replace(OLD_OVR + "\r\n", NEW_OVR + "\r\n", 1)
    io.open(P_OVR, "w", encoding="utf-8-sig", newline="").write(o)
    changed.append("overrides: NOV 改为 k_novgorod")
elif NEW_OVR + "\r\n" in o:
    changed.append("overrides: NOV 已是新值（跳过）")
else:
    sys.exit("overrides: NOV 行未匹配，请人工检查")

for x in changed:
    print(" -", x)

# ---------- 4. NOV 属地清 liege = k_opolye ----------
t = io.open(P_TITLES, encoding="utf-8-sig", newline="").read()
tops = [(m.group(1), m.start()) for m in re.finditer(r"(?m)^([a-z0-9_]+) = \{", t)]
tops.append(("__END__", len(t)))
SEG_MULTI = "\t1337.1.1 = {\r\n\t\tliege = k_opolye\r\n\t}\r\n"
SEG_ONE = "\t1337.1.1 = { liege = k_opolye }\r\n"

targets, skipped = [], []
for i in range(len(tops) - 1):
    name, s = tops[i]
    e = tops[i + 1][1]
    blk = t[s:e]
    if "liege = k_opolye" not in blk:
        continue
    holders = re.findall(r"holder = (\w+)", blk)
    if not holders or holders[-1] != "eu5_rep_nov":
        continue
    if SEG_MULTI in blk:
        targets.append((s, e, SEG_MULTI, name))
    elif SEG_ONE in blk:
        targets.append((s, e, SEG_ONE, name))
    else:
        skipped.append(name)

for s, e, seg, name in sorted(targets, key=lambda x: -x[0]):
    blk = t[s:e]
    t = t[:s] + blk.replace(seg, "", 1) + t[e:]

if targets:
    io.open(P_TITLES, "w", encoding="utf-8-sig", newline="").write(t)
print(" - 属地清 liege：%d 块 -> %s" % (len(targets), ", ".join(x[3] for x in sorted(targets, key=lambda y: y[3]))))
if skipped:
    print(" ! 以下块有 liege = k_opolye 但段格式不匹配，未处理：", skipped)

# CSV 里 29 个 county 行的 ck3_liege 同步清空
c = io.open(P_CSV, encoding="utf-8-sig", newline="").read()
lines = c.split("\r\n")
n = 0
for idx, line in enumerate(lines):
    if line.startswith("county,NOV,") and ",k_opolye,republic_government" in line:
        lines[idx] = line.replace(",k_opolye,republic_government", ",,republic_government", 1)
        n += 1
if n:
    io.open(P_CSV, "w", encoding="utf-8-sig", newline="").write("\r\n".join(lines))
print(" - csv: %d 个 NOV county 行清空 ck3_liege" % n)

# ---------- 5. 主头衔：eu5_rep_nov -> k_novgorod ----------
P_PRIM = os.path.join(ROOT, "common", "on_action", "zz_eu5_primary_titles.txt")
pm = io.open(P_PRIM, encoding="utf-8-sig", newline="").read()
OLD_PRIM = "set_primary_title_to = title:d_east_novgorod"
NEW_PRIM = "set_primary_title_to = title:k_novgorod"
if OLD_PRIM in pm:
    pm = pm.replace(OLD_PRIM, NEW_PRIM, 1)
    io.open(P_PRIM, "w", encoding="utf-8-sig", newline="").write(pm)
    print(" - primary_titles: eu5_rep_nov 主头衔 d_east_novgorod -> k_novgorod")
elif NEW_PRIM in pm:
    print(" - primary_titles: 已是 k_novgorod（跳过）")
else:
    print(" ! primary_titles: 未找到 eu5_rep_nov 的 d_east_novgorod 条目")
