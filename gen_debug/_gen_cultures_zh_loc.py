# -*- coding: utf-8 -*-
"""生成中文文化/语言/传承/人名本地化。

镜像英文侧的两个文件：
  localization/english/gen_cultures_l_english.yml   → localization/simp_chinese/gen_cultures_l_simp_chinese.yml
  localization/english/zz_eu5_names_l_english.yml   → localization/simp_chinese/zz_eu5_names_l_simp_chinese.yml

名字一律取 EU5 官方中文本地化，取不到就留空（回落英文），绝不自己音译。

纪律：
  - 目标文件已存在时**只补缺失 key**，已有的行原样保留（除非 --refresh 指定）
  - 无变化不写盘
  - BOM + CRLF
"""
import io, os, re, csv, sys, shutil, datetime, collections

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"

EN_CULT = os.path.join(MOD, "localization", "english", "gen_cultures_l_english.yml")
EN_NAME = os.path.join(MOD, "localization", "english", "zz_eu5_names_l_english.yml")
ZH_CULT = os.path.join(MOD, "localization", "simp_chinese", "gen_cultures_l_simp_chinese.yml")
ZH_NAME = os.path.join(MOD, "localization", "simp_chinese", "zz_eu5_names_l_simp_chinese.yml")
CULT_ZH = os.path.join(MOD, "gen_debug", "_eu5_culture_zh.csv")
REPORT = os.path.join(MOD, "gen_debug", "_zh_loc_missing.csv")

RE_EN = re.compile(r'^\s*([A-Za-z0-9_]+):\d*\s*"([^"]*)"\s*$')
RE_ZH = re.compile(r'^\s*([A-Za-z0-9_]+):\d*\s*"([^"]*)"\s*$')
RE_EU5 = re.compile(r'^\s*([A-Za-z0-9_.]+):\s*"([^"]*)"\s*(?:#.*)?$')

# ---------- 1. EU5 中文本地化 ----------
eu5 = {}
for root, _, fs in os.walk(os.path.join(EU5, "main_menu", "localization", "simp_chinese")):
    for fn in fs:
        if not fn.endswith(".yml"):
            continue
        for line in io.open(os.path.join(root, fn), encoding="utf-8-sig", errors="replace"):
            m = RE_EU5.match(line)
            if m and m.group(1) not in eu5:
                eu5[m.group(1)] = m.group(2)

# ---------- 2. 我们的英文 key ----------
def load_en(p):
    d = {}
    for line in io.open(p, encoding="utf-8-sig"):
        m = RE_EN.match(line)
        if m:
            d[m.group(1)] = m.group(2)
    return d

en_cult = load_en(EN_CULT)
en_name = load_en(EN_NAME)

# ---------- 3. 文化中文名 ----------
cult_zh = {}
for r in csv.DictReader(io.open(CULT_ZH, encoding="utf-8-sig")):
    if r["name_zh"]:
        cult_zh[r["culture"]] = r["name_zh"]
CULT = set(cult_zh) | {r["culture"] for r in csv.DictReader(
    io.open(CULT_ZH, encoding="utf-8-sig"))}

# ---------- 4. 传承 / 语言 key 集合 ----------
heritage_keys, language_keys = set(), set()
pillar = os.path.join(MOD, "common", "culture", "pillars", "00_generated_pillars.txt")
if os.path.exists(pillar):
    cur, typ = None, None
    for line in io.open(pillar, encoding="utf-8-sig", errors="replace"):
        m = re.match(r'^([a-z0-9_]+)\s*=\s*\{', line)
        if m:
            cur, typ = m.group(1), None
            continue
        if cur:
            m2 = re.match(r'^\s*type\s*=\s*(\w+)', line)
            if m2:
                typ = m2.group(1)
                (heritage_keys if typ == "heritage" else language_keys if typ == "language" else set()).add(cur)
            if line.strip() == "}":
                cur = None

# ---------- 5. 名字解析 ----------
def zh_of_heritage(k):
    for cand in (k,
                 k[:-len("_culture_group")] + "_culture" if k.endswith("_culture_group") else None,
                 k[:-len("_group")] + "_culture" if k.endswith("_group") else None,
                 k[:-len("_culture_group")] if k.endswith("_culture_group") else None,
                 k[:-len("_group")] if k.endswith("_group") else None):
        if cand and cand in eu5:
            return eu5[cand]
    return ""

