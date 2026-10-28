# -*- coding: utf-8 -*-
"""收尾：① 在 zz 文件里把 prussian 覆盖成波罗的古普鲁士（西波罗的 30 男爵领用它）
        ② 删掉文化定义已不存在的 history/cultures/*.txt 孤儿文件
默认 dry-run。
"""
import glob
import io
import os
import re
import sys

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
BASE = r"E:/SteamLibrary/steamapps/common/Crusader Kings III/game"
ZZ = os.path.join(MOD, "common", "culture", "cultures", "zz_eu5_culture_merge.txt")
APPLY = "--apply" in sys.argv

PRUSSIAN = """
# prussian 在生成物里是按 EU5 的德意志普鲁士建的（低地德语、central_germanic），
# 但省份里剩下的 30 个 prussian（pruthenian 15 + sudovian 9 + curonian 6）是西波罗的
# 古普鲁士人。此处覆盖回 CK3 原版的波罗的定义。德意志普鲁士另用 teutonic。
prussian = {
\tcolor = { 0.56 0.55 0.4 }

\tethos = ethos_bureaucratic
\theritage = heritage_baltic
\tlanguage = language_baltic
\tmartial_custom = martial_custom_male_only
\thead_determination = head_determination_domain

\ttraditions = {
\t\ttradition_sacred_groves
\t\ttradition_equitable
\t\ttradition_forest_wardens
\t\ttradition_welcoming
\t}

\tname_list = name_list_prussian

\tcoa_gfx = { baltic_group_coa_gfx steppe_coa_gfx western_coa_gfx }
\tbuilding_gfx = { western_building_gfx }
\tclothing_gfx = { northern_clothing_gfx }
\tunit_gfx = { northern_unit_gfx }
\thouse_coa_frame = house_frame_21
\thouse_coa_mask_offset = { 0.0 0.0 }
\thouse_coa_mask_scale = { 1.0 1.0 }

\tethnicities = {
\t\t80 = caucasian_northern_blond
\t\t15 = caucasian_northern_ginger
\t\t3 = caucasian_northern_brown_hair
\t\t2 = caucasian_northern_dark_hair
\t}
}
"""


def keys_of(pat):
    s = set()
    for f in glob.glob(pat):
        if ".bak" in f:
            continue
        t = io.open(f, encoding="utf-8-sig", errors="replace").read()
        s |= set(re.findall(r"(?m)^([a-z_0-9]+)\s*=\s*\{", t))
    return s


NOISE = {"color", "traditions", "coa_gfx", "building_gfx", "clothing_gfx", "unit_gfx",
         "ethnicities", "name_list", "ethos", "heritage", "language", "martial_custom",
         "head_determination", "house_coa_frame", "house_coa_mask_offset",
         "house_coa_mask_scale", "parents", "created"}

van = keys_of(os.path.join(BASE, "common/culture/cultures/*.txt")) - NOISE
mod = keys_of(os.path.join(MOD, "common/culture/cultures/*.txt")) - NOISE
alive = van | mod

# ---- ① prussian 覆盖 ----
t = io.open(ZZ, encoding="utf-8-sig").read()
has = re.search(r"(?m)^prussian\s*=\s*\{", t)
print("zz 文件已有 prussian 覆盖:", bool(has))
if not has:
    if APPLY:
        io.open(ZZ, "w", encoding="utf-8-sig", newline="\n").write(t.rstrip() + "\n" + PRUSSIAN)
        print("已追加 prussian 覆盖块")
    else:
        print("[dry-run] 将追加 prussian 覆盖块")

# ---- ② 孤儿 history/cultures ----
files = [f for f in glob.glob(os.path.join(MOD, "history", "cultures", "*.txt")) if ".bak" not in f]
orphan = [f for f in files if os.path.basename(f)[:-4] not in alive]
print()
print("history/cultures 文件 %d 个，孤儿（文化已无定义）%d 个" % (len(files), len(orphan)))
for f in orphan[:10]:
    print("   ", os.path.basename(f))
if len(orphan) > 10:
    print("    ...")

if APPLY and orphan:
    for f in orphan:
        os.remove(f)
    print("已删 %d 个孤儿文件" % len(orphan))
elif not APPLY:
    print("[dry-run] 未删除")
