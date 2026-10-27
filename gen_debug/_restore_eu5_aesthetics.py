# -*- coding: utf-8 -*-
"""把 culture 定义里的 gfx 四件套（coa/building/clothing/unit）按 CK3 heritage 对齐原版。

思路（CK3 原版本身就是 heritage 与 gfx 强绑定，见 _vanilla_gfx_quads.txt）：
  1. 文化有映射后的 CK3 heritage（heritage_*）-> 用该 heritage 在原版里的代表四件套
  2. 文化仍是自定义 EU5 组名 -> 只在 EU5 tag 有最近似原版家族时替换
     （aboriginal/papuan -> papuan 家族；austronesian/polynesian -> malay 家族；
       african -> 泛西非家族）；美洲各族的 tag 在原版没有对应家族，保持原样
  3. gen_culture_unsettled 无 EU5 来源，保持原样

默认 dry-run，--apply 才写（先备份）。
"""
import io, os, re, sys, shutil, time
from collections import Counter, defaultdict

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game\in_game"
SRC = os.path.join(MOD, "common", "culture", "cultures", "00_generated_cultures.txt")
OUTDIR = os.path.join(MOD, "gen_debug")
DRY = "--apply" not in sys.argv

BLOCK = re.compile(r"([A-Za-z0-9_]+)\s*=\s*\{")


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


def walk(text, path=()):
    i, n = 0, len(text)
    while i < n:
        m = BLOCK.search(text, i)
        if not m:
            return
        j, d = m.end(), 1
        while j < n and d:
            c = text[j]
            if c == "{":
                d += 1
            elif c == "}":
                d -= 1
            j += 1
        yield path, m.group(1), text[m.end():j - 1]
        yield from walk(text[m.end():j - 1], path + (m.group(1),))
        i = j


def C(coa, bld, clo, uni):
    return (coa, bld, clo, uni)


