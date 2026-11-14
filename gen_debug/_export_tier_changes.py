# -*- coding: utf-8 -*-
"""从 gen_debug/eu5_ck3_title_map.csv 抽出「EU5 原始等级 → CK3 实际等级」发生变化的行。

等级序：e 帝国 > k 王国 > d 公国 > c 伯爵 > b 男爵 > - 无地。
CK3 的 h（中华帝国 h_china）按帝国级 e 计。

**参与统计的门槛：EU5 里必须有领土。**
判据读 `…/Europa Universalis V/game/main_menu/setup/1337/10_countries.txt`：
  - 块内出现任意 `own_*`（own_control_core / own_control_integrated /
    own_control_conquered / own_core / own_control_colony）＝ 有领土。
  - `type = building`（汉萨、意大利银行家族、日本朝廷与武家）＝ 建筑型实体，没有领土，
    不参与等级比较。
  - 两者都没有 ＝ 真无地（只剩核心宣称 / 元末群雄 / 已灭亡的名义国家），不参与。
所以 ALG 阿尔及尔（只有 our_cores_conquered_by_others，地被 TLE 占着）不会出现在表里。

分类：
  up           升
  demote-soft  结构性降级 —— EU5 里本来就没有自己的伯爵领（c→b / c→-），
               在 CK3 只能当别人伯爵领里的男爵或无地，属既有设计
  demote-hard  实质降级 —— 有地却掉级（k→d、d→c、k→b …）

用法：python gen_debug/_export_tier_changes.py [--out 路径] [--eu5-setup 目录]
"""
import argparse
import csv
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ORDER = "ekdcb-"
TIER_ZH = {"e": "帝国", "k": "王国", "d": "公国", "c": "伯爵", "b": "男爵", "-": "无地"}
COLS = ["change", "eu5_tag", "eu5_country_en", "eu5_country_zh", "eu5_tier", "eu5_tier_zh",
        "ck3_tier", "ck3_tier_zh", "ck3_key", "ck3_name_en", "ck3_name_zh",
        "ck3_holder", "ck3_liege", "ck3_government", "note"]

DEFAULT_SETUP = (r"D:/Program Files (x86)/Steam/steamapps/common/Europa Universalis V"
                 r"/game/main_menu/setup/1337")
BLOCK = re.compile(r'(?ms)^\t([A-Z][A-Z0-9]{2}) = \{[^\n]*\n(.*?)^\t\}')
HAS_LAND = re.compile(r'(?m)^\t+own_[a-z_]+\s*=')
IS_BUILDING = re.compile(r'(?m)^\t+type = building\b')


def read_setup(setup_dir):
    """tag -> (has_land, is_building)。"""
    path = os.path.join(setup_dir, "10_countries.txt")
    text = io.open(path, encoding="utf-8-sig", errors="ignore").read()
    out = {}
    for m in BLOCK.finditer(text):
        body = m.group(2)
        out[m.group(1)] = (bool(HAS_LAND.search(body)), bool(IS_BUILDING.search(body)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mod", default=os.path.abspath(os.path.join(HERE, "..")))
    ap.add_argument("--out", default=os.path.join(HERE, "eu5_ck3_tier_changes.csv"))
    ap.add_argument("--eu5-setup", default=DEFAULT_SETUP)
    args = ap.parse_args()

    setup = read_setup(args.eu5_setup)

    src = os.path.join(args.mod, "gen_debug", "eu5_ck3_title_map.csv")
    rows = list(csv.DictReader(io.open(src, encoding="utf-8-sig", newline="")))
    out = []
    skipped = {"building": 0, "landless": 0, "unknown": 0}
    for r in rows:
        if r["kind"] != "country":
            continue
        tag = r["eu5_tag"]
        if tag not in setup:
            skipped["unknown"] += 1
            continue
        has_land, is_building = setup[tag]
        if is_building:
            skipped["building"] += 1
            continue
        if not has_land:
            skipped["landless"] += 1
            continue
        a = r["eu5_tier"]
        b = "e" if r["ck3_tier"] == "h" else (r["ck3_tier"] or "-")
        if a == b:
            continue
        ia, ib = ORDER.index(a), ORDER.index(b)
        if ib < ia:
            change = "up"
        elif a == "c":
            change = "demote-soft"
        else:
            change = "demote-hard"
        out.append({
            "change": change,
            "eu5_tag": tag,
            "eu5_country_en": r["eu5_country_en"],
            "eu5_country_zh": r["eu5_country_zh"],
            "eu5_tier": a, "eu5_tier_zh": TIER_ZH[a],
            "ck3_tier": b, "ck3_tier_zh": TIER_ZH[b],
            "ck3_key": r["ck3_key"],
            "ck3_name_en": r["ck3_name_en"],
            "ck3_name_zh": r["ck3_name_zh"],
            "ck3_holder": r["ck3_holder"],
            "ck3_liege": r["ck3_liege"],
            "ck3_government": r["ck3_government"],
            "note": r["note"],
        })

    # 排序：升在前，再按落差大小、EU5 等级高低、tag
    seq = {"up": 0, "demote-hard": 1, "demote-soft": 2}
    out.sort(key=lambda x: (seq[x["change"]],
                            -(ORDER.index(x["eu5_tier"]) - ORDER.index(x["ck3_tier"])),
                            ORDER.index(x["eu5_tier"]), x["eu5_tag"]))

    with io.open(args.out, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS, lineterminator="\r\n")
        w.writeheader()
        w.writerows(out)

    from collections import Counter
    print("setup tag: %d（有地 %d / 建筑 %d / 真无地 %d）" % (
        len(setup),
        sum(1 for v in setup.values() if v[0]),
        sum(1 for v in setup.values() if v[1]),
        sum(1 for v in setup.values() if not v[0] and not v[1])))
    print("排除（CSV country 行）:", skipped)
    print("变化行: %d -> %s" % (len(out), args.out))
    print("分类:", dict(Counter(x["change"] for x in out)))
    print("迁移:", dict(Counter((x["eu5_tier"], x["ck3_tier"]) for x in out)))


if __name__ == "__main__":
    main()
