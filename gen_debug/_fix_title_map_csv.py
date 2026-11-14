# -*- coding: utf-8 -*-
"""把 gen_debug/eu5_ck3_title_map.csv 的两列纠正为「真值」。

一、eu5_tier：改用 EU5 原始 country_rank（main_menu/setup/1337/10_countries.txt）。
    EU5 里没有 country_rank 的国家默认就是伯国（用户 2026-11-13 明确），
    所以缺字段写 c，而不是当前 CSV 里的 `-`。

二、ck3_key / ck3_tier / ck3_holder / ck3_liege / ck3_government / ck3_declared：
    按 history/titles 里 1337.4.1 真正生效的持有重算。

    关键：`eu5_politics.json` 的 `counties[].owner` 是 EU5 导出的原值，本 mod 后续
    手工改绑（c_elbmarch 归 HAM、c_wesermarch 归 BRM、c_hanover 归 BRU …）它并不知道。
    所以「这块地是不是我的」以 history 的 holder 为准，不以 owner 为准。

    候选集 = 本国自己的头衔：
      · e_eu5_tag / k_eu5_tag / d_eu5_tag（PAP 用 k_papal_state）
      · _title_overrides.csv 的 title_key
      · _grant_landed_duchies.compute() 里指向本国的公国、以及同名公国
      · EU5 owner 是本国、或首都所在、或 history 持有者是本国 ruler 的伯爵领
      · EU5 tag 是本国、或 b_<首都> 的男爵领
    候选里只保留「history holder == 本国 ruler」的；旧值仍在其中就原样保留（不折腾），
    否则按 e>k>d>c>b 取最高一级。

用法：python gen_debug/_fix_title_map_csv.py [--mod .] [--write]
不带 --write 只试算并打印统计，不写盘。
"""
import argparse
import csv
import io
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATE = (1337, 4, 1)
EU5_GAME = (r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V"
            r"\game\main_menu\setup\1337")
RANK = {"rank_county": "c", "rank_duchy": "d", "rank_kingdom": "k", "rank_empire": "e"}
TIER = {"e": 4, "k": 3, "d": 2, "c": 1, "b": 0}
# 这些不是「有人持有」，只是转换留下的占位
PLACEHOLDER = {"0", "gen_wilderness_holder", "gen_wilderness"}
# 身份型候选：定义上就是「这个国家的头衔」，不受持有者是谁影响
IDENTITY = {"own-e", "own-k", "own-d", "papal", "override", "grant", "same-name"}
COLS = ["kind", "eu5_tag", "eu5_tier", "eu5_country_en", "eu5_country_zh",
        "eu5_place_en", "eu5_place_zh", "ck3_key", "ck3_tier", "ck3_name_en",
        "ck3_name_zh", "eu5_holder", "ck3_holder", "ck3_liege", "ck3_government",
        "ck3_declared", "note"]


# 同级优先：override > 生成等级头衔 > 授公国 > 同名公国/首都所在县 > 首都在别县/本国伯爵领 >
#           人工主头衔 > 其他本国伯爵领/同名县 > 男爵领
PREF = {"override": 9, "own-e": 8, "own-k": 8, "own-d": 8, "papal": 8,
        "grant": 7, "same-name": 6, "county-of-capital": 6,
        "capital-elsewhere": 5, "county-owner": 5, "county-held": 4,
        "primary": 4, "county-owner-other": 4, "county-name": 3,
        "barony-of-capital": 2, "barony-tag": 2}


def yml(path):
    """key -> text，Paradox 本地化文件。"""
    out = {}
    if not os.path.exists(path):
        return out
    for line in io.open(path, encoding="utf-8-sig", errors="ignore"):
        m = re.match(r'^\s*([A-Za-z0-9_.]+):\d*\s*"(.*)"', line.rstrip("\n"))
        if m:
            out.setdefault(m.group(1), m.group(2))
    return out


CK3_LOC = (r"D:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III Beta"
           r"\game\localization")


