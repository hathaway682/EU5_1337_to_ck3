# -*- coding: utf-8 -*-
"""对比当前文件与最早的备份，确认只有 heritage/language/gfx 行发生变化。只读。"""
import io, os, re, glob

CULT = os.path.join(r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape",
                    "common", "culture", "cultures", "00_generated_cultures.txt")
baks = sorted(glob.glob(CULT + ".bak_*"))
print("备份链:")
for b in baks:
    print("  %s  (%d bytes)" % (os.path.basename(b), os.path.getsize(b)))

oldest = baks[0]
newest = CULT


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


a = read(oldest).split("\n")
b = read(newest).split("\n")
print("\n行数: %d -> %d" % (len(a), len(b)))
assert len(a) == len(b), "行数不一致！"

from collections import Counter
kinds = Counter()
samples = []
for i, (x, y) in enumerate(zip(a, b)):
    if x == y:
        continue
    mx = re.match(r"^\s*([a-z_]+)\s*=", x)
    my = re.match(r"^\s*([a-z_]+)\s*=", y)
    kx = mx.group(1) if mx else "(other)"
    ky = my.group(1) if my else "(other)"
    if kx != ky:
        kinds["MISMATCH_FIELD %s/%s" % (kx, ky)] += 1
    else:
        kinds[kx] += 1
    if len(samples) < 8:
        samples.append((i + 1, x.strip()[:70], y.strip()[:70]))
print("\n变化的行按字段分类:")
for k, v in kinds.most_common():
    print("  %-24s %d" % (k, v))
print("\nsamples:")
for ln, x, y in samples:
    print("  L%-6d %s\n           -> %s" % (ln, x, y))
