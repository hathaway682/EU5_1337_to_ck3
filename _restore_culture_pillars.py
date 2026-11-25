# -*- coding: utf-8 -*-
"""恢复被 git checkout 冲掉的 ethos / martial_custom / heritage+language。
来源：对话记录中已落盘过的脚本（行 1127 ETHOS、1220/1231/1239 调整、1207 MARTIAL、
921/949/957/1055/1073/1085 语系与安第斯/澳洲）。
默认 dry run，加 --apply 才写。
"""
import os, re, sys, tempfile

FILES = [
    "common/culture/cultures/zz_eu5_culture_americas.txt",
    "common/culture/cultures/zz_eu5_culture_group.txt",
    "common/culture/cultures/zz_eu5_culture_new.txt",
]

# ---------------- ETHOS（行 1155 最终表 + 1220/1231/1239 调整） ----------------
ETHOS = {}
def _add(v, keys):
    for k in keys.split():
        ETHOS[k] = v

_add("bellicose", "nahua dakota dhegiha chiwere apsaalooke_hiraaca siksika tsehesenestsestotse shawnee "
     "nuuchi_nuwu caribe tupi muchik chicham waqha mataco_guaicuru zamuco charrua panche pijao tarairiu mapudungun")
_add("stoic", "inuit yaghan kawesqar tshon chono nadene abenakian shoshoni paiute takic atakapa "
     "coahuilteco choco pukina ckunsa cacan warao")
_add("spiritual", "maya puebloan tanoan yutonahua anishinabe hinonoeitiit yupik australian pama_nyungan "
     "calima barbakoan jirajaran cuicas")
_add("egalitarian", "muskogee ta_arawakan tucanoan chumashan atallan malagasy lenape malibu")
_add("courtly", "natchez caddoan tsimshian wakashan tayrona sinu polynesian micronesian")
_add("bureaucratic", "quechuan quingnam purepecha eastern_otomanguean haudenosaunee powhatan")
_add("communal", "massachusett myaamia cree cherokee chickasaw_choctaw chitimacha timucua tutelo iroquoian "
     "skarureh wendat ktunaxa penutian hokan salishan otopamean totozoquean cuitlatec chibchan guahibo pume "
     "macro_je txapakura movima besiro napuruna henia_kamiare misumalpan aymara seeptsa warpe khoisan")
# 1220 批量调整
for _k in ["muskogee", "chickasaw_choctaw", "chitimacha", "hokan", "penutian", "salishan", "chibchan"]:
    ETHOS[_k] = "spiritual"
ETHOS["haudenosaunee"] = "egalitarian"
# 1231
ETHOS["timucua"] = "spiritual"
# 1239
ETHOS["powhatan"] = "communal"

# ---------------- MARTIAL（其余全部 male_only，female_only 清零） ----------------
EQUAL = {
    "cherokee", "haudenosaunee", "iroquoian", "wendat", "skarureh",
    "muskogee", "chickasaw_choctaw", "natchez", "puebloan", "tanoan",
    "siksika", "apsaalooke_hiraaca", "dakota",
    "mapudungun", "ta_arawakan", "nahua", "maya", "polynesian",
}

# ---------------- HERITAGE ----------------
HERITAGE = {}
for k in ["apsaalooke_hiraaca", "chiwere", "dakota", "dhegiha", "tutelo"]:
    HERITAGE[k] = "siouan_language_family"
for k in ["cherokee", "haudenosaunee", "iroquoian", "skarureh", "wendat"]:
    HERITAGE[k] = "iroquoian_language_family"
for k in ["abenakian", "lenape", "massachusett", "powhatan", "anishinabe",
          "cree", "myaamia", "shawnee", "hinonoeitiit", "siksika",
          "tsehesenestsestotse"]:
    HERITAGE[k] = "algonquian_language_family"
for k in ["nahua", "yutonahua", "nuuchi_nuwu", "paiute", "shoshoni", "takic"]:
    HERITAGE[k] = "yutonahua_language_family"
for k in ["chickasaw_choctaw", "muskogee"]:
    HERITAGE[k] = "muskogean_language_family"
for k in ["eastern_otomanguean", "otopamean"]:
    HERITAGE[k] = "otomanguean_language_family"
for k in ["inuit", "yupik"]:
    HERITAGE[k] = "eskaleut_language_family"
HERITAGE["caribe"] = "cariban_language_family"
HERITAGE["ta_arawakan"] = "arawakan_language_family"
# 安第斯 10 个
for k in ["atallan", "aymara", "cacan", "muchik", "pukina", "quechuan",
          "quingnam", "seeptsa", "ckunsa", "chicham"]:
    HERITAGE[k] = "andean_group"
# 澳洲
HERITAGE["pama_nyungan"] = "australian_group"

# ---------------- LANGUAGE ----------------
LANGUAGE = {}
for k in ["apsaalooke_hiraaca", "chiwere", "dakota", "dhegiha", "tutelo"]:
    LANGUAGE[k] = "eu5_language_siouan_language_family"
