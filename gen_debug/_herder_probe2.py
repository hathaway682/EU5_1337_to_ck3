# -*- coding: utf-8 -*-
"""只读盘点 2：herder 国家的统治者、县、首府地产、跨文件引用。"""
import json, os, re, collections

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
EXPORT = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"

d = json.load(open(os.path.join(EXPORT, "eu5_politics.json"), encoding="utf-8"))
cs, cts = d["countries"], d["counties"]
herd = {t for t, v in cs.items() if v.get("government") == "herder"}
herd_cts = {c: v for c, v in cts.items() if v.get("owner") in herd}

with_ruler = {t: cs[t]["ruler"] for t in herd if cs[t].get("ruler")}
print("herder tag 总数:", len(herd))
print("有真实 ruler 的 herder:", len(with_ruler))
print("无 ruler（用 eu5_regent_）:", len(herd) - len(with_ruler))

# 这些 ruler 是否也统治非 herder 国家
ruler_count = collections.Counter(v.get("ruler") for v in cs.values() if v.get("ruler"))
shared = {r: ruler_count[r] for r in with_ruler.values() if ruler_count[r] > 1}
print("统治多个国家的 herder ruler:", len(shared), list(shared.items())[:10])

# 603 县的 holder 来源
hold_kind = collections.Counter()
for c, v in herd_cts.items():
    r = v.get("ruler")
    if not r:
        hold_kind["no_ruler"] += 1
    elif r.startswith("eu5_regent_"):
        hold_kind["eu5_regent"] += 1
    else:
        hold_kind["real"] += 1
print("603 县 holder 类型:", dict(hold_kind))

# 这些县在 provinces 文件里首府地产
prov = open(os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt"), encoding="utf-8-sig", errors="ignore").read()
# 每县首府 location：从 definitions 取（province -> first location）
GAME = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"
BLOCK = re.compile(r"([A-Za-z0-9_]+)\s*=\s*\{")
def walk_blocks(text, path=()):
    i, n = 0, len(text)
    while i < n:
        m = BLOCK.search(text, i)
        if not m:
            return
        j, depth = m.end(), 1
        while j < n and depth:
            ch = text[j]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
            j += 1
        body = text[m.end():j - 1]
        yield path, m.group(1), body
        yield from walk_blocks(body, path + (m.group(1),))
        i = j
defs = re.sub(r"#[^\n]*", "", open(os.path.join(GAME, "in_game", "map_data", "definitions.txt"), encoding="utf-8", errors="ignore").read())
prov_cap, MANCHU = {}, set()
for path, key, body in walk_blocks(defs):
    if not key.endswith("_province"):
        continue
    first = body.split()
    if first:
        prov_cap["c_" + key[: -len("_province")]] = first[0]
    if "manchuria_region" in path and "liaodong_area" not in path:
        MANCHU.add("c_" + key[: -len("_province")])

in_m = [c for c in herd_cts if c in MANCHU]
print("外东北 herder 县:", len(in_m), "| 其余:", len(herd_cts) - len(in_m))
print("外东北县首府:", [(c, prov_cap.get(c)) for c in sorted(in_m)])
