# -*- coding: utf-8 -*-
"""把文化分类表落到游戏：欧洲范围。

做三件事：
  1) history/provinces/00_generated_provinces.txt 里，欧洲文化的 culture 值改成分类表的 target
     （NEW: 前缀去掉；kazani 属草原方案，跳过）
  2) 新建 common/culture/cultures/zz_eu5_culture_merge.txt，定义 5 个新文化
     （anglo_irish / norse_gael / walloon 覆盖生成物同名 key；pomeranian / teutonic 全新）
  3) 新建 localization/simp_chinese/zz_eu5_culture_merge_l_simp_chinese.yml
     新文化中文名 + 让位改名（pommeranian→卡舒比、prussian→古普鲁士）

默认 dry-run；加 --apply 才写。
"""
import csv
import io
import os
import re
import shutil
import sys
import time

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
GEN = os.path.join(MOD, "gen_debug")
SRC = os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt")
CSV = os.path.join(GEN, "_culture_classification.csv")
CULT_OUT = os.path.join(MOD, "common", "culture", "cultures", "zz_eu5_culture_merge.txt")
LOC_OUT = os.path.join(MOD, "localization", "simp_chinese", "zz_eu5_culture_merge_l_simp_chinese.yml")

APPLY = "--apply" in sys.argv

# 草原组归亚洲方案，不落欧洲
SKIP = {"kazani"}


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


def fk(t):
    return t[4:] if t.startswith("NEW:") else t


# ---------- 1) 映射 ----------
rows = list(csv.DictReader(io.open(CSV, encoding="utf-8-sig")))
EU = {r["culture"]: r for r in rows if r.get("continent") == "欧洲"}
MAP = {}
for c, r in EU.items():
    if c in SKIP:
        continue
    t = fk(r["target"])
    if t and t != c:
        MAP[c] = t

print("欧洲文化 %d，需要改 culture 值的 %d" % (len(EU), len(MAP)))

# ---------- 2) 改省份 ----------
raw = read(SRC)
out = []
changed = 0
by_pair = {}
for line in raw.split("\n"):
    m = re.match(r"^(\s*)culture\s*=\s*(\S+)\s*$", line)
    if m:
        old = m.group(2)
        new = MAP.get(old)
        if new and new != old:
            changed += 1
            by_pair[(old, new)] = by_pair.get((old, new), 0) + 1
            out.append("%sculture = %s" % (m.group(1), new))
            continue
    out.append(line)
new_prov = "\n".join(out)
print("省份 culture 行改动 %d" % changed)
print("涉及映射对 %d 组" % len(by_pair))
print()
print("== 改动量 Top 20 ==")
for (o, n), c in sorted(by_pair.items(), key=lambda kv: -kv[1])[:20]:
    print("   %-26s -> %-22s %d" % (o, n, c))

if not APPLY:
    print("\n[dry-run] 未写文件。加 --apply 才写。")
    sys.exit(0)

# ---------- 3) 写省份 ----------
if new_prov != raw:
    ts = time.strftime("%Y%m%d_%H%M%S")
    bak = SRC + ".bak_eumerge_" + ts
    shutil.copy2(SRC, bak)
    io.open(SRC, "w", encoding="utf-8-sig", newline="\n").write(new_prov)
    print("\n省份已写入，备份:", os.path.basename(bak))
    print("花括号 %d / %d" % (new_prov.count("{"), new_prov.count("}")))
else:
    print("\n省份无变化")

# ---------- 4) 写文化定义 ----------
ctxt = read(os.path.join(MOD, "common", "culture", "cultures", "00_generated_cultures.txt"))


def old_color(key, default):
    """沿用 mod 现有定义的 color，避免地图配色跳变。"""
    m = re.search(r"(?m)^%s\s*=\s*\{.*?^\tcolor\s*=\s*(\{[^}]*\})" % re.escape(key), ctxt, re.S)
    return m.group(1).strip() if m else default


