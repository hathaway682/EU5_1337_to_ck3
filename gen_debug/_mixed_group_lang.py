# -*- coding: utf-8 -*-
"""查 celtic/indian/german 等混合组里，我们各文化的 EU5 language，判断能不能按语言拆 heritage。只读。"""
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
        lg = re.search(r"(?m)^\s*language\s*=\s*(\S+)", body)
        gr = re.search(r"(?ms)^\s*culture_groups\s*=\s*\{(.*?)\}", body)
        tg = re.search(r"(?m)^\s*tags\s*=\s*\{([^}]*)\}", body)
        eu5[key] = {
            "language": lg.group(1) if lg else "",
            "groups": set(gr.group(1).split()) if gr else set(),
            "tags": set(tg.group(1).split()) if tg else set(),
        }

ours = [key for path, key, body in walk(read(os.path.join(MOD, "common", "culture", "cultures", "00_generated_cultures.txt")))
        if not path]

for grp in ("celtic_group", "indian_group", "german_group", "british_group"):
    rows = [(k, eu5[k]["language"]) for k in ours if grp in eu5.get(k, {}).get("groups", set())]
    by_lang = defaultdict(list)
    for k, lg in rows:
        by_lang[lg].append(k)
    print("== %s (%d cultures) ==" % (grp, len(rows)))
    for lg, ks in sorted(by_lang.items(), key=lambda x: -len(x[1])):
        print("   %-28s %3d  %s" % (lg, len(ks), " ".join(sorted(ks)[:8])))
    print()
