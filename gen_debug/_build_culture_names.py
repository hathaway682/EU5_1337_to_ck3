# -*- coding: utf-8 -*-
"""把 CK3 原版文化的 key / 中英文显示名 对出来，并附上我们 mod 的文化中文名。

用途：11 类分类里说的「同名文化」指的是**显示名**，不是 key。
（例：CK3 的 turkish 显示名是「乌古斯」，turkmen 才是「土库曼」。）
"""
import io, os, re, csv

CK3 = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game\localization"
MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
OUT = os.path.join(MOD, "gen_debug", "_ck3_culture_names.csv")
OUT2 = os.path.join(MOD, "gen_debug", "_our_culture_names.csv")

RE_ZH = re.compile(r'^\s*([A-Za-z0-9_]+):\s*"(.*)"\s*$')
RE_EN = re.compile(r'^\s*([A-Za-z0-9_]+):\d*\s*"(.*)"\s*$')


def parse(path, rx):
    d = {}
    if not os.path.exists(path):
        return d
    for line in io.open(path, encoding="utf-8-sig", errors="replace"):
        m = rx.match(line)
        if m:
            k, v = m.group(1), m.group(2)
            if k not in d:
                d[k] = v
    return d


zh = parse(os.path.join(CK3, "simp_chinese", "culture", "cultures_l_simp_chinese.yml"), RE_ZH)
en = parse(os.path.join(CK3, "english", "culture", "cultures_l_english.yml"), RE_EN)

van = list(csv.DictReader(io.open(os.path.join(MOD, "gen_debug", "_ck3_vanilla_cultures.csv"),
                                  encoding="utf-8-sig")))
rows = []
for v in van:
    k = v["culture"]
    rows.append({
        "culture": k,
        "name_zh": zh.get(k, ""),
        "name_en": en.get(k, ""),
        "heritage": v["heritage"],
        "language": v["language"],
    })
rows.sort(key=lambda x: x["culture"])
with io.open(OUT, "w", encoding="utf-8-sig", newline="") as fp:
    w = csv.DictWriter(fp, fieldnames=["culture", "name_zh", "name_en", "heritage", "language"])
    w.writeheader()
    w.writerows(rows)

miss = [r["culture"] for r in rows if not r["name_zh"]]
print("CK3 原版文化 %d 个，缺中文名 %d 个：%s" % (len(rows), len(miss), ", ".join(miss[:20])))

# 我们 mod 的文化中文名
our_zh = {}
locdir = os.path.join(MOD, "localization", "simp_chinese")
if os.path.isdir(locdir):
    for fn in os.listdir(locdir):
        if fn.endswith(".yml"):
            our_zh.update(parse(os.path.join(locdir, fn), RE_ZH))

base = list(csv.DictReader(io.open(os.path.join(MOD, "gen_debug", "_culture_classify_base.csv"),
                                   encoding="utf-8-sig")))
with io.open(OUT2, "w", encoding="utf-8-sig", newline="") as fp:
    w = csv.DictWriter(fp, fieldnames=["culture", "name_zh", "name_en", "heritage", "language",
                                       "eu5_language", "eu5_groups", "baronies", "kingdoms"])
    w.writeheader()
    for b in base:
        w.writerow({
            "culture": b["culture"],
            "name_zh": our_zh.get(b["culture"], ""),
            "name_en": b["name_en"],
            "heritage": b["heritage"],
            "language": b["language"],
            "eu5_language": b["eu5_language"],
            "eu5_groups": b["eu5_groups"],
            "baronies": b["baronies"],
            "kingdoms": b["kingdoms"],
        })
print("我们 mod 文化 %d 个，缺中文名 %d 个" %
      (len(base), sum(1 for b in base if b["culture"] not in our_zh)))
