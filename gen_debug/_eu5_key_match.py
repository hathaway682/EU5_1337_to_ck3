# -*- coding: utf-8 -*-
"""EU5 圣地 vs CK3 圣地：按 key 归一化匹配，找出「同一个圣地、落点不同」的。

归一化规则（保守，只认这三种）：
  1. 完全相同
  2. EU5 = "mount_" + CK3            （hiei <-> mount_hiei）
  3. EU5 = CK3 + "_holy_city..." 之类后缀 / EU5 以 "_"+CK3 结尾
只读，输出 gen_debug/_eu5_key_match.out
"""
import io
import os
import re
import glob

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game\in_game"
OUT = os.path.join(MOD, "gen_debug", "_eu5_key_match.out")


def load_loc(d):
    out = {}
    for fn in glob.glob(os.path.join(d, "**", "*.yml"), recursive=True):
        s = io.open(fn, encoding="utf-8-sig", errors="ignore").read()
        for x in re.finditer(r'(?m)^\s*([A-Za-z0-9_.\-]+):\d*\s*"((?:[^"]|"")*)"', s):
            out.setdefault(x.group(1), x.group(2))
    return out


locm = load_loc(os.path.join(MOD, "localization", "simp_chinese"))
locg = load_loc(r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game\localization\simp_chinese")
zh = lambda k: locm.get(k) or locg.get(k) or ""

# EU5
eu5 = []
for fn in sorted(glob.glob(os.path.join(EU5, "common", "holy_sites", "*.txt"))):
    if os.path.basename(fn).lower() == "readme.txt":
        continue
    txt = io.open(fn, encoding="utf-8-sig", errors="ignore").read()
    depth = 0
    cur = None
    for ln in txt.split("\n"):
        code = ln.split("#")[0]
        if depth == 0:
            m = re.match(r"^([A-Za-z0-9_\-]+)\s*=\s*\{", code)
            if m:
                cur = {"key": m.group(1), "loc": None, "imp": None, "file": os.path.basename(fn)}
        if cur is not None and depth <= 1:
            ml = re.match(r"^\s*location\s*=\s*([A-Za-z0-9_\-]+)", code)
            mi = re.match(r"^\s*importance\s*=\s*(\d+)", code)
            if ml:
                cur["loc"] = ml.group(1)
            if mi:
                cur["imp"] = int(mi.group(1))
        depth += code.count("{") - code.count("}")
        if cur is not None and depth == 0:
            eu5.append(cur)
            cur = None

# mod barony -> county
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

# CK3
SRC = os.path.join(MOD, "common", "religion", "holy_site_types", "00_holy_site_types.txt")
ck = {}
depth = 0
cur = None
lines = io.open(SRC, "rb").read().decode("utf-8-sig").split("\r\n")
for i, ln in enumerate(lines):
    code = ln.split("#")[0]
    if depth == 0:
        m = re.match(r"^([A-Za-z0-9_\-]+)\s*=\s*\{", code)
        if m:
            cur = {"key": m.group(1), "b": None, "c": None, "ln": i + 1}
            ck[cur["key"]] = cur
    if depth == 1 and cur:
        mb = re.match(r"^\s*barony\s*=\s*([A-Za-z0-9_]+)", code)
        mc = re.match(r"^\s*county\s*=\s*([A-Za-z0-9_]+)", code)
        if mb:
            cur["b"] = mb.group(1)
        if mc:
            cur["c"] = mc.group(1)
    depth += code.count("{") - code.count("}")


def norm_match(ek):
    """EU5 key -> 可能的 CK3 key 列表"""
    cands = []
    if ek in ck:
        cands.append(ek)
    if ek.startswith("mount_") and ek[6:] in ck:
        cands.append(ek[6:])
    # EU5 后缀式：xxx_holy_city_gnostic / xxx_temple / xxx_shrine / xxx_taisha
    for suf in ("_holy_city_gnostic", "_holy_site", "_temple", "_shrine", "_taisha",
                "_jinguuji", "_sanzan", "_mandir", "_mosque", "_mela", "_ji",
                "_perumal_temple", "_taisha"):
        if ek.endswith(suf) and ek[:-len(suf)] in ck:
            cands.append(ek[:-len(suf)])
    # 前缀式：xxx_yyy，取第一段
    if "_" in ek:
        head = ek.split("_")[0]
        if head in ck:
            cands.append(head)
    return list(dict.fromkeys(cands))


same = []      # barony 相同
diffb = []     # 同县不同 barony
diffc = []     # 县都不同
for e in eu5:
    if not e["loc"]:
        continue
    tb = "b_" + e["loc"]
    tc = bar2c.get(tb)
    for k in norm_match(e["key"]):
        c = ck[k]
        cb, cc = c["b"], c["c"] or bar2c.get(c["b"] or "")
        rec = (e, k, tb, tc, cb, cc)
        if cb == tb:
            same.append(rec)
        elif cc and tc and cc == tc:
            diffb.append(rec)
        else:
            diffc.append(rec)

out = []
out.append("EU5 圣地 %d / CK3 圣地 %d" % (len(eu5), len(ck)))
out.append("key 匹配上：barony 相同 %d / 同县不同 barony %d / 县不同 %d"
           % (len(same), len(diffb), len(diffc)))
out.append("")
out.append("=== 同县不同 barony（EU5 更精确，建议照 EU5）===")
for e, k, tb, tc, cb, cc in diffb:
    out.append("  CK3 %-22s L%-5d 现 %-24s(%s)  ->  EU5 %-26s %-24s(%s)" % (
        k, ck[k]["ln"], cb or "-", zh(cb or "") or zh(cc or ""),
        e["key"], tb, zh(tb)))
out.append("")
out.append("=== 县都不同（重点核对）===")
for e, k, tb, tc, cb, cc in diffc:
    out.append("  CK3 %-22s L%-5d 现 %-24s(%s/%s)  ->  EU5 %-26s %-24s(%s)" % (
        k, ck[k]["ln"], cb or "-", zh(cb or ""), zh(cc or ""),
        e["key"], tb, zh(tb)))
out.append("")
out.append("=== barony 相同（%d，已对）===" % len(same))
for e, k, tb, tc, cb, cc in same:
    out.append("  %-22s = %-24s %s" % (k, tb, zh(tb)))

io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("\n".join(out[:3]))
print("输出 ->", OUT)
