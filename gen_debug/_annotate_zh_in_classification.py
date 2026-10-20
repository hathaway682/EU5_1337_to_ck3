# -*- coding: utf-8 -*-
"""给 _culture_classification.csv 里提到的每个文化补上中文本地化。

文件里有两类文化 key：
  culture   我们 mod 的 2088 个文化
  target    目标文化，分三种
              - CK3 原版文化（bodpa / nepali / karluk …）
              - CK3 融合文化名（anatolian_turkish / norse_gael …）
              - NEW:xxx 需要新建的文化（xxx 取自 EU5 语言键或文化组键）

中文名解析顺序（取到即止，绝不自己音译）：
  1. _ck3_culture_names.csv            CK3 244 个原版文化的中文显示名
  2. CK3 culture_creation_names        融合文化名
  3. CK3 cultures_l_simp_chinese       原版文化裸键
  4. 我们 gen_cultures_*_zh            <k>_culture
  5. 我们 gen_cultures_*_zh            eu5_language_<k>_language_name（去「语」）
  6. 我们 gen_cultures_*_zh            <k>_group_name / <k>_culture_group_name
  7. EU5 官方中文全表                   <k>_culture / _language / _dialect / _group / _province
  8. ALIAS 表                           key 拼写差异（ubangi→ubangian 等）
  9. MANUAL 表                          mod 自造、无任何外部来源的 key

用法：
  python _annotate_zh_in_classification.py            # 只报告
  python _annotate_zh_in_classification.py --apply    # 落盘（先备份）
"""
import io, os, re, csv, sys, glob, shutil, datetime, collections

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
GD = os.path.join(MOD, "gen_debug")
CSV_IN = os.path.join(GD, "_culture_classification.csv")
CK3_LOC = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game\localization\simp_chinese\culture"
EU5_LOC = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game\main_menu\localization\simp_chinese"
OUR_LOC = os.path.join(MOD, "localization", "simp_chinese", "gen_cultures_l_simp_chinese.yml")

APPLY = "--apply" in sys.argv

RE_LOC = re.compile(r'^\s*([A-Za-z0-9_.\-]+):\s*"((?:[^"\\]|\\.)*)"\s*(?:#.*)?$')


def load_yml(path):
    d = {}
    if not os.path.exists(path):
        return d
    with io.open(path, encoding="utf-8-sig", errors="ignore") as fp:
        for line in fp:
            m = RE_LOC.match(line)
            if m:
                d[m.group(1)] = m.group(2)
    return d


def load_dir(pattern):
    d = {}
    for p in glob.glob(pattern):
        for k, v in load_yml(p).items():
            d.setdefault(k, v)
    return d


# ---------- 数据源 ----------
ck3_names = {}
p = os.path.join(GD, "_ck3_culture_names.csv")
if os.path.exists(p):
    for r in csv.DictReader(io.open(p, encoding="utf-8-sig")):
        if r.get("name_zh"):
            ck3_names[r["culture"]] = r["name_zh"]

ck3_culture = load_yml(os.path.join(CK3_LOC, "cultures_l_simp_chinese.yml"))
ck3_hybrid = load_yml(os.path.join(CK3_LOC, "culture_creation_names_l_simp_chinese.yml"))
our_loc = load_yml(OUR_LOC)
eu5_loc = load_dir(os.path.join(EU5_LOC, "*.yml"))

eu5_zh = {}
p = os.path.join(GD, "_eu5_culture_zh.csv")
if os.path.exists(p):
    for r in csv.DictReader(io.open(p, encoding="utf-8-sig")):
        if r.get("name_zh"):
            eu5_zh[r["culture"]] = r["name_zh"]

# key 拼写差异：我们按 EU5 语言键取名，EU5 中文表里却挂在别的拼法下
ALIAS = {
    "ubangi": "ubangian",
}

# mod 自造、任何外部数据都没有的 key —— 只能我们自己定名，不是翻译
MANUAL = {
    "caucasian_avar": "高加索阿瓦尔",
    "turkic_steppe":  "突厥草原",
    "yao_malawi":     "马拉维瑶",
    "unsettled":      "无主之地",
    "gen_culture_unsettled": "无主之地",
    "iraqw":          "伊拉库",
}


def strip_yu(s):
    return s[:-1] if s.endswith("语") and len(s) > 1 else s


RE_VAR = re.compile(r"\$([A-Za-z0-9_.\-]+)\$")


