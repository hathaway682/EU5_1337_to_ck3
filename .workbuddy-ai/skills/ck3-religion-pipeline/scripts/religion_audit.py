# -*- coding: utf-8 -*-
"""宗教地图只读体检。

不写任何文件。回答四类问题：
  1. 文件本身有没有坏（BOM / 纯 CRLF / 括号平衡）
  2. faith / rite 各有多少省，中文名是什么
  3. **rite 的父 faith 和省里的 faith 对不对得上**（写错 faith 是 CK3 里最隐蔽的 bug）
  4. 有多少省靠 faith 的 main_rite 回落（= 没写 rite 行）

用法：
    python religion_audit.py                 # 全量概览
    python religion_audit.py --top 40        # 看更长的榜
    python religion_audit.py --faith mahayana_faith
    python religion_audit.py --rite dhyana
    python religion_audit.py --county c_ninghai
    python religion_audit.py --provs dhyana  # 列出该 rite 的所有省 id
"""
import argparse
import sys
from collections import Counter, defaultdict

import _common as C


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--faith")
    ap.add_argument("--rite")
    ap.add_argument("--county")
    ap.add_argument("--provs", metavar="RITE_OR_FAITH",
                    help="列出该值对应的所有省 id")
    ap.add_argument("--no-loc", action="store_true", help="不加载中文名（更快）")
    a = ap.parse_args()

    lines, sep = C.read_prov()
    faith, rite = C.parse_state(lines)
    faiths = C.load_faiths()
    rites = C.load_rites()
    loc = {} if a.no_loc else C.load_loc_zh()

    def zh(k):
        return loc.get(k, "")

    def tag(k):
        z = zh(k)
        return "%s(%s)" % (k, z) if z else k

    # ---------- 1) 字节体检 ----------
    st = C.byte_stats()
    print("=" * 74)
    print("文件：%s" % C.PROV)
    print("  %d 字节 | BOM %s | CRLF %d | LF %d | 裸 LF %d | 括号 %d/%d %s"
          % (st["bytes"], "有" if st["bom"] else "★缺",
             st["crlf"], st["lf"], st["lone_lf"],
             st["open"], st["close"],
             "OK" if st["open"] == st["close"] else "★不平衡"))
    if st["lone_lf"]:
        print("  ★ 存在裸 LF，说明某次写盘没保住 CRLF")
    print("  省份块 %d 个 | 有 faith %d | 有 rite %d"
          % (len({p for p, _b, _i in C.iter_blocks(lines) if p is not None}),
             len(faith), len(rite)))

    # ---------- 2) 统计 ----------
    print("=" * 74)
    print("faith 分布（共 %d 种）" % len(set(faith.values())))
    for k, v in Counter(faith.values()).most_common(a.top):
        print("  %-34s %5d  %s" % (k, v, zh(k)))

    print("-" * 74)
    print("rite 分布（共 %d 种）" % len(set(rite.values())))
    for k, v in Counter(rite.values()).most_common(a.top):
        print("  %-34s %5d  %s" % (k, v, zh(k)))

    # ---------- 3) rite 与省 faith 是否同一个 religion ----------
    # 判据是 religion 而不是 faith：vanilla 的 9 个基督教礼全绑在伞形 faith
    # `christian_faith` 上，而省份写的是 orthodox / catholic，这是正常的。
    print("=" * 74)
    bad = defaultdict(list)
    sibling = Counter()
    for p, r in rite.items():
        parent = rites.get(r, {}).get("faith")
        if parent is None:
            bad["rite 未定义或无 faith 字段"].append((p, r, None))
            continue
        own = faith.get(p)
        if own is None:
            continue                      # 只有 rite 行、没有 faith 行 = 故意的写法
        rel_own = faiths.get(own, {}).get("religion")
        rel_par = faiths.get(parent, {}).get("religion")
        if rel_own and rel_par and rel_own != rel_par:
            bad["★省 faith 与 rite 的 religion 不同（真错）"].append(
                (p, r, "%s(%s) vs %s(%s)" % (own, rel_own, parent, rel_par)))
        elif own != parent:
            sibling[(r, own, parent)] += 1
    if not bad:
        print("rite 归属校验：没有跨 religion 的错配 ✓")
    for k, rows in bad.items():
        print("%s：%d 省" % (k, len(rows)))
        for p, r, d in rows[:20]:
            print("   %-7d %-18s %s" % (p, r, d or ""))
        if len(rows) > 20:
            print("   ...（共 %d 省，用 --provs 或 --rite 细查）" % len(rows))
    if sibling:
        print("同 religion 内的兄弟 faith（正常，不用改）：%d 省" % sum(sibling.values()))
        for (r, own, parent), n in sibling.most_common(8):
            print("   rite %-18s 省faith %-18s 父faith %-20s %5d" % (r, own, parent, n))

    # ---------- 4) 靠 main_rite 回落的省 ----------
    print("=" * 74)
    fallback = Counter()
    no_main = Counter()
    for p, f in faith.items():
        if p in rite:
            continue
        mr = faiths.get(f, {}).get("main_rite")
        if mr:
            fallback[(f, mr)] += 1
        else:
            no_main[f] += 1
    print("没写 rite 行、靠 faith 的 main_rite 回落：%d 省" % sum(fallback.values()))
    for (f, mr), n in fallback.most_common(a.top):
        print("  %-28s -> main_rite %-16s %5d" % (f, mr, n))
    if no_main:
        print("★ faith 没有 main_rite（这些省在游戏里 fallback 到 religion 默认，容易出错）：")
        for f, n in no_main.most_common():
            print("  %-34s %5d  %s" % (f, n, zh(f)))

    # ---------- 5) 未定义 key ----------
    print("=" * 74)
    und = sorted({f for f in faith.values() if f not in faiths})
    unr = sorted({r for r in rite.values() if r not in rites})
    print("省份里出现但 faith_types 未定义的 faith：%d %s" % (len(und), und[:10]))
    print("省份里出现但 rite_types 未定义的 rite：%d %s" % (len(unr), unr[:10]))

    # ---------- 6) 定向查询 ----------
    if a.faith:
        sel = sorted(p for p, f in faith.items() if f == a.faith)
        print("=" * 74)
        print("faith = %s：%d 省" % (a.faith, len(sel)))
        for r, n in Counter(rite.get(p, "<无 rite 行>") for p in sel).most_common():
            print("  rite %-24s %4d  %s" % (r, n, zh(r)))
    if a.rite:
        sel = sorted(p for p, r in rite.items() if r == a.rite)
        print("=" * 74)
        print("rite = %s：%d 省（父 faith %s）"
              % (a.rite, len(sel), rites.get(a.rite, {}).get("faith")))
        for f, n in Counter(faith.get(p, "<无 faith 行>") for p in sel).most_common():
            print("  faith %-28s %4d" % (f, n))
    if a.county:
        pc = C.load_prov_county()
        sel = sorted(p for p, c in pc.items() if c == a.county)
        if not sel:
            print("★ 没找到伯爵领 %s" % a.county)
        else:
            print("=" * 74)
            print("%s：%d 省" % (a.county, len(sel)))
            for p in sel:
                print("  %-7d faith=%-26s rite=%-18s %s"
                      % (p, faith.get(p, "-"), rite.get(p, "-"),
                         zh(rite.get(p, ""))))
    if a.provs:
        key = a.provs
        sel = sorted(p for p, r in rite.items() if r == key) or \
              sorted(p for p, f in faith.items() if f == key)
        print("=" * 74)
        print("%s 的省（%d 个）：" % (key, len(sel)))
        print("  " + " ".join(str(p) for p in sel))


if __name__ == "__main__":
    sys.exit(main())
