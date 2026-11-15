# -*- coding: utf-8 -*-
"""把欧洲的 d_eu5_* 一地公国撤掉，国家改挂所在伯爵领。

依据（用户 2026-11-15 22:42 指令）：
  「把所有欧洲的_eu5一地公国撤了改挂所在伯爵领，除了康诺特改挂同名有地公国」

口径：
  - 对象 = d_eu5_* 里 holder 在 1337.4.1 只持 1 个 c_、且无伯爵封臣的公国，共 25 个。
  - 排除 ITZ（伊察，c_tah_itza，尤卡坦，非欧洲），保留 d_eu5_itz 不动。
  - 其余 24 个：
      * 23 个改挂自己持有的那个 c_（tier d -> c，头衔名换成县名）；
      * CNN 康诺特特殊：改挂同名法理公国 d_connaught
        （c_roscommon 的 de jure 上级正是 d_connaught，该公国在
          00_landed_titles.txt 有声明、11 语言有本地化、纹章有映射，只是无 history 块）。
  - 头衔本体「撤了」= 删 history 块 + 删 titular 声明 + 删 11 语言本地化 + 记 dropped 清单。
  - KNI 医院骑士团在 common/scripted_effects/zz_eu5_1337_historical_orders.txt 里
    有 set_primary_title_to = title:d_eu5_kni，一并改指 c_rodos。

安全约束：
  - 读用 io.open(encoding="utf-8-sig", newline="") 保留 CRLF。
  - 写一律 临时文件 + os.replace，绝不对原文件开 "wb"。
  - 幂等：已落地状态再跑不会重复改。
"""
import io
import os
import re
import csv
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WRITE = "--write" in sys.argv

P_TITLES = os.path.join(ROOT, "history", "titles", "zz_eu5_titles.txt")
P_TITULAR = os.path.join(ROOT, "common", "landed_titles", "zz_eu5_titular.txt")
P_CSV = os.path.join(ROOT, "gen_debug", "eu5_ck3_title_map.csv")
P_OVR = os.path.join(ROOT, "gen_debug", "_title_overrides.csv")
P_DROP = os.path.join(ROOT, "gen_debug", "eu5_titles_dropped.txt")
P_ORDERS = os.path.join(ROOT, "common", "scripted_effects", "zz_eu5_1337_historical_orders.txt")

LANGS = ["braz_por", "english", "french", "german", "japanese", "korean",
         "polish", "russian", "simp_chinese", "spanish", "turkish"]

# (tag, 旧公国 key, 新 key, 新 tier, 新英文名, 新中文名)
PAIRS = [
    ("ARB", "d_eu5_arb", "c_arborea",    "c", "Arborea",       "阿尔博雷阿"),
    ("CNN", "d_eu5_cnn", "d_connaught",  "d", "Connaught",     "康诺特"),
    ("DRU", "d_eu5_dru", "c_barysaw",    "c", "Barysaw",       "鲍里索夫"),
    ("FEO", "d_eu5_feo", "c_gothia",     "c", "Gothia",        "哥提亚"),
    ("GLO", "d_eu5_glo", "c_glogow",     "c", "Glogow",        "格沃古夫"),
    ("KNI", "d_eu5_kni", "c_rodos",      "c", "Rhodes",        "罗得"),
    ("LCZ", "d_eu5_lcz", "c_leczyca",    "c", "Leczyca",       "文奇察"),
    ("LGC", "d_eu5_lgc", "c_legnica",    "c", "Legnica",       "莱格尼察"),
    ("LIE", "d_eu5_lie", "c_liege",      "c", "Liege",         "列日"),
    ("MPE", "d_eu5_mpe", "c_wizi",       "c", "Wizna",         "维济"),
    ("MRM", "d_eu5_mrm", "c_murom",      "c", "Murom",         "穆罗姆"),
    ("OEL", "d_eu5_oel", "c_olesnica",   "c", "Olesnica",      "奥莱希尼察"),
    ("OPL", "d_eu5_opl", "c_opole",      "c", "Opole",         "奥波莱"),
    ("OPV", "d_eu5_opv", "c_opavsko",    "c", "Opava",         "奥帕瓦斯科"),
    ("PLK", "d_eu5_plk", "c_plock",      "c", "Plock",         "普沃茨克"),
    ("RZH", "d_eu5_rzh", "c_rzhev",      "c", "Rzhev",         "勒热夫"),
    ("SDZ", "d_eu5_sdz", "c_sieradz",    "c", "Sieradz",       "谢拉兹"),
    ("SKY", "d_eu5_sky", "c_starodub",   "c", "Starodub",      "斯塔罗杜布"),
    ("SWD", "d_eu5_swd", "c_swidnica",   "c", "Swidnica",      "希维德尼察"),
    ("TES", "d_eu5_tes", "c_tesin",      "c", "Tesin",         "捷欣"),
    ("TPS", "d_eu5_tps", "c_toropets",   "c", "Toropets",      "托罗佩茨"),
    ("TRS", "d_eu5_trs", "c_tarusa",     "c", "Tarusa",        "塔鲁萨"),
    ("TUV", "d_eu5_tuv", "c_turov",      "c", "Turov",         "图罗夫"),
    ("ZAG", "d_eu5_zag", "c_zagan",      "c", "Zagan",         "扎甘"),
]
OLD_KEYS = [p[1] for p in PAIRS]