for k in ["cherokee", "haudenosaunee", "iroquoian", "skarureh", "wendat"]:
    LANGUAGE[k] = "eu5_language_iroquoian_language_family"
for k in ["abenakian", "lenape", "massachusett", "powhatan"]:
    LANGUAGE[k] = "eu5_language_eastern_algonquian_language_family"
for k in ["anishinabe", "cree", "myaamia", "shawnee"]:
    LANGUAGE[k] = "eu5_language_central_algonquian_language_family"
for k in ["hinonoeitiit", "siksika", "tsehesenestsestotse"]:
    LANGUAGE[k] = "eu5_language_plains_algonquian_language_family"
for k in ["nuuchi_nuwu", "paiute", "shoshoni", "takic"]:
    LANGUAGE[k] = "eu5_language_northern_yutonahua_language_family"
for k in ["nahua", "yutonahua"]:
    LANGUAGE[k] = "eu5_language_southern_yutonahua_language_family"
for k in ["chickasaw_choctaw", "muskogee"]:
    LANGUAGE[k] = "eu5_language_muskogean_language_family"
for k in ["eastern_otomanguean", "otopamean"]:
    LANGUAGE[k] = "eu5_language_otomanguean_language_family"
for k in ["inuit", "yupik"]:
    LANGUAGE[k] = "eu5_language_eskaleut_language_family"
LANGUAGE["caribe"] = "eu5_language_cariban_language_family"
LANGUAGE["ta_arawakan"] = "eu5_language_arawakan_language_family"


def blocks(text):
    """返回 [(key, start, end)]，end 指向块内最后一个字符之后（不含 \n}）。"""
    out = []
    for m in re.finditer(r'(?m)^([A-Za-z0-9_-]+) = \{', text):
        k = m.group(1)
        s = m.start()
        e = text.find("\n}", m.end())
        if e < 0:
            e = len(text)
        out.append((k, s, e))
    return out


def main():
    apply = "--apply" in sys.argv
    stat = {"ethos": 0, "martial": 0, "heritage": 0, "language": 0}
    missing = set()
    for p in FILES:
        raw = open(p, "rb").read()
        bom = raw[:3] == b"\xef\xbb\xbf"
        text = raw[3:].decode("utf-8") if bom else raw.decode("utf-8")
        edits = []
        for k, s, e in blocks(text):
            blk = text[s:e]
            nb = blk
            if k in ETHOS:
                nb2 = re.sub(r'(?m)^(\tethos = )ethos_[a-z_]+', lambda m: m.group(1) + "ethos_" + ETHOS[k], nb)
                if nb2 == nb and not re.search(r'(?m)^\tethos = ', nb):
                    missing.add(("ethos", k))
                elif nb2 != nb:
                    stat["ethos"] += 1
                nb = nb2
            if re.search(r'(?m)^\tmartial_custom = ', blk):
                tgt = "martial_custom_equal" if k in EQUAL else "martial_custom_male_only"
                nb2 = re.sub(r'(?m)^(\tmartial_custom = )martial_custom_[a-z_]+', lambda m: m.group(1) + tgt, nb)
                if nb2 != nb:
                    stat["martial"] += 1
                nb = nb2
            if k in HERITAGE:
                nb2 = re.sub(r'(?m)^(\theritage = )[A-Za-z0-9_]+', lambda m: m.group(1) + HERITAGE[k], nb)
                if nb2 == nb and not re.search(r'(?m)^\theritage = ', nb):
                    missing.add(("heritage", k))
                elif nb2 != nb:
                    stat["heritage"] += 1
                nb = nb2
            if k in LANGUAGE:
                nb2 = re.sub(r'(?m)^(\tlanguage = )[A-Za-z0-9_]+', lambda m: m.group(1) + LANGUAGE[k], nb)
                if nb2 == nb and not re.search(r'(?m)^\tlanguage = ', nb):
                    missing.add(("language", k))
                elif nb2 != nb:
                    stat["language"] += 1
                nb = nb2
            if nb != blk:
                edits.append((s, e, nb))
        print("%-52s 改动块 %d" % (p.split("/")[-1], len(edits)))
        if apply and edits:
            for s, e, nb in sorted(edits, key=lambda x: -x[0]):
                text = text[:s] + nb + text[e:]
            fd, tmp = tempfile.mkstemp(dir=os.path.dirname(p), suffix=".tmp")
            with os.fdopen(fd, "wb") as fh:
                fh.write((b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8"))
            os.replace(tmp, p)
    print("统计：", stat)
    print("缺行：", sorted(missing) or "无")
    print("映射表：ethos %d / heritage %d / language %d / equal %d"
          % (len(ETHOS), len(HERITAGE), len(LANGUAGE), len(EQUAL)))
    print("模式：", "已写入" if apply else "dry run（加 --apply 写盘）")


if __name__ == "__main__":
    main()
