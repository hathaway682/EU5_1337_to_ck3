# -*- coding: utf-8 -*-
"""严格对比：去掉新插入的 313 行后，是否与原备份逐行一致。"""
import io, re

LOC = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape\localization\english\gen_cultures_l_english.yml"
BAK = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape\localization\english\gen_cultures_l_english.yml.bak_langloc_20261020_011828"

t = io.open(LOC, encoding="utf-8-sig").read()
o = io.open(BAK, encoding="utf-8-sig").read()
lines = t.split("\n")
kept = [l for l in lines if not re.match(r"^\s*eu5_language_[a-z0-9_]+_name:\d+", l)]
print("总行 %d | 移出 %d | 剩余 %d | 备份 %d"
      % (len(lines), len(lines) - len(kept), len(kept), len(o.split("\n"))))
print("逐行一致: %s" % (kept == o.split("\n")))
if kept != o.split("\n"):
    ol = o.split("\n")
    for i in range(max(len(kept), len(ol))):
        a = kept[i] if i < len(kept) else "<none>"
        b = ol[i] if i < len(ol) else "<none>"
        if a != b:
            print("首个差异第 %d 行:\n  new=%r\n  old=%r" % (i + 1, a, b))
            break
idx = [i for i, l in enumerate(lines) if re.match(r"^\s*eu5_language_[a-z0-9_]+_name:\d+", l)]
print("新行是连续块: %s (位置 %d-%d)"
      % (idx == list(range(idx[0], idx[-1] + 1)), idx[0] + 1, idx[-1] + 1))
ks = [re.match(r"^\s*([a-z0-9_]+):", lines[i]).group(1) for i in idx]
print("新行排序正确: %s" % (ks == sorted(ks)))
