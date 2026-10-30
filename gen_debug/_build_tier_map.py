# -*- coding: utf-8 -*-
"""按「伯爵领的最高归属头衔」给每个 province 分类，生成 mapviz spec。

分类：
  帝国·真实头衔 -> 粉   帝国·e_eu5_* -> 紫
  王国·真实头衔 -> 青   王国·k_eu5_* -> 蓝
  公国·真实头衔 -> 黄   公国·d_eu5_* -> 橙
  h_ / k_gen_wilderness / 无高级头衔的独立伯爵 -> 不涂（留底色）
"""
import re, csv, json, collections, os

ROOT = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
TITLES = os.path.join(ROOT, "history", "titles", "zz_eu5_titles.txt")
PROVMAP = os.path.join(ROOT, "gen_debug", "_tier_province_map.csv")
SPEC = os.path.join(ROOT, "gen_debug", "_tier_map_spec.json")
OUT = os.path.join(ROOT, "gen_debug", "eu5_tier_map")

# ---------- 解析头衔历史 ----------
txt = open(TITLES, encoding="utf-8-sig").read()
blocks = {}
lines = txt.splitlines()
cur = None; depth = 0; buf = []
for ln in lines:
    if depth == 0:
        m = re.match(r"^([A-Za-z0-9_.-]+)\s*=\s*\{", ln)
        if m:
            cur = m.group(1); buf = [ln]; depth = 1; continue
    else:
        buf.append(ln); depth += ln.count("{") - ln.count("}")
        if depth == 0:
            blocks[cur] = "\n".join(buf); cur = None

def field(block, name):
    v = re.findall(rf"(?<![a-z_]){name}\s*=\s*([A-Za-z0-9_-]+)", block)
    return v[-1] if v else None

holder, liege = {}, {}
for k, b in blocks.items():
    h = field(b, "holder"); lg = field(b, "liege")
    if h: holder[k] = h
    if lg: liege[k] = lg

rank = {"h": 5, "e": 4, "k": 3, "d": 2, "c": 1, "b": 0}
held = collections.defaultdict(list)
for k, h in holder.items():
    if k[0] in "ekdh":
        held[h].append(k)
top_of = {h: max(ks, key=lambda x: rank[x[0]]) for h, ks in held.items()}

def climb(k):
    seen = set()
    while k in liege and k not in seen:
        seen.add(k); k = liege[k]
    return k

def top_title(c):
    """实际持有者：取 c_ 的 holder 本人持有的最高头衔。"""
    h = holder.get(c)
    return top_of.get(h)

# ---------- 分类 ----------
PINK = "#E86BA8"   # 帝国·真实
PURP = "#7B3FA0"   # 帝国·e_eu5
CYAN = "#1FB6C1"   # 王国·真实
BLUE = "#2B5FD9"   # 王国·k_eu5
YELL = "#E8C22B"   # 公国·真实
ORAN = "#E8791E"   # 公国·d_eu5

GROUPS = [
    ("帝国（原版同名头衔）", PINK),
    ("帝国（e_eu5_* 头衔）", PURP),
    ("王国（原版同名头衔）", CYAN),
    ("王国（k_eu5_* 头衔）", BLUE),
    ("公国（原版同名头衔）", YELL),
    ("公国（d_eu5_* 头衔）", ORAN),
]

# ---------- 只保留 eu5_ck3_title_map.csv 里出现过的头衔 ----------
TITLEMAP = os.path.join(ROOT, "gen_debug", "eu5_ck3_title_map.csv")
allowed = set()
for x in csv.DictReader(open(TITLEMAP, encoding="utf-8-sig")):
    if x["ck3_key"]:
        allowed.add(x["ck3_key"])

def classify(top):
    if not top:
        return None
    if top.startswith("h_"):
        return None
    if top == "k_gen_wilderness":
        return None
    if top not in allowed:
        return None
    tier = top[0]
    if tier not in "ekd":
        return None
    eu5 = "_eu5_" in top
    idx = {"e": 0, "k": 2, "d": 4}[tier] + (1 if eu5 else 0)
    return idx

cat_of_county = {}
skipped = collections.Counter()
for c in blocks:
    if not c.startswith("c_"):
        continue
    t = top_title(c)
    idx = classify(t)
    if idx is None:
        key = t if t else "NONE"
        skipped[key] += 1
        continue
    cat_of_county[c] = idx

# ---------- province 归类 ----------
rows = list(csv.DictReader(open(PROVMAP, encoding="utf-8-sig")))
groups = [[] for _ in GROUPS]
unmapped = 0
for r in rows:
    c = r["county"]
    idx = cat_of_county.get(c)
    if idx is None:
        unmapped += 1
        continue
    groups[idx].append(int(r["province"]))

spec = {
    "mod_root": ROOT,
    "out": OUT,
    "title": "EU5 国家按头衔等级",
    "subtitle": "按伯爵领归属头衔上色（1337.4.1）",
    "layer": "county",
    "groups": [
        {"name": n, "color": col, "provs": groups[i]}
        for i, (n, col) in enumerate(GROUPS)
    ],
    "on_conflict": "first",
    "base": {"unassigned": "#FFFFFF"},
    "color": {"mode": "direct"},
    "legend": {"enabled": True, "unit": "provinces", "show_counts": True},
}
json.dump(spec, open(SPEC, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print("每组 province 数：")
for i, (n, col) in enumerate(GROUPS):
    print(f"  {n:26s} {len(groups[i]):6d}")
print("未涂（无头衔/荒野/中国/无男爵领）:", unmapped)
print("\n被跳过的头衔 Top10：")
for k, v in skipped.most_common(10):
    print(f"  {k:26s} {v} counties")
print("\nspec ->", SPEC)
