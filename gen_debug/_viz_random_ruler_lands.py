# -*- coding: utf-8 -*-
"""可视化 EU5 1337 开局「由 random 统治者控制的土地」，按 EU5 国家颜色着色。

口径：
- 判据：10_countries.txt 里国家块内含 `ruler = random`（即 government 块随机生成统治者）。
- 土地：同块内 own_control_core / own_control_integrated / own_control_conquered /
  own_control_colony / control / control_core 列出的 location。
- 颜色：EU5 国家颜色。优先取 _rebuild_export/eu5_politics.json 的 color；
  缺失时回源 setup/countries/*.txt 的 `color = map_xxx`，再到
  main_menu/common/named_colors/02_map.txt 解析 rgb/hsv360/hsv。
- 地图：location 名 -> CK3 `b_<location>` -> province，交给 ck3-mapviz 渲染。

只读游戏目录，产物写 gen_debug/。
"""
import colorsys
import glob
import io
import json
import os
import re

EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"
EU5_COUNTRIES = os.path.join(EU5, r"main_menu\setup\1337\10_countries.txt")
EU5_COUNTRY_DEFS = os.path.join(EU5, r"in_game\setup\countries")
EU5_MAP_COLORS = os.path.join(EU5, r"main_menu\common\named_colors\02_map.txt")

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLITICS = os.path.join(MOD, r"gen_debug\_rebuild_export\eu5_politics.json")
LANDED_DIR = os.path.join(MOD, r"common\landed_titles")
OUT_SPEC = os.path.join(MOD, r"gen_debug\_viz_random_ruler_lands_spec.json")
OUT_BASE = os.path.join(MOD, r"gen_debug\_viz_random_ruler_lands")

LAND_KEYS = (
    "own_control_core", "own_control_integrated", "own_control_conquered",
    "own_control_colony", "control", "control_core",
)
LAND_RE = re.compile(r"^\t\t(" + "|".join(LAND_KEYS) + r")\s*=\s*\{(.*)$")


def parse_countries(path):
    lines = io.open(path, encoding="utf-8-sig", errors="replace").read().splitlines()
    pat = re.compile(r"^\t([A-Z][A-Z0-9_]{1,5})\s*=\s*\{")
    starts = [(i, pat.match(l).group(1)) for i, l in enumerate(lines) if pat.match(l)]
    blocks = {}
    for n, (i, tag) in enumerate(starts):
        j = starts[n + 1][0] if n + 1 < len(starts) else len(lines)
        blocks[tag] = lines[i:j]
    return blocks


def parse_lands(block):
    out, cur = [], None
    for line in block:
        if cur is None:
            m = LAND_RE.match(line)
            if m:
                rest = m.group(2).strip()
                if rest.endswith("}"):
                    out += [x for x in rest[:-1].split() if x and not x.startswith("#")]
                else:
                    cur = m.group(1)
            continue
        if re.match(r"^\t\t\}", line):
            cur = None
            continue
        out += [x for x in line.split() if x and not x.startswith("#")]
    return out


def load_named_colors(path):
    txt = io.open(path, encoding="utf-8-sig", errors="replace").read()
    out = {}
    pat = re.compile(
        r"([A-Za-z0-9_]+)\s*=\s*(rgb|hsv360|hsv)\s*\{\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*\}"
    )
    for m in pat.finditer(txt):
        name, kind = m.group(1), m.group(2)
        a, b, c = float(m.group(3)), float(m.group(4)), float(m.group(5))
        if kind == "rgb":
            rgb = (a / 255.0, b / 255.0, c / 255.0)
        elif kind == "hsv360":
            rgb = colorsys.hsv_to_rgb(a / 360.0, b / 100.0, c / 100.0)
        else:
            rgb = colorsys.hsv_to_rgb(a, b, c)
        out[name] = tuple(int(round(x * 255)) for x in rgb)
    return out


