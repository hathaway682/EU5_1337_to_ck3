# -*- coding: utf-8 -*-
"""只读：检查 history/characters 里的 rite 是否与角色 faith 自洽（不在本次重算范围内）。"""
import io, os, re
from collections import Counter

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
REL = os.path.join(MOD, "common/religion")
CH = os.path.join(MOD, "history/characters")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_char_rite_check.out")


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


def read_dir(sub):
    d = os.path.join(REL, sub)
    return "\n".join(io.open(os.path.join(d, fn), encoding="utf-8-sig", errors="ignore").read()
                     for fn in sorted(os.listdir(d)) if fn.endswith(".txt"))


rite_family = {}
for k, b in blocks(read_dir("rite_types")).items():
    m = re.search(r"(?m)^\s*faith\s*=\s*([A-Za-z0-9_]+)", b)
    if m:
        rite_family[k] = m.group(1)
faith_origin = {}
for k, b in blocks(read_dir("faith_types")).items():
    m = re.search(r"(?m)^\s*origin\s*=\s*([A-Za-z0-9_]+)", b)
    if m:
        faith_origin[k] = m.group(1)

L = []
tot = 0
bad = Counter()
files = []
for fn in sorted(os.listdir(CH)):
    if not fn.endswith(".txt"):
        continue
    p = os.path.join(CH, fn)
    txt = io.open(p, encoding="utf-8-sig", errors="ignore").read()
    if "rite = " not in txt:
        continue
    files.append((fn, len(re.findall(r"(?m)^\s*rite = ", txt))))
    for m in re.finditer(r"(?m)^(\d+)\s*=\s*\{(.*?)^\}", txt, re.S):
        body = m.group(2)
        f = re.search(r"(?m)^\s*faith\s*=\s*(\S+)", body)
        r = re.search(r"(?m)^\s*rite\s*=\s*(\S+)", body)
        if not r:
            continue
        tot += 1
        if not f:
            bad[("(无 faith)", r.group(1))] += 1
            continue
        fam = faith_origin.get(f.group(1), f.group(1))
        if rite_family.get(r.group(1)) != fam:
            bad[(f.group(1), r.group(1))] += 1

L.append("带 rite 的角色文件: %s" % files)
L.append("角色 rite 总数: %d" % tot)
L.append("与 faith 家族不匹配: %d" % sum(bad.values()))
for (f, r), n in bad.most_common(15):
    L.append("   faith=%-24s rite=%-18s %d" % (f, r, n))

io.open(OUT, "w", encoding="utf-8-sig", newline="\n").write("\n".join(L))