CULT_HEAD = """# =========================================================
# EU5 -> CK3 文化归并：欧洲方案（2026-10-21 用户定）
# 本文件由 gen_debug/_apply_eu_culture_merge.py 生成。
# zz_ 前缀晚于 00_generated_cultures.txt 加载，同名 key 覆盖生效。
#   anglo_irish / norse_gael / walloon  : 覆盖生成物同名定义（改 traditions 与 heritage/language）
#   pomeranian / teutonic        : 全新文化
# =========================================================

"""

BLOCKS = []

BLOCKS.append("""anglo_irish = {
\tcolor = %s
\tparents = { english irish }

\tethos = ethos_bureaucratic
\theritage = heritage_west_germanic
\tlanguage = language_anglic
\tmartial_custom = martial_custom_male_only
\thead_determination = head_determination_domain

\ttraditions = {
\t\ttradition_hereditary_hierarchy
\t\ttradition_chivalry
\t\ttradition_castle_keepers
\t\ttradition_pastoralists
\t\ttradition_poetry
\t\ttradition_maritime_mercantilism
\t}

\tname_list = name_list_english

\tcoa_gfx = { english_coa_gfx western_coa_gfx }
\tbuilding_gfx = { western_building_gfx }
\tclothing_gfx = { english_clothing_gfx western_clothing_gfx }
\tunit_gfx = { western_unit_gfx }
\thouse_coa_frame = house_frame_24
\thouse_coa_mask_offset = { 0.0 0.055 }
\thouse_coa_mask_scale = { 0.9 0.9 }

\tethnicities = {
\t\t25 = caucasian_blond
\t\t15 = caucasian_ginger
\t\t35 = caucasian_brown_hair
\t\t25 = caucasian_dark_hair
\t}
}
""" % old_color("anglo_irish", "{ 173 68 94 }"))

BLOCKS.append("""norse_gael = {
\tcolor = %s
\tparents = { norse gaelic }

\tethos = ethos_bellicose
\theritage = heritage_goidelic
\tlanguage = language_goidelic
\tmartial_custom = martial_custom_male_only
\thead_determination = head_determination_domain

\ttraditions = {
\t\ttradition_fishermen
\t\ttradition_strong_kinship
\t\ttradition_concubines
\t\ttradition_fp1_coastal_warriors
\t\ttradition_maritime_mercantilism
\t\ttradition_storytellers
\t}

\tname_list = name_list_gaelic

\tcoa_gfx = { scottish_coa_gfx western_coa_gfx }
\tbuilding_gfx = { western_building_gfx }
\tclothing_gfx = { northern_clothing_gfx }
\tunit_gfx = { western_unit_gfx }
\thouse_coa_frame = house_frame_24
\thouse_coa_mask_offset = { 0.0 0.055 }
\thouse_coa_mask_scale = { 0.9 0.9 }

\tethnicities = {
\t\t5 = caucasian_blond
\t\t30 = caucasian_ginger
\t\t35 = caucasian_brown_hair
\t\t30 = caucasian_dark_hair
\t}
}
""" % old_color("norse_gael", "{ 96 140 110 }"))

BLOCKS.append("""pomeranian = {
\tcolor = { 108 132 168 }
\tparents = { saxon pommeranian }

\tethos = ethos_stoic
\theritage = heritage_central_germanic
\tlanguage = language_saxon
\tmartial_custom = martial_custom_male_only
\thead_determination = head_determination_domain

\ttraditions = {
\t\ttradition_stand_and_fight
\t\ttradition_religious_patronage
\t\ttradition_maritime_mercantilism
\t}

\tname_list = name_list_saxon

\tcoa_gfx = { german_group_coa_gfx western_coa_gfx }
\tbuilding_gfx = { western_building_gfx }
\tclothing_gfx = { dde_hre_clothing_gfx western_clothing_gfx }
\tunit_gfx = { western_unit_gfx }
\thouse_coa_frame = house_frame_25
\thouse_coa_mask_offset = { 0.0 0.025 }
\thouse_coa_mask_scale = { 0.95 0.95 }

\tethnicities = {
\t\t25 = caucasian_blond
\t\t15 = caucasian_ginger
\t\t35 = caucasian_brown_hair
\t\t25 = caucasian_dark_hair
\t}
}
""")

