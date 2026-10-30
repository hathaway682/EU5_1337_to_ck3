# -*- coding: utf-8 -*-
"""把 EU5 development（按 province 内最高 location）写进 CK3 伯爵领历史的
change_development_level。

写入位置：每个 county 的首府 barony 对应 province id 块。
负值截断为 0（用户口径）。

用法：
    python gen_debug/_apply_county_development.py --dry
    python gen_debug/_apply_county_development.py
"""
import os, re, csv, sys, shutil, collections

ROOT = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
DEV = os.path.join(ROOT, "gen_debug", "_county_development.csv")
PROVMAP = os.path.join(ROOT, "gen_debug", "_tier_province_map.csv")
TARGET = os.path.join(ROOT, "history", "provinces", "00_generated_provinces.txt")
BAK_DIR = r"F:\EU5_Modern_Borders_bak\history\provinces"
BAK = os.path.join(BAK_DIR, "00_generated_provinces.txt.bak_dev_20261030")

DRY = "--dry" in sys.argv

# county -> development
dev = {}
with open(DEV, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["development"] == "":
            continue
        dev[r["county"]] = max(0, int(round(float(r["development"]))))

# county -> 首府 province id（CSV 里首次出现的那个）
capital = {}
with open(PROVMAP, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        if r["class"] != "land":
            continue
        c = r["county"]
        if c not in capital:
            capital[c] = int(r["province"])

prov_dev = {}
for c, d in dev.items():
    pid = capital.get(c)
    if pid is None:
        continue
    prov_dev[pid] = d

print(f"county 有值 {len(dev)}，落到 province {len(prov_dev)}")
print("值分布", collections.Counter(prov_dev.values()).most_common(12))

with open(TARGET, "rb") as f:
    raw = f.read()
bom = raw.startswith(b"\xef\xbb\xbf")
text = raw.decode("utf-8-sig")
lines = text.split("\r\n") if "\r\n" in text else text.split("\n")
eol = "\r\n" if "\r\n" in text else "\n"

out = []
i = 0
written = 0
replaced = 0
missing = set(prov_dev)
while i < len(lines):
    ln = lines[i]
    m = re.match(r"^(\d+)\s*=\s*\{", ln)
    if m and int(m.group(1)) in prov_dev:
        pid = int(m.group(1))
        missing.discard(pid)
        # 找块尾
        j = i + 1
        depth = 1
        while j < len(lines):
            depth += lines[j].count("{") - lines[j].count("}")
            if depth == 0:
                break
            j += 1
        block = lines[i:j + 1]
        val = prov_dev[pid]
        has = None
        for k, bl in enumerate(block):
            if re.match(r"^\s*change_development_level\s*=", bl):
                has = k
                break
        if has is not None:
            block[has] = re.sub(r"(change_development_level\s*=\s*)-?\d+",
                                rf"\g<1>{val}", block[has])
            replaced += 1
        else:
            # 插在闭合行之前，沿用块内已有缩进
            indent = "    "
            for bl in block[1:]:
                mm = re.match(r"^(\s+)\S", bl)
                if mm:
                    indent = mm.group(1)
                    break
            block.insert(len(block) - 1, f"{indent}change_development_level = {val}")
        written += 1
        out.extend(block)
        i = j + 1
        continue
    out.append(ln)
    i += 1

print(f"写入块 {written}（替换已有 {replaced}），没找到块的 province: {len(missing)}")
if missing:
    print("  样例", list(missing)[:10])

if DRY:
    print("dry run，未写文件")
    sys.exit(0)

os.makedirs(BAK_DIR, exist_ok=True)
if not os.path.exists(BAK):
    shutil.copy2(TARGET, BAK)
    print("已备份 ->", BAK)

data = eol.join(out)
with open(TARGET, "wb") as f:
    if bom:
        f.write(b"\xef\xbb\xbf")
    f.write(data.encode("utf-8"))
print("已写入", TARGET)
