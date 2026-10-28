# -*- coding: utf-8 -*-
"""只读探查：EU5 type=pop（herder）国家在成品里占了哪些县，其中多少属于外东北（元的满洲）。"""
import json, re, collections, os

GAME = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"
EXPORT = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"

BLOCK = re.compile(r"([A-Za-z0-9_]+)\s*=\s*\{")


def walk_blocks(text, path=()):
    i, n = 0, len(text)
    while i < n:
        m = BLOCK.search(text, i)
        if not m:
            return
        j, depth = m.end(), 1
        while j < n and depth:
            c = text[j]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            j += 1
        body = text[m.end():j - 1]
        yield path, m.group(1), body
        yield from walk_blocks(body, path + (m.group(1),))
        i = j


defs = open(os.path.join(GAME, "in_game", "map_data", "definitions.txt"), encoding="utf-8", errors="ignore").read()
defs = re.sub(r"#[^\n]*", "", defs)
MANCHU = set()
for path, key, body in walk_blocks(defs):
    if not key.endswith("_province"):
        continue
    if "manchuria_region" in path and "liaodong_area" not in path:
        MANCHU.add("c_" + key[: -len("_province")])

d = json.load(open(os.path.join(EXPORT, "eu5_politics.json"), encoding="utf-8"))
cs, cts = d["countries"], d["counties"]
herd = {t for t, v in cs.items() if v.get("government") == "herder"}
herd_cts = {c: v for c, v in cts.items() if v.get("owner") in herd}

print("MANCHU_COUNTIES:", len(MANCHU))
print("herder tags:", len(herd), "| herder counties:", len(herd_cts))
in_m = {c: v for c, v in herd_cts.items() if c in MANCHU}
print("其中在外东北的县:", len(in_m), "涉及 herder:", len({v['owner'] for v in in_m.values()}))
print("外东北 herder 县样例:", sorted(in_m.items())[:15])
print("外东北之外 herder 县:", len(herd_cts) - len(in_m))
print("外东北范围内总县数:", len(MANCHU), "| 其中非 herder 占的:",
      len([c for c in MANCHU if c in cts and cts[c].get('owner') not in herd]))
print("外东北范围内 owner 分布:", collections.Counter(cts[c].get('owner') for c in MANCHU if c in cts).most_common(8))
