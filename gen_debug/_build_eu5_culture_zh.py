# -*- coding: utf-8 -*-
"""从 EU5 取中文文化名，覆盖我们 mod 的 2088 个文化。

取源优先级：
  1. EU5 官方中文本地化（main_menu/localization/simp_chinese/**.yml）
  2. EU5 文化定义文件里的行内注释（in_game/common/cultures/*.txt → `zhongyuan_culture = { #中原`）
  3. CK3 原版中文名（key 撞上 CK3 时）
  4. 都没有则留空

注意：EU5 本地化里**有些文化用裸键**（andalusi = 安达卢斯），有些带 _culture 后缀
（turkmen_culture = 土库曼）；而裸键会和**人名键**撞车（han = 汉恩，是名字不是汉族）。
所以只接受「确实是 EU5 文化定义里存在的 key」的本地化条目。
"""
import io, os, re, csv

EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"
MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
OUT = os.path.join(MOD, "gen_debug", "_eu5_culture_zh.csv")

RE_LOC = re.compile(r'^\s*([A-Za-z0-9_.]+):\s*"([^"]*)"\s*(?:#.*)?$')
RE_DEF_KEY = re.compile(r'^\s*([a-z0-9_]+)\s*=\s*\{')
RE_DEF_CMT = re.compile(r'^\s*([a-z0-9_]+)\s*=\s*\{[^#\n]*#\s*([^\n#]+?)\s*$')

# ---- 1) EU5 文化定义里出现过哪些 key ----
cult_keys = set()
cmt = {}
defdir = os.path.join(EU5, "in_game", "common", "cultures")
for root, _, files in os.walk(defdir):
    for fn in files:
        if not fn.endswith(".txt"):
            continue
        for line in io.open(os.path.join(root, fn), encoding="utf-8-sig", errors="replace"):
            m = RE_DEF_KEY.match(line)
            if m:
                cult_keys.add(m.group(1))
            m = RE_DEF_CMT.match(line)
            if m and re.search(r"[\u4e00-\u9fff]", m.group(2)):
                cmt.setdefault(m.group(1), m.group(2).strip())

# ---- 2) 官方中文本地化 ----
zh = {}
locdir = os.path.join(EU5, "main_menu", "localization", "simp_chinese")
for root, _, files in os.walk(locdir):
    for fn in files:
        if not fn.endswith(".yml"):
            continue
        for line in io.open(os.path.join(root, fn), encoding="utf-8-sig", errors="replace"):
            m = RE_LOC.match(line)
            if m and m.group(1) not in zh:
                zh[m.group(1)] = m.group(2)

# ---- 3) CK3 原版中文名兜底 ----
ck3 = {}
p = os.path.join(MOD, "gen_debug", "_ck3_culture_names.csv")
if os.path.exists(p):
    for r in csv.DictReader(io.open(p, encoding="utf-8-sig")):
        if r["name_zh"]:
            ck3[r["culture"]] = r["name_zh"]

ours = list(csv.DictReader(io.open(os.path.join(MOD, "gen_debug", "_culture_classify_base.csv"),
                                   encoding="utf-8-sig")))

rows = []
for o in ours:
    c = o["culture"]
    base = c[:-8] if c.endswith("_culture") else c
    cands = [c, c + "_culture", base, base + "_culture"]
    nm, s = "", ""
    for k in cands:
        if k in cult_keys and k in zh:
            nm, s = zh[k], "EU5本地化"
            break
    if not nm:
        for k in cands:
            if k in cmt:
                nm, s = cmt[k], "EU5定义注释"
                break
    if not nm and base in ck3:
        nm, s = ck3[base], "CK3原版"
    rows.append({"culture": c, "name_en": o["name_en"], "name_zh": nm, "source": s,
                 "baronies": o["baronies"]})

with io.open(OUT, "w", encoding="utf-8-sig", newline="") as fp:
    w = csv.DictWriter(fp, fieldnames=["culture", "name_en", "name_zh", "source", "baronies"])
    w.writeheader()
    w.writerows(rows)

import collections
print("EU5 文化定义 key %d 个" % len(cult_keys))
print("覆盖统计：", dict(collections.Counter(r["source"] or "缺失" for r in rows)))
miss = [r for r in rows if not r["name_zh"]]
print("缺中文名 %d 个：" % len(miss))
for r in miss[:50]:
    print("  %-28s %s" % (r["culture"], r["name_en"]))
