# -*- coding: utf-8 -*-
"""找出 CK3 faith 与 EU5 religion 里「本地化值一样或极其接近」的配对。

两边数据：
  CK3  faith    E:/.../CK3/game/common/religion/faith_types/00_faith_types.txt
      中文     localization/simp_chinese/religion/*.yml   （key = faith / faith_adj / faith_adherent）
      英文     localization/english/religion/*.yml
  EU5  religion D:/.../EU5/game/in_game/common/religions/*.txt
      中文     main_menu/localization/simp_chinese/religion_l_simp_chinese.yml （key = religion / religion_ADJ）
      英文     main_menu/localization/english/religion_l_english.yml

输出：
  _same_name_religions.csv   （ck3 / ck3_zh / eu5 / eu5_zh / 关系 / 相似度 / 是否在 mod 内）
  console 摘要
"""
import io, os, re, csv, glob, sys, difflib

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
CK3 = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"
OUT = os.path.join(MOD, "gen_debug", "_same_name_religions.csv")

RE_KEY = re.compile(r"^([a-z][a-z0-9_]*)\s*=\s*\{")
RE_LOC = re.compile(r'^\s*([A-Za-z0-9_.\-]+):\s*"((?:[^"\\]|\\.)*)"\s*(?:#.*)?$')


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


def keys_of(path):
    out = []
    for line in read(path).split("\n"):
        m = RE_KEY.match(line)
        if m:
            out.append(m.group(1))
    return out


def load_yml(path):
    d = {}
    if not os.path.exists(path):
        return d
    for line in io.open(path, encoding="utf-8-sig", errors="ignore"):
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


# ---------- 键 ----------
ck3_faiths = keys_of(os.path.join(CK3, "common", "religion", "faith_types", "00_faith_types.txt"))
eu5_religs = []
for p in glob.glob(os.path.join(EU5, "in_game", "common", "religions", "*.txt")):
    eu5_religs += keys_of(p)
ck3_faiths = sorted(set(ck3_faiths))
eu5_religs = sorted(set(eu5_religs))
print("CK3 faith %d / EU5 religion %d" % (len(ck3_faiths), len(eu5_religs)))

# ---------- 本地化 ----------
ck3_zh = load_dir(os.path.join(CK3, "localization", "simp_chinese", "religion", "*.yml"))
ck3_en = load_dir(os.path.join(CK3, "localization", "english", "religion", "*.yml"))
eu5_zh = load_yml(os.path.join(EU5, "main_menu", "localization", "simp_chinese",
                               "religion_l_simp_chinese.yml"))
eu5_en = load_yml(os.path.join(EU5, "main_menu", "localization", "english",
                               "religion_l_english.yml"))


def pick(d, *names):
    for n in names:
        if n in d and d[n] and not d[n].startswith("$"):
            return d[n]
    return ""


def ck3_zh_of(f):
    return pick(ck3_zh, f, f + "_adherent", f + "_adj")


def ck3_en_of(f):
    return pick(ck3_en, f, f + "_adherent", f + "_adj")


def eu5_zh_of(r):
    return pick(eu5_zh, r, r + "_ADJ", r + "_adj")


def eu5_en_of(r):
    return pick(eu5_en, r, r + "_ADJ", r + "_adj")


# ---------- 归一化 ----------
STRIP = set("派教宗门语人的之地·・‐‑–—－()（）「」『』 ")
# 先去掉多字后缀，再去单字，否则「博里泛灵论」和「博里教」对不上
STRIP_MULTI = ("泛灵论", "崇拜", "信仰")


def norm_zh(s):
    s = s or ""
    for w in STRIP_MULTI:
        s = s.replace(w, "")
    return "".join(ch for ch in s if ch not in STRIP).lower()


def norm_en(s):
    return re.sub(r"[^a-z]", "", (s or "").lower())


# mod 里实际用到的 faith
used = set()
prov = os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt")
if os.path.exists(prov):
    used = set(re.findall(r"(?m)^\s*faith\s*=\s*([a-z0-9_]+)", read(prov)))

# ---------- 比对 ----------
rows = []
for f in ck3_faiths:
    fz, fe = ck3_zh_of(f), ck3_en_of(f)
    nfz, nfe = norm_zh(fz), norm_en(fe)
    if not nfz and not nfe:
        continue
    for r in eu5_religs:
        rz, re_ = eu5_zh_of(r), eu5_en_of(r)
        nrz, nre = norm_zh(rz), norm_en(re_)
        if not nrz and not nre:
            continue

        why, ratio = [], 0.0
        if nfz and nfz == nrz:
            why.append("中文完全相同")
        if nfe and nfe == nre:
            why.append("英文完全相同")
        if nfz and nrz:
            ratio = difflib.SequenceMatcher(None, nfz, nrz).ratio()
            if nfz != nrz and ratio >= 0.75:
                why.append("中文极接近")
        if nfe and nre and nfe != nre and min(len(nfe), len(nre)) >= 5 and nfe[0] == nre[0]:
            er = difflib.SequenceMatcher(None, nfe, nre).ratio()
            if er >= 0.90:
                why.append("英文极接近")
                ratio = max(ratio, er)
        if not why:
            continue
        rows.append({
            "ck3": f, "ck3_zh": fz, "ck3_en": fe,
            "eu5": r, "eu5_zh": rz, "eu5_en": re_,
            "关系": "+".join(why),
            "键关系": "同名" if f == r else "异名",
            "相似度": round(ratio, 2),
            "ck3在mod内": "是" if f in used else "",
        })

