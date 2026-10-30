# -*- coding: utf-8 -*-
"""探测 EU5 rivers.png 各颜色含义：统计每种颜色落在哪些 location 上。

只读。
"""
import os, re, collections
import numpy as np
from PIL import Image

EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"
MAP = os.path.join(EU5, "in_game", "map_data")

Image.MAX_IMAGE_PIXELS = None

# named_locations: name = hex
loc_rgb = {}
for ln in open(os.path.join(MAP, "named_locations", "00_default.txt"), encoding="utf-8-sig", errors="replace"):
    s = ln.split("#")[0].strip()
    m = re.match(r"^([A-Za-z0-9_-]+)\s*=\s*([0-9a-fA-F]{6})\s*$", s)
    if m:
        h = m.group(2)
        loc_rgb[m.group(1)] = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
print("named locations:", len(loc_rgb))

rgb2loc = {v: k for k, v in loc_rgb.items()}

riv = np.array(Image.open(os.path.join(MAP, "rivers.png")))
print("rivers shape", riv.shape, riv.dtype)

pal = Image.open(os.path.join(MAP, "rivers.png")).getpalette()
def pal_rgb(i):
    return (pal[i*3], pal[i*3+1], pal[i*3+2])

idxs = [i for i in range(16) if (riv == i).any()]
print("used palette indices:", [(i, pal_rgb(i), int((riv == i).sum())) for i in idxs])

# 只取非陆地/非海洋色
land = 0  # (0,255,0)?? 先看实际
# 找出最大两个颜色当底色
counts = {i: int((riv == i).sum()) for i in idxs}
bg = sorted(counts, key=lambda i: -counts[i])[:2]
print("bg idx", [(i, pal_rgb(i)) for i in bg])

loc = np.array(Image.open(os.path.join(MAP, "locations.png")))

for i in idxs:
    if i in bg:
        continue
    ys, xs = np.nonzero(riv == i)
    print(f"\n=== idx {i} rgb {pal_rgb(i)} px {len(ys)} ===")
    # 抽样 200000 个点
    step = max(1, len(ys) // 200000)
    yy, xx = ys[::step], xs[::step]
    cols = loc[yy, xx]
    c = collections.Counter(map(tuple, cols))
    for rgb, n in c.most_common(8):
        print("   ", rgb, rgb2loc.get(rgb, "?"), n)
