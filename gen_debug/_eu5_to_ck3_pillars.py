# -*- coding: utf-8 -*-
"""生成 EU5 culture_group -> CK3 原版 heritage / language 的映射表（人工定稿数据，只读 mod）。

输出：
  gen_debug/_eu5_to_ck3_pillars.csv   映射表（后续改 culture 定义时按它替换 key）
  gen_debug/_eu5_to_ck3_pillars.log   覆盖率报告
"""
import io, os, re, csv
from collections import Counter, defaultdict

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
OUTDIR = os.path.join(MOD, "gen_debug")

# EU5 culture_group -> (CK3 heritage, CK3 language)
# None = CK3 原版没有对应（新大陆 / 大洋洲 / 极地），保留 mod 自定义
MAP = {
    # --- 东亚 ---
    "chinese_group":            ("heritage_chinese", "language_chinese"),
    "confucian_group":          ("heritage_korean", "language_korean"),
    "japanese_group":           ("heritage_japonic", "language_japonic"),
    "ryukyu_culture_group":     ("heritage_japonic", "language_japonic"),
    "ainu_culture_group":       ("heritage_ainuic", "language_ainu"),
    "tibetan_group":            ("heritage_tibetan", "language_tibetan"),
    "tibeto_burman_group":      ("heritage_burman", "language_burmese"),
    "macro_je_group":           None,
    # --- 东南亚 / 大洋洲 ---
    "thai_group":               ("heritage_tai", "language_tai"),
    "shan_group":               ("heritage_tai", "language_tai"),
    "austroasiatic_group":      ("heritage_mon_khmer", "language_mon_khmer"),
    "hmong_mien_group":         ("heritage_hmongic", "language_hmongic"),
    "austronesian_group":       ("heritage_austronesian", "language_austronesian"),
    "polynesian_group":         ("heritage_austronesian", "language_austronesian"),
    "micronesian_group":        ("heritage_austronesian", "language_austronesian"),
    "malagasy_group":           ("heritage_austronesian", "language_austronesian"),
    "papuan_group":             ("heritage_austronesian", "language_papuan"),
    "pama_nyungan_group":       None,
    "australian_group":         None,
    # --- 内亚 / 北亚 ---
    "mongolian_group":          ("heritage_mongolic", "language_mongolic"),
    "tungusic_group":           ("heritage_tungusic", "language_tungusic"),
    "jurchen_group":            ("heritage_tungusic", "language_tungusic"),
    "turkic_group":             ("heritage_turkic", "language_turkic"),
    "tatar_group":              ("heritage_turkic", "language_turkic"),
    "iranian_group":            ("heritage_iranian", "language_iranian"),
    "alan_culture_group":       ("heritage_iranian", "language_scythian"),
    "caucasian_group":          ("heritage_caucasian", "language_georgian"),
    "albanian_group":           ("heritage_albanian", "language_albanian"),
    "greek_group":              ("heritage_byzantine", "language_greek"),
    "arabian_group":            ("heritage_arabic", "language_arabic"),
    "arabic_group":             ("heritage_arabic", "language_arabic"),
    "jewish_group":             ("heritage_israelite", "language_israelite"),
    "mandean_culture_group":    ("heritage_syriac", "language_aramaic"),
    "samaritan_culture_group":  ("heritage_israelite", "language_israelite"),
    "coptic_culture_group":     ("heritage_egyptian", "language_egyptian"),
    "romani_group":             None,
    # --- 南亚 ---
    "indian_group":             ("heritage_indo_aryan", "language_sauraseni"),
    "indo_aryan_group":         ("heritage_indo_aryan", "language_sauraseni"),
    "nepali_group":             ("heritage_indo_aryan", "language_pahari"),
    "dravidian_group":          ("heritage_dravidian", "language_tamil"),
    # --- 欧洲 ---
    "german_group":             ("heritage_central_germanic", "language_high_german"),
    "netherlandish_group":      ("heritage_central_germanic", "language_dutch"),
    "british_group":            ("heritage_west_germanic", "language_anglic"),
    "scottish_group":           ("heritage_goidelic", "language_goidelic"),
    "celtic_group":             ("heritage_goidelic", "language_goidelic"),
    "hibernian_group":          ("heritage_goidelic", "language_goidelic"),
    "french_group":             ("heritage_frankish", "language_french"),
    "pyrenean_group":           ("heritage_iberian", "language_basque"),
    "iberian_group":            ("heritage_iberian", "language_iberian"),
    "italian_group":            ("heritage_latin", "language_italian"),
    "romanian_group":           ("heritage_vlach", "language_wallachian"),
    "hungarian_group":          ("heritage_magyar", "language_magyar"),
    "jasz_culture_group":       ("heritage_magyar", "language_magyar"),
    "polish_group":             ("heritage_west_slavic", "language_lechitic"),
    "bohemian_group":           ("heritage_west_slavic", "language_czech_slovak"),
    "carpathian_group":         ("heritage_west_slavic", "language_czech_slovak"),
    "slavic_group":             ("heritage_south_slavic", "language_south_slavic"),
    "russian_group":            ("heritage_east_slavic", "language_east_slavic"),
    "baltic_group":             ("heritage_baltic", "language_baltic"),
    "lithuanian_group":         ("heritage_baltic", "language_baltic"),
    "finnic_group":             ("heritage_balto_finnic", "language_finnic"),
    "sapmi_group":              ("heritage_balto_finnic", "language_sami"),
    "permic_group":             ("heritage_ugro_permian", "language_ugro_permian"),
    "mordvinic_group":          ("heritage_volga_finnic", "language_volga_finnic"),
    "mari_culture_group":       ("heritage_volga_finnic", "language_volga_finnic"),
    "merya_culture_group":      ("heritage_volga_finnic", "language_volga_finnic"),
    "khanty_culture_group":     ("heritage_ugro_permian", "language_ugro_permian"),
    "mansi_culture_group":      ("heritage_ugro_permian", "language_ugro_permian"),
    "nenets_culture_group":     ("heritage_ugro_permian", "language_finnic"),
    "enets_culture_group":      ("heritage_ugro_permian", "language_finnic"),
    "selkup_culture_group":     ("heritage_ugro_permian", "language_ugro_permian"),
    "scandinavian_group":       ("heritage_north_germanic", "language_norse"),
    "amazigh_group":            ("heritage_berber", "language_berber"),
    # --- 非洲 ---
    "west_african_group":       ("heritage_west_african", "language_manding"),
    "volta_niger_group":        ("heritage_yoruba", "language_yoruba"),
    "kwa_group":                ("heritage_yoruba", "language_kwa"),
    "kru_group":                ("heritage_west_african", "language_kru"),
    "atlantic_group":           ("heritage_senegambian", "language_senegambian"),
    "nilosahelian_group":       ("heritage_sahelian", "language_ayneha"),
    "tunjur_culture_group":     ("heritage_sahelian", "language_sudanic"),
    "nilotic_group":            ("heritage_east_african", "language_sudanic"),
    "nubian_group":             ("heritage_east_african", "language_sudanic"),
    "funj_culture_group":       ("heritage_east_african", "language_sudanic"),
    "ethiopian_group":          ("heritage_east_african", "language_ethiopic"),
    "cushitic_group":           ("heritage_somalian", "language_cushitic"),
    "bantu_group":              ("heritage_bantu", "language_sabaki"),
    "central_african_group":    ("heritage_central_african", "language_chadic"),
    "khoisan_group":            None,
}

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
        body = text[m.end():j - 1]
        yield path, m.group(1), body
        yield from walk(body, path + (m.group(1),))
        i = j