rows.sort(key=lambda x: (-x["相似度"], x["ck3"], x["eu5"]))

# 同一个 CK3 faith 若已有「中文完全相同」的对手，其余近似配对多半是假朋友
# （例：博里教 真身是 bori_religion 博里泛灵论，而 ebore/mbori 是另两个宗教）
by_ck3 = {}
for x in rows:
    by_ck3.setdefault(x["ck3"], []).append(x)
for f, sub in by_ck3.items():
    exact = [x for x in sub if "中文完全相同" in x["关系"]]
    if exact:
        for x in sub:
            x["备注"] = "最佳" if "中文完全相同" in x["关系"] else "疑似假朋友（同信仰已有同名匹配）"
    else:
        top = max(sub, key=lambda x: x["相似度"])
        for x in sub:
            x["备注"] = "最佳（近似）" if x is top else "次优"

with io.open(OUT, "w", encoding="utf-8-sig", newline="") as fp:
    w = csv.DictWriter(fp, fieldnames=["ck3", "ck3_zh", "ck3_en", "eu5", "eu5_zh", "eu5_en",
                                       "关系", "键关系", "相似度", "备注", "ck3在mod内"],
                       lineterminator="\n")
    w.writeheader()
    w.writerows(rows)

print("命中 %d 对，写出 %s" % (len(rows), OUT))

# ---------- 同名直接对应表 ----------
# 只收「中文完全相同」的配对；3 个假朋友不进这张表。
# aluk 是用户点名补进来的：键干相同、明显同一宗教（托拉查 Aluk To Dolo），
# 只是中文一个译「阿卢克」一个译「阿鲁克」，不算同名，故显式追加。
# satsana_phi 是用户点名补进来的（2026-10-21）：**键完全相同**，但中文译名不同
# （EU5「丕教」/ CK3「守护灵教」），自动比对收不到，故显式追加。
MAP = os.path.join(MOD, "gen_debug", "_same_name_religion_map.csv")
EXTRA = [
    {"eu5_religion": "aluk_religion", "eu5_zh": "阿鲁克古道",
     "ck3_faith": "aluk", "ck3_zh": "阿卢克古道",
     "依据": "键干相同 + 译字不一致（卢/鲁）", "字面同名": "",
     "ck3在mod内": "是" if "aluk" in used else ""},
    {"eu5_religion": "satsana_phi", "eu5_zh": "丕教",
     "ck3_faith": "satsana_phi", "ck3_zh": "守护灵教",
     "依据": "键完全相同 + 译名不同（丕教/守护灵教）", "字面同名": "",
     "ck3在mod内": "是" if "satsana_phi" in used else ""},
]
mp = [x for x in rows if "中文完全相同" in x["关系"]]
mp.sort(key=lambda x: (x["键关系"] != "同名", x["eu5"]))
mp = [{"eu5_religion": x["eu5"], "eu5_zh": x["eu5_zh"], "ck3_faith": x["ck3"],
       "ck3_zh": x["ck3_zh"], "键关系": x["键关系"], "ck3在mod内": x["ck3在mod内"]} for x in mp]
mp += EXTRA
with io.open(MAP, "w", encoding="utf-8-sig", newline="") as fp:
    w = csv.DictWriter(fp, fieldnames=["eu5_religion", "eu5_zh", "ck3_faith", "ck3_zh",
                                       "依据", "字面同名", "ck3在mod内"], lineterminator="\n")
    w.writeheader()
    for x in mp:
        if x.get("依据"):
            w.writerow(x)
            continue
        lit = x["ck3_zh"] == x["eu5_zh"]
        if x["键关系"] == "同名":
            basis = "键同名 + 字面同名" if lit else "键同名 + 去后缀同名"
        else:
            basis = "中文字面同名" if lit else "中文去后缀同名（教/派/信仰/崇拜）"
        w.writerow({"eu5_religion": x["eu5_religion"], "eu5_zh": x["eu5_zh"],
                    "ck3_faith": x["ck3_faith"], "ck3_zh": x["ck3_zh"],
                    "依据": basis, "字面同名": "是" if lit else "",
                    "ck3在mod内": x["ck3在mod内"]})
print("同名直接对应 %d 条，写出 %s" % (len(mp), MAP))
print()
GROUPS = [("A 键同名 · 中文同名（可直接对应）",
           lambda x: x["键关系"] == "同名" and "中文完全相同" in x["关系"]),
          ("B 键异名 · 中文同名（同概念不同拼法，需确认）",
           lambda x: x["键关系"] == "异名" and "中文完全相同" in x["关系"]),
          ("C 中文极接近（差一两个字）",
           lambda x: "中文完全相同" not in x["关系"] and "中文极接近" in x["关系"]),
          ("D 只有英文接近", lambda x: "中文" not in x["关系"])]
shown = set()
for title, pred in GROUPS:
    sub = [x for x in rows if pred(x)]
    if not sub:
        continue
    print("== %s：%d 对 ==" % (title, len(sub)))
    for x in sub:
        print("   %-26s %-12s | %-24s %-12s  %s"
              % (x["ck3"], x["ck3_zh"], x["eu5"], x["eu5_zh"],
                 ("【mod】" if x["ck3在mod内"] else "") + x["备注"]))
    shown |= {id(x) for x in sub}
    print()
rest = [x for x in rows if id(x) not in shown]
if rest:
    print("== 其他：%d 对 ==" % len(rest))
    for x in rest:
        print("   %-26s %-12s | %-24s %-12s %s" % (x["ck3"], x["ck3_zh"], x["eu5"], x["eu5_zh"], x["关系"]))
