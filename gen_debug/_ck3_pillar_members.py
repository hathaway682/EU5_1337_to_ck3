# -*- coding: utf-8 -*-
"""列出 CK3 原版每个 heritage / language 下挂了哪些文化，便于人工映射。"""
import io, os, re
from collections import defaultdict

CK3 = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"
OUT = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape\gen_debug\_ck3_heritage_members.log"
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


her = defaultdict(list)
lang = defaultdict(list)
d = os.path.join(CK3, "common", "culture", "cultures")
for fn in sorted(os.listdir(d)):
    if not fn.endswith(".txt"):
        continue
    for path, key, body in walk(read(os.path.join(d, fn))):
        if path:
            continue
        h = re.search(r"(?m)^\s*heritage\s*=\s*(\S+)", body)
        lg = re.search(r"(?m)^\s*language\s*=\s*(\S+)", body)
        if h:
            her[h.group(1)].append(key)
        if lg:
            lang[lg.group(1)].append(key)

L = []
L.append("== CK3 heritage -> cultures ==")
for h in sorted(her):
    L.append("%-32s (%2d) %s" % (h, len(her[h]), " ".join(sorted(her[h]))))
L.append("")
L.append("== CK3 language -> cultures ==")
for lg in sorted(lang):
    L.append("%-32s (%2d) %s" % (lg, len(lang[lg]), " ".join(sorted(lang[lg]))))
io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L))
print("ok")
