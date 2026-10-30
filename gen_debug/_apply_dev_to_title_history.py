# -*- coding: utf-8 -*-
"""把 change_development_level 按 CK3 原版格式写成**独立的日期块**，
插在 c_xxx 块开头（holder 块之前）。

原版样例（game/history/titles/e_china.txt）：
    k_hedong = {
        867.1.1 = { change_development_level = 8 }
        867.1.1 = {
            holder = han_50000
            ...
        }
    }

用法：
    python gen_debug/_apply_dev_to_title_history.py --dry
    python gen_debug/_apply_dev_to_title_history.py
"""
import os, re, csv, sys, shutil

ROOT = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
DEV = os.path.join(ROOT, "gen_debug", "_county_development.csv")
TITLES = os.path.join(ROOT, "history", "titles", "zz_eu5_titles.txt")
BAK_T = r"F:\EU5_Modern_Borders_bak\history\titles"

DRY = "--dry" in sys.argv

dev = {}
with open(DEV, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["development"] == "":
            continue
        dev[r["county"]] = max(0, int(round(float(r["development"]))))
print("county 有值", len(dev))

raw = open(TITLES, "rb").read()
bom = raw.startswith(b"\xef\xbb\xbf")
text = raw.decode("utf-8-sig")
eol = "\r\n" if "\r\n" in text else "\n"
lines = text.split(eol)

# 1. 先清掉所有已存在的 change_development_level：两种历史写法都要清
#    a) 塞在 holder 块里：  \t\tchange_development_level = 24
#    b) 独立日期块：        \t1337.4.1 = { change_development_level = 24 }
def is_dev_line(ln):
    return bool(re.match(r"^\s*change_development_level\s*=", ln)
                or re.match(r"^\s*\d+\.\d+\.\d+ = \{ change_development_level = -?\d+ \}\s*$", ln))


clean = [ln for ln in lines if not is_dev_line(ln)]
print(f"清掉旧字段行 {len(lines) - len(clean)}")

# 2. 在每个 c_xxx 块开头插入独立日期块
out = []
i = 0
written = 0
while i < len(clean):
    m = re.match(r"^(c_[A-Za-z0-9_-]+) = \{", clean[i])
    if m and m.group(1) in dev:
        out.append(clean[i])
        out.append(f"\t1337.4.1 = {{ change_development_level = {dev[m.group(1)]} }}")
        written += 1
        i += 1
        continue
    out.append(clean[i])
    i += 1

print(f"插入独立 development 块 {written}")

if DRY:
    print("dry run")
    sys.exit(0)

os.makedirs(BAK_T, exist_ok=True)
b = os.path.join(BAK_T, "zz_eu5_titles.txt.bak_devblock_20261030")
if not os.path.exists(b):
    shutil.copy2(TITLES, b)
    print("已备份 ->", b)

with open(TITLES, "wb") as f:
    if bom:
        f.write(b"\xef\xbb\xbf")
    f.write(eol.join(out).encode("utf-8"))
print("已写入", TITLES)
