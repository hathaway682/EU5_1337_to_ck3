# -*- coding: utf-8 -*-
"""只读补查：哪些 province 既没有 rite 行、faith 本身也没有 main_rite（会落空）。"""
import io, os, re
from collections import Counter

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
REL = os.path.join(MOD, "common/religion")
SRC = os.path.join(MOD, "history/provinces/00_generated_provinces.txt")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_verify_gap.out")


def blocks(text):
    out = {}
    for m in re.finditer(r"(?m)^([A-Za-z0-9_\-]+)\s*=\s*\{", text):
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


d = os.path.join(REL, "faith_types")
ftxt = "\n".join(io.open(os.path.join(d, fn), encoding="utf-8-sig", errors="ignore").read()
                 for fn in sorted(os.listdir(d)) if fn.endswith(".txt"))
faith_main = {}
for k, b in blocks(ftxt).items():
    m = re.search(r"(?m)^\s*main_rite\s*=\s*([A-Za-z0-9_]+)", b)
    faith_main[k] = m.group(1) if m else None

txt = io.open(SRC, encoding="utf-8-sig", newline="").read()
prov = {}
for m in re.finditer(r"(?m)^(\d+) = \{(.*?)\n\}", txt, re.S):
    body = m.group(2)
    f = re.search(r"(?m)^\s*faith\s*=\s*(\S+)", body)
    r = re.search(r"(?m)^\s*rite\s*=\s*(\S+)", body)
    prov[int(m.group(1))] = (f.group(1) if f else None, r.group(1) if r else None)

L = []
gap = [(p, f) for p, (f, r) in prov.items() if not r and f and not faith_main.get(f)]
L.append("既无 rite 行、faith 又无 main_rite 的 province: %d" % len(gap))
L.append("   按 faith: %s" % dict(Counter(f for _, f in gap).most_common(20)))

# 未知 faith
unk = [(p, f) for p, (f, r) in prov.items() if f and f not in faith_main]
L.append("faith 键在 faith_types 里找不到的: %d %s" % (len(unk), unk[:5]))

# 伊斯兰各派里没 rite 的（可接受，但看规模）
for tgt in ("sunni", "shia", "kharijite"):
    ps = [p for p, (f, r) in prov.items() if f == tgt]
    no = [p for p in ps if not prov[p][1]]
    L.append("%-10s province %d，其中无 rite %d" % (tgt, len(ps), len(no)))

io.open(OUT, "w", encoding="utf-8-sig", newline="\n").write("\n".join(L))
