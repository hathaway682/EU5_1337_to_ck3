# -*- coding: utf-8 -*-
"""从 EU5 rivers.png + locations.png 取每个 location 的 river size。

rivers.png 调色板里河流色只有 4 种被使用（其余是陆地/海洋底色）：
  idx 11 (0,0,100)   尼罗/多瑙/莱茵 -> size 5
  idx 15 (24,206,0)  叶尼塞/伯朝拉等北方大河 -> size 4
  idx  5 (0,150,255) 塞纳/底格里斯 -> size 3
  idx  4 (0,200,255) 泰晤士/撒马尔罕 -> size 1
  idx 0/1/2 (纯绿/红/黄，各几百像素) 视为标记，忽略

只读，输出 gen_debug/_eu5_river_size.csv
"""
import os, re
import numpy as np
from PIL import Image

EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"
MAP = os.path.join(EU5, "in_game", "map_data")
ROOT = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
OUT = os.path.join(ROOT, "gen_debug", "_eu5_river_size.csv")

Image.MAX_IMAGE_PIXELS = None

SIZE = {11: 5, 15: 4, 5: 3, 4: 1}

loc_rgb = {}
for ln in open(os.path.join(MAP, "named_locations", "00_default.txt"), encoding="utf-8-sig", errors="replace"):
    s = ln.split("#")[0].strip()
    m = re.match(r"^([A-Za-z0-9_-]+)\s*=\s*([0-9a-fA-F]{6})\s*$", s)
    if m:
        h = m.group(2)
        loc_rgb[m.group(1)] = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
rgb2loc = {v: k for k, v in loc_rgb.items()}

riv = np.array(Image.open(os.path.join(MAP, "rivers.png")))
loc = np.array(Image.open(os.path.join(MAP, "locations.png")))

best = {}
for idx, size in SIZE.items():
    ys, xs = np.nonzero(riv == idx)
    cols = loc[ys, xs]
    keys = cols[:, 0].astype(np.int32) * 65536 + cols[:, 1].astype(np.int32) * 256 + cols[:, 2]
    uniq, cnt = np.unique(keys, return_counts=True)
    for k, n in zip(uniq.tolist(), cnt.tolist()):
        rgb = ((k >> 16) & 255, (k >> 8) & 255, k & 255)
        name = rgb2loc.get(rgb)
        if not name:
            continue
        if n < 3:          # 边缘抗锯齿噪点
            continue
        if size > best.get(name, 0):
            best[name] = size

with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write("location,river_size\n")
    for k in sorted(best):
        f.write(f"{k},{best[k]}\n")

print("locations with river:", len(best))
import collections
print(collections.Counter(best.values()))
for t in ["cairo", "paris", "london", "vienna", "baghdad", "samarkand", "cologne", "yeniseysk", "pechora"]:
    print(" ", t, best.get(t, 0))
