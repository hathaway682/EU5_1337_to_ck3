# -*- coding: utf-8 -*-
"""第二版：按「random 统治者在 CK3 侧控制的伯爵领」整县涂 EU5 国家色。

与第一版 _viz_random_ruler_lands.py 的区别：
- 第一版按 EU5 location -> CK3 b_<location> 逐男爵领上色（细）；
- 本版按 eu5_politics.json 的 counties[].owner（CK3 侧该县归属国家 tag）整县上色（粗）。

口径：
- random 国家：10_countries.txt 国家块内含 `ruler = random`。
- 伯爵领：counties[c]["owner"] == 该 tag（实测对 random 国家而言与 ruler 口径结果一致：
  392 国 / 603 县；用 owner 可避免联统共主把别国的县涂成本国色）。
- 颜色：同第一版，EU5 国家原色。
- 渲染：ck3-mapviz，groups 里直接放 c_ 头衔（expand=true 展开整县）。
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _viz_random_ruler_lands import (  # noqa: E402
    EU5_COUNTRIES, EU5_COUNTRY_DEFS, EU5_MAP_COLORS, MOD, POLITICS,  # noqa: F401
    load_country_color_refs, load_named_colors, parse_countries, to_hex,
)
import colorsys  # noqa: E402

OUT_SPEC = os.path.join(MOD, r"gen_debug\_viz_random_ruler_counties_spec.json")
OUT_BASE = os.path.join(MOD, r"gen_debug\_viz_random_ruler_counties")


def main():
    blocks = parse_countries(EU5_COUNTRIES)
    random_tags = [t for t, b in blocks.items() if any("ruler = random" in x for x in b)]

    data = json.load(io.open(POLITICS, encoding="utf-8-sig"))
    pol = data["countries"]
    counties = data["counties"]

    named = load_named_colors(EU5_MAP_COLORS)
    refs = load_country_color_refs(EU5_COUNTRY_DEFS)

    by_owner = {}
    for ck, v in counties.items():
        o = v.get("owner")
        if o:
            by_owner.setdefault(o, []).append(ck)

    src = {"politics": 0, "named_color": 0, "inline": 0, "none": 0}
    groups, no_county = [], []
    for tag in sorted(random_tags):
        cs = by_owner.get(tag)
        if not cs:
            no_county.append(tag)
            continue
        rgb = None
        v = pol.get(tag, {}).get("color")
        if v and len(v) == 3:
            rgb = tuple(int(x) for x in v)
            src["politics"] += 1
        elif tag in refs:
            kind, val = refs[tag]
            if kind == "name" and val in named:
                rgb = named[val]
                src["named_color"] += 1
            elif kind == "rgb":
                rgb = val
                src["inline"] += 1
            elif kind == "hsv":
                rgb = tuple(int(round(x * 255)) for x in colorsys.hsv_to_rgb(*val))
                src["inline"] += 1
        if rgb is None:
            rgb = (150, 150, 150)
            src["none"] += 1
        groups.append({
            "name": tag,
            "color": to_hex(rgb),
            "titles": sorted(cs),
            "expand": True,
        })

    spec = {
        "mod_root": MOD,
        "out": OUT_BASE,
        "title": "EU5 1337: counties held by countries with random rulers",
        "subtitle": "%d countries / %d counties" % (len(groups), sum(len(g["titles"]) for g in groups)),
        "groups": groups,
        "color": {"mode": "direct"},
        "base": {"unassigned": "#F2F2F2", "waste": "#9A9A9A"},
        "legend": {"enabled": False},
    }
    with io.open(OUT_SPEC, "w", encoding="utf-8", newline="\n") as f:
        json.dump(spec, f, ensure_ascii=False, indent=1)

    print("countries with ruler=random :", len(random_tags))
    print("  holding >=1 CK3 county    :", len(groups))
    print("  total counties            :", sum(len(g["titles"]) for g in groups))
    print("  countries without county  :", len(no_county))
    print("color source:", src)
    print("spec ->", OUT_SPEC)


if __name__ == "__main__":
    main()
