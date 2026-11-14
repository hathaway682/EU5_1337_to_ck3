# -*- coding: utf-8 -*-
"""从 common/on_action/game_start.txt 提取「特殊建筑 → 男爵领」的真实挂载，再和圣地落点对照。

mod 的特殊建筑不是写在 history/provinces 里，而是在 game_start.txt 用
    title:b_XXX.title_province = { add_special_district = <building>_district }
开局挂上去的。这就是「建筑位置」的唯一真源。

输出 gen_debug/_special_building_vs_holysite.out
"""
import io
import os
import re
import glob

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GS = os.path.join(MOD, "common", "on_action", "game_start.txt")
SRC = os.path.join(MOD, "common", "religion", "holy_site_types", "00_holy_site_types.txt")
OUT = os.path.join(MOD, "gen_debug", "_special_building_vs_holysite.out")


def load_loc(d):
    out = {}
    for fn in glob.glob(os.path.join(d, "**", "*.yml"), recursive=True):
        s = io.open(fn, encoding="utf-8-sig", errors="ignore").read()
        for x in re.finditer(r'(?m)^\s*([A-Za-z0-9_.\-]+):\d*\s*"((?:[^"]|"")*)"', s):
            out.setdefault(x.group(1), x.group(2))
    return out


lm = load_loc(os.path.join(MOD, "localization", "simp_chinese"))
lg = load_loc(r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game\localization\simp_chinese")
zh = lambda k: (lm.get(k) or lg.get(k) or "").strip()

# --- 建筑 -> barony ---
builds = []  # [{bld, bar, ln}]
lines = io.open(GS, "rb").read().decode("utf-8-sig").split("\n")
for i, ln in enumerate(lines, 1):
    for m in re.finditer(r"title:(b_[A-Za-z0-9_\-]+)\.title_province\s*=\s*\{[^}]*?add_special_district(?:_slot)?\s*=\s*([A-Za-z0-9_]+)", ln):
        builds.append({"bld": m.group(2), "bar": m.group(1), "ln": i})
    # 一条语句里可能有多个 special_district = { add_building = xxx }
    for m in re.finditer(r"title:(b_[A-Za-z0-9_\-]+)\.title_province\s*=\s*\{.*?add_building\s*=\s*([A-Za-z0-9_]+)", ln):
        builds.append({"bld": m.group(2), "bar": m.group(1), "ln": i})

# --- barony -> county ---
t = io.open(os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt"),
            encoding="utf-8-sig", errors="ignore").read()
bar2c = {}
cur_c = None
for ln in t.split("\n"):
    s = ln.strip()
    m = re.match(r"^(c_[A-Za-z0-9_]+)\s*=\s*\{", s)
    if m:
        cur_c = m.group(1)
        continue
    m = re.match(r"^(b_[A-Za-z0-9_]+)\s*=\s*\{", s)
    if m and cur_c:
        bar2c[m.group(1)] = cur_c

# --- 圣地 ---
hs = []
depth = 0
cur = None
for i, ln in enumerate(io.open(SRC, "rb").read().decode("utf-8-sig").split("\r\n"), 1):
    code = ln.split("#")[0]
    if depth == 0:
        m = re.match(r"^([A-Za-z0-9_\-]+)\s*=\s*\{", code)
        if m:
            cur = {"key": m.group(1), "b": None, "c": None, "ln": i}
            hs.append(cur)
    if depth == 1 and cur:
        mb = re.match(r"^\s*barony\s*=\s*([A-Za-z0-9_]+)", code)
        mc = re.match(r"^\s*county\s*=\s*([A-Za-z0-9_]+)", code)
        if mb:
            cur["b"] = mb.group(1)
        if mc:
            cur["c"] = mc.group(1)
    depth += code.count("{") - code.count("}")

hs_by_b = {}
hs_by_c = {}
for x in hs:
    if x["b"]:
        hs_by_b.setdefault(x["b"], []).append(x)
    c = x["c"] or bar2c.get(x["b"] or "")
    if c:
        hs_by_c.setdefault(c, []).append(x)

out = []
out.append("特殊建筑挂载 = %d 条（game_start.txt）" % len(builds))
out.append("")

# A: 每条建筑 -> 同 barony 的圣地
out.append("=== A. 建筑 → 男爵领（同 barony 是否有圣地）===")
for b in builds:
    c = bar2c.get(b["bar"])
    h = hs_by_b.get(b["bar"], [])
    tag = ""
    if h:
        tag = "  ← 圣地: " + ", ".join("%s(%s)" % (x["key"], zh("holy_site_%s_name" % x["key"])) for x in h)
    elif c:
        tag = "  [同县圣地: %s]" % ", ".join(x["key"] for x in hs_by_c.get(c, []))
    out.append("  %-34s %-22s %-12s%s" % (
        b["bld"], b["bar"], zh(c) if c else "?", tag))
out.append("")

# B: 建筑名与圣地 key 疑似同名，但落点不同
def stem(s):
    s = re.sub(r"_\d+$", "", s)
    s = re.sub(r"_district$", "", s)
    return s


out.append("=== B. 建筑名与圣地 key 疑似同名 ===")
found = 0
for b in builds:
    st = stem(b["bld"])
    cands = [x for x in hs if x["key"] == st or st.startswith(x["key"]) or x["key"].startswith(st.split("_")[0])]
    # 只保留真正像的
    for x in cands:
        if b["bar"] == x["b"]:
            continue
        found += 1
        out.append("  建筑 %-32s 在 %-22s(%s) | 圣地 %-20s 在 %-22s(%s)" % (
            b["bld"], b["bar"], zh(bar2c.get(b["bar"]) or ""),
            x["key"], x["b"] or x["c"], zh(x["c"] or "")))
if not found:
    out.append("  （无）")

io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("\n".join(out[:5]))
print("...")
print("输出 ->", OUT)
