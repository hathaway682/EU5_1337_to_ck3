# -*- coding: utf-8 -*-
"""用原版 CK3 的「圣地所在男爵领有无特殊建筑」来核对 mod 圣地落点。

跨版本锚点：mod 的 province id 被重新分配过（原版 3323=Sanchi，mod 3323=b_zagare），
不能直接对 id。但 mod 的 game_start.txt 每条建筑挂载行尾都写了原版 province id
（如 `title:b_bhilsa...sanchi_stupa_01_district #3323`），这个注释就是锚点。

流程：
  1. 原版 landed_titles: b_xxx -> province id
  2. 原版 history/provinces: province id -> [special_building]
  3. 原版 holy_site_types: 圣地 -> barony
  => 原版「圣地 -> 建筑」
  4. mod game_start.txt: 建筑 -> mod barony（+ 注释里的原版 id）
  5. mod holy_site_types: 圣地 -> barony
  => 对比：原版圣地有建筑时，mod 的圣地是否落在该建筑所在的 mod barony
"""
import io
import os
import re
import glob

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"
OUT = os.path.join(MOD, "gen_debug", "_vanilla_bld_vs_holysite.out")


def load_loc(d):
    out = {}
    for fn in glob.glob(os.path.join(d, "**", "*.yml"), recursive=True):
        s = io.open(fn, encoding="utf-8-sig", errors="ignore").read()
        for x in re.finditer(r'(?m)^\s*([A-Za-z0-9_.\-]+):\d*\s*"((?:[^"]|"")*)"', s):
            out.setdefault(x.group(1), x.group(2))
    return out


lm = load_loc(os.path.join(MOD, "localization", "simp_chinese"))
lg = load_loc(os.path.join(GAME, "localization", "simp_chinese"))
zh = lambda k: (lm.get(k) or lg.get(k) or "").strip()


def bar_prov(path):
    """barony -> province id（正则取 b_ 块紧跟的 province 行）"""
    txt = io.open(path, encoding="utf-8-sig", errors="ignore").read()
    out = {}
    for m in re.finditer(r"(?m)^\s*(b_[A-Za-z0-9_]+)\s*=\s*\{\s*\r?\n\s*province\s*=\s*(\d+)", txt):
        out[m.group(1)] = int(m.group(2))
    return out


def prov_bld(d):
    """province id -> [special_building]"""
    out = {}
    for fn in glob.glob(os.path.join(d, "*.txt")):
        txt = io.open(fn, encoding="utf-8-sig", errors="ignore").read()
        depth = 0
        cur = None
        for ln in txt.split("\n"):
            code = ln.split("#")[0]
            if depth == 0:
                m = re.match(r"^(\d+)\s*=\s*\{", code)
                if m:
                    cur = int(m.group(1))
            if cur is not None and depth <= 1:
                m = re.match(r"^\s*special_building(?:_slot)?\s*=\s*([A-Za-z0-9_]+)", code)
                if m:
                    out.setdefault(cur, [])
                    if m.group(1) not in out[cur]:
                        out[cur].append(m.group(1))
            depth += code.count("{") - code.count("}")
            if cur is not None and depth == 0:
                cur = None
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


# ---- 原版 ----
v_bar = bar_prov(os.path.join(GAME, "common", "landed_titles", "00_landed_titles.txt"))
v_pb = prov_bld(os.path.join(GAME, "history", "provinces"))
v_hs = {x["key"]: x for x in holy(os.path.join(GAME, "common", "religion", "holy_site_types", "00_holy_site_types.txt"))}

# 原版圣地 -> 建筑
v_hs_bld = {}
for k, x in v_hs.items():
    b = x["b"]
    if not b:
        continue
    p = v_bar.get(b)
    if p and v_pb.get(p):
        v_hs_bld[k] = (b, p, v_pb[p])

# ---- mod ----
m_bar = bar_prov(os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt"))
m_hs = {x["key"]: x for x in holy(os.path.join(MOD, "common", "religion", "holy_site_types", "00_holy_site_types.txt"))}

# mod 建筑 -> barony（含注释原版 id）
bld2bar = {}
for ln in io.open(os.path.join(MOD, "common", "on_action", "game_start.txt"), "rb").read().decode("utf-8-sig").split("\n"):
    for m in re.finditer(r"title:(b_[A-Za-z0-9_\-]+)\.title_province\s*=\s*\{[^}]*?add_special_district(?:_slot)?\s*=\s*([A-Za-z0-9_]+)", ln):
        bld2bar.setdefault(m.group(2), []).append(m.group(1))
# mod history/provinces 里按 id 挂的
m_pb = prov_bld(os.path.join(MOD, "history", "provinces"))
m_prov2bar = {}
for b, p in m_bar.items():
    m_prov2bar.setdefault(p, []).append(b)
for p, bl in m_pb.items():
    for b in m_prov2bar.get(p, []):
        for x in bl:
            bld2bar.setdefault(x, []).append(b)

out = []
out.append("原版：有特殊建筑的圣地 = %d / %d" % (len(v_hs_bld), len(v_hs)))
out.append("mod：建筑挂载点 = %d 个建筑 / %d 个 barony" % (
    len(bld2bar), len(set(b for v in bld2bar.values() for b in v))))
out.append("")

ok, bad, nomod = [], [], []
for k, (vb, p, bls) in sorted(v_hs_bld.items()):
    if k not in m_hs:
        nomod.append((k, vb, p, bls))
        continue
    mb = m_hs[k]["b"]
    mc = m_hs[k]["c"]
    # 找这些建筑在 mod 挂到哪个 barony
    targets = set()
    for x in bls:
        for b in bld2bar.get(x, []):
            targets.add(b)
    if not targets:
        nomod.append((k, vb, p, bls))
        continue
    if mb in targets:
        ok.append((k, vb, p, bls, mb))
    else:
        bad.append((k, vb, p, bls, mb, mc, sorted(targets)))

out.append("=== A. 原版圣地有建筑，mod 圣地落在同一 barony（%d）===" % len(ok))
for k, vb, p, bls, mb in ok:
    out.append("  %-20s 原版 %-20s(prov %d) 建筑 %-28s mod %s ✓" % (
        k, vb, p, ",".join(bls), mb))
out.append("")
out.append("=== B. 原版圣地有建筑，但 mod 圣地不在建筑所在 barony（%d）===" % len(bad))
for k, vb, p, bls, mb, mc, tg in bad:
    out.append("  %-20s 原版 %-18s(prov %d) 建筑 %-26s | mod 圣地 %-20s 而建筑在 %s" % (
        k, vb, p, ",".join(bls), mb or mc, ",".join(tg)))
out.append("")
out.append("=== C. 原版圣地有建筑，但 mod 没有对应圣地或建筑没迁移（%d）===" % len(nomod))
for k, vb, p, bls in nomod:
    inm = "mod 有圣地" if k in m_hs else "mod 无此圣地"
    out.append("  %-20s 原版 %-18s(prov %d) 建筑 %-28s %s" % (k, vb, p, ",".join(bls), inm))

io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("\n".join(out[:4]))
print("A=%d B=%d C=%d" % (len(ok), len(bad), len(nomod)))
print("输出 ->", OUT)