CONNAUGHT_BLOCK = (
    "d_connaught = {\r\n"
    "\t1324.1.1 = {\r\n"
    "\t\tholder = cnn_toirdelbach_o_conchobair\r\n"
    "\t}\r\n"
    "\t1337.4.1 = {\r\n"
    "\t\tholder = cnn_toirdelbach_o_conchobair\r\n"
    "\t\tgovernment = tribal_government\r\n"
    "\t}\r\n"
    "}"
)


def rd(p):
    return io.open(p, encoding="utf-8-sig", newline="").read()


def wr(p, text):
    tmp = p + ".tmp_new"
    with io.open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        f.write(text)
    os.replace(tmp, p)


def top_blocks(t):
    """返回 [(name, start, end)]，end 为下一个顶层块的起点。"""
    tops = [(m.group(1), m.start()) for m in re.finditer(r"(?m)^([a-z0-9_]+) = \{", t)]
    out = []
    for i in range(len(tops)):
        name, s = tops[i]
        e = tops[i + 1][1] if i + 1 < len(tops) else len(t)
        out.append((name, s, e))
    return out


def drop_blocks(t, targets, replace_with=None):
    """删掉顶层块（连块后空行），replace_with={name: text} 可原地替换。"""
    replace_with = replace_with or {}
    blocks = top_blocks(t)
    out = []
    last = 0
    n = 0
    for name, s, e in blocks:
        out.append(t[last:s])
        if name in targets:
            k = e
            while t.startswith("\r\n", k):
                k += 2
            if name in replace_with:
                out.append(replace_with[name])
            last = k
            n += 1
        else:
            out.append(t[s:e])
            last = e
    out.append(t[last:])
    return "".join(out), n


# ---------------------------------------------------------------- 1. history
t = rd(P_TITLES)
present = [p[1] for p in PAIRS if re.search(r"(?m)^" + p[1] + r" = \{", t)]
print("[history] 待删块 %d / %d: %s" % (len(present), len(PAIRS), ", ".join(present) if present else "无"))
new_t, n = drop_blocks(t, set(OLD_KEYS), {"d_eu5_cnn": CONNAUGHT_BLOCK})
print("[history] 实际删除 %d 块，插入 d_connaught：%s" % (
    n, "是" if re.search(r"(?m)^d_connaught = \{", new_t) else "否"))
if n:
    if WRITE:
        wr(P_TITLES, new_t)
    t = new_t

# ---------------------------------------------------------------- 2. titular
t = rd(P_TITULAR)
present = [p[1] for p in PAIRS if re.search(r"(?m)^" + p[1] + r" = \{", t)]
print("[titular] 待删声明 %d / %d" % (len(present), len(PAIRS)))
new_t, n = drop_blocks(t, set(OLD_KEYS))
print("[titular] 实际删除 %d 块" % n)
if n:
    if WRITE:
        wr(P_TITULAR, new_t)
    t = new_t

