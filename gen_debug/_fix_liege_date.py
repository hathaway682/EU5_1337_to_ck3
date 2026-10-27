#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
把 6 个头衔的 `liege` 从 1337.1.1 块里摘出来，单独放到 1337.4.1 块（2026-10-27）。

为什么：
  `_split_start_date_1337.py` 的 process_titles 只改日期行的文本，块内其余行跟着 holder 的
  EU5 `ruler_term start_date` 一起走。下面 6 个块的 holder 恰好是 EU5 里 1337.1.1 即位的
  角色（eng_hugh_le_despenser、gen_galeotto_spinola），整块被保留在 1.1，把本无日期的
  `liege` 也带了过去；而 liege 指向的领主头衔（e_hre / d_eu5_wls）的 holder 钉在 1337.4.1，
  于是 1.1 时刻领主头衔无人持有，封臣关系建立失败，开局就是无上级领主。

  改法：1.1 块只留 EU5 真正声明过日期的东西（holder / government），liege 挪到 4.1 块，
  与领主头衔上位同时建立。

默认 dry run，加 --apply 落盘。保持 BOM + CRLF。可重复跑（已有 4.1 块则跳过）。
"""
import io
import os
import re
import sys

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REL = os.path.join("history", "titles", "zz_eu5_titles.txt")
APPLY = "--apply" in sys.argv

# key -> liege 目标（改完写进 4.1 块）
TARGETS = {
    "d_eu5_gen": "e_hre",
    "c_cismonte": "e_hre",
    "c_glamorgan": "d_eu5_wls",
    "c_levante": "e_hre",
    "c_pumonte": "e_hre",
    "c_punente": "e_hre",
}

DATE_11 = "\t1337.1.1 = {"
DATE_41 = "\t1337.4.1 = {"
LOW_LIEGE = re.compile(r"^\t\tliege = (\w+)$")


def block_range(lines, key):
    """顶层块 key 的行号范围（含首尾）。"""
    pat = re.compile(r"^" + re.escape(key) + r" = \{$")
    for i, ln in enumerate(lines):
        if pat.match(ln):
            depth = 0
            for j in range(i, len(lines)):
                depth += lines[j].count("{") - lines[j].count("}")
                if depth == 0:
                    return i, j
            raise RuntimeError(f"{key}: 括号不闭合")
    return None, None


def sub_block(lines, lo, hi, header):
    """块内某个日期子块的范围（含首尾）。"""
    for i in range(lo, hi + 1):
        if lines[i] == header:
            depth = 0
            for j in range(i, hi + 1):
                depth += lines[j].count("{") - lines[j].count("}")
                if depth == 0:
                    return i, j
            raise RuntimeError(f"{header} 括号不闭合")
    return None, None


def main():
    path = os.path.join(MOD, REL)
    raw = open(path, "rb").read()
    assert raw.startswith(b"\xef\xbb\xbf"), "BOM 丢了"
    lines = raw.decode("utf-8-sig").split("\r\n")

    done, skipped = [], []
    # 行号从大到小处理，前面的插入不会影响后面的定位
    order = sorted(TARGETS, key=lambda k: -(block_range(lines, k)[0] or 0))
    for key in order:
        lo, hi = block_range(lines, key)
        if lo is None:
            skipped.append((key, "块不存在"))
            continue
        i0, i1 = sub_block(lines, lo, hi, DATE_11)
        if i0 is None:
            skipped.append((key, "没有 1337.1.1 块"))
            continue
        # 已经修过
        j0, _ = sub_block(lines, lo, hi, DATE_41)
        if j0 is not None:
            skipped.append((key, "已有 1337.4.1 块"))
            continue

        liege_idx = [k for k in range(i0, i1 + 1) if LOW_LIEGE.match(lines[k])]
        if len(liege_idx) != 1:
            skipped.append((key, f"liege 行数 {len(liege_idx)}"))
            continue
        k = liege_idx[0]
        target = LOW_LIEGE.match(lines[k]).group(1)
        if target != TARGETS[key]:
            skipped.append((key, f"liege 是 {target}，与预期 {TARGETS[key]} 不符"))
            continue

        del lines[k]                    # 摘掉 1.1 块里的 liege 行
        i1 -= 1                         # 子块尾随之上移
        lines[i1 + 1:i1 + 1] = [DATE_41, f"\t\tliege = {target}", "\t}"]
        done.append((key, target, lo + 1))

    if APPLY:
        open(path, "wb").write(b"\xef\xbb\xbf" + "\r\n".join(lines).encode("utf-8"))

    for key, target, line in done:
        print(f"  {key:14s} liege={target:10s} -> 4.1 块（块首绝对行 {line}）")
    for key, why in skipped:
        print(f"  跳过 {key:14s} {why}")
    print(f"{'已写入' if APPLY else 'dry run'}：改 {len(done)} 处，跳过 {len(skipped)} 处")


if __name__ == "__main__":
    main()
