# -*- coding: utf-8 -*-
"""按「半径内同名地块」修圣地位置：只改圣地块的 county= / barony= 指向，不动任何本地化文本。

规则（用户 2026-10-23 拍板）：
  - 半径 300 km
  - 判定：圣地中文本地化名 == 男爵领中文本地化名（严格同名），或 男爵领 key 去 b_ 前缀 == 圣地 key
  - 当前 barony 已同名则跳过
  - 取半径内最近同名男爵领；county 同步改为该男爵领所属县（位置整体迁移）
默认 dry-run，--apply 才写（先备份，保 BOM + CRLF）。
"""
import io, json, math, os, re, shutil, sys, time, collections

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
GAME = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"
CENT = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export\_ck3_province_centroid.json"
SRC = os.path.join(MOD, "common", "religion", "holy_site_types", "00_holy_site_types.txt")
LT = os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt")
RADIUS = 300.0
APPLY = "--apply" in sys.argv
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


def main():
    # ---- 男爵领 -> 县 / 质心 ----
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

    name2bar = collections.defaultdict(list)
    for b in barpos:
        nm = loc(b)
        if nm:
            name2bar[nm].append(b)
    allbars = [(b, loc(b)) for b in barpos if loc(b)]

    # ---- 行级扫描圣地文件 ----
    raw = io.open(SRC, "rb").read()
    text = raw.decode("utf-8-sig")
    lines = text.split("\r\n")

    # 记录每个顶层块的行范围
    blocks, depth, cur = [], 0, None
    for i, ln in enumerate(lines):
        m = re.match(r"^([A-Za-z0-9_\-]+)\s*=\s*\{", ln)
        if depth == 0 and m:
            cur = {"key": m.group(1), "start": i, "end": None, "c": None, "b": None}
            blocks.append(cur)
        if depth == 1 and cur is not None:
            mc = re.match(r"^\s*county\s*=\s*(\S+)", ln)
            mb = re.match(r"^\s*barony\s*=\s*(\S+)", ln)
            if mc:
                cur["c"] = (i, mc.group(1))
            if mb:
                cur["b"] = (i, mb.group(1))
        depth += ln.count("{") - ln.count("}")
        if depth == 0 and cur is not None and cur["end"] is None and i > cur["start"]:
            cur["end"] = i

    plan, skipped, noref = [], 0, 0
    for blk in blocks:
        key = blk["key"]
        if not blk["b"]:
            skipped += 1
            continue
        sname = loc("holy_site_%s_name" % key) or loc("holy_site_%s" % key)
        if not sname:
            skipped += 1
            continue
        curb = blk["b"][1]
        if loc(curb) == sname or curb[2:] == key:
            skipped += 1
            continue
        ref = barpos.get(curb)
        if not ref:
            noref += 1
            continue
        best = None
        for cb, nm in allbars:
            if cb == curb or cb not in barpos:
                continue
            if nm == sname:
                lv = 0
            elif len(sname) >= 2 and nm.startswith(sname):
                lv = 1          # 圣地亚哥 -> 圣地亚哥‑德孔波斯特拉
            else:
                continue
            dd = km(ref, barpos[cb])
            if dd <= RADIUS and (best is None or (dd, lv) < (best[0], best[2])):
                best = (dd, cb, lv, nm)
        if not best:
            continue
        plan.append({"key": key, "name": sname, "old_c": blk["c"][1] if blk["c"] else None,
                     "old_b": curb, "new_b": best[1], "new_c": bar2c.get(best[1]),
                     "km": best[0], "lv": best[2], "new_name": best[3],
                     "li_c": blk["c"][0] if blk["c"] else None,
                     "li_b": blk["b"][0]})

    print("扫描 %d 个圣地块；跳过（无 barony/无中文名/已同名）%d；无质心 %d；可修 %d"
          % (len(blocks), skipped, noref, len(plan)))
    for p in sorted(plan, key=lambda x: x["km"]):
        print("  [%d] %-26s %-12s %5.0fkm  %s(%s) -> %s/%s(%s)"
              % (p["lv"], p["key"], p["name"], p["km"], p["old_b"], p["old_c"],
                 p["new_b"], p["new_name"], p["new_c"]))

    if not APPLY:
        print("\n[dry-run] 未写文件。")
        return
    if not plan:
        print("无改动。")
        return

    for p in plan:
        if p["li_c"] is not None and p["new_c"]:
            old = lines[p["li_c"]]
            lines[p["li_c"]] = re.sub(r"(county\s*=\s*)\S+", r"\g<1>" + p["new_c"], old)
        old = lines[p["li_b"]]
        lines[p["li_b"]] = re.sub(r"(barony\s*=\s*)\S+", r"\g<1>" + p["new_b"], old)

    new = "\r\n".join(lines)
    ts = time.strftime("%Y%m%d_%H%M%S")
    bak = SRC + ".bak_holysite_radius_" + ts
    shutil.copy2(SRC, bak)
    io.open(SRC, "wb").write(b"\xef\xbb\xbf" + new.encode("utf-8"))
    print("\nAPPLIED %d 处。备份：%s" % (len(plan), bak))
    print("braces: %d %d" % (new.count("{"), new.count("}")))


if __name__ == "__main__":
    main()