def zh_of_language(k):
    for cand in (k, k[:-len("_dialect")] + "_language" if k.endswith("_dialect") else None,
                 k + "_language" if not k.endswith("_language") else None):
        if cand and cand in eu5:
            return eu5[cand]
    return ""

def zh_of_person(x):
    for cand in (x, "name_" + x, x + "_province", x + "_culture", x + "_location",
                 x + "_area", x + "_region", x + "_language"):
        if cand in eu5:
            return eu5[cand]
    return ""

def resolve(key):
    """返回 (中文, 归类)；无解返回 ('', 归类)。"""
    if key.startswith("name_eu5_"):
        return zh_of_person(key[9:]), "人名"
    for suf in ("_collective_noun", "_prefix", "_name"):
        if key.endswith(suf):
            base = key[:-len(suf)]
            if base in CULT:
                return cult_zh.get(base, ""), "文化"
            if base.startswith("eu5_language_"):
                return zh_of_language(base[len("eu5_language_"):]), "语言"
            if base.startswith("eu5_heritage_"):
                return zh_of_heritage(base[len("eu5_heritage_"):]), "传承"
            if base in language_keys:
                return zh_of_language(base), "语言"
            if base in heritage_keys:
                return zh_of_heritage(base), "传承"
            return "", "?"
    if key in CULT:
        return cult_zh.get(key, ""), "文化"
    if key.startswith("name_list_"):
        return cult_zh.get(key[10:], ""), "文化"
    return "", "?"

# ---------- 6. 生成 ----------
def build(en, label, refresh):
    existing = {}
    target = ZH_CULT if label == "cult" else ZH_NAME
    if os.path.exists(target):
        for line in io.open(target, encoding="utf-8-sig"):
            m = RE_ZH.match(line)
            if m:
                existing[m.group(1)] = m.group(2)

    want, missing = {}, []
    for k in en:
        z, fam = resolve(k)
        if z:
            want[k] = z
        else:
            missing.append((k, en[k], fam))
    return target, existing, want, missing

for label, en, title in (("cult", en_cult, "文化/语言/传承"), ("name", en_name, "人名")):
    target, existing, want, missing = build(en, label, False)
    added = [k for k in want if k not in existing]
    upd = [k for k in want if k in existing and existing[k] != want[k]]
    print("=== %s (%s) ===" % (title, os.path.basename(target)))
    print("  英文 %d / 可译 %d / 缺 %d" % (len(en), len(want), len(missing)))
    print("  文件已有 %d；新增 %d，值有变 %d" % (len(existing), len(added), len(upd)))
    fam = collections.Counter(f for _, _, f in missing)
    print("  缺失归类：", dict(fam))

    final = dict(existing)
    if label == "cult":
        # 这份文件 100% 由本脚本生成、无手改，直接按源重算（_collective_noun 要去掉「人」）
        final.update(want)
        dirty = bool(added or upd)
    else:
        # 人名文件是既有产物、可能有手改，只补缺失，且没有新增就完全不碰（避免整表重排 churn）
        for k, v in want.items():
            final.setdefault(k, v)
        dirty = bool(added)
    if not dirty:
        print("  无需要写入的改动，不写盘。\n")
        continue

    if os.path.exists(target):
        bak = target + ".bak_zh_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(target, bak)
        print("  已备份 →", os.path.basename(bak))

    fmt = ' %s:0 "%s"' if label == "name" else ' %s: "%s"'
    lines = ["\ufeffl_simp_chinese:"]
    for k in sorted(final):
        lines.append(fmt % (k, final[k]))
    with io.open(target, "w", encoding="utf-8", newline="\r\n") as fp:
        fp.write("\n".join(lines) + "\n")
    print("  写出 %d 条\n" % len(final))

# ---------- 7. 缺失清单 ----------
FAMS = {"文化", "语言", "传承", "人名"}
allmiss = []
for label, en, title in (("cult", en_cult, "文化/语言/传承"), ("name", en_name, "人名")):
    _, _, _, missing = build(en, label, False)
    for k, v, fam in missing:
        if fam in FAMS:
            allmiss.append({"key": k, "family": fam, "name_en": v})
with io.open(REPORT, "w", encoding="utf-8-sig", newline="") as fp:
    w = csv.DictWriter(fp, fieldnames=["key", "family", "name_en"])
    w.writeheader()
    w.writerows(sorted(allmiss, key=lambda x: (x["family"], x["key"])))
print("缺失清单 →", os.path.basename(REPORT), len(allmiss), "条")
