# -*- coding: utf-8 -*-
"""
把宗族（common/dynasties）与支系（common/dynasty_houses）里的 culture
按欧洲落地方案改到新 key。

映射来源与 _apply_eu_culture_merge.py 完全一致：
  _culture_classification.csv 里 continent == 欧洲 且 target != 自身的行，
  跳过 kazani（草原组归亚洲）。

用法：
  python _apply_eu_culture_dynasty.py            # 只统计
  python _apply_eu_culture_dynasty.py --apply    # 落盘（带备份）
"""
import csv
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(ROOT, "gen_debug", "_culture_classification.csv")

FILES = [
    "common/dynasties/00_generated_dynasties.txt",
    "common/dynasties/zz_eu5_dynasties.txt",
    "common/dynasties/zz_gen_adventurers.txt",
    "common/dynasty_houses/zz_eu5_merged_houses.txt",
    "common/dynasty_houses/zz_gen_adventurers.txt",
]

SKIP = {"kazani"}

# 只吃 culture 字段，值可带引号也可裸写；分组保留原始格式
RE_CULT = re.compile(r'^([ \t]*)culture([ \t]*=[ \t]*)("?)([A-Za-z0-9_]+)("?)[ \t]*$')


def build_map():
    rows = list(csv.DictReader(open(CSV, encoding="utf-8-sig")))
    eu = {r["culture"]: r for r in rows if r.get("continent") == "欧洲"}
    m = {}
    for c, r in eu.items():
        if c in SKIP:
            continue
        t = r["target"]
        if not t:
            continue
        if t.startswith("NEW:"):
            t = t[4:]
        if t and t != c:
            m[c] = t
    return m


def main():
    apply = "--apply" in sys.argv
    MAP = build_map()
    print("映射条目 %d（欧洲方案）" % len(MAP))

    stamp = time.strftime("%Y%m%d_%H%M%S")
    grand = 0
    for rel in FILES:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            print("  跳过（不存在）: %s" % rel)
            continue
        raw = open(path, "rb").read()
        bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8-sig")
        lines = text.splitlines(keepends=True)

        out = []
        changed = 0
        hits = {}
        for ln in lines:
            body = ln.rstrip("\r\n")
            tail = ln[len(body):]
            m = RE_CULT.match(body)
            if m:
                old = m.group(4)
                new = MAP.get(old)
                if new and new != old:
                    changed += 1
                    hits[old] = hits.get(old, 0) + 1
                    body = "%sculture%s%s%s%s" % (
                        m.group(1), m.group(2), m.group(3), new, m.group(5))
            out.append(body + tail)

        if changed == 0:
            print("  %-50s 无改动，不碰文件" % rel)
            continue

        print("  %-50s %5d 处" % (rel, changed))
        for k, v in sorted(hits.items(), key=lambda x: -x[1]):
            print("        %-28s %4d -> %s" % (k, v, MAP[k]))
        grand += changed

        if apply:
            bak = path + ".bak_dyncult_" + stamp
            open(bak, "wb").write(raw)
            new_raw = "".join(out).encode("utf-8")
            if bom:
                new_raw = b"\xef\xbb\xbf" + new_raw
            open(path, "wb").write(new_raw)
            print("        备份 %s" % os.path.basename(bak))

    print("\n合计改动 %d 处" % grand)
    if not apply:
        print("（只统计，未落盘；加 --apply 生效）")


if __name__ == "__main__":
    main()