def main():
    ours = {}
    for path, key, body in walk(read(os.path.join(MOD, "common", "culture", "cultures", "00_generated_cultures.txt"))):
        if path:
            continue
        h = re.search(r"(?m)^\s*heritage\s*=\s*(\S+)", body)
        lg = re.search(r"(?m)^\s*language\s*=\s*(\S+)", body)
        ours[key] = (h.group(1) if h else "", lg.group(1) if lg else "")

    raw = read(os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt"))
    cnt = Counter(re.findall(r"(?m)^\s*culture\s*=\s*(\S+)", raw))

    grp = defaultdict(lambda: {"cultures": 0, "baronies": 0})
    for c, (h, lg) in ours.items():
        if not h:
            continue
        grp[h]["cultures"] += 1
        grp[h]["baronies"] += cnt.get(c, 0)

    rows = []
    for g, s in sorted(grp.items(), key=lambda kv: -kv[1]["baronies"]):
        m = MAP.get(g, None)
        if m:
            her, lg = m
            status = "mapped"
        else:
            her, lg = "", ""
            status = "keep"
        rows.append({
            "eu5_group": g, "cultures": s["cultures"], "baronies": s["baronies"],
            "ck3_heritage": her, "ck3_language": lg, "status": status,
        })

    with io.open(os.path.join(OUTDIR, "_eu5_to_ck3_pillars.csv"), "w",
                 encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["eu5_group", "cultures", "baronies",
                                          "ck3_heritage", "ck3_language", "status"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    tot = sum(r["baronies"] for r in rows)
    mapped = sum(r["baronies"] for r in rows if r["status"] == "mapped")
    n_all = len(rows)
    n_map = sum(1 for r in rows if r["status"] == "mapped")

    L = []
    L.append("EU5 culture_group 总数: %d" % n_all)
    L.append("已映射到 CK3 原版 heritage: %d 个 group，覆盖 %d/%d 男爵领 = %.1f%%"
             % (n_map, mapped, tot, 100.0 * mapped / tot))
    L.append("保留自定义: %d 个 group，%d 男爵领 (%.1f%%)"
             % (n_all - n_map, tot - mapped, 100.0 * (tot - mapped) / tot))
    L.append("")
    L.append("未映射（CK3 原版无对应 heritage）:")
    for r in rows:
        if r["status"] == "keep":
            L.append("  %-34s %5d 男爵领  %3d 文化" % (r["eu5_group"], r["baronies"], r["cultures"]))

    # 未在 MAP 里出现的 group（防止漏）
    missing = [g for g in grp if g not in MAP]
    L.append("")
    L.append("MAP 里没有显式声明、按 keep 处理的 group: %d 个" % len(missing))
    if missing:
        L.append("  " + " ".join(missing))

    io.open(os.path.join(OUTDIR, "_eu5_to_ck3_pillars.log"), "w",
            encoding="utf-8", newline="\n").write("\n".join(L))
    print("ok")


if __name__ == "__main__":
    main()
