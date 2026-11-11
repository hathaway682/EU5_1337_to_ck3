# -*- coding: utf-8 -*-
"""重算 _eu5_seat_rules_spec.json 的 groups（只重算数据层）。

spec 里的 title / subtitle / base / color / legend / layer 等静态接线字段
一律沿用现有文件，本脚本只按 EU5 原生数据重算 groups。

口径（全部来自 EU5 原生，不含 mod 首府/持有人内容）：
  B = province 内人口最多的 location        06_pops.txt 的 size
  G = province 内最高地点等级者中人口最多   07_cities_and_buildings.txt 的 rank
  R = definitions.txt 里该 province 块顺序第一的 location

2026-11-09 修复：definitions.txt 的 province 块名并非都带 _province 后缀
（印度 79 个、澳洲 23 个等共 159 个不带，另有 makarikha_procince 拼写错误）。
旧正则硬要求后缀，整批块被跳过，印度半岛中南部因此全白。
现改为按 4-tab 缩进取全部 province 块，块名不再参与筛选。
"""
import collections
import io
import json
import os
import re
import sys

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace("\\", "/")
EX = "D:/Documents/Paradox Interactive/Crusader Kings III/mod/Global_modern_map/eu5_export"
EU5 = "D:/Program Files (x86)/Steam/steamapps/common/Europa Universalis V/game"
SETUP = EU5 + "/main_menu/setup/1337"
POPS = SETUP + "/06_pops.txt"
BUILDINGS = SETUP + "/07_cities_and_buildings.txt"
DEFINITIONS = EU5 + "/in_game/map_data/definitions.txt"
SPEC = MOD + "/gen_debug/_eu5_seat_rules_spec.json"

TIER = {"megalopolis": 4, "city": 3, "town": 2, "rural_settlement": 1}

CAT = [
    (frozenset("B"), "人口最多（蓝）", "#2F6FE4"),
    (frozenset("G"), "最高等级中人口最多（绿）", "#1F9D55"),
    (frozenset("R"), "EU5 文件顺序第一（红）", "#D93838"),
    (frozenset("BG"), "蓝+绿 · 深青", "#0B5E73"),
    (frozenset("BR"), "蓝+红 · 深紫", "#6B2D91"),
    (frozenset("GR"), "绿+红 · 深黄", "#B8860B"),
    (frozenset("BGR"), "三者重合 · 黑", "#111111"),
]


def load_pop():
    """location -> 人口权重，复用 _capital_correct.py 的现成解析。"""
    sys.path.insert(0, EX)
    saved = sys.argv
    sys.argv = ["_capital_correct", "--pops", POPS, "--eu5-export", EX]
    import _capital_correct as cc
    sys.argv = saved
    return cc.load_pop()


def load_ranks():
    """location -> EU5 settlement rank。"""
    txt = io.open(BUILDINGS, encoding="utf-8-sig", errors="replace").read()
    return {
        m.group(1).lower(): m.group(2).lower()
        for m in re.finditer(
            r"(?m)^\s*([A-Za-z0-9_]+)\s*=\s*\{[^{}]*?\brank\s*=\s*([A-Za-z0-9_]+)",
            txt,
        )
    }


def parse_provinces():
    """按缩进层取全部 province 块，返回 {province: [location 顺序列表]}。

    definitions.txt 用 tab 缩进：1=大陆 2=region 3=area 4=province。
    块名后缀不统一（uppland_province / akara / cola_nadu / makarikha_procince），
    所以只认缩进层，不认名字。
    块内还有 `#7` 注释和 `not_eligible_for_dynamic_country_name = yes` 这类参数，
    必须先清掉，否则会被当成 location 造出 b_7 / b_yes 垃圾键。
    """
    txt = io.open(DEFINITIONS, encoding="utf-8-sig", errors="replace").read()
    out = collections.OrderedDict()
    for m in re.finditer(r"(?m)^\t{4}([A-Za-z0-9_-]+)\s*=\s*\{([^}]*)\}", txt):
        body = re.sub(r"#[^\r\n]*", "", m.group(2))
        body = re.sub(r"\b[A-Za-z0-9_]+\s*=\s*[A-Za-z0-9_]+\b", " ", body)
        locs = re.findall(r"[A-Za-z0-9_]+", body)
        if locs:
            out[re.sub(r"_province$", "", m.group(1))] = locs
    return out


def main():
    pop = load_pop()
    ranks = load_ranks()
    provs = parse_provinces()
    print("province 块:", len(provs), " 有 pop 的 location:", len(pop), " 有 rank 的 location:", len(ranks))

    flags = collections.defaultdict(set)
    for locs in provs.values():
        idx = {n.lower(): i for i, n in enumerate(locs)}

        def popof(n):
            return pop.get(n.lower(), 0.0)

        def tierof(n):
            return TIER.get(ranks.get(n.lower(), ""), 0)

        blue = max(locs, key=lambda n: (popof(n), -idx[n.lower()]))
        top = max(tierof(n) for n in locs)
        green = max((n for n in locs if tierof(n) == top),
                    key=lambda n: (popof(n), -idx[n.lower()]))
        red = locs[0]
        flags[blue.lower()].add("B")
        flags[green.lower()].add("G")
        flags[red.lower()].add("R")

    buckets = collections.defaultdict(list)
    for name, fl in flags.items():
        buckets[frozenset(fl)].append("b_" + name)

    spec = json.load(io.open(SPEC, encoding="utf-8"))
    old = {t.lower() for g in spec["groups"] for t in g["titles"]}
    groups = []
    for key, label, color in CAT:
        titles = sorted(buckets.get(key, []))
        groups.append({"name": "%s（%d）" % (label, len(titles)),
                       "color": color, "titles": titles})
        print("  %-24s %5d  %s" % (label, len(titles), color))
    spec["groups"] = groups

    with io.open(SPEC, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(spec, ensure_ascii=False, indent=2) + "\n")
    new = {t.lower() for g in groups for t in g["titles"]}
    print("被选中 location: %d（较修复前新增 %d，消失 %d）"
          % (len(new), len(new - old), len(old - new)))
    print("已写回:", SPEC)


if __name__ == "__main__":
    main()
