# -*- coding: utf-8 -*-
"""八个国家改挂（用户 2026-11-17 20:12 指令）。

d_eu5_dgh -> d_tarim                  DGH 朵豁剌惕
d_eu5_mkr -> d_baluchistan            MKR 莫克兰（用户原写 b_baluchistan，确认为 d_baluchistan）
d_eu5_krt -> d_eastern_khorasan       KRT 库尔特
k_eu5_grg -> k_khorasan               GRG 朱里章
k_eu5_jal -> k_mesopotamia            JAL 札剌亦儿
d_eu5_sut -> d_armenian_highlands     SUT 速台
d_eu5_ath -> d_northern_greece        ATH 雅典
d_eu5_ach -> d_morea                  ACH 亚该亚

八个目标键在 history 里原本都没有块，整块改名，世系跟着走。
ATH 的 liege 保持 k_trinacria、ACH 的 liege 保持 k_naples（历史上分别是西西里、那不勒斯的附庸）。

改动：
1 history/titles/zz_eu5_titles.txt   八个块改键名；12 处属县 liege 跟着改
2 common/landed_titles/zz_eu5_titular.txt  删八个声明
3 localization  11 语言删八键、补 k_mesopotamia；9 个 zzzz 文件删八键及 _adj
4 gen_debug/eu5_titles_dropped.txt   +8
5 gen_debug/eu5_ck3_title_map.csv    8 行 country 改 key/tier/名字/note
6 gen_debug/_title_overrides.csv     +8

写入：读全文 -> 替换 -> 临时文件 -> os.replace。
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
    tmp = p + ".tmp_rebind8"
    with io.open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        f.write(text)
    os.replace(tmp, p)

MAP = [
    ("d_eu5_dgh", "d_tarim"),
    ("d_eu5_mkr", "d_baluchistan"),
    ("d_eu5_krt", "d_eastern_khorasan"),
    ("k_eu5_grg", "k_khorasan"),
    ("k_eu5_jal", "k_mesopotamia"),
    ("d_eu5_sut", "d_armenian_highlands"),
    ("d_eu5_ath", "d_northern_greece"),
    ("d_eu5_ach", "d_morea"),
]
changed = []

# ---------- 1. history ----------
p = P("history", "titles", "zz_eu5_titles.txt")
t = read(p)
for old, new in MAP:
    if re.search(r"(?m)^" + re.escape(new) + r" = \{", t):
        print(" - history: %s 已存在，跳过" % new)
        continue
    pat = re.compile(r"(?m)^" + re.escape(old) + r" = \{")
    if not pat.search(t):
        print(" - history: 找不到 %s，跳过" % old)
        continue
    t = pat.sub(new + " = {", t, count=1)
    changed.append("history: %s -> %s" % (old, new))
# 属县 liege
n_liege = 0
for old, new in MAP:
    c = t.count("liege = " + old)
    if c:
        t = t.replace("liege = " + old, "liege = " + new)
        n_liege += c
if n_liege:
    changed.append("history: %d 处属县 liege 跟着改" % n_liege)
write(p, t)

# ---------- 2. titular ----------
p = P("common", "landed_titles", "zz_eu5_titular.txt")
t = read(p)
n_tit = 0
for old, _ in MAP:
    pat = re.compile(
        r"(?m)^" + re.escape(old) +
        r" = \{\r?\n\tlandless = yes\r?\n\tcolor = \{[^}]*\}\r?\n\tcapital = \S+\r?\n\}\r?\n(\r?\n)?"
    )
    t, n = pat.subn("", t)
    n_tit += n
if n_tit:
    write(p, t)
    changed.append("titular: 删 %d 个声明" % n_tit)
else:
    print(" - titular: 无声明，跳过")

# ---------- 3. 本地化 ----------
OLDS = [o for o, _ in MAP]
n_loc = 0
FILES = sorted(glob.glob(P("localization", "*", "zz_eu5_politics_l_*.yml"))) + \
        sorted(glob.glob(P("localization", "*", "zzzz_eu5_title_missing_l_*.yml")))
for f in FILES:
    t = read(f)
    NL = "\r\n" if "\r\n" in t else "\n"
    lines = t.split(NL)
    keep = []
    for ln in lines:
        s = ln.lstrip()
        if any(s.startswith(o + ":") or s.startswith(o + "_adj:") for o in OLDS):
            continue
        keep.append(ln)
    changed_here = len(keep) != len(lines)
    # 只给 politics 文件补 k_mesopotamia
    if "zz_eu5_politics_l_" in f and "k_mesopotamia:" not in t:
        zh = "simp_chinese" in f
        while keep and keep[-1].strip() == "":
            keep.pop()
        keep.append(' k_mesopotamia:0 "%s"' % ("美索不达米亚" if zh else "Mesopotamia"))
        changed_here = True
    if changed_here:
        write(f, NL.join(keep) + NL)
        n_loc += 1
if n_loc:
    changed.append("本地化: %d 个文件（删八键 + 补 k_mesopotamia）" % n_loc)
else:
    print(" - 本地化: 无改动，跳过")

# ---------- 4. dropped ----------
p = P("gen_debug", "eu5_titles_dropped.txt")
t = read(p)
have = set(t.split("\n"))
add = [o for o in OLDS if o not in have]
if add:
    if not t.endswith("\n"):
        t += "\n"
    t += "\n".join(add) + "\n"
    write(p, t)
    changed.append("dropped: +%d" % len(add))
else:
    print(" - dropped: 已存在，跳过")

# ---------- 5. CSV ----------
p = P("gen_debug", "eu5_ck3_title_map.csv")
t = read(p)
CSV = {
    "DGH": ("d_eu5_dgh", "d_tarim,d,Tarim,塔里木"),
    "MKR": ("d_eu5_mkr", "d_baluchistan,d,Baluchistan,俾路支斯坦"),
    "KRT": ("d_eu5_krt", "d_eastern_khorasan,d,Eastern Khorasan,东呼罗珊"),
    "GRG": ("k_eu5_grg", "k_khorasan,k,Khorasan,呼罗珊"),
    "JAL": ("k_eu5_jal", "k_mesopotamia,k,Mesopotamia,美索不达米亚"),
    "SUT": ("d_eu5_sut", "d_armenian_highlands,d,Armenian Highlands,亚美尼亚高地"),
    "ATH": ("d_eu5_ath", "d_northern_greece,d,Northern Greece,北希腊"),
    "ACH": ("d_eu5_ach", "d_morea,d,Morea,摩里亚"),
}
import csv as _csv
import io as _io
lines = t.split("\r\n")
n_csv = 0
for i, ln in enumerate(lines):
    if not ln.startswith("country,"):
        continue
    tag = ln.split(",")[1]
    if tag not in CSV:
        continue
    old_key, new_mid = CSV[tag]
    rec = next(_csv.reader(_io.StringIO(ln)))
    if len(rec) < 17 or rec[7] != old_key:
        print(" - csv: %s 行已是 %s，跳过" % (tag, rec[7] if len(rec) > 7 else "?"))
        continue
    rec[7:11] = new_mid.split(",")
    rec[16] = "rebind to %s (was %s)" % (new_mid.split(",")[0], old_key)
    buf = _io.StringIO()
    _csv.writer(buf, lineterminator="").writerow(rec)
    lines[i] = buf.getvalue()
    n_csv += 1
if n_csv:
    write(p, "\r\n".join(lines))
    changed.append("csv: %d 行改绑" % n_csv)
else:
    print(" - csv: 无待改行，跳过")

# ---------- 6. overrides ----------
p = P("gen_debug", "_title_overrides.csv")
t = read(p)
n_ovr = 0
for tag, (old_key, new_mid) in CSV.items():
    new_key = new_mid.split(",")[0]
    if ("\ncountry,%s,title_key," % tag) in t:
        print(" - overrides: %s 已存在，跳过" % tag)
        continue
    if not t.endswith("\n"):
        t += "\n"
    t += "country,%s,title_key,%s,改挂到 %s（原 %s）\n" % (tag, new_key, new_key, old_key)
    n_ovr += 1
if n_ovr:
    write(p, t)
    changed.append("overrides: +%d" % n_ovr)

print("完成:")
for c in changed:
    print(" -", c)
