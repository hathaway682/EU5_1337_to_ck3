# -*- coding: utf-8 -*-
"""伊察改挂 d_peten、马圭拉改挂 d_kongo（用户 2026-11-15 指令）。

伊察 ITZ：原本自铸 d_eu5_itz（titular，capital c_tah_itza）。
  d_peten 是地图上真实公国，capital 正是 c_tah_itza，直接把 history 块改名过去。
马圭拉 MPE：原本挂 c_wizi（伯国级，note 记 rebind to c_wizi (was d_eu5_mpe)）。
  c_wizi 的 de jure 父公国就是 d_kongo，改挂回公国级。
  （用户写 d_congo，库里实际键名是 d_kongo，已确认。）

改动：
1 history/titles/zz_eu5_titles.txt  d_eu5_itz 块改名 d_peten；新增 d_kongo 块（holder eu5_regent_mpe）
2 common/landed_titles/zz_eu5_titular.txt  删 d_eu5_itz 声明
3 localization/*/zz_eu5_politics_l_*.yml   删 d_eu5_itz 条目（11 语言）
4 gen_debug/eu5_titles_dropped.txt         追加 d_eu5_itz
5 gen_debug/eu5_ck3_title_map.csv          ITZ / MPE 两行 ck3_key、tier、名字、note
6 gen_debug/_title_overrides.csv           追加两行

写入一律 读全文 -> 替换 -> 临时文件 -> os.replace，绝不对原文件开 wb。
"""
import glob
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def P(*a):
    return os.path.join(ROOT, *a)

def read(p):
    with io.open(p, "r", encoding="utf-8-sig", newline="") as f:
        return f.read()

def write(p, text):
    tmp = p + ".tmp_itzmpe"
    with io.open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        f.write(text)
    os.replace(tmp, p)

changed = []

# ---------- 1. history ----------
p = P("history", "titles", "zz_eu5_titles.txt")
t = read(p)
old_itz = (
    "d_eu5_itz = {\n"
    "\t1337.4.1 = {\n"
    "\t\tholder = itz_kan_ek\n"
    "\t\tgovernment = feudal_government\n"
    "\t}\n"
    "}\n"
)
new_block = (
    "d_peten = {\n"
    "\t1337.4.1 = {\n"
    "\t\tholder = itz_kan_ek\n"
    "\t\tgovernment = feudal_government\n"
    "\t}\n"
    "}\n"
    "\n"
    "d_kongo = {\n"
    "\t1337.4.1 = {\n"
    "\t\tholder = eu5_regent_mpe\n"
    "\t\tgovernment = feudal_government\n"
    "\t}\n"
    "}\n"
)
if "d_peten = {\n\t1337.4.1 = {\n\t\tholder = itz_kan_ek" in t:
    print(" - history: 已是目标状态，跳过")
elif old_itz in t:
    t = t.replace(old_itz, new_block, 1)
    write(p, t)
    changed.append("history: d_eu5_itz -> d_peten, +d_kongo")
else:
    raise SystemExit("history: 找不到 d_eu5_itz 原块，未改动")

# ---------- 2. titular 声明 ----------
p = P("common", "landed_titles", "zz_eu5_titular.txt")
t = read(p)
NL = "\r\n" if "\r\n" in t else "\n"
old_decl = NL.join([
    "d_eu5_itz = {",
    "\tlandless = yes",
    "\tcolor = { 94 236 191 }",
    "\tcapital = c_tah_itza",
    "}", "", "",
])
if old_decl in t:
    t = t.replace(old_decl, "", 1)
    write(p, t)
    changed.append("titular: 删 d_eu5_itz 声明")
else:
    print(" - titular: 无 d_eu5_itz 声明，跳过")

# ---------- 3. 本地化 ----------
n_loc = 0
for f in sorted(glob.glob(P("localization", "*", "zz_eu5_politics_l_*.yml"))):
    t = read(f)
    lines = t.split("\n")
    keep = [ln for ln in lines if not ln.lstrip().startswith("d_eu5_itz:")]
    if len(keep) != len(lines):
        write(f, "\n".join(keep))
        n_loc += 1
if n_loc:
    changed.append("本地化: %d 个语言删 d_eu5_itz" % n_loc)
else:
    print(" - 本地化: 已无 d_eu5_itz，跳过")

# ---------- 4. dropped ----------
p = P("gen_debug", "eu5_titles_dropped.txt")
t = read(p)
if "d_eu5_itz" not in t.split("\n"):
    if not t.endswith("\n"):
        t += "\n"
    t += "d_eu5_itz\n"
    write(p, t)
    changed.append("dropped: +d_eu5_itz")
else:
    print(" - dropped: 已有 d_eu5_itz，跳过")

# ---------- 5. CSV ----------
p = P("gen_debug", "eu5_ck3_title_map.csv")
t = read(p)
subs = [
    ("country,ITZ,d,Itza,伊察,,,d_eu5_itz,d,Itza,伊察,itz_kan_ek,itz_kan_ek,,feudal_government,yes,",
     "country,ITZ,d,Itza,伊察,,,d_peten,d,Peten,佩滕,itz_kan_ek,itz_kan_ek,,feudal_government,yes,rebind to d_peten (was d_eu5_itz)"),
    ("country,MPE,d,Maguela,马圭拉,,,c_wizi,c,Wizi,维济,eu5_regent_mpe,eu5_regent_mpe,,feudal_government,yes,generated-regent | rebind to c_wizi (was d_eu5_mpe)",
     "country,MPE,d,Maguela,马圭拉,,,d_kongo,d,Congo,刚果,eu5_regent_mpe,eu5_regent_mpe,,feudal_government,yes,generated-regent | rebind to d_kongo (was d_eu5_mpe)"),
]
n_csv = 0
for a, b in subs:
    if a in t:
        t = t.replace(a, b, 1)
        n_csv += 1
if n_csv:
    write(p, t)
    changed.append("csv: %d 行改绑" % n_csv)
else:
    print(" - csv: 无待改行（可能已落地），跳过")

# ---------- 6. overrides ----------
p = P("gen_debug", "_title_overrides.csv")
t = read(p)
OLD_MPE = "country,MPE,title_key,c_wizi,改挂到伯爵领 c_wizi（原 d_eu5_mpe）"
NEW_MPE = "country,MPE,title_key,d_kongo,改挂到公国 d_kongo（原 c_wizi）"
if OLD_MPE in t:
    t = t.replace(OLD_MPE, NEW_MPE, 1)
    write(p, t)
    changed.append("overrides: MPE 行 c_wizi -> d_kongo")
rows = [
    ("ITZ", "country,ITZ,title_key,d_peten,改挂到公国 d_peten（原 d_eu5_itz）"),
]
n_ovr = 0
for tag, row in rows:
    if ("\ncountry,%s,title_key," % tag) not in t:
        if not t.endswith("\n"):
            t += "\n"
        t += row + "\n"
        n_ovr += 1
if n_ovr:
    write(p, t)
    changed.append("overrides: +%d 行" % n_ovr)
else:
    print(" - overrides: ITZ 行已存在，跳过")

print("完成:")
for c in changed:
    print(" -", c)
if not changed:
    print(" - 无改动")
