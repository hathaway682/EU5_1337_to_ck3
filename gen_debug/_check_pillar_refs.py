# -*- coding: utf-8 -*-
"""校验：culture 定义里所有 heritage / language 值是否都有定义（CK3 原版 + 本 mod pillars）。"""
import io, os, re
from collections import Counter

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
CK3 = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"
OUT = os.path.join(MOD, "gen_debug", "_pillar_ref_check.log")
BLOCK = re.compile(r"([A-Za-z0-9_]+)\s*=\s*\{")


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


def keys_of(path):
    out = set()
    t = read(path)
    for m in re.finditer(r"(?m)^([a-z0-9_]+)\s*=\s*\{", t):
        out.add(m.group(1))
    return out


her_def = keys_of(os.path.join(CK3, "common", "culture", "pillars", "00_heritage.txt"))
lang_def = keys_of(os.path.join(CK3, "common", "culture", "pillars", "00_language.txt"))
her_def |= keys_of(os.path.join(MOD, "common", "culture", "pillars", "00_generated_pillars.txt"))
lang_def |= keys_of(os.path.join(MOD, "common", "culture", "pillars", "00_generated_pillars.txt"))

t = read(os.path.join(MOD, "common", "culture", "cultures", "00_generated_cultures.txt"))
hers = Counter(re.findall(r"(?m)^\s*heritage\s*=\s*(\S+)", t))
langs = Counter(re.findall(r"(?m)^\s*language\s*=\s*(\S+)", t))

bad_h = {k: v for k, v in hers.items() if k not in her_def}
bad_l = {k: v for k, v in langs.items() if k not in lang_def}

L = []
L.append("heritage 值 %d 种，未定义 %d 种" % (len(hers), len(bad_h)))
for k, v in sorted(bad_h.items(), key=lambda kv: -kv[1]):
    L.append("  MISSING %-40s x%d" % (k, v))
L.append("language 值 %d 种，未定义 %d 种" % (len(langs), len(bad_l)))
for k, v in sorted(bad_l.items(), key=lambda kv: -kv[1]):
    L.append("  MISSING %-40s x%d" % (k, v))
io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L))
print("ok")
