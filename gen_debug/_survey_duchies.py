"""Read-only survey: what the three duchy rules would hand out.

Mirrors the pipeline's own state: herder countries are dropped (their ground is
wilderness, except the 17 Manchu counties that go back to CHI), and the de jure
duchy table comes from 00_landed_titles.txt.
"""
import collections
import io
import json
import re

MOD = "D:/Documents/Paradox Interactive/Crusader Kings III/mod/EU5_Modern_Borders_noshape"
EXPORT = "D:/Documents/Paradox Interactive/Crusader Kings III/mod/Global_modern_map/eu5_export"

# de jure duchies -> counties
lines = io.open(MOD + "/common/landed_titles/00_landed_titles.txt",
                encoding="utf-8-sig", errors="replace").read().split("\n")
stack = []
D = collections.OrderedDict()
for n, l in enumerate(lines, 1):
    m = re.match(r"^(\t*)([a-z]_[a-z0-9_]+)\s*=\s*\{", l)
    if not m:
        continue
    depth, key = len(m.group(1)), m.group(2)
    stack = [x for x in stack if x[0] < depth]
    stack.append((depth, key, n))
    if key.startswith("d_"):
        D.setdefault(key, [])
    elif key.startswith("c_"):
        for x in reversed(stack[:-1]):
            if x[1].startswith("d_"):
                D.setdefault(x[1], []).append(key)
                break

# names
zh, en = {}, {}
for p, tgt in ((MOD + "/localization/simp_chinese/eu5_titles_l_simp_chinese.yml", zh),
               (MOD + "/localization/english/eu5_titles_l_english.yml", en)):
    t = io.open(p, encoding="utf-8-sig", errors="replace").read()
    for m in re.finditer(r'(?m)^\s*([dek]_[a-z0-9_]+):0 "([^"]*)"', t):
        tgt[m.group(1)] = m.group(2)

d = json.load(io.open(EXPORT + "/eu5_politics.json", encoding="utf-8"))
C = d["countries"]
co = {k: dict(v) for k, v in d["counties"].items()}

# herder removal, same shape as _herders.apply
herd = {t for t, c in C.items() if c.get("government") == "herder"}
for tag in herd:
    C.pop(tag, None)
for k, v in co.items():
    if v.get("owner") in herd:
        v["owner"] = None
        v["ruler"] = "gen_wilderness_holder"
print("herders dropped:", len(herd), "countries")

# de jure duchy -> controlling tag (strict majority)
county_duchy = {c: k for k, v in D.items() for c in v}
decl = io.open(MOD + "/common/landed_titles/zz_eu5_titular.txt", encoding="utf-8-sig").read()
eu5_seat = {}
for m in re.finditer(r"(?m)^([dek]_[a-z0-9_]+) = \{\r?\n\tcolor = \{ [\d ]+ \}\r?\n\tcapital = ([a-z0-9_]+)", decl):
    eu5_seat[m.group(1)] = m.group(2)
occupied = collections.defaultdict(list)
for k, c in eu5_seat.items():
    if k.startswith("d_") and c in county_duchy:
        occupied[county_duchy[c]].append(k)

same_zh = collections.defaultdict(list)
for t, c in C.items():
    if c.get("name_zh"):
        same_zh[c["name_zh"]].append(t)

majority = []
for k, cs in D.items():
    if not cs:
        continue
    own = collections.Counter(co.get(c, {}).get("owner") for c in cs)
    tag, n = own.most_common(1)[0]
    if tag and n * 2 > len(cs):
        majority.append((k, tag, n, len(cs)))

rule3 = [x for x in majority if x[0] not in occupied]
rule1, rule2, rule1_none = [], [], []
for k, tag, n, tot in majority:
    tz = same_zh.get(zh.get(k) or "", [])
    if tag not in tz:
        continue
    r = C[tag].get("rank")
    if r in ("c", "d"):
        rule1.append((k, tag, r, n, tot))
    elif r in ("k", "e"):
        rule2.append((k, tag, r, n, tot))
    else:
        rule1_none.append((k, tag, r, n, tot))

print()
print("strict-majority duchies:", len(majority))
print("  blocked by an EU5 ducal seat inside:", len(majority) - len(rule3))
print("  rule 3 candidates:", len(rule3))
print("  rule 1 (same name, c/d):", len(rule1))
print("  rule 2 (same name, k/e):", len(rule2))
print("  same name but rank None:", len(rule1_none), rule1_none)
print()
print("--- rule 1 ---")
for x in sorted(rule1):
    print("  %-24s %-6s rank=%s %d/%d" % x)
print("--- rule 2 ---")
for x in sorted(rule2):
    print("  %-24s %-6s rank=%s %d/%d" % x)
print()
print("--- rule 3 by tag (top) ---")
by = collections.Counter(x[1] for x in rule3)
for tag, n in by.most_common(25):
    print("  %-6s rank=%-4s %d duchies" % (tag, C[tag].get("rank"), n))
print("  ... total tags", len(by))