# heritage -> (coa_gfx, building_gfx, clothing_gfx, unit_gfx)，取自原版同族文化的实际组合
HERITAGE_GFX = {
    "heritage_west_germanic":    C("english_coa_gfx western_coa_gfx", "western_building_gfx", "english_clothing_gfx western_clothing_gfx", "western_unit_gfx"),
    "heritage_central_germanic": C("german_group_coa_gfx western_coa_gfx", "western_building_gfx", "dde_hre_clothing_gfx western_clothing_gfx", "western_unit_gfx"),
    "heritage_north_germanic":   C("norse_coa_gfx western_coa_gfx", "norse_building_gfx", "northern_clothing_gfx", "norse_unit_gfx"),
    "heritage_frankish":         C("frankish_group_coa_gfx western_coa_gfx", "western_building_gfx", "french_clothing_gfx western_clothing_gfx", "western_unit_gfx"),
    "heritage_latin":            C("latin_group_coa_gfx western_coa_gfx", "mediterranean_building_gfx", "western_clothing_gfx", "western_unit_gfx"),
    "heritage_iberian":          C("iberian_group_coa_gfx western_coa_gfx", "iberian_building_gfx", "iberian_christian_clothing_gfx western_clothing_gfx", "iberian_christian_unit_gfx"),
    "heritage_goidelic":         C("irish_coa_gfx western_coa_gfx", "western_building_gfx", "northern_clothing_gfx", "western_unit_gfx"),
    "heritage_brythonic":        C("welsh_coa_gfx western_coa_gfx", "western_building_gfx", "welsh_clothing_gfx western_clothing_gfx", "western_unit_gfx"),
    "heritage_east_slavic":      C("east_slavic_group_coa_gfx western_coa_gfx", "east_slavic_building_gfx western_building_gfx", "east_slavic_clothing_gfx northern_clothing_gfx", "eastern_unit_gfx"),
    "heritage_west_slavic":      C("polish_coa_gfx west_slavic_group_coa_gfx western_coa_gfx", "western_building_gfx", "west_slavic_clothing_gfx western_clothing_gfx", "eastern_unit_gfx"),
    "heritage_south_slavic":     C("south_slavic_group_coa_gfx western_coa_gfx", "mediterranean_building_gfx", "byzantine_clothing_gfx", "eastern_unit_gfx"),
    "heritage_baltic":           C("baltic_group_coa_gfx steppe_coa_gfx western_coa_gfx", "western_building_gfx", "northern_clothing_gfx", "northern_unit_gfx"),
    "heritage_balto_finnic":     C("balto_finnic_group_coa_gfx steppe_coa_gfx western_coa_gfx", "western_building_gfx", "northern_clothing_gfx", "northern_unit_gfx"),
    "heritage_ugro_permian":     C("ugro_permian_group_coa_gfx steppe_coa_gfx", "western_building_gfx", "ugro_permian_clothing_gfx northern_clothing_gfx", "northern_unit_gfx"),
    "heritage_volga_finnic":     C("steppe_coa_gfx volga_finnic_group_coa_gfx", "western_building_gfx", "northern_clothing_gfx", "northern_unit_gfx"),
    "heritage_magyar":           C("magyar_group_coa_gfx ugro_permian_group_coa_gfx steppe_coa_gfx", "western_building_gfx", "western_clothing_gfx", "eastern_unit_gfx"),
    "heritage_vlach":            C("south_slavic_group_coa_gfx western_coa_gfx", "mediterranean_building_gfx", "byzantine_clothing_gfx", "eastern_unit_gfx"),
    "heritage_byzantine":        C("byzantine_group_coa_gfx", "byzantine_building_gfx", "byzantine_clothing_gfx", "eastern_unit_gfx"),
    "heritage_caucasian":        C("byzantine_group_coa_gfx", "caucasian_building_gfx byzantine_building_gfx", "byzantine_clothing_gfx", "eastern_unit_gfx"),
    "heritage_iranian":          C("iranian_group_coa_gfx", "iranian_building_gfx", "iranian_clothing_gfx mena_clothing_gfx", "iranian_unit_gfx"),
    "heritage_arabic":           C("arabic_group_coa_gfx", "arabic_group_building_gfx mena_building_gfx", "dde_abbasid_clothing_gfx mena_clothing_gfx", "mena_unit_gfx"),
    "heritage_berber":           C("berber_group_coa_gfx", "berber_group_building_gfx mena_building_gfx", "afr_berber_clothing_gfx mena_clothing_gfx", "mena_unit_gfx"),
    "heritage_east_african":     C("east_african_group_coa_gfx", "african_building_gfx mena_building_gfx", "african_clothing_gfx", "mena_unit_gfx"),
    "heritage_west_african":     C("west_african_group_coa_gfx", "african_building_gfx mena_building_gfx", "african_clothing_gfx", "sub_sahran_unit_gfx"),
    "heritage_central_african":  C("central_african_group_coa_gfx", "african_building_gfx mena_building_gfx", "african_clothing_gfx", "sub_sahran_unit_gfx"),
    "heritage_senegambian":      C("west_african_group_coa_gfx", "african_building_gfx mena_building_gfx", "african_clothing_gfx", "sub_sahran_unit_gfx"),
    "heritage_sahelian":         C("west_african_group_coa_gfx", "african_building_gfx mena_building_gfx", "african_clothing_gfx", "sub_sahran_unit_gfx"),
    "heritage_yoruba":           C("central_african_group_coa_gfx", "african_building_gfx mena_building_gfx", "african_clothing_gfx", "sub_sahran_unit_gfx"),
    "heritage_akan":             C("west_african_group_coa_gfx", "african_building_gfx mena_building_gfx", "african_clothing_gfx", "sub_sahran_unit_gfx"),
    "heritage_somalian":         C("east_african_group_coa_gfx", "african_building_gfx mena_building_gfx", "african_clothing_gfx", "mena_unit_gfx"),
    "heritage_bantu":            C("east_african_group_coa_gfx", "african_building_gfx mena_building_gfx", "african_clothing_gfx", "mena_unit_gfx"),
    "heritage_turkic":           C("turkic_group_coa_gfx steppe_coa_gfx", "steppe_building_gfx", "turkic_clothing_gfx mongol_clothing_gfx", "mongol_unit_gfx"),
    "heritage_mongolic":         C("mongol_coa_gfx steppe_coa_gfx", "steppe_building_gfx", "mongol_clothing_gfx", "mongol_unit_gfx"),
    "heritage_tungusic":         C("mongol_coa_gfx steppe_coa_gfx", "amuric_building_gfx steppe_building_gfx", "jurchen_clothing_gfx nivkh_clothing_gfx mongol_clothing_gfx", "mongol_unit_gfx"),
    "heritage_tibetan":          C("tibetan_group_coa_gfx", "tibetan_building_gfx", "mongol_clothing_gfx", "mongol_unit_gfx"),
    "heritage_ainuic":           C("mongol_coa_gfx steppe_coa_gfx", "amuric_building_gfx steppe_building_gfx", "emishi_clothing_gfx ainu_clothing_gfx", "emishi_unit_gfx japanese_unit_gfx"),
    "heritage_chinese":          C("chinese_group_coa_gfx", "chinese_building_gfx", "chinese_clothing_gfx", "chinese_unit_gfx"),
    "heritage_korean":           C("chinese_group_coa_gfx", "chinese_building_gfx", "korean_clothing_gfx chinese_clothing_gfx", "chinese_unit_gfx"),
    "heritage_japonic":          C("japanese_coa_gfx", "japanese_building_gfx", "japanese_clothing_gfx", "japanese_unit_gfx"),
    "heritage_burman":           C("burman_group_coa_gfx", "southeast_asian_building_gfx", "malay_clothing_gfx southeast_asian_clothing_gfx", "southeast_asian_unit_gfx indian_unit_gfx"),
    "heritage_mon_khmer":        C("burman_group_coa_gfx", "southeast_asian_building_gfx", "malay_clothing_gfx southeast_asian_clothing_gfx", "southeast_asian_unit_gfx indian_unit_gfx"),
    "heritage_tai":              C("chinese_group_coa_gfx", "southeast_asian_building_gfx", "tai_clothing_gfx southeast_asian_clothing_gfx", "southeast_asian_unit_gfx indian_unit_gfx"),
    "heritage_hmongic":          C("burman_group_coa_gfx", "chinese_building_gfx", "chinese_clothing_gfx", "chinese_unit_gfx"),
    "heritage_dravidian":        C("dravidian_group_coa_gfx", "indian_building_gfx", "indian_clothing_gfx", "indian_unit_gfx"),
    "heritage_indo_aryan":       C("indo_aryan_group_coa_gfx", "indian_building_gfx", "indian_clothing_gfx", "indian_unit_gfx"),
    "heritage_austronesian":     C("burman_group_coa_gfx", "southeast_asian_building_gfx", "malay_clothing_gfx southeast_asian_clothing_gfx", "southeast_asian_unit_gfx indian_unit_gfx"),
    "heritage_israelite":        C("israelite_group_coa_gfx", "mena_building_gfx", "byzantine_clothing_gfx", "mena_unit_gfx"),
    "heritage_syriac":           C("byzantine_group_coa_gfx", "mena_building_gfx", "byzantine_clothing_gfx", "mena_unit_gfx"),
    "heritage_nivkh":            C("mongol_coa_gfx steppe_coa_gfx", "amuric_building_gfx steppe_building_gfx", "nivkh_clothing_gfx mongol_clothing_gfx", "mongol_unit_gfx"),
    "heritage_gothic":           C("latin_group_coa_gfx western_coa_gfx", "mediterranean_building_gfx", "western_clothing_gfx", "western_unit_gfx"),
    "heritage_albanian":         C("south_slavic_group_coa_gfx western_coa_gfx", "mediterranean_building_gfx", "byzantine_clothing_gfx", "eastern_unit_gfx"),
    "heritage_egyptian":         C("arabic_group_coa_gfx", "arabic_group_building_gfx mena_building_gfx", "dde_abbasid_clothing_gfx mena_clothing_gfx", "mena_unit_gfx"),
}

