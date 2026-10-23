# -*- coding: utf-8 -*-
"""对未处理的圣地，列出同县男爵领的「mod 中文名」与「CK 原版中文名」，供知识匹配。只读。"""
import io, os, re, collections

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
GAME = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"
SRC = os.path.join(MOD, "common", "religion", "holy_site_types", "00_holy_site_types.txt")
LT = os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt")
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
    bar2c = {}
    for path, key, body in walk(lt):
        if not key.startswith("b_"):
            continue
        c = next((x for x in reversed(path) if x.startswith("c_")), None)
        if c:
            bar2c[key] = c
    c2bars = collections.defaultdict(list)
    for b, c in bar2c.items():
        c2bars[c].append(b)

    locm = load_loc(os.path.join(MOD, "localization", "simp_chinese"))
    locg = load_loc(os.path.join(GAME, "localization", "simp_chinese"))

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

    src = io.open(os.path.join(MOD, "gen_debug", "_apply_holy_site_knowledge_map.py"),
                  encoding="utf-8").read()
    done = set(re.findall(r'"([a-z0-9_\-]+)":\s*"b_', src))

    n_diff = 0
    for blk in blocks:
        key, c, b = blk["key"], blk["c"], blk["b"]
        if key in done or not c:
            continue
        sname = locm.get("holy_site_%s_name" % key) or locg.get("holy_site_%s_name" % key) or ""
        if not sname:
            continue
        print("### %s | %s | 当前 %s(%s)" % (key, sname, b, locm.get(b) or locg.get(b) or "?"))
        for cb in sorted(c2bars.get(c, [])):
            m1 = locm.get(cb) or ""
            m2 = locg.get(cb) or ""
            tag = ""
            if m2 and m1 != m2:
                tag = "  [CK原版: %s]" % m2
                n_diff += 1
            print("    %-26s %s%s" % (cb, m1 or "(无中文名)", tag))
    print("\n# CK原版名与mod名不同的男爵领条数：%d" % n_diff)


if __name__ == "__main__":
    main()
