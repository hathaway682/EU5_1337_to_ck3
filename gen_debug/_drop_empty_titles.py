# -*- coding: utf-8 -*-
"""删除「EU5 里没有领土、也没有任何世系」的空壳头衔。

对象：`gen_debug/eu5_ck3_title_map.csv` 里 note 带 `landless-in-eu5` /
`building-in-eu5`、原键形如 `{e,k,d}_eu5_<tag>` 的行（共 32 个）。
这些是 `_export_title_map.py` 按 EU5 国家批量铸的空壳，1337 年既没人持有、
EU5 侧也没有 `ruler_term` 世系，留着只会占位。

**不动** `c_` / `b_` 开头的地理头衔（属于 CU 法理树），也不动日本 `c_nf_*`
与 `e_eu5_ntc|stc|ymt`。

删除范围（只这三个地方，全库已确认无其它引用）：
  1. common/landed_titles/zz_eu5_titular.txt 的声明块
  2. localization/<11 种语言>/zz_eu5_politics_l_<lang>.yml 的键行
  3. gen_debug/eu5_ck3_title_map.csv 的 note 不动（`was <key>` 保留线索）

用法：python gen_debug/_drop_empty_titles.py [--write]
"""
import argparse
import csv
import io
import os
import re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
SHELL = re.compile(r'^[ekd]_eu5_[a-z0-9]+$')


def collect_keys(mod):
    path = os.path.join(mod, "gen_debug", "eu5_ck3_title_map.csv")
    rows = csv.DictReader(io.open(path, encoding="utf-8-sig", newline=""))
    keys = {}
    for r in rows:
        if r["kind"] != "country":
            continue
        if "landless-in-eu5" not in r["note"] and "building-in-eu5" not in r["note"]:
            continue
        m = re.search(r'(?:^|,)was ([A-Za-z0-9_-]+)', r["note"])
        if m and SHELL.match(m.group(1)):
            keys[m.group(1)] = r["eu5_tag"]
    return keys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mod", default=os.path.abspath(os.path.join(HERE, "..")))
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    keys = collect_keys(args.mod)
    print("空壳头衔: %d 个" % len(keys))
    print("  " + " ".join(sorted(keys)))

    # ---- 1. 声明
    p1 = os.path.join(args.mod, "common", "landed_titles", "zz_eu5_titular.txt")
    t1 = io.open(p1, encoding="utf-8-sig", errors="ignore", newline="").read()
    n1 = 0
    for k in keys:
        t1, c = re.subn(r'(?ms)^' + k + r' = \{\r?\n.*?^\}\r?\n(?:\r?\n)?', '', t1)
        n1 += c
        if c == 0:
            print("  !! 声明缺失: %s" % k)

    # ---- 2. 本地化
    n2 = 0
    loc_dir = os.path.join(args.mod, "localization")
    loc_files = []
    for lang in sorted(os.listdir(loc_dir)):
        f = os.path.join(loc_dir, lang, "zz_eu5_politics_l_%s.yml" % lang)
        if os.path.isfile(f):
            loc_files.append(f)
    for f in loc_files:
        txt = io.open(f, encoding="utf-8-sig", errors="ignore", newline="").read()
        before = txt
        for k in keys:
            txt = re.sub(r'(?m)^\s*' + k + r':\d*\s*"[^"]*"\s*\r?\n', '', txt)
        if txt != before:
            n2 += len(before.splitlines()) - len(txt.splitlines())
            if args.write:
                with io.open(f, "wb") as fh:
                    fh.write(b"\xef\xbb\xbf")
                    fh.write(txt.encode("utf-8"))

    print("声明块删除: %d 条" % n1)
    print("本地化行删除: %d 行（%d 个语言文件）" % (n2, len(loc_files)))

    if not args.write:
        print("\n(dry-run，未写盘。加 --write 落盘)")
        return

    with io.open(p1, "wb") as fh:
        fh.write(b"\xef\xbb\xbf")
        fh.write(t1.encode("utf-8"))
    print("\nwritten: %s" % p1)


if __name__ == "__main__":
    main()
