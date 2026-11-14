# -*- coding: utf-8 -*-
"""特殊建筑 vs 圣地：用相似度找「建筑与圣地明显是同一个地方、但不在同一男爵领」的情况。

建筑挂载真源：common/on_action/game_start.txt 的
    title:b_XXX.title_province = { add_special_district = <bld>_district }
"""
import io
import os
import re
import glob
import difflib

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GS = os.path.join(MOD, "common", "on_action", "game_start.txt")
SRC = os.path.join(MOD, "common", "religion", "holy_site_types", "00_holy_site_types.txt")


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

builds = []
for i, ln in enumerate(io.open(GS, "rb").read().decode("utf-8-sig").split("\n"), 1):
    for m in re.finditer(r"title:(b_[A-Za-z0-9_\-]+)\.title_province\s*=\s*\{[^}]*?add_special_district(?:_slot)?\s*=\s*([A-Za-z0-9_]+)", ln):
        builds.append({"bld": m.group(2), "bar": m.group(1), "ln": i})

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

# 建筑主干 -> 候选圣地
SKIP = {"generic", "university", "district", "bazaar", "market", "citadel", "walls",
        "palace", "temple", "mosque", "cathedral", "abbey", "basins", "fort", "bay",
        "grottoes", "academy", "pagoda", "tomb", "sanctuary", "stupa", "caves",
        "megaliths", "hills", "pyramid", "kilns", "observatory", "towers", "gate",
        "bridge", "harbor", "harbour", "castle", "mining", "mines", "lighthouse"}

print("=== 建筑名与圣地 key 相似度 >= 0.72，且不在同一男爵领 ===")
hits = 0
for b in builds:
    st = re.sub(r"_\d+$", "", b["bld"])
    st = re.sub(r"_district$", "", st)
    words = [w for w in st.split("_") if w not in SKIP and len(w) >= 4]
    best = []
    for x in hs:
        for w in words + [st]:
            r = difflib.SequenceMatcher(None, w, x["key"]).ratio()
            if r >= 0.72:
                best.append((r, x, w))
    if not best:
        continue
    best.sort(key=lambda z: -z[0])
    r, x, w = best[0]
    same = (b["bar"] == x["b"])
    if same:
        continue
    hits += 1
    print("  %-34s %-20s(%s)  vs  圣地 %-18s %-20s(%s)  r=%.2f [%s]"
          % (b["bld"], b["bar"], zh(bar2c.get(b["bar"]) or ""),
             x["key"], x["b"] or x["c"], zh(x["c"] or ""), r, w))
print("合计 %d 条" % hits)
