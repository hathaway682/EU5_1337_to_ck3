# -*- coding: utf-8 -*-
"""查无原版对应区域（美洲/澳洲/太平洋/科伊桑/西伯利亚）的文化带哪些 tag。只读。"""
import io, os, re
from collections import defaultdict

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game\in_game"
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
        yield path, m.group(1), text[m.end():j - 1]
        yield from walk(text[m.end():j - 1], path + (m.group(1),))
        i = j


eu5 = {}
for fn in sorted(os.listdir(os.path.join(EU5, "common", "cultures"))):
    if not fn.endswith(".txt"):
        continue
    for path, key, body in walk(read(os.path.join(EU5, "common", "cultures", fn))):
        if path:
            continue
        tg = re.search(r"(?m)^\s*tags\s*=\s*\{([^}]*)\}", body)
        gr = re.search(r"(?ms)^\s*culture_groups\s*=\s*\{(.*?)\}", body)
        eu5[key] = (set(tg.group(1).split()) if tg else set(),
                    set(gr.group(1).split()) if gr else set())

SRC = os.path.join(MOD, "common", "culture", "cultures", "00_generated_cultures.txt")
ours = [key for path, key, body in walk(read(SRC)) if not path]

# 按组聚合 tag
grp_tags = defaultdict(lambda: defaultdict(int))
grp_n = defaultdict(int)
for c in ours:
    e = eu5.get(c)
    if not e:
        continue
    tags, grps = e
    for g in grps:
        grp_n[g] += 1
        for t in tags:
            grp_tags[g][t] += 1

for g in sorted(grp_n, key=lambda x: grp_n[x]):
    print("%-28s n=%-3d %s" % (g, grp_n[g],
          " ".join("%s:%d" % kv for kv in sorted(grp_tags[g].items(), key=lambda x: -x[1])[:6])))
