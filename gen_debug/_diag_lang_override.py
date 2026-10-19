# -*- coding: utf-8 -*-
"""诊断：LANG_OVERRIDE 里的语言在我们文化中的命中情况。只读。"""
import io, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _restore_eu5_heritage import LANG_OVERRIDE, CULT_OVERRIDE, walk, read, EU5, MOD

SRC = os.path.join(MOD, "common", "culture", "cultures", "00_generated_cultures.txt")
eu5_lang, eu5_grp = {}, {}
for fn in os.listdir(os.path.join(EU5, "common", "cultures")):
    if not fn.endswith(".txt"):
        continue
    for path, key, body in walk(read(os.path.join(EU5, "common", "cultures", fn))):
        if path:
            continue
        lg = re.search(r"(?m)^\s*language\s*=\s*(\S+)", body)
        gr = re.search(r"(?ms)^\s*culture_groups\s*=\s*\{(.*?)\}", body)
        if lg:
            eu5_lang[key] = lg.group(1)
        if gr:
            eu5_grp[key] = gr.group(1).split()

ours = [key for path, key, body in walk(read(SRC)) if not path]
print("our cultures: %d" % len(ours))
hits = 0
miss = []
for c in ours:
    lg = eu5_lang.get(c, "")
    if c in CULT_OVERRIDE:
        hits += 1
        print("CULT  %-24s %s" % (c, CULT_OVERRIDE[c]))
    elif lg in LANG_OVERRIDE:
        hits += 1
        print("LANG  %-24s %-24s -> %-22s | %s" % (c, lg, LANG_OVERRIDE[lg], ";".join(eu5_grp.get(c, []))))
print("total hits: %d" % hits)
# 反向：我们文化里出现的、属于 overridden 语言但没进 hits 的
for lg in sorted(LANG_OVERRIDE):
    cs = [c for c in ours if eu5_lang.get(c) == lg]
    if cs:
        print("lang %-26s cultures=%d %s" % (lg, len(cs), " ".join(cs)))
