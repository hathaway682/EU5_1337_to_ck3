# -*- coding: utf-8 -*-
"""只读进度盘点：按第一轮同名规则 + 知识映射 MAP，统计圣地位置修复的剩余量。

口径（与 _fix_holy_site_by_same_name.py 一致）：
  已对   = 当前 barony 中文名 == 圣地中文名，或 barony key 去 b_ 前缀 == 圣地 key
  已修   = 不同名，但 key 在 _apply_holy_site_knowledge_map.MAP 里
  剩余   = 不同名，也不在 MAP 里
剩余再分两类：
  有同名候选 = 半径 300km 内存在同名/前缀同名地块（说明还能自动修，属漏网）
  无同名候选 = 半径内找不到同名地块（只能靠知识判断，或地图无对应点）
"""
import collections
import importlib.util
import io
import json
import math
import os
import re

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"
CENT = os.path.join(os.path.dirname(MOD), "Global_modern_map", "eu5_export", "_ck3_province_centroid.json")
SRC = os.path.join(MOD, "common", "religion", "holy_site_types", "00_holy_site_types.txt")
LT = os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt")
MAPFILE = os.path.join(MOD, "gen_debug", "_apply_holy_site_knowledge_map.py")
RADIUS = 300.0
BLOCK = re.compile(r"([A-Za-z0-9_\-]+)\s*=\s*\{")


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


def walk(s, path=()):
    i, n = 0, len(s)
    while i < n:
        m = BLOCK.search(s, i)
        if not m:
            return
        j, d = m.end(), 1
        while j < n and d:
            if s[j] == "{":
                d += 1
            elif s[j] == "}":
                d -= 1
            j += 1
        body = s[m.end():j - 1]
        yield path, m.group(1), body
        yield from walk(body, path + (m.group(1),))
        i = j


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


def load_map():
    spec = importlib.util.spec_from_file_location("hsmap", MAPFILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.MAP


def main():
    lt = read(LT)
    bar2c, bar2p = {}, {}
    for path, key, body in walk(lt):
        if not key.startswith("b_"):
            continue
        c = next((x for x in reversed(path) if x.startswith("c_")), None)
        if not c:
            continue
        bar2c[key] = c
        mp = re.search(r"province\s*=\s*(\d+)", body)
        if mp:
            bar2p[key] = int(mp.group(1))

    cent = {int(k): v for k, v in json.load(io.open(CENT, encoding="utf-8")).items()}
    barpos = {b: cent[p][:2] for b, p in bar2p.items() if p in cent}

    def km(a, b):
        def ll(p):
            return (90.0 - p[1] * 180.0 / 8192.0, -180.0 + p[0] * 360.0 / 16384.0)
        la1, lo1 = ll(a)
        la2, lo2 = ll(b)
        p1, p2 = math.radians(la1), math.radians(la2)
        h = (math.sin((p2 - p1) / 2) ** 2
             + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lo2 - lo1) / 2) ** 2)
        return 2 * 6371.0 * math.asin(math.sqrt(h))

    locm = load_loc(os.path.join(MOD, "localization", "simp_chinese"))
    locg = load_loc(os.path.join(GAME, "localization", "simp_chinese"))
    loc = lambda k: locm.get(k) or locg.get(k)
    HS = load_map()

    name2bar = collections.defaultdict(list)
    for b in barpos:
        nm = loc(b)
        if nm:
            name2bar[nm].append(b)
    allbars = [(b, loc(b)) for b in barpos if loc(b)]

    lines = io.open(SRC, "rb").read().decode("utf-8-sig").split("\r\n")
    blocks, depth, cur = [], 0, None
    for i, ln in enumerate(lines):
        m = re.match(r"^([A-Za-z0-9_\-]+)\s*=\s*\{", ln)
        if depth == 0 and m:
            cur = {"key": m.group(1), "c": None, "b": None}
            blocks.append(cur)
        if depth == 1 and cur is not None:
            mc = re.match(r"^\s*county\s*=\s*(\S+)", ln)
            mb = re.match(r"^\s*barony\s*=\s*(\S+)", ln)
            if mc:
                cur["c"] = mc.group(1)
            if mb:
                cur["b"] = mb.group(1)
        depth += ln.count("{") - ln.count("}")

    ok, fixed, noName, noBar, rest = [], [], [], [], []
    for blk in blocks:
        key = blk["key"]
        sname = loc("holy_site_%s_name" % key) or loc("holy_site_%s" % key)
        if not blk["b"]:
            (noBar if not sname else noName).append(key)
            continue
        curb = blk["b"]
        if sname and (loc(curb) == sname or loc(curb).startswith(sname)
                      or curb[2:] == key):
            ok.append(key)
            continue
        if key in HS:
            fixed.append(key)
            continue
        if not sname:
            noName.append(key)
            continue
        # 剩余：找半径内同名候选
        cand = None
        ref = barpos.get(curb)
        if ref:
            for cb, nm in allbars:
                if cb == curb or cb not in barpos:
                    continue
                if nm == sname:
                    lv = 0
                elif len(sname) >= 2 and nm.startswith(sname):
                    lv = 1
                else:
                    continue
                dd = km(ref, barpos[cb])
                if dd <= RADIUS and (cand is None or (dd, lv) < (cand[0], cand[1])):
                    cand = (dd, lv, cb, nm)
        rest.append({"key": key, "name": sname, "cur": curb,
                     "cur_name": loc(curb) or "", "cand": cand})

    total = len(blocks)
    print("=" * 72)
    print("圣地块总数              %4d" % total)
    print("  已对（当前指向即同名）  %4d" % len(ok))
    print("  已修（知识映射 MAP）    %4d" % len(fixed))
    print("  无中文名（无法判定）    %4d" % len(noName))
    print("  无 barony 行            %4d" % len(noBar))
    print("  剩余未处理              %4d" % len(rest))
    print("=" * 72)
    auto = [r for r in rest if r["cand"]]
    manual = [r for r in rest if not r["cand"]]
    print("剩余 %d 里：半径内仍有同名候选（可自动修）%d；无同名候选（需知识判断）%d"
          % (len(rest), len(auto), len(manual)))

    if auto:
        print("\n--- 半径内仍有同名候选（漏网）---")
        for r in sorted(auto, key=lambda x: x["cand"][0]):
            d, lv, cb, nm = r["cand"]
            print("  [%d] %-24s %-12s %4.0fkm  %s(%s) -> %s(%s)"
                  % (lv, r["key"], r["name"], d, r["cur"], r["cur_name"], cb, nm))

    print("\n--- 剩余明细（无同名候选）---")
    for r in manual:
        print("  %-24s %-12s 现指 %-22s(%s)" % (r["key"], r["name"], r["cur"], r["cur_name"]))


if __name__ == "__main__":
    main()
