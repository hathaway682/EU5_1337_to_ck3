# -*- coding: utf-8 -*-
"""补漏：用模糊相似度把 EU5 圣地 key 与 CK3 圣地 key 对齐，找出之前严格规则漏掉的配对。

教训（2026-11-14）：`olympos`(EU5) vs `olympus`(CK3) 只差一个字母，严格规则没匹配上，
导致把本来正确的 b_hatera 误判成存疑。
"""
import io
import os
import re
import glob
import difflib

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game\in_game"


def load_loc(d):
    out = {}
    for fn in glob.glob(os.path.join(d, "**", "*.yml"), recursive=True):
        s = io.open(fn, encoding="utf-8-sig", errors="ignore").read()
        for x in re.finditer(r'(?m)^\s*([A-Za-z0-9_.\-]+):\d*\s*"((?:[^"]|"")*)"', s):
            out.setdefault(x.group(1), x.group(2))
    return out


lm = load_loc(os.path.join(MOD, "localization", "simp_chinese"))
lg = load_loc(r"D:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III Beta\game\localization\simp_chinese")
zh = lambda k: (lm.get(k) or lg.get(k) or "").strip()

eu5 = {}
for fn in sorted(glob.glob(os.path.join(EU5, "common", "holy_sites", "*.txt"))):
    if os.path.basename(fn).lower() == "readme.txt":
        continue
    txt = io.open(fn, encoding="utf-8-sig", errors="ignore").read()
    depth = 0
    cur = None
    for ln in txt.split("\n"):
        raw = ln
        code = ln.split("#")[0]
        if depth == 0:
            m = re.match(r"^([A-Za-z0-9_\-]+)\s*=\s*\{", code)
            if m:
                cur = {"key": m.group(1), "loc": None, "commented": raw.strip().startswith("#")}
        if cur is not None and depth <= 1:
            ml = re.match(r"^\s*location\s*=\s*([A-Za-z0-9_\-]+)", code)
            if ml:
                cur["loc"] = ml.group(1)
        depth += code.count("{") - code.count("}")
        if cur is not None and depth == 0:
            if cur["loc"]:
                eu5[cur["key"]] = cur
            cur = None

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

SRC = os.path.join(MOD, "common", "religion", "holy_site_types", "00_holy_site_types.txt")
ck = {}
depth = 0
cur = None
for i, ln in enumerate(io.open(SRC, "rb").read().decode("utf-8-sig").split("\r\n"), 1):
    code = ln.split("#")[0]
    if depth == 0:
        m = re.match(r"^([A-Za-z0-9_\-]+)\s*=\s*\{", code)
        if m:
            cur = {"key": m.group(1), "b": None, "c": None, "ln": i}
            ck[cur["key"]] = cur
    if depth == 1 and cur:
        mb = re.match(r"^\s*barony\s*=\s*([A-Za-z0-9_]+)", code)
        mc = re.match(r"^\s*county\s*=\s*([A-Za-z0-9_]+)", code)
        if mb:
            cur["b"] = mb.group(1)
        if mc:
            cur["c"] = mc.group(1)
    depth += code.count("{") - code.count("}")

print("=== EU5 圣地 key 与 CK3 圣地 key 相似度 >= 0.85，但落点不同 ===")
hits = 0
for ek, e in sorted(eu5.items()):
    best = None
    for k in ck:
        r = difflib.SequenceMatcher(None, ek, k).ratio()
        if r >= 0.78 and (best is None or r > best[0]):
            best = (r, k)
    if not best:
        continue
    r, k = best
    tb = "b_" + e["loc"]
    if ck[k]["b"] == tb:
        continue
    hits += 1
    tc = bar2c.get(tb)
    print("  EU5 %-24s -> %-22s(%s) | CK3 %-20s 现 %-22s(%s)  r=%.2f" % (
        ek, tb, zh(tc), k, ck[k]["b"] or ck[k]["c"], zh(ck[k]["c"] or ""), r))
print("合计 %d 条" % hits)
