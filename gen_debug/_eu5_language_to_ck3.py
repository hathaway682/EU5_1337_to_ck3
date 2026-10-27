# -*- coding: utf-8 -*-
"""把 EU5 的 language 映射到 CK3 原版 language（人工定稿规则，只读 mod）。

口径：
  - 我们的 culture 定义里 language 现在是 eu5_heritage_<group>（自造 key，丢了 EU5 原始 language）
  - EU5 每个 culture 自带 language 字段（593 个被我们用到），按语系归并到 CK3 的 91 个 language
  - CK3 没有的语系（新大陆 / 大洋洲 / 科伊桑 / 西伯利亚极地）→ keep，保留自定义

输出：
  gen_debug/_eu5_language_to_ck3.csv
  gen_debug/_eu5_language_to_ck3.log
"""
import io, os, re, csv
from collections import Counter, defaultdict

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
CK3 = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game\in_game"
OUTDIR = os.path.join(MOD, "gen_debug")

# 精确映射（EU5 language -> CK3 language）
EXACT = {
    # --- 东亚 ---
    "northern_mandarin_dialect": "language_chinese",
    "southern_mandarin_dialect": "language_chinese",
    "jin_language": "language_chinese",
    "shu_language": "language_chinese",
    "wu_language": "language_chinese",
    "gan_language": "language_chinese",
    "yue_language": "language_chinese",
    "min_language": "language_chinese",
    "kejia_language": "language_chinese",
    "xiang_language": "language_chinese",
    "huizhou_language": "language_chinese",
    "ping_language": "language_chinese",
    "bai_language": "language_chinese",
    "tujia_language": "language_tai",
    "qiangic_language": "language_qiangic",
    "tibetan_language": "language_tibetan",
    "japanese_language": "language_japonic",
    "ryukyu_language": "language_japonic",
    "ainu_language": "language_ainu",
    "korean_language": "language_korean",
    # --- 内亚 / 北亚 ---
    "mongolian_language": "language_mongolic",
    "evenk_language": "language_tungusic",
    "jurchen_language": "language_tungusic",
    "nanai_language": "language_tungusic",
    "udege_language": "language_tungusic",
    "lamut_language": "language_tungusic",
    "nipchak_language": "language_nivkh",
    "nivkh_language": "language_nivkh",
    "turkic_language": "language_turkic",
    "kipchak_language": "language_turkic",
    "karluk_language": "language_turkic",
    "turkish_dialect": "language_turkic",
    "turkmen_dialect": "language_turkic",
    "azeri_dialect": "language_turkic",
    "oghuric_language": "language_oghur",
    # --- 伊朗 ---
    "persian_language": "language_iranian",
    "kurdish_language": "language_iranian",
    "balochi_language": "language_iranian",
    "adharic_language": "language_iranian",
    "tabaristani_language": "language_iranian",
    "median_dialect": "language_italian",
    "afghani_language": "language_scythian",
    "alanic_language": "language_scythian",
    "sogdian_language": "language_scythian",
    "khwarezmian_language": "language_scythian",
    # --- 高加索 ---
    "armenian_language": "language_armenian",
    "georgian_language": "language_georgian",
    "circassian_language": "language_georgian",
    "dagestanian_language": "language_georgian",
    # --- 阿拉伯 / 近东 ---
    "peninsular_dialect": "language_arabic",
    "egyptian_dialect": "language_arabic",
    "maghrebi_dialect": "language_arabic",
    "levantine_dialect": "language_arabic",
    "iraqi_dialect": "language_arabic",
    "south_arabic_language": "language_arabic",
    "aramaic_language": "language_aramaic",
    "hebrew_language": "language_israelite",
    "greek_language": "language_greek",
    "albanian_language": "language_albanian",
    # --- 欧洲：日耳曼 ---
    "low_german_dialect": "language_saxon",
    "central_german_dialect": "language_high_german",
    "upper_german_dialect": "language_high_german",
    "alemannic_dialect": "language_high_german",
    "francique_dialect": "language_high_german",
    "silesian_dialect": "language_high_german",
    "dutch_dialect": "language_dutch",
    "frisian_language": "language_anglic",
    "english_dialect": "language_anglic",
    "scots_dialect": "language_anglic",
    "northumbrian_dialect": "language_anglic",
    "icelandic_dialect": "language_norse",
    "danish_dialect": "language_norse",
    "swedish_dialect": "language_norse",
    "norwegian_dialect": "language_norse",
    # --- 欧洲：罗曼 ---
    "castilian_dialect": "language_iberian",
    "leonese_dialect": "language_iberian",
    "galician_dialect": "language_iberian",
    "portuguese_dialect": "language_iberian",
    "catalan_dialect": "language_occitano_romance",
    "aragonese_dialect": "language_occitano_romance",
    "gascon_dialect": "language_occitano_romance",
    "occitan_dialect": "language_occitano_romance",
    "arpitan_dialect": "language_occitano_romance",
    "french_language": "language_french",
    "norman_dialect": "language_french",
    "angevin_dialect": "language_french",
    "poitevin_dialect": "language_french",
    "burgundian_dialect": "language_french",
    "neapolitan_dialect": "language_italian",
    "sicilian_dialect": "language_italian",
    "lombard_dialect": "language_italian",
    "tuscan_dialect": "language_italian",
    "venetian_dialect": "language_italian",
    "emilian_dialect": "language_italian",
    "romagnol_dialect": "language_italian",
    "ligurian_dialect": "language_italian",
    "piedmontese_dialect": "language_italian",
    "dalmatian_dialect": "language_italian",
    "rhaetian_dialect": "language_italian",
    "sardinian_dialect": "language_sardinian",
    "romanian_language": "language_wallachian",
    "basque_language": "language_basque",
    # --- 欧洲：斯拉夫 / 波罗的 / 芬兰 ---
    "russian_dialect": "language_east_slavic",
    "ukrainian_dialect": "language_east_slavic",
    "belarusian_dialect": "language_east_slavic",
    "novgorodian_dialect": "language_east_slavic",
    "polish_dialect": "language_lechitic",
    "kashubian_dialect": "language_lechitic",
    "polabian_dialect": "language_lechitic",
    "czech_dialect": "language_czech_slovak",
    "slovak_dialect": "language_czech_slovak",
    "sorbian_dialect": "language_czech_slovak",
    "croatian_dialect": "language_south_slavic",
    "serbian_dialect": "language_south_slavic",
    "slovene_dialect": "language_south_slavic",
    "bosnian_dialect": "language_south_slavic",
    "bulgarian_language": "language_slavonic",
    "macedonian_dialect": "language_slavonic",
    "lithuanian_dialect": "language_baltic",
    "latvian_dialect": "language_baltic",
    "western_baltic_dialect": "language_baltic",
    "prussian_dialect": "language_baltic",
    "finnish_dialect": "language_finnic",
    "estonian_dialect": "language_finnic",
    "karelian_dialect": "language_finnic",
    "sami_language": "language_sami",
    "permic_language": "language_ugro_permian",
    "ugrian_language": "language_ugro_permian",
    "nenets_language": "language_finnic",
    "mordvinic_language": "language_volga_finnic",
    "mari_language": "language_volga_finnic",
    "hungarian_language": "language_magyar",
    "magyar_language": "language_magyar",
    # --- 欧洲：凯尔特 ---
    "irish_dialect": "language_goidelic",
    "scottish_gaelic_dialect": "language_goidelic",
    "welsh_dialect": "language_brythonic",
    "breton_dialect": "language_brythonic",
    "cornish_dialect": "language_brythonic",
    # --- 南亚 ---
    "hindustani_language": "language_sauraseni",
    "bihari_language": "language_magadhan",
    "bengali_language": "language_magadhan",
    "oriya_language": "language_magadhan",
    "kamarupi_language": "language_magadhan",
    "punjabi_language": "language_vrachada",
    "sindhi_language": "language_vrachada",
    "gujarati_language": "language_rajasthani",
    "rajasthani_language": "language_rajasthani",
    "malvi_language": "language_rajasthani",
    "bhili_language": "language_rajasthani",
    "marathi_language": "language_marathi",
    "nepali_language": "language_pahari",
    "pahari_language": "language_pahari",
    "kashmiri_language": "language_kashmiri",
    "sinhala_language": "language_sinhalese",
    "tamil_language": "language_tamil",
    "malayalam_language": "language_tamil",
    "telugu_language": "language_telugu",
    "kannada_language": "language_kannada",
    "gondi_language": "language_telugu",
    "north_dravidian_language": "language_north_dravidian",
    # --- 东南亚 ---
    "burmese_language": "language_burmese",
    "yi_language": "language_burmese",
    "kachinic_language": "language_burmese",
    "karenic_language": "language_burmese",
    "brahmaputran_language": "language_burmese",
    "meitei_language": "language_burmese",
    "palaungic_language": "language_mon_khmer",
    "khmu_language": "language_mon_khmer",
    "mon_language": "language_mon_khmer",
    "khmer_language": "language_mon_khmer",
    "bahnaric_language": "language_mon_khmer",
    "katuic_language": "language_mon_khmer",
    "aslian_language": "language_mon_khmer",
    "khasi_language": "language_mon_khmer",
    "vietnamese_language": "language_vietnamese",
    "thai_dialect": "language_tai",
    "lao_dialect": "language_tai",
    "shan_dialect": "language_tai",
    "dai_dialect": "language_tai",
    "zhuang_language": "language_tai",
    "hlai_language": "language_tai",
    "kam_language": "language_tai",
    "hmong_language": "language_hmongic",
    "yao_language": "language_hmongic",
    # --- 海洋东南亚 / 太平洋 ---
    "malay_dialect": "language_austronesian",
    "javanese_language": "language_austronesian",
    "sundanese_language": "language_austronesian",
    "balinese_language": "language_austronesian",
    "madurese_language": "language_austronesian",
    "minangkabau_dialect": "language_austronesian",
    "banjarese_dialect": "language_austronesian",
    "iban_dialect": "language_austronesian",
    "lampung_language": "language_austronesian",
    "achenese_dialect": "language_austronesian",
    "buginese_language": "language_austronesian",
    "dayak_language": "language_austronesian",
    "barito_language": "language_austronesian",
    "kayanic_language": "language_austronesian",
    "maluku_language": "language_austronesian",
    "ternate_language": "language_austronesian",
    "halmaheran_language": "language_austronesian",
    "gorontalo_language": "language_austronesian",
    "celebic_language": "language_austronesian",
    "sumba_language": "language_austronesian",
    "timoric_language": "language_austronesian",
    "rejang_language": "language_austronesian",
    "kutai_dialect": "language_austronesian",
    "bornean_language": "language_austronesian",
    "cham_dialect": "language_chamic",
    "tagalog_language": "language_austronesian",
    "ilocano_language": "language_austronesian",
    "cebuano_dialect": "language_austronesian",
    "hiligaynon_dialect": "language_austronesian",
    "waray_dialect": "language_austronesian",
    "bikol_language": "language_austronesian",
    "kapampangan_language": "language_austronesian",
    "manobo_dialect": "language_austronesian",
    "subanon_dialect": "language_austronesian",
    "danao_dialect": "language_austronesian",
    "sama_language": "language_austronesian",
    "palawanic_dialect": "language_austronesian",
    "southern_visayan_dialect": "language_austronesian",
    "formosan_language": "language_austronesian",
    "maori_language": "language_austronesian",
    "paumotu_language": "language_austronesian",
    "kajin_majel_language": "language_austronesian",
    "i_kiribati_language": "language_austronesian",
    "reo_maohi_language": "language_austronesian",
    "olelo_hawaii_language": "language_austronesian",
    "tongic_language": "language_austronesian",
    "vosa_vaka_viti_language": "language_austronesian",
    "eo_enana_language": "language_austronesian",
    "malagasy_language": "language_austronesian",
    # --- 巴布亚 ---
    "awyu_language": "language_papuan",
    "asmat_language": "language_papuan",
    "madang_language": "language_papuan",
    "siar_language": "language_papuan",
    "guhu_oro_language": "language_papuan",
    "nehan_language": "language_papuan",
    "moru_madi_language": "language_papuan",
    # --- 非洲 ---
    "ethiopic_language": "language_ethiopic",
    "north_ethiopic_language": "language_ethiopic",
    "somali_dialect": "language_cushitic",
    "afar_dialect": "language_cushitic",
    "beja_language": "language_cushitic",
    "oromo_dialect": "language_cushitic",
    "agaw_language": "language_cushitic",
    "highland_cushitic_dialect": "language_cushitic",
    "south_cushitic_language": "language_cushitic",
    "rendille_dialect": "language_cushitic",
    "dahalo_dialect": "language_cushitic",
    "omotic_language": "language_omotic",
    "nubian_language": "language_sudanic",
    "daju_language": "language_sudanic",
    "dinka_language": "language_sudanic",
    "lotuko_language": "language_sudanic",
    "luo_language": "language_sudanic",
    "kalenjin_language": "language_sudanic",
    "baguirmi_language": "language_sudanic",
    "hausa_language": "language_chadic",
    "sao_language": "language_chadic",
    "mande_language": "language_manding",
    "mel_language": "language_manding",
    "senegambian_language": "language_senegambian",
    "nigerian_language": "language_yoruba",
    "ijaw_language": "language_yoruba",
    "kwa_language": "language_kwa",
    "kru_language": "language_kru",
    "gur_language": "language_gur",
    "senufo_language": "language_gur",
    "adamawa_language": "language_gur",
    "ubangian_language": "language_gur",
    "songhai_language": "language_ayneha",
    "dogon_language": "language_soninke",
    "saharan_language": "language_tubu",
    "kanuri_language": "language_tubu",
    "swahili_language": "language_sabaki",
    "kongo_language": "language_sabaki",
    "luba_language": "language_sabaki",
    "kavango_language": "language_sabaki",
    "chokwe_language": "language_sabaki",
    "shona_dialect": "language_sabaki",
    "sotho_dialect": "language_sabaki",
    "nguni_dialect": "language_sabaki",
    "nyasa_language": "language_sabaki",
    "rwanda_language": "language_sabaki",
    "rukwa_language": "language_sabaki",
    "makhuwa_dialect": "language_sabaki",
    "tswa_ronga_dialect": "language_sabaki",
    "nyamwezi_language": "language_sabaki",
    "lega_language": "language_sabaki",
    "rufiji_ruvuma_language": "language_sabaki",
    "bantoid_language": "language_sabaki",
    "tsogo_language": "language_sabaki",
    "bassa_language": "language_sabaki",
    "bangi_language": "language_sabaki",
}

