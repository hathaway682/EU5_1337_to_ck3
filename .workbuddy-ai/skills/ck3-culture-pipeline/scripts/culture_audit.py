# -*- coding: utf-8 -*-
"""文化体检（只读）。任何文化改动前后都可以跑，不改文件。

用法：
    python culture_audit.py            # 全量体检
    python culture_audit.py --brief    # 只看有问题的项

检查项：
  1. CSV 里还剩多少 NEW:（= 尚未给落点）
  2. CSV 的 target 是否有未定义的文化
  3. 省份层 / 人物层是否还有「EU5 key 但 CSV 已给落点」= 未同步
  4. 省份层 / 人物层是否引用了未定义文化
  5. county 内文化是否一致
  6. 省份文件 BOM / CRLF
"""
import collections
import os
import sys

import _common as C


def main():
    brief = "--brief" in sys.argv
    rows = C.load_classif()
    defined = C.defined_cultures()

    mapping = {}
    for r in rows:
        t = r["target"]
        if not t or t.startswith("NEW:") or t == r["culture"]:
            continue
        mapping[r["culture"]] = t

    print("CSV %d 行 | 有效映射 %d 条 | 已定义文化 %d 个\n"
          % (len(rows), len(mapping), len(defined)))

    # 1) 剩余 NEW:
    news = [r for r in rows if r["target"].startswith("NEW:")]
    print("[1] 剩余 NEW: %d 个" % len(news))
    if news:
        for r in sorted(news, key=lambda x: -int(x["baronies"] or 0))[:20]:
            print("    %-28s %-12s %4s bar  %s"
                  % (r["culture"], r["continent"], r["baronies"], r["target"]))

    # 2) target 未定义
    bad_target = sorted({v for v in mapping.values() if v not in defined})
    print("[2] target 未定义 %d 个 %s" % (len(bad_target), bad_target[:10]))

    # 3) 省份层未同步
    pc = C.province_cultures()
    stale_p = {k: v for k, v in pc.items() if k in mapping and mapping[k] != k}
    print("[3] 省份层未同步 %d 个 province" % len(stale_p))
    if stale_p and not brief:
        c = collections.Counter(stale_p.values())
        for k, v in c.most_common(10):
            print("    %-28s %4d -> %s" % (k, v, mapping[k]))

    # 4) 人物层未同步
    tot_stale = 0
    per_file = {}
    for rel in C.PEOPLE:
        p = os.path.join(C.MOD, rel)
        if not os.path.exists(p):
            continue
        text, _ = C.read_text(p)
        n = 0
        for line in text.split("\n"):
            mm = C.RE_CULT.match(line.rstrip("\r"))
            if not mm:
                continue
            k = mm.group(3)
            if k in mapping and mapping[k] != k and k not in C.KEEP_IN_PEOPLE:
                n += 1
        if n:
            per_file[rel] = n
            tot_stale += n
    print("[4] 人物层未同步 %d 行" % tot_stale)
    for rel, n in sorted(per_file.items(), key=lambda x: -x[1]):
        print("    %-52s %6d" % (rel, n))

    # 5) 引用未定义文化
    undef_p = sorted({v for v in pc.values() if v not in defined})
    undef_people = set()
    for rel in C.PEOPLE:
        p = os.path.join(C.MOD, rel)
        if not os.path.exists(p):
            continue
        text, _ = C.read_text(p)
        for line in text.split("\n"):
            mm = C.RE_CULT.match(line.rstrip("\r"))
            if mm and mm.group(3) not in defined:
                undef_people.add(mm.group(3))
    print("[5] 未定义文化：省份 %d 个 %s | 人物 %d 个 %s"
          % (len(undef_p), undef_p[:5], len(undef_people), sorted(undef_people)[:5]))

    # 6) county 一致性
    bars, pids = C.county_structure()
    mixed = tot = 0
    for cty, ids in pids.items():
        vals = [pc[p] for p in ids if p in pc]
        if len(vals) < 2:
            continue
        tot += 1
        if len(set(vals)) > 1:
            mixed += 1
    print("[6] county 内不一致 %d/%d" % (mixed, tot))

    # 7) 文件格式
    fmt = C.check_format(C.PROV)
    print("[7] 省份文件 BOM=%s CRLF=%d 裸LF=%d"
          % (fmt["bom"], fmt["crlf"], fmt["bare_lf"]))

    # 8) 分布
    cnt = collections.Counter(pc.values())
    print("[8] 省份文化 %d 种 / %d 引用；前 10：%s"
          % (len(cnt), sum(cnt.values()), cnt.most_common(10)))


if __name__ == "__main__":
    main()
