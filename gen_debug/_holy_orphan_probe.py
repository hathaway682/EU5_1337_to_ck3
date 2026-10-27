# -*- coding: utf-8 -*-
"""只读：找出没有被任何 faith 引用的「孤儿圣地」。

判定：holy_site_types 里定义的 key，在 common/religion/ 下除 holy_site_types 自身以外的
所有 .txt（跳过 # 注释行）里是否作为独立词出现过。
"""
import io
import os
import re

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RELDIR = os.path.join(MOD, "common", "religion")
HSDIR = os.path.join(RELDIR, "holy_site_types")
LT = os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt")
SRC = os.path.join(HSDIR, "00_holy_site_types.txt")


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


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


# ---- 1. 圣地 key + 当前指向 ----
lines = io.open(SRC, "rb").read().decode("utf-8-sig").split("\r\n")
depth, cur, hs = 0, None, {}
for i, ln in enumerate(lines):
    m = re.match(r"^([A-Za-z0-9_\-]+)\s*=\s*\{", ln)
    if depth == 0 and m:
        cur = m.group(1)
        hs[cur] = {"c": None, "b": None, "ln": i + 1}
    if depth == 1 and cur:
        mc = re.match(r"^\s*county\s*=\s*(\S+)", ln)
        mb = re.match(r"^\s*barony\s*=\s*(\S+)", ln)
        if mc:
            hs[cur]["c"] = mc.group(1)
        if mb:
            hs[cur]["b"] = mb.group(1)
    depth += ln.count("{") - ln.count("}")

# ---- 2. 收集 religion 目录下所有引用（跳过注释行、跳过 holy_site_types）----
referenced = {}
for dp, _, fs in os.walk(RELDIR):
    if os.path.normcase(dp).startswith(os.path.normcase(HSDIR)):
        continue
    for f in fs:
        if not f.endswith(".txt"):
            continue
        p = os.path.join(dp, f)
        rel = os.path.relpath(p, MOD)
        for ln in read(p).split("\n"):
            s = ln.split("#", 1)[0]
            for w in re.findall(r"[A-Za-z][A-Za-z0-9_\-]*", s):
                if w in hs:
                    referenced.setdefault(w, set()).add(rel)

# ---- 3. barony 中文名 ----
locm = load_loc(os.path.join(MOD, "localization", "simp_chinese"))
GAME = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"
locg = load_loc(os.path.join(GAME, "localization", "simp_chinese"))
loc = lambda k: locm.get(k) or locg.get(k)

orphans = sorted(k for k in hs if k not in referenced)
print("圣地块总数 = %d；被引用 = %d；孤儿 = %d"
      % (len(hs), len(referenced), len(orphans)))
print()
for k in orphans:
    h = hs[k]
    tgt = h["b"] or h["c"] or ""
    print("  %-22s L%-5d %-24s %-10s (县 %s)"
          % (k, h["ln"], tgt, loc(tgt) or "", h["c"] or "-"))
