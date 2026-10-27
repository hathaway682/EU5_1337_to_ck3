# -*- coding: utf-8 -*-
"""文化分类基础表：我们的文化 × EU5 数据 × 地理 × CK3 原版文化对照。

输出 gen_debug/_culture_classify_base.csv：
culture, name_en, heritage, language, eu5_language, eu5_groups, baronies,
kingdoms, duchies, provinces_top

另输出 gen_debug/_ck3_vanilla_cultures.csv：
culture, name_en, heritage, language
"""
import io, os, re, csv, collections

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game\in_game"
CK3 = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"

CULT = os.path.join(MOD, "common", "culture", "cultures", "00_generated_cultures.txt")
LT = os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt")
PROV = os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt")
LOC = os.path.join(MOD, "localization", "english", "gen_cultures_l_english.yml")
OUT_BASE = os.path.join(MOD, "gen_debug", "_culture_classify_base.csv")
OUT_VAN = os.path.join(MOD, "gen_debug", "_ck3_vanilla_cultures.csv")

DEF = re.compile(r"(?ms)^\t?([a-z0-9_]+)\s*=\s*\{")


def rd(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


def top_keys(text):
    out, i, n = {}, 0, len(text)
    while i < n:
        m = DEF.search(text, i)
        if not m:
            break
        j, d = m.end(), 1
        while j < n and d:
            if text[j] == "{":
                d += 1
            elif text[j] == "}":
                d -= 1
            j += 1
        out[m.group(1)] = text[m.end():j - 1]
        i = j
    return out


def f(b, k):
    m = re.search(r"(?m)^\s*" + k + r"\s*=\s*([a-z0-9_]+)", b)
    return m.group(1) if m else ""


# ---------- 1. 我们的文化 ----------
ours = top_keys(rd(CULT))
print("我们的文化: %d" % len(ours))

# 本地化显示名
names = {}
for line in rd(LOC).split("\n"):
    m = re.match(r'^\s*([a-z0-9_]+):\d*\s*"([^"]*)"\s*$', line)
    if m and not m.group(1).endswith(("_name", "_prefix", "_male", "_female",
                                      "_collective_noun", "_noun")):
        names.setdefault(m.group(1), m.group(2))

# ---------- 2. EU5 语言 / 文化组 ----------
eu5_lang, eu5_grp = {}, {}
cd = os.path.join(EU5, "common", "cultures")
for fn in sorted(os.listdir(cd)):
    if not fn.endswith(".txt"):
        continue
    for k, b in top_keys(rd(os.path.join(cd, fn))).items():
        lg = f(b, "language")
        if lg:
            eu5_lang[k] = lg
        g = re.search(r"(?ms)^\s*culture_groups\s*=\s*\{(.*?)\}", b)
        if g:
            eu5_grp[k] = g.group(1).split()

# ---------- 3. 地理：province -> culture，barony -> province -> 王国/公国 ----------
pt = rd(PROV)
pc = {}
for m in re.finditer(r"(?m)^(\d+)\s*=\s*\{", pt):
    k, dd = m.end(), 1
    while k < len(pt) and dd:
        if pt[k] == "{":
            dd += 1
        elif pt[k] == "}":
            dd -= 1
        k += 1
    mc = re.search(r"(?m)^\s*culture\s*=\s*([a-z0-9_]+)", pt[m.end():k - 1])
    pc.setdefault(m.group(1), mc.group(1) if mc else "")

t = rd(LT)
tok = re.compile(r"([a-z0-9_]+)\s*=\s*\{|\{|\}")
stack, rec = [], {}
for m in tok.finditer(t):
    s = m.group(0)
    if s == "}":
        if stack:
            stack.pop()
        continue
    if s == "{":
        stack.append("?")
        continue
    key = m.group(1)
    stack.append(key)
    if key.startswith("b_"):
        mp = re.search(r"\bprovince\s*=\s*(\d+)", t[m.end():m.end() + 400])
        if mp:
            d = next((x for x in reversed(stack[:-1]) if x.startswith("d_")), "")
            kk = next((x for x in reversed(stack[:-1]) if x.startswith("k_")), "")
            rec.setdefault(mp.group(1), (key[2:], d[2:], kk[2:]))

geo = collections.defaultdict(lambda: {"n": 0, "k": collections.Counter(),
                                       "d": collections.Counter(), "p": []})
for pid, cult in pc.items():
    if not cult:
        continue
    g = geo[cult]
    g["n"] += 1
    b, d, k = rec.get(pid, ("?", "?", "?"))
    g["k"][k] += 1
    g["d"][d] += 1
    if len(g["p"]) < 8:
        g["p"].append(b)

# ---------- 4. 输出 ----------
rows = []
for c in sorted(ours):
    g = geo.get(c, {"n": 0, "k": collections.Counter(), "d": collections.Counter(), "p": []})
    rows.append({
        "culture": c,
        "name_en": names.get(c, ""),
        "heritage": f(ours[c], "heritage"),
        "language": f(ours[c], "language"),
        "eu5_language": eu5_lang.get(c, ""),
        "eu5_groups": ";".join(eu5_grp.get(c, [])),
        "baronies": g["n"],
        "kingdoms": ";".join("%s:%d" % kv for kv in g["k"].most_common(3)),
        "duchies": ";".join("%s:%d" % kv for kv in g["d"].most_common(3)),
        "provinces": ";".join(g["p"]),
    })
with io.open(OUT_BASE, "w", encoding="utf-8-sig", newline="") as fp:
    w = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print("写出 %s (%d 行)" % (OUT_BASE, len(rows)))

# CK3 原版
vrows = []
vd = os.path.join(CK3, "common", "culture", "cultures")
vnames = {}
for fn in sorted(os.listdir(os.path.join(CK3, "localization", "english"))):
    if fn.endswith("_l_english.yml"):
        for line in rd(os.path.join(CK3, "localization", "english", fn)).split("\n"):
            m = re.match(r'^\s*([a-z0-9_]+):\d*\s*"([^"]*)"\s*$', line)
            if m:
                vnames.setdefault(m.group(1), m.group(2))
for fn in sorted(os.listdir(vd)):
    if not fn.endswith(".txt"):
        continue
    for k, b in top_keys(rd(os.path.join(vd, fn))).items():
        if not f(b, "heritage"):
            continue
        vrows.append({"culture": k, "name_en": vnames.get(k, ""),
                      "heritage": f(b, "heritage"), "language": f(b, "language")})
with io.open(OUT_VAN, "w", encoding="utf-8-sig", newline="") as fp:
    w = csv.DictWriter(fp, fieldnames=["culture", "name_en", "heritage", "language"])
    w.writeheader()
    w.writerows(vrows)
print("CK3 原版文化: %d -> %s" % (len(vrows), OUT_VAN))
