# -*- coding: utf-8 -*-
"""查：当前文件里哪些 heritage_* 值没有对应 gfx 映射。只读。"""
import io, os, re, sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _restore_eu5_aesthetics as A

SRC = os.path.join(A.MOD, "common", "culture", "cultures", "00_generated_cultures.txt")
t = io.open(SRC, encoding="utf-8-sig").read()
cur = None
cnt = Counter()
miss = Counter()
missing_cults = {}
for line in t.split("\n"):
    m = re.match(r"^([a-z0-9_]+)\s*=\s*\{\s*$", line)
    if m:
        cur = m.group(1)
        continue
    mh = re.match(r"^\s*heritage\s*=\s*(\S+)", line)
    if mh and cur:
        h = mh.group(1)
        cnt[h] += 1
        if h.startswith("heritage_") and h not in A.HERITAGE_GFX:
            miss[h] += 1
            missing_cults.setdefault(h, []).append(cur)
print("heritage 值总数: %d" % sum(cnt.values()))
print("heritage_* 值 %d 种，表中缺 %d 种" % (
    len([k for k in cnt if k.startswith("heritage_")]), len(miss)))
for k, v in miss.most_common():
    print("  %-30s %3d  %s" % (k, v, " ".join(missing_cults[k][:10])))
