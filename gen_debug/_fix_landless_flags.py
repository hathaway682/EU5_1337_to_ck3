# -*- coding: utf-8 -*-
"""landless 标记的两处调整（用户 2026-11-14 拍板）。

1. **去掉** `zz_vanilla_titulars.txt` 里 `e_latin_empire` / `k_jerusalem` /
   `k_spanish_galicia` 的 `landless = yes` —— 这三个将来要实际给地，不能锁成
   「无法理领地」的 titular。
2. **加上** 所有本 mod 自铸的 `{e,k,d}_eu5_<tag>` 头衔的 `landless = yes` ——
   它们是按 EU5 国家批量铸的空壳，本来就没有 de jure 领地，不标 landless 会让
   ledger 里出现「有 capital、没有法理」的怪头衔。

覆盖文件：`zz_eu5_titular.txt`、`zzz_eu5_updated_1337_titles.txt`、
`zzzz_eu5_1337_religious_orders.txt`（只处理顶层 `[ekd]_eu5_` 块，别的键不动）。

保留 UTF-8-BOM + CRLF。幂等。

用法：python gen_debug/_fix_landless_flags.py [--write]
"""
import argparse
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

REMOVE = ["e_latin_empire", "k_jerusalem", "k_spanish_galicia"]
ADD_FILES = [
    "zz_eu5_titular.txt",
    "zzz_eu5_updated_1337_titles.txt",
    "zzzz_eu5_1337_religious_orders.txt",
]
EU5_KEY = re.compile(r'(?m)^([ekd]_eu5_[a-z0-9_]+) = \{\r?\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mod", default=os.path.abspath(os.path.join(HERE, "..")))
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    root = os.path.join(args.mod, "common", "landed_titles")

    # ---- 1. 去掉三个
    p = os.path.join(root, "zz_vanilla_titulars.txt")
    txt = io.open(p, encoding="utf-8-sig", errors="ignore", newline="").read()
    for k in REMOVE:
        pat = r'(?ms)(^' + k + r' = \{\r?\n)(\tlandless = yes\r?\n)'
        txt, n = re.subn(pat, r'\1', txt)
        print("  %-20s 去掉 landless: %d" % (k, n))
    if args.write:
        with io.open(p, "wb") as fh:
            fh.write(b"\xef\xbb\xbf")
            fh.write(txt.encode("utf-8"))

    # ---- 2. 给所有 EU5 头衔加
    total_add = 0
    for name in ADD_FILES:
        p = os.path.join(root, name)
        if not os.path.isfile(p):
            print("  !! 缺文件 %s" % name)
            continue
        txt = io.open(p, encoding="utf-8-sig", errors="ignore", newline="").read()

        # 先找出所有块，跳过已经有 landless 的
        out = []
        pos = 0
        for m in EU5_KEY.finditer(txt):
            head = m.group(1)
            start = m.end()
            # 取块内容（到行首 } 为止）
            end = txt.find("\n}", start)
            body = txt[start:end if end != -1 else start + 400]
            if re.search(r'(?m)^\tlandless = yes', body):
                continue
            out.append((m.start(), m.end(), head))
        # 从后往前插入，避免位移
        for s, e, head in reversed(out):
            txt = txt[:s] + head + " = {\r\n\tlandless = yes\r\n" + txt[e:]
        total_add += len(out)
        print("  %-40s 新增 landless: %d" % (name, len(out)))
        if args.write:
            with io.open(p, "wb") as fh:
                fh.write(b"\xef\xbb\xbf")
                fh.write(txt.encode("utf-8"))

    print("\n合计新增: %d" % total_add)
    if not args.write:
        print("(dry-run，未写盘。加 --write 落盘)")


if __name__ == "__main__":
    main()
