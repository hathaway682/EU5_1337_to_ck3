# -*- coding: utf-8 -*-
"""导出 CK3 原版全部文化的 gfx 四件套，供挑区域组合用。只读。"""
import io, os, re

CK3 = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"
OUT = os.path.join(r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape",
                   "gen_debug", "_vanilla_gfx_quads.txt")
BLOCK = re.compile(r"([A-Za-z0-9_]+)\s*=\s*\{")


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


def walk(text, path=()):
    i, n = 0, len(text)
    while i < n:
        m = BLOCK.search(text, i)
        if not m:
            return
        j, d = m.end(), 1
        while j < n and d:
            c = text[j]
            if c == "{":
                d += 1
            elif c == "}":
                d -= 1
            j += 1
        body = text[m.end():j - 1]
        yield path, m.group(1), body
        yield from walk(body, path + (m.group(1),))
        i = j


KEYS = ("coa_gfx", "building_gfx", "clothing_gfx", "unit_gfx")


def quad(b):
    if not all(re.search(k + r"\s*=\s*\{", b) for k in KEYS):
        return None
    out = []
    for k in KEYS:
        m = re.search(k + r"\s*=\s*\{([^}]*)\}", b)
        out.append(" ".join(m.group(1).split()))
    return out


rows = []
for fn in sorted(os.listdir(os.path.join(CK3, "common", "culture", "cultures"))):
    if not fn.endswith(".txt"):
        continue
    for path, key, body in walk(read(os.path.join(CK3, "common", "culture", "cultures", fn))):
        if path:
            continue
        q = quad(body)
        if q:
            rows.append((key, q))

with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
    for k, q in sorted(rows):
        f.write("%-24s | %s\n" % (k, " ; ".join(q)))
print("vanilla cultures with quad: %d" % len(rows))
print("out: %s" % OUT)
