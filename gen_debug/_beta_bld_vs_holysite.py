# -*- coding: utf-8 -*-
"""用 CK3 Beta 版原版数据核对 mod 圣地落点。

用户定的标准（2026-11-14）：
    原版 CK3 里圣地如果和某个特殊建筑在同一位置，mod 里也必须和该建筑同一位置。

关联方式（不用 province id，因为 mod 重新分配过）：
    建筑 key 是继承原版的（sanchi_stupa_01_district 两边同名）
    1. 原版 Beta game_start.txt: barony -> [建筑]
    2. 原版 Beta holy_site_types: 圣地 -> barony
    => 原版「圣地 -> 它的建筑」
    3. mod game_start.txt: 建筑 -> mod barony
    4. mod holy_site_types: 圣地 -> mod barony
    => 对比 3 和 4 是否同一 barony
"""
import io
import os
import re
import glob

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BETA = r"D:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III Beta\game"
OUT = os.path.join(MOD, "gen_debug", "_beta_bld_vs_holysite.out")


def load_loc(d):
    out = {}
    for fn in glob.glob(os.path.join(d, "**", "*.yml"), recursive=True):
        s = io.open(fn, encoding="utf-8-sig", errors="ignore").read()
        for x in re.finditer(r'(?m)^\s*([A-Za-z0-9_.\-]+):\d*\s*"((?:[^"]|"")*)"', s):
            out.setdefault(x.group(1), x.group(2))
    return out


lm = load_loc(os.path.join(MOD, "localization", "simp_chinese"))
lg = load_loc(os.path.join(BETA, "localization", "simp_chinese"))
zh = lambda k: (lm.get(k) or lg.get(k) or "").strip()


def gs_buildings(path):
    """game_start.txt -> {barony: [building]}（含 add_special_district / _slot）"""
    out = {}
    txt = io.open(path, encoding="utf-8-sig", errors="ignore").read()
    for ln in txt.split("\n"):
        for m in re.finditer(r"title:(b_[A-Za-z0-9_\-]+)\.title_province\s*=\s*\{[^}]*?add_special_district(?:_slot)?\s*=\s*([A-Za-z0-9_]+)", ln):
            out.setdefault(m.group(1), [])
            if m.group(2) not in out[m.group(1)]:
                out[m.group(1)].append(m.group(2))
    return out


def holy(p):
    lines = io.open(p, "rb").read().decode("utf-8-sig").split("\r\n")
    depth = 0
    cur = None
    out = []
    for i, ln in enumerate(lines):
        code = ln.split("#")[0]
        if depth == 0:
            m = re.match(r"^([A-Za-z0-9_\-]+)\s*=\s*\{", code)
            if m:
                cur = {"key": m.group(1), "b": None, "c": None, "ln": i + 1}
                out.append(cur)
        if depth == 1 and cur:
            mb = re.match(r"^\s*barony\s*=\s*([A-Za-z0-9_]+)", code)
            mc = re.match(r"^\s*county\s*=\s*([A-Za-z0-9_]+)", code)
            if mb:
                cur["b"] = mb.group(1)
            if mc:
                cur["c"] = mc.group(1)
        depth += code.count("{") - code.count("}")
    return out


v_bar_bld = gs_buildings(os.path.join(BETA, "common", "on_action", "game_start.txt"))
v_hs = {x["key"]: x for x in holy(os.path.join(BETA, "common", "religion", "holy_site_types", "00_holy_site_types.txt"))}
m_bar_bld = gs_buildings(os.path.join(MOD, "common", "on_action", "game_start.txt"))
m_hs = {x["key"]: x for x in holy(os.path.join(MOD, "common", "religion", "holy_site_types", "00_holy_site_types.txt"))}

bld2bar = {}
for bar, bls in m_bar_bld.items():
    for b in bls:
        bld2bar.setdefault(b, []).append(bar)

# 原版：圣地 -> 建筑
v_pairs = []
for k, x in v_hs.items():
    b = x["b"]
    if b and v_bar_bld.get(b):
        v_pairs.append((k, b, v_bar_bld[b]))

out = []
out.append("原版 Beta：有特殊建筑的男爵领 = %d；其中是圣地的 = %d" % (len(v_bar_bld), len(v_pairs)))
out.append("mod：有特殊建筑的男爵领 = %d；建筑数 = %d" % (len(m_bar_bld), len(bld2bar)))
out.append("")

ok, bad, lost = [], [], []
for k, vb, bls in sorted(v_pairs):
    if k not in m_hs:
        lost.append((k, vb, bls, "mod 无此圣地"))
        continue
    mb, mc = m_hs[k]["b"], m_hs[k]["c"]
    tgt = set()
    for b in bls:
        for x in bld2bar.get(b, []):
            tgt.add(x)
    if not tgt:
        lost.append((k, vb, bls, "建筑未迁移到 mod"))
        continue
    (ok if mb in tgt else bad).append((k, vb, bls, mb, mc, sorted(tgt)))

out.append("=== A. 原版圣地与建筑同位，mod 也同位（%d）===" % len(ok))
for k, vb, bls, mb, mc, _ in ok:
    out.append("  %-22s 原版 %-22s 建筑 %-30s mod %s ✓" % (k, vb, ",".join(bls), mb))
out.append("")
out.append("=== B. 原版同位，mod 不同位（%d）===" % len(bad))
for k, vb, bls, mb, mc, tgt in bad:
    out.append("  %-22s 原版 %-20s 建筑 %-28s | mod 圣地 %-20s(%s) 建筑在 %s" % (
        k, vb, ",".join(bls), mb or "-", zh(mc), ",".join(tgt)))
out.append("")
out.append("=== C. 原版同位但 mod 缺（%d）===" % len(lost))
for k, vb, bls, why in lost:
    out.append("  %-22s 原版 %-20s 建筑 %-30s %s" % (k, vb, ",".join(bls), why))

io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("\n".join(out[:3]))
print("A=%d B=%d C=%d" % (len(ok), len(bad), len(lost)))
print("输出 ->", OUT)