# ---------------------------------------------------------------- 3. 本地化
tot = 0
for lg in LANGS:
    p = os.path.join(ROOT, "localization", lg, "zz_eu5_politics_l_%s.yml" % lg)
    if not os.path.exists(p):
        print("  !! 缺文件", p)
        continue
    t = rd(p)
    lines = t.split("\r\n")
    keep = []
    hit = 0
    for ln in lines:
        m = re.match(r"^\s*([a-z0-9_]+)\s*:", ln)
        if m and m.group(1) in OLD_KEYS:
            hit += 1
            continue
        keep.append(ln)
    if hit:
        tot += hit
        if WRITE:
            wr(p, "\r\n".join(keep))
    print("[loc] %-12s 删 %d 行" % (lg, hit))
print("[loc] 合计 %d 行" % tot)

# ---------------------------------------------------------------- 4. CSV
rows = list(csv.DictReader(io.open(P_CSV, encoding="utf-8-sig", newline="")))
fields = list(rows[0].keys())
byname = {p[1]: p for p in PAIRS}
# 新名字一律取同 tag 的 county 行，避免手填与县名不一致；CNN 取 d_connaught 的本地化名
county_name = {}
for r in rows:
    if r["kind"] == "county":
        county_name[(r["eu5_tag"], r["ck3_key"])] = (r["ck3_name_en"], r["ck3_name_zh"])
changed = 0
for r in rows:
    if r["kind"] == "country" and r["ck3_key"] in byname:
        tag, old, newkey, newtier, en, zh = byname[r["ck3_key"]]
        if r["eu5_tag"] != tag:
            print("  !! tag 不符", r["eu5_tag"], r["ck3_key"])
            continue
        if newkey.startswith("c_"):
            en2, zh2 = county_name.get((tag, newkey), (en, zh))
        else:
            en2, zh2 = en, zh
        r["ck3_key"] = newkey
        r["ck3_tier"] = newtier
        r["ck3_name_en"] = en2
        r["ck3_name_zh"] = zh2
        r["note"] = (r["note"] + " | rebind to %s (was %s)" % (newkey, old)).strip(" |")
        changed += 1
print("[csv] country 行改挂 %d 条" % changed)
if changed and WRITE:
    tmp = P_CSV + ".tmp_new"
    with io.open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, P_CSV)

# ---------------------------------------------------------------- 5. overrides
t = rd(P_OVR)
have = set()
for ln in t.split("\r\n"):
    parts = ln.split(",")
    if len(parts) >= 3 and parts[0] == "country":
        have.add((parts[1], parts[2]))
add = []
for tag, old, newkey, newtier, en, zh in PAIRS:
    if (tag, "title_key") in have:
        continue
    add.append("country,%s,title_key,%s,改挂到%s %s（原 %s）" % (
        tag, newkey, "伯爵领" if newtier == "c" else "法理公国", newkey, old))
print("[ovr] 追加 %d 行" % len(add))
if add and WRITE:
    body = t.rstrip("\r\n") + "\r\n" + "\r\n".join(add) + "\r\n"
    wr(P_OVR, body)

# ---------------------------------------------------------------- 6. dropped
t = rd(P_DROP)
have = set(x.strip() for x in t.splitlines() if x.strip())
add = [k for k in OLD_KEYS if k not in have]
print("[drop] 追加 %d 个 key" % len(add))
if add and WRITE:
    body = t.rstrip("\r\n") + "\r\n" + "\r\n".join(add) + "\r\n"
    wr(P_DROP, body)

# ---------------------------------------------------------------- 7. 骑士团脚本
t = rd(P_ORDERS)
n1 = t.count("set_primary_title_to = title:d_eu5_kni")
n2 = t.count("title:d_eu5_kni = { set_always_follows_primary_heir = yes }")
print("[orders] set_primary_title_to 命中 %d，always_follows 命中 %d" % (n1, n2))
if n1 or n2:
    nt = t.replace("set_primary_title_to = title:d_eu5_kni",
                   "set_primary_title_to = title:c_rodos")
    nt = nt.replace("title:d_eu5_kni = { set_always_follows_primary_heir = yes }",
                    "title:c_rodos = { set_always_follows_primary_heir = yes }")
    if WRITE:
        wr(P_ORDERS, nt)

print("\n%s" % ("已写入" if WRITE else "DRY RUN，未写任何文件（加 --write 落盘）"))
