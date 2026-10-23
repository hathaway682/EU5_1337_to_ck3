# -*- coding: utf-8 -*-
"""列出「当前地块与圣地不同名、且半径 300km 内无同名/前缀候选」的圣地，供人工知识匹配。只读。"""
import io, json, math, os, re, collections

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
GAME = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"
CENT = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export\_ck3_province_centroid.json"
SRC = os.path.join(MOD, "common", "religion", "holy_site_types", "00_holy_site_types.txt")
LT = os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt")
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
    allbars = [(b, loc(b)) for b in barpos if loc(b)]

    raw = io.open(SRC, "rb").read().decode("utf-8-sig")
    lines = raw.split("\r\n")
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

    c2bars = collections.defaultdict(list)
    for b, c in bar2c.items():
        c2bars[c].append(b)

    out = []
    for blk in blocks:
        key, c, b = blk["key"], blk["c"], blk["b"]
        sname = loc("holy_site_%s_name" % key) or loc("holy_site_%s" % key)
        if not b or not sname:
            continue
        if loc(b) == sname or b[2:] == key:
            continue
        ref = barpos.get(b)
        if not ref:
            continue
        hit = None
        for cb, nm in allbars:
            if cb == b or cb not in barpos:
                continue
            if nm == sname or (len(sname) >= 2 and nm.startswith(sname)):
                dd = km(ref, barpos[cb])
                if dd <= RADIUS and (hit is None or dd < hit[0]):
                    hit = (dd, cb)
        if hit:
            continue
        out.append((key, sname, c, b, loc(b), [loc(x) or x for x in c2bars.get(c, [])]))

    print("未匹配圣地 %d 个" % len(out))
    for key, sname, c, b, bn, sibs in out:
        print("%-24s | %-12s | %-20s | %-22s %-10s | 同县: %s"
              % (key, sname, c, b, bn or "-", "/".join(sibs[:12])))


if __name__ == "__main__":
    main()
