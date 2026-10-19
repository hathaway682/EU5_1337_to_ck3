# -*- coding: utf-8 -*-
"""只读：1146 个「组级 language」文化里，有多少在 CK3 原版有同名文化，原版给它们什么 language。"""
import io, os, re

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game\in_game"
CK3 = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"

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
            c = text[j]
            if c == "{":
                d += 1
            elif c == "}":
                d -= 1
            j += 1
        out[m.group(1)] = text[m.end():j - 1]
        i = j
    return out


def field(body, k):
    m = re.search(r"(?m)^\s*" + k + r"\s*=\s*([a-z0-9_]+)", body)
    return m.group(1) if m else ""


# EU5 culture -> language
eu5 = {}
cd = os.path.join(EU5, "common", "cultures")
for fn in sorted(os.listdir(cd)):
    if fn.endswith(".txt"):
        for k, b in top_keys(rd(os.path.join(cd, fn))).items():
            if field(b, "language"):
                eu5[k] = field(b, "language")

# 原版 culture -> language
van = {}
sd = os.path.join(CK3, "common", "culture", "cultures")
for fn in sorted(os.listdir(sd)):
    if not fn.endswith(".txt"):
        continue
    for k, b in top_keys(rd(os.path.join(sd, fn))).items():
        if k.startswith(("b_", "c_", "d_", "k_", "e_")) or k == "gen_culture_unsettled":
            continue
        van[k] = (field(b, "language"), field(b, "heritage"))

# 我们 culture -> language 行
ours = {}
for k, b in top_keys(rd(os.path.join(MOD, "common", "culture", "cultures",
                                    "00_generated_cultures.txt"))).items():
    ours[k] = field(b, "language")

lost = [c for c, v in ours.items()
        if v.startswith("eu5_heritage_") and eu5.get(c)]

print("组级 language 且有 EU5 language: %d" % len(lost))
same = [c for c in lost if c in van]
print("其中 CK3 原版有同名文化: %d" % len(same))
print()
print("%-30s %-26s %-24s %s" % ("culture", "EU5 language", "原版 language", "一致?"))
diff = 0
for c in sorted(same):
    vl, vh = van[c]
    el = eu5[c]
    ok = ""
    # 粗判：EU5 语言名是否与原版 language 键有词根重合
    root = el.replace("_language", "").replace("_dialect", "")
    if vl and (root in vl or vl.replace("language_", "") in root):
        ok = "~同源"
    elif vl:
        ok = "不同"
        diff += 1
    print("%-30s %-26s %-24s %s" % (c, el, vl or "-", ok))
print()
print("原版 language 与 EU5 语言明显不是一系的: %d" % diff)
