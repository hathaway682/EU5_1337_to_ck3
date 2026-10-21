# -*- coding: utf-8 -*-
"""只读统计：EU5 里「执政者宗教 != 所属国家宗教」的情况有多少。

数据源：
  - 国家宗教：in_game/setup/countries/*.txt 的 `religion_definition = X`
  - 角色宗教/归属：main_menu/setup/start/05_characters.txt 的 `religion = X` + `tag = TAG`
"""
import io, os, re, glob
from collections import Counter, defaultdict

EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"
CDIR = os.path.join(EU5, "in_game", "setup", "countries")
CHARS = os.path.join(EU5, "main_menu", "setup", "start", "05_characters.txt")


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


def blocks(text):
    """顶层 `key = { ... }` -> (key, body)。按大括号深度切。"""
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


# ---- 1) 国家宗教 ----
tag_rel = {}
dup = defaultdict(set)
for p in sorted(glob.glob(os.path.join(CDIR, "*.txt"))):
    for tag, body in blocks(read(p)):
        m = re.search(r"(?m)^\s*religion_definition\s*=\s*([a-z0-9_]+)", body)
        if not m:
            continue
        if tag in tag_rel and tag_rel[tag] != m.group(1):
            dup[tag].add(tag_rel[tag])
            dup[tag].add(m.group(1))
        tag_rel[tag] = m.group(1)

# ---- 2) 角色 ----
chars = []
for name, body in blocks(read(CHARS)):
    if "religion" not in body:
        continue
    r = re.search(r"(?m)^\s*religion\s*=\s*([a-z0-9_]+)", body)
    t = re.search(r"(?m)^\s*tag\s*=\s*([A-Z0-9]{2,4})", body)
    c = re.search(r"(?m)^\s*culture\s*=\s*([a-z0-9_]+)", body)
    if not r:
        continue
    chars.append({"name": name,
                  "religion": r.group(1),
                  "tag": t.group(1) if t else None,
                  "culture": c.group(1) if c else None})

with_tag = [c for c in chars if c["tag"]]
known = [c for c in with_tag if c["tag"] in tag_rel]
unknown_tag = [c for c in with_tag if c["tag"] not in tag_rel]

mism = [c for c in known if c["religion"] != tag_rel[c["tag"]]]

print("国家定义: %d 个 tag 有 religion_definition%s"
      % (len(tag_rel), ("（%d 个 tag 定义冲突）" % len(dup)) if dup else ""))
print("EU5 角色总数: %d（带 tag 的 %d，其中 tag 有宗教定义的 %d，无定义的 %d）"
      % (len(chars), len(with_tag), len(known), len(unknown_tag)))
print()
print("★ 执政者宗教 != 国家宗教: %d 人（占带 tag 角色的 %.1f%%）"
      % (len(mism), 100.0 * len(mism) / max(1, len(known))))
print()

print("按「角色宗教 -> 国家宗教」分组：")
for (a, b), n in Counter((c["religion"], tag_rel[c["tag"]]) for c in mism).most_common(30):
    print("   %-24s -> %-24s %d" % (a, b, n))
print()

print("按 tag 分组（前 30）：")
for t, n in Counter(c["tag"] for c in mism).most_common(30):
    rels = Counter(c["religion"] for c in mism if c["tag"] == t)
    print("   %-6s 国家=%-18s 不一致 %2d 人  %s"
          % (t, tag_rel[t], n, dict(rels)))
print()

print("样例（前 25 人）：")
for c in mism[:25]:
    print("   %-46s tag=%-5s 角色=%-18s 国家=%s"
          % (c["name"], c["tag"], c["religion"], tag_rel[c["tag"]]))

if unknown_tag:
    print()
    print("tag 无 religion_definition 的（前 15）：")
    for t, n in Counter(c["tag"] for c in unknown_tag).most_common(15):
        print("   %-6s %d 人" % (t, n))

# ---- 落一份 CSV 备查 ----
import csv
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_cross_religion_rulers.csv")
with io.open(OUT, "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["character", "tag", "country_religion", "char_religion", "culture"])
    for c in sorted(mism, key=lambda x: (x["tag"], x["name"])):
        w.writerow([c["name"], c["tag"], tag_rel[c["tag"]], c["religion"], c["culture"] or ""])
print()
print("明细 -> %s" % OUT)
