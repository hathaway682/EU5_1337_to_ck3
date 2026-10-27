# -*- coding: utf-8 -*-
"""只读：我们的 language_occitano_romance 文化，各自 EU5 语言 / 组 / 当前传承。"""
import io, os, re

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game\in_game"
CULT = os.path.join(MOD, "common", "culture", "cultures", "00_generated_cultures.txt")

DEF = re.compile(r"(?ms)^\t?([a-z0-9_]+)\s*=\s*\{")


def rd(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


def top_keys(text):
    out, i, n = {}, 0, len(text)
    while i < n:
        m = DEF.search(text, i)
        if not m:
            break
        j, d = m.end(), 1
        while j < n and d:
            if text[j] == "{":
                d += 1
            elif text[j] == "}":
                d -= 1
            j += 1
        out[m.group(1)] = text[m.end():j - 1]
        i = j
    return out


def f(b, k):
    m = re.search(r"(?m)^\s*" + k + r"\s*=\s*([a-z0-9_]+)", b)
    return m.group(1) if m else ""


eu5 = {}
cd = os.path.join(EU5, "common", "cultures")
for fn in sorted(os.listdir(cd)):
    if fn.endswith(".txt"):
        for k, b in top_keys(rd(os.path.join(cd, fn))).items():
            g = re.search(r"(?ms)^\s*culture_groups\s*=\s*\{(.*?)\}", b)
            eu5[k] = (f(b, "language"), g.group(1).split() if g else [])

ours = {k: b for k, b in top_keys(rd(CULT)).items()}

print("== 我们 language = language_occitano_romance 的文化 ==")
print("%-16s %-22s %-22s %-26s %s" % ("culture", "EU5 language", "EU5 groups", "heritage", "our language"))
for k in sorted(ours):
    if f(ours[k], "language") != "language_occitano_romance":
        continue
    lg, gs = eu5.get(k, ("?", []))
    print("%-16s %-22s %-22s %-26s %s"
          % (k, lg, ",".join(gs), f(ours[k], "heritage"), f(ours[k], "language")))

print()
print("== 全 mod heritage_iberian 文化的 EU5 语言 ==")
for k in sorted(ours):
    if f(ours[k], "heritage") != "heritage_iberian":
        continue
    lg, gs = eu5.get(k, ("?", []))
    print("  %-16s EU5 lang %-22s groups %-40s our lang %s"
          % (k, lg, ",".join(gs), f(ours[k], "language")))
