# -*- coding: utf-8 -*-
"""只读探查：c_chelm（西沃里尼亚）与 c_kufa（库法）的 faith/rite 及 EU5 来源。"""
import io, os, re, json
from collections import Counter

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
GEN = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_probe_chelm_kufa.out")
L = []

# ---- landed_titles: county -> [(barony, province)] ----
c2b = {}
for fn in sorted(os.listdir(os.path.join(MOD, "common/landed_titles"))):
    if not fn.endswith(".txt"):
        continue
    cur_c = None
    cur_b = None
    for line in io.open(os.path.join(MOD, "common/landed_titles", fn),
                        encoding="utf-8-sig", errors="ignore"):
        m = re.match(r"^(\t*)(c_[A-Za-z0-9_\-]+)\s*=\s*\{", line)
        if m:
            cur_c = m.group(2)
            continue
        m = re.match(r"^(\t*)(b_[A-Za-z0-9_\-]+)\s*=\s*\{", line)
        if m:
            cur_b = m.group(2)
            continue
        pm = re.match(r"^\s*province\s*=\s*(\d+)", line)
        if pm and cur_c and cur_b:
            c2b.setdefault(cur_c, []).append((cur_b, int(pm.group(1))))
            cur_b = None

hist = io.open(os.path.join(MOD, "history/provinces/00_generated_provinces.txt"),
               encoding="utf-8-sig").read()
prov = {}
for mm in re.finditer(r"(?m)^(\d+) = \{(.*?)\n\}", hist, re.S):
    body = mm.group(2)
    f = re.search(r"(?m)^\s*faith\s*=\s*(\S+)", body)
    r = re.search(r"(?m)^\s*rite\s*=\s*(\S+)", body)
    prov[int(mm.group(1))] = (f.group(1) if f else None, r.group(1) if r else None)

pol = json.load(io.open(os.path.join(GEN, "eu5_politics.json"), encoding="utf-8"))
cty = pol["counties"]
pe = json.load(io.open(os.path.join(GEN, "eu5_peoples.json"), encoding="utf-8"))
cr = pe["county_religion"]

for target in ("c_chelm", "c_kufa"):
    L.append("=" * 60)
    L.append("%s  owner=%s  eu5_religion=%s" % (target, cty.get(target, {}).get("owner"), cr.get(target)))
    for b, p in c2b.get(target, []):
        L.append("   %-20s p%-6d faith=%-14s rite=%s" % (b, p, prov.get(p, (None, None))[0], prov.get(p, (None, None))[1]))

# ---- EU5 country school / sharia / liturgical ----
def blocks(text):
    out = {}
    for m in re.finditer(r"(?m)^\t([A-Z][A-Z0-9_]{1,6})\s*=\s*\{", text):
        k = m.group(1); i = m.end() - 1; d = 0
        for j in range(i, len(text)):
            if text[j] == "{":
                d += 1
            elif text[j] == "}":
                d -= 1
                if d == 0:
                    out[k] = text[i:j + 1]
                    break
    return out

t = io.open(os.path.join(EU5, "main_menu/setup/start/10_countries.txt"),
            encoding="utf-8-sig", errors="ignore").read()
B = blocks(t)
tags = set()
for target in ("c_chelm", "c_kufa"):
    if cty.get(target, {}).get("owner"):
        tags.add(cty[target]["owner"])
L.append("")
L.append("相关 EU5 国家的字段:")
for tag in sorted(tags):
    b = B.get(tag, "")
    d = {}
    for k in ("religious_school", "sharia_law", "liturgical_language", "religion", "capital"):
        m = re.search(r"(?m)^\s*%s\s*=\s*([a-z0-9_]+)" % k, b)
        if m:
            d[k] = m.group(1)
    L.append("   %-5s %s" % (tag, d))

# ---- c_kufa 周边县（谁给了 zayidi）----
L.append("")
L.append("伊拉克/希拉一带的县与 rite:")
for c, info in cty.items():
    if info.get("owner") in ("HLL", "LCK", "YEM", "QHT", "YAM", "GRG"):
        ps = c2b.get(c, [])
        if ps:
            L.append("   %-24s owner=%-4s eu5rel=%-8s %s" % (
                c, info.get("owner"), cr.get(c),
                " ".join("%s/%s" % (prov.get(p, (None, None))[0], prov.get(p, (None, None))[1]) for _, p in ps)))

io.open(OUT, "w", encoding="utf-8-sig", newline="\n").write("\n".join(L))
