# -*- coding: utf-8 -*-
"""只读：对比 mod 与 CK3 原版，看「孤儿圣地」里哪些是原版也孤儿、哪些是 mod 漏引用的。
"""
import io
import os
import re

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
GAME = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"
SRC = os.path.join(MOD, "common", "religion", "holy_site_types", "00_holy_site_types.txt")


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


def hs_keys(path):
    lines = io.open(path, "rb").read().decode("utf-8-sig").split("\n")
    depth, cur, out = 0, None, {}
    for i, ln in enumerate(lines):
        m = re.match(r"^([A-Za-z0-9_\-]+)\s*=\s*\{", ln)
        if depth == 0 and m:
            cur = m.group(1)
            out[cur] = {"c": None, "b": None, "ln": i + 1}
        if depth == 1 and cur:
            mc = re.match(r"^\s*county\s*=\s*(\S+)", ln)
            mb = re.match(r"^\s*barony\s*=\s*(\S+)", ln)
            if mc:
                out[cur]["c"] = mc.group(1)
            if mb:
                out[cur]["b"] = mb.group(1)
        depth += ln.count("{") - ln.count("}")
    return out


def refs(relroot, keyset):
    """返回被引用的 key 集合（跳过注释、跳过 holy_site_types 目录）"""
    got = set()
    hsd = os.path.join(relroot, "holy_site_types")
    for dp, _, fs in os.walk(relroot):
        if os.path.normcase(dp).startswith(os.path.normcase(hsd)):
            continue
        for f in fs:
            if not f.endswith(".txt"):
                continue
            try:
                t = read(os.path.join(dp, f))
            except Exception:
                continue
            for ln in t.split("\n"):
                s = ln.split("#", 1)[0]
                for w in re.findall(r"[A-Za-z][A-Za-z0-9_\-]*", s):
                    if w in keyset:
                        got.add(w)
    return got


def load_loc(root):
    out = {}
    for dp, _, fs in os.walk(root):
        for f in fs:
            if not f.endswith(".yml"):
                continue
            try:
                t = io.open(os.path.join(dp, f), encoding="utf-8-sig", errors="ignore").read()
            except Exception:
                continue
            for m in re.finditer(r'(?m)^\s*([A-Za-z0-9_.\-]+):\d*\s*"((?:[^"]|"")*)"', t):
                out.setdefault(m.group(1), m.group(2).replace('""', '"'))
    return out


mod_hs = hs_keys(SRC)
van_hs = hs_keys(os.path.join(GAME, "common", "religion", "holy_site_types",
                              "00_holy_site_types.txt"))

mod_ref = refs(os.path.join(MOD, "common", "religion"), set(mod_hs))
van_ref = refs(os.path.join(GAME, "common", "religion"), set(van_hs) | set(mod_hs))

locm = load_loc(os.path.join(MOD, "localization", "simp_chinese"))
locg = load_loc(os.path.join(GAME, "localization", "simp_chinese"))
loc = lambda k: locm.get(k) or locg.get(k)

orphans = sorted(k for k in mod_hs if k not in mod_ref)
print("mod 圣地 %d，被引用 %d，孤儿 %d" % (len(mod_hs), len(mod_ref), len(orphans)))
print("原版圣地 %d，被原版引用 %d" % (len(van_hs), len(van_ref)))
print()

a = [k for k in orphans if k in van_ref]
b = [k for k in orphans if k not in van_ref]
print("A. 原版有 faith 引用、mod 没引用（= mod 漏挂，共 %d）" % len(a))
for k in a:
    h = mod_hs[k]
    print("   %-20s %-22s %s" % (k, h["b"] or h["c"] or "-", loc(h["b"] or h["c"] or "") or ""))
print()
print("B. 原版也没有 faith 引用（= 本来就无信仰使用，共 %d）" % len(b))
for k in b:
    h = mod_hs[k]
    print("   %-20s %-22s %s" % (k, h["b"] or h["c"] or "-", loc(h["b"] or h["c"] or "") or ""))
