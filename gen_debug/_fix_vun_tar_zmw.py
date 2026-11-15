# -*- coding: utf-8 -*-
"""VUN/TAR/ZMW 三个改挂（用户 2026-11-15 指令）。

- d_eu5_vun -> d_west_kongo    VUN 温古，两县 c_central_kongo / c_nzere 都在 d_west_kongo 的 de jure 下，
                              d_west_kongo 的 capital 就是 c_central_kongo。
- d_eu5_tar -> d_michoacan     TAR 普雷佩查（用户写 d_michoakan，库里真键 d_michoacan），
                              三县 c_ihuatzio / c_tzintzuntzan / c_zula 全在 d_michoacan 下，capital c_zula。
- k_eu5_zmw -> k_zimbabwe      ZMW 津巴布韦，六县全在 k_zimbabwe 的 de jure 下。

三个目标键在 history 里原本都没有块，直接整块改名（d_eu5_tar 的 5 段世系原样保留）。

改动：
1 history/titles/zz_eu5_titles.txt   三个顶层块改键名
2 common/landed_titles/zz_eu5_titular.txt  删三个 titular 声明
3 localization/*/zz_eu5_politics_l_*.yml   删三个键的条目（11 语言）
4 gen_debug/eu5_titles_dropped.txt         追加三个旧键
5 gen_debug/eu5_ck3_title_map.csv          三行 country 改 key/tier/名字/note
6 gen_debug/_title_overrides.csv           追加三行

写入：读全文 -> 替换 -> 临时文件 -> os.replace，绝不对原文件开 wb。
"""
import glob
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def P(*a):
    return os.path.join(ROOT, *a)

def read(p):
    with io.open(p, "r", encoding="utf-8-sig", newline="") as f:
        return f.read()

def write(p, text):
    tmp = p + ".tmp_vuntarzmw"
    with io.open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        f.write(text)
    os.replace(tmp, p)

changed = []

# ---------- 1. history 改键名 ----------
RENAMES = [
    ("d_eu5_vun", "d_west_kongo"),
    ("d_eu5_tar", "d_michoacan"),
    ("k_eu5_zmw", "k_zimbabwe"),
]
p = P("history", "titles", "zz_eu5_titles.txt")
t = read(p)
for old, new in RENAMES:
    if re.search(r"(?m)^%s = \{" % re.escape(new), t):
        print(" - history: %s 已存在，跳过" % new)
        continue
    pat = re.compile(r"(?m)^%s = \{" % re.escape(old))
    if not pat.search(t):
        print(" - history: 找不到 %s，跳过" % old)
        continue
    t = pat.sub("%s = {" % new, t, count=1)
    changed.append("history: %s -> %s" % (old, new))
write(p, t)

# ---------- 2. titular 删声明 ----------
p = P("common", "landed_titles", "zz_eu5_titular.txt")
t = read(p)
n_tit = 0
for old, _ in RENAMES:
    pat = re.compile(
        r"(?m)^%s = \{\r?\n\tlandless = yes\r?\n\tcolor = \{[^}]*\}\r?\n\tcapital = \S+\r?\n\}\r?\n(\r?\n)?"
        % re.escape(old)
    )
    t2, n = pat.subn("", t)
    if n:
        t = t2
        n_tit += n
if n_tit:
    write(p, t)
    changed.append("titular: 删 %d 个声明" % n_tit)
else:
    print(" - titular: 无声明，跳过")

# ---------- 3. 本地化 ----------
n_loc = 0
for f in sorted(glob.glob(P("localization", "*", "zz_eu5_politics_l_*.yml"))):
    t = read(f)
    lines = t.split("\n")
    keep = [ln for ln in lines if not any(ln.lstrip().startswith(o + ":") for o, _ in RENAMES)]
    if len(keep) != len(lines):
        write(f, "\n".join(keep))
        n_loc += 1
if n_loc:
    changed.append("本地化: %d 个语言删条目" % n_loc)
else:
    print(" - 本地化: 已无条目，跳过")

# ---------- 4. dropped ----------
p = P("gen_debug", "eu5_titles_dropped.txt")
t = read(p)
have = set(t.split("\n"))
add = [o for o, _ in RENAMES if o not in have]
if add:
    if not t.endswith("\n"):
        t += "\n"
    t += "\n".join(add) + "\n"
    write(p, t)
    changed.append("dropped: +%s" % ",".join(add))
else:
    print(" - dropped: 已存在，跳过")

# ---------- 5. CSV ----------
p = P("gen_debug", "eu5_ck3_title_map.csv")
t = read(p)
NEW_ROWS = {
    "VUN": ("d_eu5_vun", "d_west_kongo,d,West Kongo,西刚果",
            "rebind to d_west_kongo (was d_eu5_vun)"),
    "TAR": ("d_eu5_tar", "d_michoacan,d,Michoacan,米却肯",
            "rebind to d_michoacan (was d_eu5_tar)"),
    "ZMW": ("k_eu5_zmw", "k_zimbabwe,k,Zimbabwe,津巴布韦",
            "rebind to k_zimbabwe (was k_eu5_zmw) | generated-regent"),
}
lines = t.split("\r\n")
n_csv = 0
for i, ln in enumerate(lines):
    if not ln.startswith("country,"):
        continue
    tag = ln.split(",")[1]
    if tag not in NEW_ROWS:
        continue
    old_key, new_mid, new_note = NEW_ROWS[tag]
    if old_key not in ln:
        print(" - csv: %s 行已改绑，跳过" % tag)
        continue
    f = ln.split(",")
    # 字段：0 kind,1 tag,2 tier,3 en,4 zh,5 place_en,6 place_zh,7 key,8 tier,9 name_en,10 name_zh,
    #      11 eu5_holder,12 ck3_holder,13 liege,14 government,15 declared,16 note
    f[7:11] = new_mid.split(",")
    f[16] = new_note
    lines[i] = ",".join(f)
    n_csv += 1
if n_csv:
    write(p, "\r\n".join(lines))
    changed.append("csv: %d 行改绑" % n_csv)
else:
    print(" - csv: 无待改行，跳过")

# ---------- 6. overrides ----------
p = P("gen_debug", "_title_overrides.csv")
t = read(p)
OVR = [
    ("VUN", "country,VUN,title_key,d_west_kongo,改挂到公国 d_west_kongo（原 d_eu5_vun）"),
    ("TAR", "country,TAR,title_key,d_michoacan,改挂到公国 d_michoacan（原 d_eu5_tar）"),
    ("ZMW", "country,ZMW,title_key,k_zimbabwe,改挂到王国 k_zimbabwe（原 k_eu5_zmw）"),
]
n_ovr = 0
for tag, row in OVR:
    if ("\ncountry,%s,title_key," % tag) in t:
        print(" - overrides: %s 已存在，跳过" % tag)
        continue
    if not t.endswith("\n"):
        t += "\n"
    t += row + "\n"
    n_ovr += 1
if n_ovr:
    write(p, t)
    changed.append("overrides: +%d 行" % n_ovr)

print("完成:")
for c in changed:
    print(" -", c)
if not changed:
    print(" - 无改动")
