# -*- coding: utf-8 -*-
"""只读勘察：cul_ slug 在 EU5 中英文里能查到多少。"""
import io, os, re

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"

def load(path, plain=True):
    d = {}
    if not os.path.exists(path):
        return d
    for ln in io.open(path, encoding="utf-8-sig", errors="replace"):
        m = re.match(r'^\s*([A-Za-z0-9_.\-]+):\d*\s*"([^"]*)"', ln)
        if m:
            d.setdefault(m.group(1), m.group(2))
    return d

for lang in ("english", "simp_chinese"):
    base = os.path.join(EU5, "main_menu", "localization", lang)
    d = {}
    for fn in ("character_names_dynamic_l_%s.yml" % lang, "character_names_l_%s.yml" % lang):
        d.update(load(os.path.join(base, fn)))
    globals()["eu5_" + lang] = d
    print("%s name keys: %d" % (lang, len(d)))

en = load(os.path.join(MOD, "localization", "english", "gen_cultures_l_english.yml"))
cul = {k: v for k, v in en.items() if k.startswith("cul_")}
print("cul_ keys: %d" % len(cul))

# 只被新文化引用的 cul_（排除 64 个顶原版块里的）
nl_path = os.path.join(MOD, "common", "culture", "name_lists", "00_generated_name_lists.txt")
raw = io.open(nl_path, encoding="utf-8-sig", errors="replace").read()
blocks = re.findall(r'(?ms)^(name_list_[A-Za-z0-9_-]+)\s*=\s*\{(.*?)^\}', raw)
print("解析块: %d" % len(blocks))
print("样例块 key:", [b[0] for b in blocks[:3]])

hit_zh = hit_en = 0
miss = []
for k, v in cul.items():
    slug = k[4:]
    cands = [slug, "name_" + slug]
    if any(c in eu5_simp_chinese for c in cands):
        hit_zh += 1
    else:
        miss.append(slug)
    if any(c in eu5_english for c in cands):
        hit_en += 1
print("EU5 中文命中: %d / %d (%.1f%%)" % (hit_zh, len(cul), 100.0 * hit_zh / len(cul)))
print("EU5 英文命中: %d / %d (%.1f%%)" % (hit_en, len(cul), 100.0 * hit_en / len(cul)))
print("未命中样例:", miss[:25])
