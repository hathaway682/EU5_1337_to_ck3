# -*- coding: utf-8 -*-
"""只读：交叉核对「孤儿圣地（无 faith 引用）」与「无中文本地化圣地」两个集合。

用途：回答「删掉孤儿圣地后，是不是就没有无本地化的了」。
判定口径：
  - 圣地集合 = common/religion/holy_site_types/00_holy_site_types.txt 顶层块（depth==1 解析）
  - 孤儿 = 该 key 未出现在 common/religion/ 下任何其它 .txt 的 faith `holy_sites` 列表里
  - 无本地化 = 既无 holy_site_<key>_name 也无 holy_site_<key>（先查 mod，再查 CK 原版）
"""
import io
import os
import re
import glob

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"
SRC = os.path.join(MOD, "common", "religion", "holy_site_types", "00_holy_site_types.txt")


def load_loc(d):
    """递归读取（原版把圣地本地化放在 localization/simp_chinese/religion/ 子目录里）"""
    out = {}
    for fn in glob.glob(os.path.join(d, "**", "*.yml"), recursive=True):
        s = io.open(fn, encoding="utf-8-sig", errors="ignore").read()
        for x in re.finditer(r'(?m)^\s*([A-Za-z0-9_.\-]+):\d*\s*"((?:[^"]|"")*)"', s):
            out.setdefault(x.group(1), x.group(2))
    return out


def parse_blocks(p):
    lines = io.open(p, "rb").read().decode("utf-8-sig").split("\r\n")
    depth = 0
    cur = None
    blocks = []
    for i, ln in enumerate(lines):
        m = re.match(r"^([A-Za-z0-9_\-]+)\s*=\s*\{", ln)
        if depth == 0 and m:
            cur = {"key": m.group(1), "b": None, "c": None, "ln": i + 1}
            blocks.append(cur)
        if depth == 1 and cur:
            mc = re.match(r"^\s*county\s*=\s*(\S+)", ln)
            mb = re.match(r"^\s*barony\s*=\s*(\S+)", ln)
            if mc:
                cur["c"] = mc.group(1)
            if mb:
                cur["b"] = mb.group(1)
        depth += ln.count("{") - ln.count("}")
    return blocks


def faith_refs(root):
    """收集 faith_types 里 holy_sites 列表引用到的圣地 key"""
    ref = set()
    for fn in glob.glob(os.path.join(root, "common", "religion", "**", "*.txt"), recursive=True):
        if "holy_site_types" in fn.replace("\\", "/"):
            continue
        txt = io.open(fn, encoding="utf-8-sig", errors="ignore").read()
        for m in re.finditer(r"holy_sites\s*=\s*\{([^}]*)\}", txt, re.S):
            for tok in re.findall(r"[A-Za-z0-9_\-]+", m.group(1)):
                ref.add(tok)
    return ref


print("[dbg] MOD =", MOD)
print("[dbg] GAME exists =", os.path.isdir(GAME))
locm = load_loc(os.path.join(MOD, "localization", "simp_chinese"))
locg = load_loc(os.path.join(GAME, "localization", "simp_chinese"))
print("[dbg] locm =", len(locm), " locg =", len(locg))


def loc(k):
    return locm.get(k) or locg.get(k)


blocks = parse_blocks(SRC)
keys = [b["key"] for b in blocks]
ref_mod = faith_refs(MOD)
ref_van = faith_refs(GAME)

orphan = [k for k in keys if k not in ref_mod]
orphan_van = [k for k in keys if k not in ref_van]
noname = [k for k in keys if not (loc("holy_site_%s_name" % k) or loc("holy_site_%s" % k))]

print("圣地块总数           = %d" % len(keys))
print("mod faith 引用到的 key = %d" % len(ref_mod))
print("孤儿（mod 无引用）    = %d" % len(orphan))
print("原版 faith 也没引用   = %d" % len(orphan_van))
print("无中文本地化          = %d" % len(noname))
print()

nn = set(noname)
orp = set(orphan_van)   # mod 没有 faith_types，一律继承原版，故孤儿判定以原版 faith 引用为准
print("无中文名 ∩ 孤儿        = %d" % len(nn & orp))
print("无中文名 但 非孤儿     = %d %s" % (len(nn - orp), sorted(nn - orp)))
print("孤儿 但 有中文名       = %d" % len(orp - nn))
print()
print("--- 无中文本地化的 48 个（是否孤儿 / 现值）---")
bmap = {b["key"]: b for b in blocks}
for k in noname:
    b = bmap[k]
    print("  %-18s L%-5d %-22s %-10s | 孤儿=%s" % (
        k, b["ln"], b["b"] or b["c"] or "?", loc(b["b"] or b["c"] or ""), "是" if k in orp else "否"))
print()
print("--- 孤儿里有中文名的（有本地化但无 faith 引用）---")
for k in sorted(orp - nn):
    b = bmap[k]
    nm = loc("holy_site_%s_name" % k) or loc("holy_site_%s" % k)
    print("  %-18s L%-5d %-22s %-10s | %s" % (
        k, b["ln"], b["b"] or b["c"] or "?", loc(b["b"] or b["c"] or ""), nm))
