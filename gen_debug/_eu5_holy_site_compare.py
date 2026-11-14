# -*- coding: utf-8 -*-
"""读取 EU5 官方圣地定义（common/holy_sites/*.txt），与 CK3 mod 的圣地落点做对照。

EU5 格式：
    mount_hiei = {
        location = kurita #shiga
        type = mountain
        importance = 5
        religions = { shinto }
    }

CK3 mod 的 b_<name> 里 <name> = EU5 的 location 名，所以可以
    EU5 location X  ->  mod b_X  ->  county C
再和 CK3 圣地当前的 barony/county 比。

只读，输出到 gen_debug/_eu5_holy_sites.out
"""
import io
import os
import re
import glob

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game\in_game"
OUT = os.path.join(MOD, "gen_debug", "_eu5_holy_sites.out")


def load_loc(d):
    out = {}
    for fn in glob.glob(os.path.join(d, "**", "*.yml"), recursive=True):
        s = io.open(fn, encoding="utf-8-sig", errors="ignore").read()
        for x in re.finditer(r'(?m)^\s*([A-Za-z0-9_.\-]+):\d*\s*"((?:[^"]|"")*)"', s):
            out.setdefault(x.group(1), x.group(2))
    return out


locm = load_loc(os.path.join(MOD, "localization", "simp_chinese"))
locg = load_loc(r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game\localization\simp_chinese")


def zh(k):
    return locm.get(k) or locg.get(k) or ""


# ---- EU5 圣地 ----
eu5 = []  # [{key, loc, typ, imp, rels, file}]
for fn in sorted(glob.glob(os.path.join(EU5, "common", "holy_sites", "*.txt"))):
    if os.path.basename(fn).lower() == "readme.txt":
        continue
    txt = io.open(fn, encoding="utf-8-sig", errors="ignore").read()
    lines = txt.split("\n")
    depth = 0
    cur = None
    for ln in lines:
        code = ln.split("#")[0]
        if depth == 0:
            m = re.match(r"^([A-Za-z0-9_\-]+)\s*=\s*\{", code)
            if m:
                cur = {"key": m.group(1), "loc": None, "typ": None, "imp": None,
                       "rels": [], "file": os.path.basename(fn)}
        if cur is not None and depth <= 1:
            ml = re.match(r"^\s*location\s*=\s*([A-Za-z0-9_\-]+)", code)
            mt = re.match(r"^\s*type\s*=\s*([A-Za-z0-9_\-]+)", code)
            mi = re.match(r"^\s*importance\s*=\s*(\d+)", code)
            mr = re.match(r"^\s*religions\s*=\s*\{([^}]*)\}", code)
            if ml:
                cur["loc"] = ml.group(1)
            if mt:
                cur["typ"] = mt.group(1)
            if mi:
                cur["imp"] = int(mi.group(1))
            if mr:
                cur["rels"] = re.findall(r"[A-Za-z0-9_\-]+", mr.group(1))
        depth += code.count("{") - code.count("}")
        if cur is not None and depth == 0:
            eu5.append(cur)
            cur = None

# ---- mod barony -> county ----
t = io.open(os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt"),
            encoding="utf-8-sig", errors="ignore").read()
bar2c = {}
counties = {}
cur_c = None
for ln in t.split("\n"):
    s = ln.strip()
    m = re.match(r"^(c_[A-Za-z0-9_]+)\s*=\s*\{", s)
    if m:
        cur_c = m.group(1)
        counties[cur_c] = []
        continue
    m = re.match(r"^(b_[A-Za-z0-9_]+)\s*=\s*\{", s)
    if m and cur_c:
        bar2c[m.group(1)] = cur_c
        counties[cur_c].append(m.group(1))

# ---- CK3 圣地 ----
SRC = os.path.join(MOD, "common", "religion", "holy_site_types", "00_holy_site_types.txt")
ck = []
lines = io.open(SRC, "rb").read().decode("utf-8-sig").split("\r\n")
depth = 0
cur = None
for i, ln in enumerate(lines):
    code = ln.split("#")[0]
    if depth == 0:
        m = re.match(r"^([A-Za-z0-9_\-]+)\s*=\s*\{", code)
        if m:
            cur = {"key": m.group(1), "b": None, "c": None, "ln": i + 1}
            ck.append(cur)
    if depth == 1 and cur:
        mb = re.match(r"^\s*barony\s*=\s*([A-Za-z0-9_]+)", code)
        mc = re.match(r"^\s*county\s*=\s*([A-Za-z0-9_]+)", code)
        if mb:
            cur["b"] = mb.group(1)
        if mc:
            cur["c"] = mc.group(1)
    depth += code.count("{") - code.count("}")
ck = [x for x in ck if x["b"] or x["c"]]

# CK3: county -> 圣地列表
ck_by_c = {}
ck_by_b = {}
for x in ck:
    if x["c"]:
        ck_by_c.setdefault(x["c"], []).append(x["key"])
    if x["b"]:
        ck_by_b.setdefault(x["b"], []).append(x["key"])

out = []
out.append("EU5 圣地总数 = %d" % len(eu5))
out.append("CK3 mod 圣地 = %d" % len(ck))
out.append("")

# ---- 逐条对照 ----
exact = []   # EU5 location 的 barony 正好就是 CK3 的 barony
samec = []   # 同县但不同 barony
diff = []    # 同县都没有
noloc = []   # mod 里没有 b_<location>

for e in eu5:
    L = e["loc"]
    if not L:
        noloc.append(e)
        continue
    b = "b_" + L
    if b in bar2c:
        c = bar2c[b]
        hit_b = ck_by_b.get(b)
        hit_c = ck_by_c.get(c)
        if hit_b:
            exact.append((e, b, c, hit_b))
        elif hit_c:
            samec.append((e, b, c, hit_c))
        else:
            diff.append((e, b, c, None))
    else:
        noloc.append(e)

out.append("=== A. EU5 location 的 barony 正是 CK3 某个圣地的 barony（%d）===" % len(exact))
for e, b, c, ks in exact:
    out.append("  %-26s -> %-20s %-10s | CK3: %s" % (
        e["key"], b, zh(c), ", ".join(ks)))
out.append("")

out.append("=== B. 同县不同 barony（%d）===" % len(samec))
for e, b, c, ks in samec:
    cur = []
    for k in ks:
        x = next((y for y in ck if y["key"] == k), None)
        if x:
            cur.append("%s=%s(%s)" % (k, x["b"] or "-", zh(x["b"] or x["c"] or "")))
    out.append("  EU5 %-26s -> %-22s %-12s | CK3 %s" % (
        e["key"], b, zh(c), "; ".join(cur)))
out.append("")

out.append("=== C. 该县没有任何 CK3 圣地（%d）===" % len(diff))
for e, b, c, _ in diff:
    sibs = [x for x in counties.get(c, [])]
    out.append("  %-26s -> %-20s %-10s(%s) 同县: %s" % (
        e["key"], b, zh(c), c,
        " ".join("%s=%s" % (x, zh(x)) for x in sibs[:10])))
out.append("")

out.append("=== D. mod 里没有 b_<location>（%d）===" % len(noloc))
for e in noloc:
    out.append("  %-26s loc=%-22s %s %s" % (
        e["key"], e["loc"], e["file"], " ".join(e["rels"])))

io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("\n".join(out[:6]))
print("...")
print("A=%d B=%d C=%d D=%d" % (len(exact), len(samec), len(diff), len(noloc)))
print("输出 ->", OUT)
