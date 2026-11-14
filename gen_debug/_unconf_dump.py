# -*- coding: utf-8 -*-
"""把 81 个未确认圣地连同「所在县全部男爵领（拉丁名+中文名）」一起打印，供人工判定同词/异名同地。"""
import csv, io, os, re

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HS = os.path.join(MOD, "common", "religion", "holy_site_types", "00_holy_site_types.txt")
LT = os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt")

def read(p):
    return io.open(p, encoding="utf-8-sig").read()

# ---- 本地化 ----
loc = {}
for root, _, fs in os.walk(os.path.join(MOD, "localization")):
    for f in fs:
        if not f.endswith(".yml"):
            continue
        try:
            for ln in io.open(os.path.join(root, f), encoding="utf-8-sig"):
                m = re.match(r'\s*([A-Za-z0-9_.\-]+):\d*\s*"(.*)"', ln)
                if m:
                    loc.setdefault(m.group(1), m.group(2))
        except Exception:
            pass

# ---- 法理树：c_ -> [b_] ----
stack = []          # [(indent, key)]
county_of = {}      # c_ -> [b_...]
bar_of = {}         # b_ -> c_
for ln in read(LT).split("\n"):
    s = ln.strip()
    ind = len(ln) - len(ln.lstrip("\t "))
    if s.startswith("}"):
        while stack and stack[-1][0] >= ind:
            stack.pop()
        continue
    m = re.match(r'^([a-z])_([A-Za-z0-9_\-]+)\s*=\s*\{', s)
    if not m:
        continue
    rank, key = m.group(1), m.group(1) + "_" + m.group(2)
    while stack and stack[-1][0] >= ind:
        stack.pop()
    if rank == "c":
        county_of.setdefault(key, [])
    elif rank == "b":
        for sind, skey in reversed(stack):
            if skey.startswith("c_"):
                county_of.setdefault(skey, []).append(key)
                bar_of[key] = skey
                break
    stack.append((ind, key))

# ---- 圣地块（1 tab = 顶层 key，2 tab = county/barony）----
blocks = {}
cur = None
for ln_no, ln in enumerate(read(HS).split("\n"), 1):
    m = re.match(r'^([a-z0-9_\-]+)\s*=\s*\{', ln)
    if m:
        cur = m.group(1)
        blocks[cur] = {"line": ln_no, "c": None, "b": None}
        continue
    if cur:
        mm = re.match(r'^\t(county|barony)\s*=\s*([a-z0-9_\-]+)', ln)
        if mm:
            blocks[cur]["c" if mm.group(1) == "county" else "b"] = mm.group(2)

# ---- 原版 CK3 ----
VAN = r"D:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III Beta\game\common\religion\holy_site_types\00_holy_site_types.txt"
van, vcur = {}, None
for ln in io.open(VAN, encoding="utf-8-sig"):
    ln = ln.rstrip("\r\n")
    m = re.match(r'^([a-z0-9_\-]+)\s*=\s*\{', ln)
    if m:
        vcur = m.group(1)
        van[vcur] = {"c": None, "b": None}
        continue
    if vcur:
        mm = re.match(r'^\t(county|barony)\s*=\s*([a-z0-9_\-]+)', ln)
        if mm:
            van[vcur]["c" if mm.group(1) == "county" else "b"] = mm.group(2)

def cn(k):
    return loc.get(k, "") if k else ""

rows = list(csv.DictReader(io.open(os.path.join(MOD, "gen_debug", "holy_sites_table.csv"), encoding="utf-8-sig")))
un = [r for r in rows if r["状态"] != "已确认"]

out = []
for r in un:
    k = r["圣地key"]
    b = blocks.get(k, {})
    c = b.get("c")
    v = van.get(k, {})
    out.append("=" * 78)
    out.append("%-22s 圣地=%s   van: c=%s b=%s" % (k, r["圣地中文名"], v.get("c"), v.get("b")))
    out.append("  现值  %s %s  /  %s %s" % (c, cn(c), b.get("b"), cn(b.get("b") or "")))
    if c and c in county_of:
        for bb in county_of[c]:
            mark = "  <<<" if bb == b.get("b") else ""
            out.append("    - %-30s %s%s" % (bb, cn(bb), mark))
    else:
        out.append("    (县 %s 不在法理树)" % c)
io.open(os.path.join(MOD, "gen_debug", "_unconf_dump.out"), "w", encoding="utf-8").write("\n".join(out))
print("wrote", len(out), "lines;", len(un), "unconfirmed; baronies", len(bar_of))
