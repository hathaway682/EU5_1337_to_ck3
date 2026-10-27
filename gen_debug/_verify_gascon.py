# -*- coding: utf-8 -*-
"""校验本次 gascon 修正：两段改动各自的差异行。"""
import io

BASE = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape\common\culture\cultures"
NOW = BASE + r"\00_generated_cultures.txt"


def rd(p):
    return io.open(p, encoding="utf-8-sig").read().split("\n")


a = rd(NOW)
b1 = rd(BASE + r"\00_generated_cultures.txt.bak_heritagerestore_20261020_180912")
b2 = rd(BASE + r"\00_generated_cultures.txt.bak_aesthetics_20261020_180940")

for tag, b in (("传承步（heritage）", b1), ("美学步（gfx）", b2)):
    d = [(i + 1, b[i].strip(), a[i].strip()) for i in range(min(len(a), len(b))) if a[i] != b[i]]
    print("%s 差异 %d 行（行数 %d/%d）" % (tag, len(d), len(a), len(b)))
    for x in d:
        print("   第%d行: %s  ->  %s" % x)
    print()

print("大括号: %d / %d" % (io.open(NOW, encoding="utf-8-sig").read().count("{"),
                          io.open(NOW, encoding="utf-8-sig").read().count("}")))