def load_country_color_refs(dirpath):
    refs = {}
    for fn in glob.glob(os.path.join(dirpath, "*.txt")):
        txt = io.open(fn, encoding="utf-8-sig", errors="replace").read()
        for m in re.finditer(r"^([A-Z][A-Z0-9_]{1,5})\s*=\s*\{(.*?)^\}", txt, re.S | re.M):
            tag, body = m.group(1), m.group(2)
            cm = re.search(r"^\tcolor\s*=\s*(.+)$", body, re.M)
            if not cm:
                continue
            val = cm.group(1).strip()
            vm = re.match(r"(rgb|hsv360|hsv)\s*\{\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*\}", val)
            if vm:
                kind = vm.group(1)
                a, b, c = float(vm.group(2)), float(vm.group(3)), float(vm.group(4))
                if kind == "rgb":
                    refs[tag] = ("rgb", (int(a), int(b), int(c)))
                elif kind == "hsv360":
                    refs[tag] = ("hsv", (a / 360.0, b / 100.0, c / 100.0))
                else:
                    refs[tag] = ("hsv", (a, b, c))
            else:
                refs[tag] = ("name", val)
    return refs


def load_baronies(dirpath):
    names = set()
    for fn in glob.glob(os.path.join(dirpath, "*.txt")):
        txt = io.open(fn, encoding="utf-8-sig", errors="replace").read()
        names.update(re.findall(r"\bb_[A-Za-z0-9_-]+", txt))
    return names


def to_hex(rgb):
    return "#%02X%02X%02X" % tuple(max(0, min(255, int(x))) for x in rgb)


def main():
    blocks = parse_countries(EU5_COUNTRIES)
    random_tags = [t for t, b in blocks.items() if any("ruler = random" in x for x in b)]
    lands = {t: parse_lands(blocks[t]) for t in random_tags}
    lands = {t: v for t, v in lands.items() if v}

    pol = json.load(io.open(POLITICS, encoding="utf-8-sig"))["countries"]
    named = load_named_colors(EU5_MAP_COLORS)
    refs = load_country_color_refs(EU5_COUNTRY_DEFS)
    baronies = load_baronies(LANDED_DIR)

    src = {"politics": 0, "named_color": 0, "inline": 0, "none": 0}
    colors = {}
    for tag in lands:
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
        colors[tag] = rgb

    groups, miss_loc, no_barony_country = [], 0, []
    for tag in sorted(lands):
        bs = []
        for loc in lands[tag]:
            b = "b_" + loc
            if b in baronies:
                bs.append(b)
            else:
                miss_loc += 1
        if not bs:
            no_barony_country.append(tag)
            continue
        groups.append({
            "name": tag,
            "color": to_hex(colors[tag]),
            "titles": bs,
            "expand": False,
        })

    spec = {
        "mod_root": MOD,
        "out": OUT_BASE,
        "title": "EU5 1337: land of countries ruled by random rulers",
        "subtitle": "%d countries / %d locations" % (len(groups), sum(len(g["titles"]) for g in groups)),
        "groups": groups,
        "color": {"mode": "direct"},
        "base": {"unassigned": "#F2F2F2", "waste": "#9A9A9A"},
        "legend": {"enabled": False},
    }
    with io.open(OUT_SPEC, "w", encoding="utf-8", newline="\n") as f:
        json.dump(spec, f, ensure_ascii=False, indent=1)

    print("countries with ruler=random :", len(random_tags))
    print("  with land                 :", len(lands))
    print("  total locations           :", sum(len(v) for v in lands.values()))
    print("  mapped to CK3 barony      :", sum(len(g["titles"]) for g in groups))
    print("  locations without barony  :", miss_loc)
    print("  countries with 0 barony   :", len(no_barony_country), no_barony_country[:10])
    print("color source:", src)
    print("spec ->", OUT_SPEC)


if __name__ == "__main__":
    main()
