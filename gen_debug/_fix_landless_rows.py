# -*- coding: utf-8 -*-
"""把 title_map 里「EU5 没有领土、也没有世系」的 country 行清空 CK3 侧。

判据（唯一真源 …/Europa Universalis V/game/main_menu/setup/1337/10_countries.txt）：

  1. 块内有任意 `own_*`（core / integrated / conquered / colony / own_core）
     → 有领土，一律不动。
  2. `type = building` 且是日本那一群（`c_nf_*` 家族头衔、`e_eu5_ntc|stc|ymt`
     两统皇统、setup 里 ruler 以 `jap_` 开头）
     → 我们专门建了对应头衔，保留。
  3. `type = building` 且不是日本（意大利银行 ACC/BRD/PRZ、汉萨 HSA）
     → 我们没有对应头衔，清空。
  4. 无地（非 building）且块内有 `ruler_term`（EU5 自己的历代统治者世系）
     → 有历史的国家，保留（耶路撒冷 18 代、莱昂 36 代、香槟 15 代、拉丁帝国 5 代…）。
  5. 无地且没有 `ruler_term`
     → 1337 年不存在、也没有任何历史，清空（阿尔及尔、明、芬兰、美洲与非洲部落…）。

清空字段：ck3_key / ck3_tier / ck3_name_en / ck3_name_zh / ck3_holder /
ck3_liege / ck3_government / ck3_declared；note 追加 `building-in-eu5` /
`landless-in-eu5` 与原键 `was <key>`，信息不丢。

用法：python gen_debug/_fix_landless_rows.py [--write]
"""
import argparse
import csv
import io
import os
import re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SETUP = (r"D:/Program Files (x86)/Steam/steamapps/common/Europa Universalis V"
                 r"/game/main_menu/setup/1337")
BLOCK = re.compile(r'(?ms)^\t([A-Z][A-Z0-9]{2}) = \{[^\n]*\n(.*?)^\t\}')
HAS_LAND = re.compile(r'(?m)^\t+own_[a-z_]+\s*=')
IS_BUILDING = re.compile(r'(?m)^\t+type = building\b')
RULER = re.compile(r'(?m)^\t+ruler = (\w+)')
RULER_TERM = re.compile(r'(?m)^\t+ruler_term\s*=\s*\{')
CLEAR = ["ck3_key", "ck3_tier", "ck3_name_en", "ck3_name_zh",
         "ck3_holder", "ck3_liege", "ck3_government", "ck3_declared"]

JAPAN_TAGS = {"NTC", "STC", "YMT"}
JAPAN_KEYS = {"e_eu5_ntc", "e_eu5_stc", "e_eu5_ymt"}


def read_setup(setup_dir):
    path = os.path.join(setup_dir, "10_countries.txt")
    text = io.open(path, encoding="utf-8-sig", errors="ignore").read()
    out = {}
    for m in BLOCK.finditer(text):
        body = m.group(2)
        r = RULER.search(body)
        out[m.group(1)] = {
            "land": bool(HAS_LAND.search(body)),
            "building": bool(IS_BUILDING.search(body)),
            "terms": len(RULER_TERM.findall(body)),
            "ruler": r.group(1) if r else "",
        }
    return out


def is_japan(tag, row, info):
    if tag in JAPAN_TAGS or row["ck3_key"] in JAPAN_KEYS:
        return True
    if row["ck3_key"].startswith("c_nf_"):
        return True
    return info.get("ruler", "").startswith("jap_")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mod", default=os.path.abspath(os.path.join(HERE, "..")))
    ap.add_argument("--eu5-setup", default=DEFAULT_SETUP)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    setup = read_setup(args.eu5_setup)
    path = os.path.join(args.mod, "gen_debug", "eu5_ck3_title_map.csv")
    raw = io.open(path, encoding="utf-8-sig", newline="").read()
    rows = list(csv.DictReader(io.StringIO(raw)))
    cols = list(rows[0].keys())

    touched = Counter()
    kept = Counter()
    samples = []

    for r in rows:
        if r["kind"] != "country":
            continue
        tag = r["eu5_tag"]
        info = setup.get(tag)
        if info is None:
            touched["unknown"] += 1
            continue
        if info["land"]:
            kept["has-land"] += 1
            continue
        if info["building"]:
            if is_japan(tag, r, info):
                kept["japan-building"] += 1
                continue
            kind = "building"
        else:
            if info["terms"] > 0:
                kept["landless-with-history"] += 1
                continue
            kind = "landless"

        old = r["ck3_key"]
        notes = [x.strip() for x in (r["note"] or "").split(",") if x.strip()]
        if kind + "-in-eu5" not in notes:
            notes.append(kind + "-in-eu5")
        if old and not any(x.startswith("was ") for x in notes):
            notes.append("was " + old)
        r["note"] = ",".join(notes)
        for c in CLEAR:
            r[c] = ""
        touched[kind] += 1
        if len(samples) < 15:
            samples.append((tag, r["eu5_country_en"], old, kind))

    print("保留: 有地=%d  日本建筑=%d  无地但有 EU5 世系=%d"
          % (kept["has-land"], kept["japan-building"], kept["landless-with-history"]))
    print("清空: 非日本建筑=%d  无地无世系=%d  (setup 缺失未动=%d)"
          % (touched["building"], touched["landless"], touched["unknown"]))
    for tag, name, old, kind in samples:
        print("  %-4s %-18s %-10s was %s" % (tag, (name or "")[:18], kind, old or "(空)"))

    if not args.write:
        print("\n(dry-run，未写盘。加 --write 落盘)")
        return

    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\r\n")
    w.writeheader()
    w.writerows(rows)
    with io.open(path, "wb") as fh:
        fh.write(b"\xef\xbb\xbf")
        fh.write(buf.getvalue().encode("utf-8"))
    print("\nwritten: %s" % path)


if __name__ == "__main__":
    main()
