# -*- coding: utf-8 -*-
"""对账：列级块数 vs heritage/gfx 行数，找出没被计数的文化。只读。"""
import io, os, re

SRC = os.path.join(r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape",
                   "common", "culture", "cultures", "00_generated_cultures.txt")
t = io.open(SRC, encoding="utf-8-sig").read()
lines = t.split("\n")
blocks = [l for l in lines if re.match(r"^[a-z0-9_]+\s*=\s*\{\s*$", l)]
hers = [l for l in lines if re.match(r"^\s*heritage\s*=", l)]
gfx = [l for l in lines if re.match(r"^\s*[a-z_]+_gfx\s*=\s*\{", l)]
print("列级块: %d | heritage 行: %d | gfx 行: %d" % (len(blocks), len(hers), len(gfx)))
names = [re.match(r"^([a-z0-9_]+)", l).group(1) for l in blocks]
from collections import Counter
dup = {k: v for k, v in Counter(names).items() if v > 1}
print("重名块: %s" % dup)
# 没有 heritage 行的块
cur, noher = None, []
for l in lines:
    m = re.match(r"^([a-z0-9_]+)\s*=\s*\{\s*$", l)
    if m:
        if cur is not None and not has_h:
            noher.append(cur)
        cur, has_h = m.group(1), False
        continue
    if re.match(r"^\s*heritage\s*=", l):
        has_h = True
if cur is not None and not has_h:
    noher.append(cur)
print("无 heritage 行的文化: %s" % noher)
print("gen_culture_unsettled 片段:")
i = t.find("gen_culture_unsettled = {")
print(t[i:i + 700])
