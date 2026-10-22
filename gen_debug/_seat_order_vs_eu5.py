# -*- coding: utf-8 -*-
"""哪些伯爵领的男爵领顺序和 EU5 数据（definitions / location id 序）不一样。

EU5 序：mapping.json 里该 county 的 location 按 id 升序（= definitions.txt 的出现序，
        第一个就是 EU5 自己给这个省的首府）。
mod 序：mod/common/landed_titles/*.txt 里 c_ 块内 b_ 块的实际书写顺序（CK3 只读第一个）。

产出 _seat_order_vs_eu5.json：逐县的 eu5 序 / mod 序 / 差异类别。
"""
import io, json, os, re, collections

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT = r"D:/Documents/Paradox Interactive/Crusader Kings III/mod/Global_modern_map/eu5_export"

# ---------- 1. EU5 序 ----------
mp = json.load(io.open(os.path.join(EXPORT, "mapping.json"), encoding="utf-8"))
eu5 = collections.defaultdict(list)
for loc in mp["locations"]:
    if loc.get("kind") == "land" or True:
        eu5[loc["county"]].append((loc["id"], loc["name"]))
for c in eu5:
    eu5[c].sort()
eu5 = {c: [n for _, n in v] for c, v in eu5.items()}

# ---------- 2. mod 序 ----------
RE_C = re.compile(r"^(\s*)c_([A-Za-z0-9_]+)\s*=\s*\{")
RE_B = re.compile(r"^(\s*)b_([A-Za-z0-9_]+)\s*=\s*\{")
LT = os.path.join(MOD, "common", "landed_titles")
mod = {}
for fn in sorted(os.listdir(LT)):
    if ".bak_" in fn or not fn.endswith(".txt"):
        continue
    path = os.path.join(LT, fn)
    lines = io.open(path, encoding="utf-8-sig", errors="replace").read().splitlines()
    n = len(lines)
    i = 0
    while i < n:
        m = RE_C.match(lines[i])
        if not m:
            i += 1
            continue
        county = m.group(2)
        depth = 0
        j = i
        while j < n:
            depth += lines[j].count("{") - lines[j].count("}")
            j += 1
            if depth == 0:
                break
        block = lines[i:j]
        bs = []
        bd = 0
        cur = None
        for k in range(1, len(block)):
            bm = RE_B.match(block[k])
            if bm and bd == 0:
                if cur is not None:
                    bs.append(cur)
                cur = bm.group(2)
            bd += block[k].count("{") - block[k].count("}")
            if cur is not None and bd == 0 and k > 0:
                bs.append(cur)
                cur = None
        if cur is not None:
            bs.append(cur)
        mod[county.lower()] = bs
        i = j

# ---------- 3. 规则 pick ----------
rs = json.load(io.open(os.path.join(EXPORT, "RANK_STATE.json"), encoding="utf-8"))
picks = {k[2:].lower(): v.lower() for k, v in rs["counties"].items()}

# ---------- 4. 对比 ----------
rows = []
only_mod = [c for c in mod if c not in eu5]
only_eu5 = [c for c in eu5 if c not in mod]
for c, morder in mod.items():
    eorder = eu5.get(c)
    if not eorder:
        continue
    # 大小写不敏感：mapping.json 里带国家标签的地点名是大写的（constantine_ALG），
    # 落到树上被写成 b_constantine_alg。
    mset = {x.lower() for x in morder}
    efiltered = [x for x in eorder if x.lower() in mset]
    mfirst_l = morder[0].lower() if morder else None
    efirst = efiltered[0] if efiltered else None
    efirst_l = efirst.lower() if efirst else None
    if efirst is None:
        cat = "eu5_seat_no_barony"      # EU5 首府地点没建男爵领
    elif efirst_l != mfirst_l:
        cat = "seat_moved"
    elif [x.lower() for x in efiltered] != [x.lower() for x in morder]:
        cat = "order_only"
    else:
        cat = "same"
    rows.append({
        "county": "c_" + c,
        "cat": cat,
        "eu5_order": eorder,
        "mod_order": morder,
        "eu5_seat": efirst,
        "mod_seat": morder[0] if morder else None,
        "rule_pick": picks.get(c),
        "dropped": [x for x in eorder if x.lower() not in mset],
        "added": [x for x in morder if x.lower() not in {y.lower() for y in eorder}],
    })

cnt = collections.Counter(r["cat"] for r in rows)
print("mod counties:", len(mod), "eu5 counties:", len(eu5))
print("only in mod:", len(only_mod), "only in eu5:", len(only_eu5))
print("cats:", dict(cnt))
print()
sm = [r for r in rows if r["cat"] == "seat_moved"]
print("seat_moved:", len(sm))
print("  其中规则 pick 一致（rank_state 规则动的）:",
      sum(1 for r in sm if r["rule_pick"] and r["mod_seat"] == r["rule_pick"]))
print("  规则没 pick 或 pick 与现状不符（手改/其他）:",
      sum(1 for r in sm if not (r["rule_pick"] and r["mod_seat"] == r["rule_pick"])))
print("order_only（顺序变了但首府没变）:", cnt.get("order_only", 0))
print("eu5_seat_no_barony:", cnt.get("eu5_seat_no_barony", 0))
print()
print("--- 规则没覆盖的 seat_moved ---")
for r in sm:
    if not (r["rule_pick"] and r["mod_seat"] == r["rule_pick"]):
        print("  %-28s eu5=%-22s mod=%-22s rule=%s" %
              (r["county"], r["eu5_seat"], r["mod_seat"], r["rule_pick"]))
print()
print("--- 规则 pick 了但现状不是它 ---")
for r in rows:
    if r["rule_pick"] and r["mod_seat"] != r["rule_pick"]:
        print("  %-28s eu5=%-22s mod=%-22s rule=%s" %
              (r["county"], r["eu5_seat"], r["mod_seat"], r["rule_pick"]))

out = os.path.join(MOD, "gen_debug", "_seat_order_vs_eu5.json")
json.dump({"rows": rows, "only_mod": only_mod, "only_eu5": only_eu5},
          io.open(out, "w", encoding="utf-8"), ensure_ascii=False)
print("\nwritten:", out)