# 关键词兜底（按顺序匹配，EXACT 未命中时才用）
RULES = [
    (r"mandarin|^(jin|shu|wu|gan|yue|min|kejia|xiang|huizhou|ping|bai)_", "language_chinese"),
    (r"german", "language_high_german"),
    (r"slav", "language_east_slavic"),
    (r"turk", "language_turkic"),
    (r"iran|persian|kurd|baloch|tajik", "language_iranian"),
    (r"arab", "language_arabic"),
    (r"berber|tamazight|kabyl", "language_berber"),
    (r"bantu|sabaki", "language_sabaki"),
    (r"cushit", "language_cushitic"),
    (r"nilotic|sudanic", "language_sudanic"),
    (r"austrones", "language_austronesian"),
    (r"papuan", "language_papuan"),
    (r"tungus", "language_tungusic"),
    (r"mongol", "language_mongolic"),
    (r"tibet", "language_tibetan"),
    (r"tai_|^thai|zhuang", "language_tai"),
    (r"khmer|mon_|bahna|katu", "language_mon_khmer"),
    (r"dravid", "language_tamil"),
    (r"indo_aryan|sauraseni", "language_sauraseni"),
    (r"ital|romance", "language_italian"),
    (r"slavic", "language_south_slavic"),
]

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
    eu5_lang = {}
    for fn in os.listdir(os.path.join(EU5, "common", "cultures")):
        if not fn.endswith(".txt"):
            continue
        for path, key, body in walk(read(os.path.join(EU5, "common", "cultures", fn))):
            if path:
                continue
            lg = re.search(r"(?m)^\s*language\s*=\s*(\S+)", body)
            if lg:
                eu5_lang[key] = lg.group(1)

    raw = read(os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt"))
    cnt = Counter(re.findall(r"(?m)^\s*culture\s*=\s*(\S+)", raw))

    # 校验目标 key 都是 CK3 原版真实存在的
    ck3_lang = set()
    for path, key, body in walk(read(os.path.join(CK3, "common", "culture", "pillars", "00_language.txt"))):
        if not path:
            ck3_lang.add(key)

    stat = defaultdict(lambda: {"cultures": 0, "baronies": 0, "how": ""})
    for c, n in cnt.items():
        lg = eu5_lang.get(c)
        if not lg:
            continue
        s = stat[lg]
        s["cultures"] += 1
        s["baronies"] += n

    rows = []
    bad = []
    for lg, s in stat.items():
        tgt = EXACT.get(lg)
        how = "exact"
        if not tgt:
            for pat, cand in RULES:
                if re.search(pat, lg):
                    tgt, how = cand, "rule:" + pat
                    break
        if tgt and tgt not in ck3_lang:
            bad.append((lg, tgt))
            tgt = None
        rows.append({
            "eu5_language": lg, "cultures": s["cultures"], "baronies": s["baronies"],
            "ck3_language": tgt or "", "status": "mapped" if tgt else "keep", "how": how if tgt else "",
        })

    rows.sort(key=lambda r: -r["baronies"])
    with io.open(os.path.join(OUTDIR, "_eu5_language_to_ck3.csv"), "w",
                 encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["eu5_language", "cultures", "baronies",
                                          "ck3_language", "status", "how"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    tot = sum(r["baronies"] for r in rows)
    mapped = sum(r["baronies"] for r in rows if r["status"] == "mapped")
    n_map = sum(1 for r in rows if r["status"] == "mapped")
    L = []
    L.append("EU5 language: %d 个 | 男爵领 %d" % (len(rows), tot))
    L.append("映射到 CK3 原版 language: %d 个 language，覆盖 %d 男爵领 = %.1f%%"
             % (n_map, mapped, 100.0 * mapped / tot))
    L.append("保留自定义: %d 个 language，%d 男爵领 (%.1f%%)"
             % (len(rows) - n_map, tot - mapped, 100.0 * (tot - mapped) / tot))
    if bad:
        L.append("")
        L.append("目标 key 不在 CK3 原版（已作废）: %s" % bad)
    L.append("")
    L.append("保留自定义的（按男爵领降序）:")
    for r in rows:
        if r["status"] == "keep":
            L.append("  %-40s %5d 男爵领 %3d 文化" % (r["eu5_language"], r["baronies"], r["cultures"]))
    io.open(os.path.join(OUTDIR, "_eu5_language_to_ck3.log"), "w",
            encoding="utf-8", newline="\n").write("\n".join(L))
    print("ok")


if __name__ == "__main__":
    main()