PAPUAN = C("burman_group_coa_gfx", "southeast_asian_building_gfx",
           "papuan_clothing_gfx southeast_asian_clothing_gfx",
           "southeast_asian_unit_gfx indian_unit_gfx")
MALAY = C("burman_group_coa_gfx", "southeast_asian_building_gfx",
          "malay_clothing_gfx southeast_asian_clothing_gfx",
          "southeast_asian_unit_gfx indian_unit_gfx")
WEST_AFRICAN = C("west_african_group_coa_gfx", "african_building_gfx mena_building_gfx",
                 "african_clothing_gfx", "sub_sahran_unit_gfx")

# 自定义 heritage（无 CK3 对应）文化：按 EU5 tag 找最近似原版家族，优先级从上到下
TAG_GFX = [
    (("aboriginal_gfx", "papuan_gfx"), PAPUAN, "原版无澳洲/巴布亚家族，取最近的 papuan 家族"),
    (("austronesian_gfx", "polynesian_gfx"), MALAY, "原版无波利尼西亚家族，取最近的马来家族"),
    (("african_gfx",), WEST_AFRICAN, "泛非 -> 原版西非家族"),
]

FIELDS = ("coa_gfx", "building_gfx", "clothing_gfx", "unit_gfx")


def main():
    # EU5 tags
    eu5_tags = {}
    for fn in os.listdir(os.path.join(EU5, "common", "cultures")):
        if not fn.endswith(".txt"):
            continue
        for path, key, body in walk(read(os.path.join(EU5, "common", "cultures", fn))):
            if path:
                continue
            tg = re.search(r"(?m)^\s*tags\s*=\s*\{([^}]*)\}", body)
            eu5_tags[key] = set(tg.group(1).split()) if tg else set()

    raw = read(SRC)
    lines = raw.split("\n")

    cur = None
    cur_heritage = None
    pending = None          # 待写入的四件套；False = 保持原样
    changed = 0
    via_heritage = 0
    via_tag = 0
    no_target = 0
    no_gfx = 0
    samples = []
    kept_counter = Counter()
    unmapped_groups = Counter()
    combo_counter = Counter()
    out = []

    def settle():
        """结算上一个文化。"""
        nonlocal no_target, no_gfx
        if prev_cur is None:
            return
        if prev_pending is False:
            no_target += 1
            unmapped_groups[prev_heritage or "?"] += 1
        elif prev_pending is None:
            no_gfx += 1

    prev_cur, prev_heritage, prev_pending = None, None, None

    for line in lines:
        m = re.match(r"^([a-z0-9_]+)\s*=\s*\{\s*$", line)
        if m:
            settle()
            prev_cur, prev_heritage, prev_pending = cur, cur_heritage, pending
            cur, cur_heritage, pending = m.group(1), None, None
            out.append(line)
            continue
        mh = re.match(r"^(\s*)heritage\s*=\s*(\S+)", line)
        if mh and cur:
            cur_heritage = mh.group(2)
            out.append(line)
            continue
        mg = re.match(r"^(\s*)([a-z_]+_gfx)\s*=\s*\{([^}]*)\}", line)
        if mg and cur:
            field = mg.group(2)
            if field not in FIELDS:
                out.append(line)
                continue
            if pending is None:
                # 首次遇到 gfx 行时决定四件套
                her = cur_heritage
                if her and her.startswith("heritage_") and her in HERITAGE_GFX:
                    pending = HERITAGE_GFX[her]
                    via_heritage += 1
                else:
                    tags = eu5_tags.get(cur, set())
                    hit = next(((c, why) for keys, c, why in TAG_GFX if tags & set(keys)), None)
                    if hit:
                        pending = hit[0]
                        via_tag += 1
                    else:
                        pending = False      # 保持原样
            if pending is False:
                kept_counter[cur_heritage or "?"] += 1
                out.append(line)
                continue
            idx = FIELDS.index(field)
            new = pending[idx]
            old = " ".join(mg.group(3).split())
            if new != old:
                changed += 1
                if len(samples) < 20:
                    samples.append((cur, field, old, new, cur_heritage or ""))
            combo_counter[pending] += 1
            out.append("%s%s = { %s }" % (mg.group(1), field, new))
            continue
        out.append(line)

    # 结尾结算最后一个文化
    prev_cur, prev_heritage, prev_pending = cur, cur_heritage, pending
    settle()

    new_text = "\n".join(out)
    total = via_heritage + via_tag
    print("gfx 行改写: %d（文化 %d 个：heritage 驱动 %d / tag 驱动 %d）" % (changed, total, via_heritage, via_tag))
    print("保持原样: %d 个文化 | 无 gfx 行的块: %d" % (no_target, no_gfx))
    print()
    print("samples:")
    for c, f, o, n, h in samples:
        print("  %-26s %-14s %-46s -> %s   [%s]" % (c, f, o, n, h))
    print()
    print("保持原样的文化按 heritage 分组 top20:")
    for g, c in unmapped_groups.most_common(20):
        print("  %-30s %4d" % (g, c))
    print()
    print("四件套分布 top15:")
    for q, c in combo_counter.most_common(15):
        print("  %5d  %s" % (c, " | ".join(q)))

    if DRY:
        print("\n[dry-run] 未写文件。加 --apply 才写。")
        return
    if new_text == raw:
        print("\nno change")
        return
    ts = time.strftime("%Y%m%d_%H%M%S")
    shutil.copy2(SRC, SRC + ".bak_aesthetics_" + ts)
    io.open(SRC, "w", encoding="utf-8-sig", newline="\n").write(new_text)
    print("\nAPPLIED. backup: %s" % (SRC + ".bak_aesthetics_" + ts))
    print("braces: %d %d" % (new_text.count("{"), new_text.count("}")))


if __name__ == "__main__":
    main()
