# -*- coding: utf-8 -*-
"""EU5 三口径「分歧」图：整个 province 上同一种颜色。

与 _eu5_seat_rules_spec.json 的区别：
  旧的只给被选中的 1~3 个 location 上色；本图把 province 内**全部** location
  都放进同一组，所以整块 province 是一个颜色。

判定（B=人口最多、G=最高地点等级中人口最多、R=definitions 顺序第一）：
  B == G == R              -> 白色（不上色）
  B、G、R 两两互不相同     -> 黑色
  恰好两个相同，B 落单     -> 蓝色
  恰好两个相同，G 落单     -> 绿色
  恰好两个相同，R 落单     -> 红色

解析、人口、等级全部复用 _build_eu5_seat_rules_spec.py（已修好
definitions.txt 不带 _province 后缀的 province 块），规则口径不变。
"""
import collections
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
MOD = os.path.dirname(HERE).replace("\\", "/")
sys.path.insert(0, HERE)

import _build_eu5_seat_rules_spec as base  # noqa: E402

SRC_SPEC = MOD + "/gen_debug/_eu5_seat_rules_spec.json"
OUT_SPEC = MOD + "/gen_debug/_eu5_province_split_spec.json"

CAT = [
    ("white", "三者重合 · 白（不上色）", "#FFFFFF"),
    ("blue", "人口最多落单 · 蓝", "#2F6FE4"),
    ("green", "最高等级中人口最多落单 · 绿", "#1F9D55"),
    ("red", "EU5 顺序第一落单 · 红", "#D93838"),
    ("black", "三者互不相同 · 黑", "#111111"),
]


def classify(locs, pop, ranks):
    idx = {n.lower(): i for i, n in enumerate(locs)}

    def popof(n):
        return pop.get(n.lower(), 0.0)

    def tierof(n):
        return base.TIER.get(ranks.get(n.lower(), ""), 0)

    b = max(locs, key=lambda n: (popof(n), -idx[n.lower()]))
    top = max(tierof(n) for n in locs)
    g = max((n for n in locs if tierof(n) == top),
            key=lambda n: (popof(n), -idx[n.lower()]))
    r = locs[0]
    b, g, r = b.lower(), g.lower(), r.lower()

    s = {b, g, r}
    if len(s) == 1:
        return "white"
    if len(s) == 3:
        return "black"
    # 恰好两个相同：找出落单的那个
    if b != g and b != r:
        return "blue"
    if g != b and g != r:
        return "green"
    return "red"


def main():
    pop = base.load_pop()
    ranks = base.load_ranks()
    provs = base.parse_provinces()

    buckets = collections.defaultdict(list)
    nprov = collections.Counter()
    for locs in provs.values():
        key = classify(locs, pop, ranks)
        nprov[key] += 1
        buckets[key].extend("b_" + n.lower() for n in locs)

    spec = json.load(io.open(SRC_SPEC, encoding="utf-8"))
    spec["out"] = MOD + "/gen_debug/_eu5_province_split"
    spec["title"] = "EU5 三口径首府分歧（整个 province 上色）"
    spec["subtitle"] = (
        "B=人口最多；G=最高地点等级中人口最多；R=definitions 顺序第一。"
        "三者重合→白；三者互不相同→黑；恰好两者相同时，落单者决定颜色（B蓝/G绿/R红）"
    )
    spec["legend"] = {"enabled": True, "unit": "provinces", "show_counts": True}
    spec["groups"] = []
    for key, label, color in CAT:
        titles = sorted(set(buckets.get(key, [])))
        spec["groups"].append({"name": label, "color": color, "titles": titles})
        print("  %-28s %5d province  %6d location  %s"
              % (label, nprov[key], len(titles), color))
    print("province 合计:", sum(nprov.values()),
          " location 键合计:", sum(len(g["titles"]) for g in spec["groups"]))

    with io.open(OUT_SPEC, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(spec, ensure_ascii=False, indent=2) + "\n")
    print("已写:", OUT_SPEC)


if __name__ == "__main__":
    main()