def expand(s, depth=0):
    """CK3 融合名常写成 "$arpitan_name$"，把 $key$ 展开成实际文字。"""
    if not s or "$" not in s or depth > 4:
        return s
    def sub(m):
        k = m.group(1)
        for d in (ck3_hybrid, ck3_culture, our_loc, eu5_loc):
            if k in d:
                return expand(d[k], depth + 1)
        return m.group(0)
    return RE_VAR.sub(sub, s)


def zh_of(k):
    """返回 (中文名, 来源)，取不到 (None, None)。"""
    if k in ck3_names:
        return ck3_names[k], "CK3文化名"
    if k + "_name" in ck3_hybrid:
        return expand(ck3_hybrid[k + "_name"]), "CK3融合名"
    if k in ck3_culture:
        return ck3_culture[k], "CK3原版loc"
    if k + "_culture" in our_loc:
        return our_loc[k + "_culture"], "EU5文化名"
    if "eu5_language_%s_language_name" % k in our_loc:
        return strip_yu(our_loc["eu5_language_%s_language_name" % k]), "EU5语言名"
    for cand in (k + "_group_name", k + "_culture_group_name"):
        if cand in our_loc:
            return our_loc[cand], "文化组名"
    for suf in ("_culture", "_language", "_dialect", "_culture_group", "_group", "_province", "_area"):
        if k + suf in eu5_loc:
            return strip_yu(expand(eu5_loc[k + suf])), "EU5官方中文" + suf
    if k in eu5_zh:
        return eu5_zh[k], "EU5文化中文表"
    if k in ALIAS:
        return zh_of(ALIAS[k])
    if k in MANUAL:
        return MANUAL[k], "mod自定名"
    return None, None


# ---------- 读分类 ----------
rows = list(csv.DictReader(io.open(CSV_IN, encoding="utf-8-sig")))
fields = list(rows[0].keys())

miss_cult, miss_tgt = [], []
srcs = collections.Counter()
for r in rows:
    z, s = zh_of(r["culture"])
    if z and "$" in z:
        z = None
    r["name_zh"] = z or ""
    if not z:
        miss_cult.append(r["culture"])

    t = r.get("target", "")
    if not t:
        r["target_zh"] = ""
        r["target_zh_src"] = ""
        continue
    k = t[4:] if t.startswith("NEW:") else t
    z, s = zh_of(k)
    if z and "$" in z:
        z = None
    r["target_zh"] = z or ""
    r["target_zh_src"] = s or ""
    if z:
        srcs[s] += 1
    else:
        miss_tgt.append(k)

# ---------- 列顺序：name_zh 跟在 name_en 后，target_zh 跟在 target 后 ----------
out_fields = []
for f in fields:
    out_fields.append(f)
    if f == "name_en":
        out_fields.append("name_zh")
    if f == "target":
        out_fields.append("target_zh")
        out_fields.append("target_zh_src")

uniq_tgt = {r["target"] for r in rows if r["target"]}
print("文化 %d / 目标 %d 种" % (len(rows), len(uniq_tgt)))
print("我们文化缺中文名: %d %s" % (len(miss_cult), " ".join(sorted(set(miss_cult))[:10])))
print("目标缺中文名:     %d 种 %s" % (len(set(miss_tgt)), " ".join(sorted(set(miss_tgt)))))
print("目标中文名来源:", dict(srcs.most_common()))

if not APPLY:
    print("\n（未落盘，加 --apply 才写）")
    sys.exit(0)

# ---------- 落盘：备份 + BOM + LF ----------
bak = CSV_IN + ".bak_zh_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy2(CSV_IN, bak)
buf = io.StringIO()
w = csv.DictWriter(buf, fieldnames=out_fields, lineterminator="\n", extrasaction="ignore")
w.writeheader()
for r in rows:
    w.writerow(r)
try:
    io.open(CSV_IN, "w", encoding="utf-8-sig", newline="").write(buf.getvalue())
    print("\n已写入 %s\n备份 %s" % (CSV_IN, os.path.basename(bak)))
except PermissionError:
    alt = CSV_IN.replace(".csv", ".annotated.csv")
    io.open(alt, "w", encoding="utf-8-sig", newline="").write(buf.getvalue())
    print("\n!! %s 被占用（多半 Excel 开着），已改写 %s" % (os.path.basename(CSV_IN), alt))
    print("   关掉 Excel 后把 .annotated.csv 覆盖回原名即可；备份 %s" % os.path.basename(bak))