BLOCKS.append("""walloon = {
\tcolor = %s
\tparents = { french dutch }

\tethos = ethos_courtly
\theritage = heritage_frankish
\tlanguage = language_french
\tmartial_custom = martial_custom_male_only
\thead_determination = head_determination_domain

\ttraditions = {
\t\ttradition_chanson_de_geste
\t\ttradition_hereditary_hierarchy
\t\ttradition_chivalry
\t\ttradition_parochialism
\t}

\tname_list = name_list_french

\tcoa_gfx = { french_coa_gfx frankish_group_coa_gfx western_coa_gfx }
\tbuilding_gfx = { western_building_gfx }
\tclothing_gfx = { french_clothing_gfx western_clothing_gfx }
\tunit_gfx = { western_unit_gfx }
\thouse_coa_frame = house_frame_03
\thouse_coa_mask_offset = { 0.0 0.055 }
\thouse_coa_mask_scale = { 0.9 0.9 }

\tethnicities = {
\t\t10 = caucasian_blond
\t\t5 = caucasian_ginger
\t\t45 = caucasian_brown_hair
\t\t35 = caucasian_dark_hair
\t}
}
""" % old_color("walloon", "{ 130 120 170 }"))

BLOCKS.append("""teutonic = {
\tcolor = { 74 86 104 }
\tparents = { saxon }

\tethos = ethos_stoic
\theritage = heritage_central_germanic
\tlanguage = language_saxon
\tmartial_custom = martial_custom_male_only
\thead_determination = head_determination_domain

\ttraditions = {
\t\ttradition_stand_and_fight
\t\ttradition_ruling_caste
\t\ttradition_religious_patronage
\t\ttradition_by_the_sword
\t}

\tname_list = name_list_saxon

\tcoa_gfx = { german_group_coa_gfx western_coa_gfx }
\tbuilding_gfx = { western_building_gfx }
\tclothing_gfx = { dde_hre_clothing_gfx western_clothing_gfx }
\tunit_gfx = { western_unit_gfx }
\thouse_coa_frame = house_frame_25
\thouse_coa_mask_offset = { 0.0 0.025 }
\thouse_coa_mask_scale = { 0.95 0.95 }

\tethnicities = {
\t\t25 = caucasian_blond
\t\t15 = caucasian_ginger
\t\t35 = caucasian_brown_hair
\t\t25 = caucasian_dark_hair
\t}
}
""")

io.open(CULT_OUT, "w", encoding="utf-8-sig", newline="\n").write(CULT_HEAD + "\n".join(BLOCKS))
print("文化定义已写:", os.path.basename(CULT_OUT))

# ---------- 5) 写本地化 ----------
LOC = """l_simp_chinese:
 anglo_irish:0 "盎格鲁‑爱尔兰"
 anglo_irish_collective_noun:0 "盎格鲁‑爱尔兰人"
 anglo_irish_prefix:0 "盎格鲁‑爱尔兰"
 norse_gael:0 "诺斯‑盖尔"
 norse_gael_collective_noun:0 "诺斯‑盖尔人"
 norse_gael_prefix:0 "诺斯‑盖尔"
 pomeranian:0 "波美拉尼亚"
 pomeranian_collective_noun:0 "波美拉尼亚人"
 pomeranian_prefix:0 "波美拉尼亚"
 walloon:0 "瓦隆"
 walloon_collective_noun:0 "瓦隆人"
 walloon_prefix:0 "瓦隆"
 teutonic:0 "普鲁士"
 teutonic_collective_noun:0 "普鲁士人"
 teutonic_prefix:0 "普鲁士"
 pommeranian:0 "卡舒比"
 pommeranian_collective_noun:0 "卡舒比人"
 pommeranian_prefix:0 "卡舒比"
 prussian:0 "古普鲁士"
 prussian_collective_noun:0 "古普鲁士人"
 prussian_prefix:0 "古普鲁士"
"""
io.open(LOC_OUT, "w", encoding="utf-8-sig", newline="\r\n").write(LOC)
print("本地化已写:", os.path.basename(LOC_OUT))
