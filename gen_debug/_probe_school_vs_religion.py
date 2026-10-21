# -*- coding: utf-8 -*-
"""只读：国家宗教（religion_definition）与宗教学校（religious_school）不一致的 tag。

数据源：
  EU5/in_game/setup/countries/*.txt          -> TAG.religion_definition
  EU5/main_menu/setup/start/10_countries.txt -> TAG.religious_school / sharia_law
"""
import io, os, re, glob
from collections import Counter, defaultdict

EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"
CDIR = os.path.join(EU5, "in_game", "setup", "countries")
TEN = os.path.join(EU5, "main_menu", "setup", "start", "10_countries.txt")

SUNNI_LEGAL = {"shafii", "maliki", "hanafi", "hanbali"}
SUNNI_THEO = {"maturidi", "ashari"}
SHIA = {"ismaili", "zaidi", "jafari", "imamiya", "safavid"}
IBADI = {"ibadi"}
SUFI = {"mevlevi", "chishti", "shadhili", "qadiri", "naqshbandi", "bektashi", "alevism"}


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


def top_blocks(text):
    out = []
    for m in re.finditer(r"(?m)^[ \t]*([A-Za-z0-9_]+)\s*=\s*\{", text):
        i = m.end() - 1
        d = 0
        for j in range(i, len(text)):
            if text[j] == "{":
                d += 1
            elif text[j] == "}":
                d -= 1
                if d == 0:
                    break
        out.append((m.group(1), text[m.end():j]))
    return out


tag_rel = {}
for p in sorted(glob.glob(os.path.join(CDIR, "*.txt"))):
    for tag, body in top_blocks(read(p)):
        m = re.search(r"(?m)^\s*religion_definition\s*=\s*([a-z0-9_]+)", body)
        if m:
            tag_rel[tag] = m.group(1)

t = read(TEN)
tag_school, tag_law = {}, {}
for m in re.finditer(r"(?m)^\t([A-Z0-9]{2,4})\s*=\s*\{", t):
    tag = m.group(1)
    i = m.end() - 1
    d = 0
    for j in range(i, len(t)):
        if t[j] == "{":
            d += 1
        elif t[j] == "}":
            d -= 1
            if d == 0:
                break
    b = t[i:j]
    s = re.search(r"(?m)^\s*religious_school\s*=\s*([a-z0-9_]+)", b)
    l = re.search(r"(?m)^\s*sharia_law\s*=\s*([a-z0-9_]+)", b)
    if s:
        tag_school[tag] = s.group(1)
    if l:
        tag_law[tag] = l.group(1)


def fam(school):
    if not school:
        return None
    base = school[:-7] if school.endswith("_school") else school
    if base in SUNNI_LEGAL:
        return "sunni_legal"
    if base in SUNNI_THEO:
        return "sunni_theo"
    if base in SHIA:
        return "shia"
    if base in IBADI:
        return "ibadi"
    if base in SUFI:
        return "sufi"
    return "other"


print("有 religion_definition 的 tag: %d" % len(tag_rel))
print("有 religious_school 的 tag: %d" % len(tag_school))
print()

# 1) 什叶国家全表
shia_tags = sorted([tg for tg, r in tag_rel.items() if r == "shia"])
print("★ religion_definition = shia 的国家共 %d 个，其 religious_school：" % len(shia_tags))
for tg in shia_tags:
    print("   %-6s school=%-18s law=%-16s  %s"
          % (tg, tag_school.get(tg, "(无)"), tag_law.get(tg, "(无)"), fam(tag_school.get(tg))))
print()

# 2) 全库不一致
mismatch = defaultdict(list)
for tg, rel in tag_rel.items():
    s = tag_school.get(tg)
    f = fam(s)
    if f is None:
        continue
    if rel == "shia" and f in ("sunni_legal", "sunni_theo"):
        mismatch["shia国家 + 逊尼学派"].append((tg, rel, s))
    elif rel == "sunni" and f == "shia":
        mismatch["sunni国家 + 什叶学派"].append((tg, rel, s))
    elif rel == "sunni" and f == "ibadi":
        mismatch["sunni国家 + 伊巴德学派"].append((tg, rel, s))
    elif rel in ("ibadi",) and f == "sunni_legal":
        mismatch["ibadi国家 + 逊尼学派"].append((tg, rel, s))
    elif rel not in ("sunni", "shia", "ibadi") and f in ("sunni_legal", "sunni_theo", "shia", "ibadi"):
        mismatch["非穆斯林国家 + 伊斯兰学派"].append((tg, rel, s))

print("★ 宗教与学派明显冲突的组合：")
for k in ("shia国家 + 逊尼学派", "sunni国家 + 什叶学派", "sunni国家 + 伊巴德学派",
          "ibadi国家 + 逊尼学派", "非穆斯林国家 + 伊斯兰学派"):
    v = mismatch.get(k, [])
    print("   %-24s %d 个" % (k, len(v)))
    for tg, rel, s in v[:40]:
        print("       %-6s %-18s %s" % (tg, rel, s))
print()

# 3) 国家宗教分布
print("国家宗教分布（前 20）：")
for r, n in Counter(tag_rel.values()).most_common(20):
    print("   %-24s %d" % (r, n))