def ck3_strings(mod, lang):
    """头衔 key -> 本地化名。原版 titles 打底，再按文件名顺序叠本 mod 全部本地化。"""
    out = yml(os.path.join(CK3_LOC, lang, "titles_l_%s.yml" % lang))
    d = os.path.join(mod, "localization", lang)
    if os.path.isdir(d):
        for n in sorted(os.listdir(d)):
            if n.endswith(".yml"):
                out.update(yml(os.path.join(d, n)))
    return out


# note 里描述「这块地是什么」的短语，key 一变就必须跟着换
LAND_RE = re.compile(r"country-below-county-rank: its land is (?:its counties|a barony|nothing)")
DROP_FLAGS = ("primary-title", "union-junior: seat not recorded yet")


def land_phrase(key):
    if not key:
        return "country-below-county-rank: its land is nothing"
    t = key.split("_")[0]
    if t == "b":
        return "country-below-county-rank: its land is a barony"
    if t == "c":
        return "country-below-county-rank: its land is its counties"
    return ""


def renote(note, key, source):
    parts = [p.strip() for p in note.split(",") if p.strip()]
    out = []
    for p in parts:
        if LAND_RE.fullmatch(p):
            continue
        if p in DROP_FLAGS:
            continue
        if p.startswith("rank-title-dropped"):
            continue
        out.append(p)
    if source == "japan-clan" and "japan-noble-family" not in out:
        out.append("japan-noble-family")
    ph = land_phrase(key)
    if ph and ph not in out:
        out.append(ph)
    return ",".join(out)


def read(path):
    return io.open(path, encoding="utf-8-sig", errors="ignore").read().lstrip("\ufeff")


def as_tuple(d):
    try:
        return tuple(int(x) for x in d.split("."))
    except ValueError:
        return (0, 0, 0)


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


# ---------------------------------------------------------------- EU5 原始等级
def orig_ranks():
    """tag -> e/k/d/c。缺 country_rank 一律 c（EU5 里 None 就是伯国）。"""
    text = read(os.path.join(EU5_GAME, "10_countries.txt"))
    out = {}
    for m in re.finditer(r"(?ms)^\t([A-Z][A-Z0-9]{2}) = \{[^\n]*\n(.*?)^\t\}", text):
        r = re.search(r"country_rank\s*=\s*(\w+)", m.group(2))
        out[m.group(1)] = RANK.get(r.group(1), "c") if r else "c"
    return out


# ---------------------------------------------------------------- CK3 实际持有
def parse_titles(text):
    """key -> {holder, liege, government}，取 1337.4.1 及之前最后一个 holder。"""
    out = {}
    for m in re.finditer(r"(?ms)^([A-Za-z0-9_-]+) = \{\n(.*?)^\}\n?", text):
        key, body = m.group(1), m.group(2)
        holder, date = None, None
        for e in re.finditer(r"(?ms)^\t(\d+\.\d+\.\d+) = \{\n(.*?)^\t\}", body):
            d = as_tuple(e.group(1))
            if d > DATE:
                continue
            h = re.search(r"(?m)^\t\tholder = ([A-Za-z0-9_]+)$", e.group(2))
            if h and (date is None or d >= date):
                holder, date = h.group(1), d
        liege = re.findall(r"(?m)^\t\tliege = ([A-Za-z0-9_-]+)$", body)
        gov = re.findall(r"(?m)^\t\tgovernment = ([a-z_]+)$", body)
        out[key] = {"holder": holder or "",
                    "liege": liege[-1] if liege else "",
                    "government": gov[-1] if gov else ""}
    return out


def load_titles(mod):
    """history/titles 全部 *.txt 合并；zz_eu5_titles.txt 最后加载（它覆盖别人）。"""
    root = os.path.join(mod, "history", "titles")
    files = []
    for dirpath, _dirnames, names in os.walk(root):
        for n in names:
            if not n.endswith(".txt"):
                continue
            p = os.path.join(dirpath, n)
            rel = os.path.relpath(p, root).replace("\\", "/")
            files.append((0 if rel == "zz_eu5_titles.txt" else 1, rel, p))
    files.sort()
    titles = {}
    for _o, _rel, p in files:
        titles.update(parse_titles(read(p)))
    return titles


def load_declared(mod):
    out = set()
    d = os.path.join(mod, "common", "landed_titles")
    for n in os.listdir(d):
        if n.endswith(".txt"):
            out |= set(re.findall(r"(?m)^\s*([A-Za-z0-9_-]+) = \{",
                                  read(os.path.join(d, n))))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mod", default=os.path.abspath(os.path.join(HERE, "..")))
    ap.add_argument("--export", default=r"D:/Documents/Paradox Interactive/Crusader Kings III"
                                        r"/mod/Global_modern_map/eu5_export")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--why", default="", help="逗号分隔的 tag，打印它们的候选排序与最终归属")
    args = ap.parse_args()
    mod = args.mod

    pol = json.load(io.open(os.path.join(args.export, "eu5_politics.json"), encoding="utf-8"))
    countries, counties, baronies = pol["countries"], pol["counties"], pol["baronies"]
    characters = pol["characters"]
    orig = orig_ranks()
    titles = load_titles(mod)
    declared = load_declared(mod)

    mapping = json.load(io.open(os.path.join(args.export, "mapping.json"), encoding="utf-8"))
    loc_county = {l["name"]: "c_" + l["county"] for l in mapping["locations"] if l.get("county")}

    # 公国 -> tag（同名 / k-e 控制过半），抄 _grant_landed_duchies.compute()
    sys.path.insert(0, os.path.join(mod, "gen_debug", "_rebuild_export"))
    import importlib
    gld = importlib.import_module("_grant_landed_duchies")
    grants, gwhy, _blocked, _c = gld.compute(mod, args.export)
    duchy_of = defaultdict(list)
    for d, tag in grants.items():
        duchy_of[tag].append(d)

    # 主头衔：开局 set_primary_title_to 指定的那个县
    primary = {}
    pp = os.path.join(mod, "common", "on_action", "zz_eu5_primary_titles.txt")
    if os.path.exists(pp):
        for m in re.finditer(r"character:(\w+) = \{.*?set_primary_title_to = title:(\w+)",
                             read(pp), re.S):
            primary[m.group(1)] = m.group(2)

    # 日本：国家即武家
    clan, clan_of_dynasty = {}, {}
    for key, t in titles.items():
        if key.startswith("c_nf_") and t.get("holder"):
            clan[t["holder"]] = key
            dyn = (characters.get(t["holder"]) or {}).get("dynasty")
            if dyn:
                clan_of_dynasty.setdefault(dyn, []).append(key)
    clan_of_dynasty = {d: v[0] for d, v in clan_of_dynasty.items() if len(v) == 1}

    # 转换时判定丢掉的等级头衔，不能再当有效键
    dropped = set()
    dp = os.path.join(mod, "gen_debug", "eu5_titles_dropped.txt")
    if os.path.exists(dp):
        dropped = set(read(dp).split())

    overrides = {}
    ov_path = os.path.join(mod, "gen_debug", "_title_overrides.csv")
    for r in csv.DictReader(io.open(ov_path, encoding="utf-8-sig", newline="")):
        if r["scope"] == "country" and r["field"] == "title_key":
            overrides[r["key"]] = r["value"]

    NAME = {lang: ck3_strings(mod, lang) for lang in ("english", "simp_chinese")}

    # 反向索引：holder -> 头衔，用于「history 持有者是本国 ruler 的伯爵领」
    held_by = defaultdict(set)
    for k, t in titles.items():
        if t.get("holder"):
            held_by[t["holder"]].add(k)

    def candidates(tag, ruler):
        """本国自己的头衔候选：key -> 来源标签（同一键取更强的来源）。"""
        c = countries[tag]
        out = {}

        def put(k, s):
            if k not in out or PREF.get(s, 0) > PREF.get(out[k], 0):
                out[k] = s

        for t in ("e", "k", "d"):
            k = "%s_eu5_%s" % (t, tag.lower())
            if k in declared and k not in dropped:
                put(k, "own-" + t)
        if tag == "PAP" and "k_papal_state" in declared:
            put("k_papal_state", "papal")
        if tag in overrides:
            put(overrides[tag], "override")
        for d in duchy_of.get(tag, []):
            put(d, "grant")
        dn = norm(c.get("name_en"))
        if dn:
            for k in titles:
                if k[0] in "dk" and norm(k[2:]) == dn:
                    put(k, "same-name")
            for k in counties:
                if norm(k[2:]) == dn:
                    put(k, "county-name")
        cap = c.get("capital") or ""
        cap_county = loc_county.get(cap) if cap else None
        owned = sorted(k for k, v in counties.items() if v.get("owner") == tag)
        # 座席县：首都所在县（本国拥有时），否则本国第一个县 —— 与 _export_title_map.py 的 seat 一致
        if owned:
            seat_c = cap_county if cap_county in owned else owned[0]
            put(seat_c, "county-of-capital" if seat_c == cap_county else "county-owner")
            for k in owned:
                put(k, "county-owner-other")
        if cap_county:
            put(cap_county, "capital-elsewhere")
        if cap:
            kb = "b_" + cap
            if kb in declared:
                put(kb, "barony-of-capital")
        for k, v in baronies.items():
            if v.get("tag") == tag:
                put(k, "barony-tag")
        # 人工主头衔：生成器的条件是「那个县是本国的」，这里照抄
        prim = primary.get(ruler) or ""
        if prim.startswith("c_") and (counties.get(prim) or {}).get("owner") == tag:
            put(prim, "primary")
        # history 里由本国 ruler 持有、且 EU5 owner 也是本国（补 politics 旧值的缺口）
        if ruler:
            for k in held_by.get(ruler, ()):
                if k.startswith("c_") and (counties.get(k) or {}).get("owner") == tag:
                    put(k, "county-held")
        return out

    # 同级优先见模块级 PREF
    def ranked(tag, old_key):
        """按优先级排好的候选 [(key, 来源)]；kept=True 表示旧值仍然成立。"""
        c = countries[tag]
        ruler = c.get("ruler") or c.get("regent") or ""
        if tag in overrides:
            return [(overrides[tag], "override")], False
        if ruler.startswith("jap_") and tag not in ("JAP", "NTC", "STC"):
            k = (clan.get(ruler)
                 or clan_of_dynasty.get((characters.get(ruler) or {}).get("dynasty")) or "")
            return ([(k, "japan-clan")] if k else []), False
        cand = candidates(tag, ruler)
        # 身份型候选（本国生成头衔 / 人工裁决 / 授公国 / 同名）本身就是「本国的头衔」，
        # 即便被联统宗主戴着也照记（ck3_holder 列会显示成宗主，正是这张表要暴露的东西）。
        # 地面型候选（首都所在县、owner、男爵领）才需要排除「被别的真实角色持有」。
        # ruler 为空时无从比较，不做过滤。
        def other(k):
            if not ruler or cand[k] in IDENTITY:
                return False
            h = (titles.get(k) or {}).get("holder") or ""
            return bool(h) and h not in PLACEHOLDER and h != ruler
        ok = {k: s for k, s in cand.items() if not other(k)}
        # 先按层级，再按「旧值仍成立」，最后按来源强度 —— 旧值不能压过更高的层级，
        # 否则勃兰登堡这种「实际已升公国、表里还写着伯爵领」的永远纠正不过来。
        order = sorted(ok, key=lambda k: (-TIER.get(k.split("_")[0], -1),
                                          0 if k == old_key else 1,
                                          -PREF.get(ok[k], 0), k))
        kept = old_key in ok
        return [(k, ok[k]) for k in order], kept

    # ---------------------------------------------------------------- 读旧表
    path = os.path.join(mod, "gen_debug", "eu5_ck3_title_map.csv")
    raw = io.open(path, encoding="utf-8-sig", newline="").read()
    rows = list(csv.DictReader(io.StringIO(raw)))
    n_country = sum(1 for r in rows if r["kind"] == "country")
    old_tier = Counter(r["eu5_tier"] for r in rows if r["kind"] == "country")
    missing_rank = sum(1 for r in rows if r["kind"] == "country" and r["eu5_tag"] not in orig)

    plans = {}
    for r in rows:
        if r["kind"] == "country":
            plans[r["eu5_tag"]] = ranked(r["eu5_tag"], r["ck3_key"])

    # 一个头衔只能归一个国家：按「是否真的持有 > 候选强度」排序贪心占位，抢不到就顺延
    def strength(tag):
        lst, kept = plans[tag]
        if not lst:
            return (0, 0, 0, 0)
        k, s = lst[0]
        c = countries[tag]
        ruler = c.get("ruler") or c.get("regent") or ""
        held = 1 if ruler and (titles.get(k) or {}).get("holder") == ruler else 0
        return (held, PREF.get(s, 0), TIER.get(k.split("_")[0], -1), 1 if kept else 0)

    assigned, used = {}, {}
    for tag in sorted(plans, key=lambda t: (-strength(t)[0], -strength(t)[1],
                                            -strength(t)[2], -strength(t)[3], t)):
        for k, s in plans[tag][0]:
            if k not in used:
                assigned[tag] = (k, s)
                used[k] = tag
                break
        else:
            assigned[tag] = ("", "none")

    changed_tier = changed_key = 0
    tier_diff = Counter()
    why_cnt = Counter()
    old_ck3 = Counter()
    samples, downgrades, dup = [], [], []
    for r in rows:
        if r["kind"] != "country":
            continue
        tag = r["eu5_tag"]
        nt = orig.get(tag) or "c"
        if r["eu5_tier"] != nt:
            changed_tier += 1
            tier_diff[(r["eu5_tier"], nt)] += 1
        r["eu5_tier"] = nt
        k, w = assigned[tag]
        old_k = r["ck3_key"]
        old_ck3[r["ck3_tier"] or "(空)"] += 1
        why_cnt[w.split("(")[0]] += 1
        if r["ck3_key"] != k:
            changed_key += 1
            o, n = r["ck3_key"], k
            if TIER.get(o.split("_")[0] if o else "", -1) > TIER.get(n.split("_")[0] if n else "", -1):
                downgrades.append((tag, r["eu5_country_en"], o, n, w))
            elif len(samples) < 30:
                samples.append((tag, r["eu5_country_en"], o, n, w))
        r["ck3_key"] = k
        r["ck3_tier"] = k.split("_")[0] if k else ""
        # 名字跟着 key 走；键没变且本地化查不到时保留原值（教权 d_et_* 的名字在别的文件里）
        if k:
            en = NAME["english"].get(k, "")
            zh = NAME["simp_chinese"].get(k, "")
            if k != old_k:
                r["ck3_name_en"], r["ck3_name_zh"] = en, zh
            else:
                r["ck3_name_en"] = en or r["ck3_name_en"]
                r["ck3_name_zh"] = zh or r["ck3_name_zh"]
        else:
            r["ck3_name_en"] = r["ck3_name_zh"] = ""
        t = titles.get(k) or {}
        r["ck3_holder"] = t.get("holder") or ""
        r["ck3_liege"] = t.get("liege") or ""
        r["ck3_government"] = t.get("government") or ""
        r["ck3_declared"] = "yes" if k and k in declared else ("no" if k else "")
        r["note"] = renote(r["note"], k, w)

    print("rows total: %d, country rows: %d (旧 %d)" % (len(rows), n_country, n_country))
    print("10_countries.txt 里查不到原始等级的国家: %d" % missing_rank)
    print("eu5_tier 旧分布: %s" % dict(old_tier))
    print("eu5_tier 新分布: %s" % dict(Counter(r["eu5_tier"] for r in rows
                                               if r["kind"] == "country")))
    print("eu5_tier 改动: %d" % changed_tier)
    print("ck3_key  改动: %d（其中降级 %d）" % (changed_key, len(downgrades)))
    print("ck3_tier 旧分布: %s" % dict(old_ck3))
    print("ck3_tier 新分布: %s" % dict(Counter(r["ck3_tier"] or "(空)" for r in rows
                                               if r["kind"] == "country")))
    print("ck3_key 重复: %d 个键被多国占用" %
          sum(1 for k, v in Counter(k for k, _ in assigned.values() if k).items() if v > 1))
    print("\n取键依据:")
    for k, v in why_cnt.most_common():
        print("  %-28s %d" % (k, v))
    print("\neu5_tier 变动:")
    for (a, b), n in tier_diff.most_common(12):
        print("  %-3s -> %-3s  %d" % (a or "''", b, n))
    print("\n【降级】%d 条:" % len(downgrades))
    for tag, name, a, b, w in downgrades[:60]:
        print("  %-4s %-24s %-24s -> %-24s [%s]" % (tag, (name or "")[:24], a, b, w))
    print("\n【其他改动】:")
    for tag, name, a, b, w in samples:
        print("  %-4s %-24s %-24s -> %-24s [%s]" % (tag, (name or "")[:24], a, b, w))
    print("\nck3_key 落空（无键）: %d" %
          sum(1 for r in rows if r["kind"] == "country" and not r["ck3_key"]))
    print("ck3_key 未声明: %d" %
          sum(1 for r in rows if r["kind"] == "country" and r["ck3_declared"] == "no"))
    print("ck3_key 有键但英文名为空: %d" %
          sum(1 for r in rows if r["kind"] == "country" and r["ck3_key"]
              and not r["ck3_name_en"]))
    print("ck3_key 有键但中文名为空: %d" %
          sum(1 for r in rows if r["kind"] == "country" and r["ck3_key"]
              and not r["ck3_name_zh"]))

    # 审计：拿到男爵领 / 落空、但在 EU5 里其实有县的国家
    odd = []
    for r in rows:
        if r["kind"] != "country":
            continue
        if r["ck3_tier"] not in ("b", ""):
            continue
        own = [k for k, v in counties.items() if v.get("owner") == r["eu5_tag"]]
        if own:
            odd.append((r["eu5_tag"], r["eu5_country_en"], r["ck3_key"], own[:3],
                        (titles.get(own[0]) or {}).get("holder", "")))
    print("\n【有县却拿男爵/落空】%d 条（前 20）:" % len(odd))
    for tag, name, key, own, h in odd[:20]:
        print("  %-4s %-22s -> %-22s own=%s holder(%s)=%s"
              % (tag, (name or "")[:22], key, own, own[0], h))

    # 被别国抢走首选键的情况
    stolen = []
    for tag, (k, s) in assigned.items():
        lst = plans[tag][0]
        if not lst or not k:
            continue
        if k != lst[0][0]:
            top = lst[0][0]
            stolen.append((tag, countries[tag].get("name_en"), top, lst[0][1],
                           used.get(top, ""), k, s))
    print("\n【首选键被别国占用】%d 条（前 25）:" % len(stolen))
    for tag, name, top, s, by, k, s2 in stolen[:25]:
        print("  %-4s %-20s 想拿 %-22s[%s] 被 %-4s 占了 -> %-22s[%s]"
              % (tag, (name or "")[:20], top, s, by, k, s2))

    if args.why:
        for t in [x.strip() for x in args.why.split(",") if x.strip()]:
            lst, kept = plans.get(t, ([], False))
            c = countries.get(t) or {}
            print("\n[%s] %s ruler=%s cap=%s 最终=%s"
                  % (t, c.get("name_en"), c.get("ruler"), c.get("capital"),
                     assigned.get(t, ("", ""))))
            for k, s in lst[:8]:
                print("    %-26s %-22s holder=%s" % (k, s,
                                                     (titles.get(k) or {}).get("holder", "")))

    if not args.write:
        print("\n[dry-run] 未写盘")
        return

    bak = path + ".bak_fixtier_" + time.strftime("%Y%m%d_%H%M%S")
    with io.open(bak, "w", encoding="utf-8-sig", newline="") as fh:
        fh.write(raw)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLS, lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL)
    w.writeheader()
    for r in rows:
        w.writerow(r)
    with io.open(path, "w", encoding="utf-8-sig", newline="") as fh:
        fh.write(buf.getvalue())
    print("\nwritten -> %s (backup %s)" % (path, os.path.basename(bak)))


if __name__ == "__main__":
    main()
