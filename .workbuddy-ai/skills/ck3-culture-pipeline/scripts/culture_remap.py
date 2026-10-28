# -*- coding: utf-8 -*-
"""改一个 EU5 文化的落点，并把省份层 + 人物层一次同步到位。

这是最常用的操作：用户说「XX 文化改成 YY」，就只跑这一条。

用法：
    python culture_remap.py <eu5_culture> <ck3_target> [--apply] [--note "说明"]
                             [--scope all|prov|people]

    eu5_culture   CSV 里的 culture 列，如 arpitan / balkar_culture
    ck3_target    CK3 文化 key，如 french / khazar（必须已定义）

默认 dry run。--apply 才写，且每个被改文件先备份 .bak_remap_<时间戳>。

注意：本脚本只改 CSV + 省份 + 人物层。**规则文件 `_classify_cultures.py`
必须自己用编辑工具改**（CULT_RULE 优先，必要时 LANG_RULE 一起改），
否则下次重跑分类会把改动冲掉。脚本会在最后提示需要改哪一行。
"""
import collections
import os
import re
import sys

import _common as C


def find_rule_lines(culture, language=None):
    """在规则文件里找这个 culture（及其 EU5 语言）出现在哪些表的哪一行（绝对行号）。"""
    out = []
    table = None
    keys = {'"%s"' % culture}
    if language:
        keys.add('"%s"' % language)
    for i, line in enumerate(open(C.RULES, encoding="utf-8").read().split("\n"), 1):
        m = re.match(r"^([A-Z_]+)\s*=\s*\{", line)
        if m:
            table = m.group(1)
        head = line.strip().split(":")[0].strip()
        if head in keys and table:
            out.append((i, table, line.strip()))
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    apply = "--apply" in sys.argv
    scope = "all"
    note = None
    for i, a in enumerate(sys.argv):
        if a == "--scope" and i + 1 < len(sys.argv):
            scope = sys.argv[i + 1]
        if a == "--note" and i + 1 < len(sys.argv):
            note = sys.argv[i + 1]

    if len(args) < 2:
        print(__doc__)
        sys.exit(1)
    eu5, target = args[0], args[1]

    rows = C.load_classif()
    header = list(rows[0].keys())
    row = next((r for r in rows if r["culture"] == eu5), None)
    if row is None:
        print("✗ CSV 里没有 %s" % eu5)
        sys.exit(1)

    defined = C.defined_cultures()
    if target not in defined:
        print("✗ 目标文化 %s 未定义（mod + CK3 原版都查不到），先建定义再改" % target)
        sys.exit(1)

    old = row["target"]
    print("EU5 culture : %s (%s)" % (eu5, row["name_en"]))
    print("当前 target : %s" % old)
    print("改为        : %s" % target)
    print("模式        : %s\n" % ("APPLY 落盘" if apply else "DRY RUN"))

    # ---- 规则文件提示 ----
    hits = find_rule_lines(eu5, row.get("eu5_language", "").strip() or None)
    if hits:
        print("规则文件里相关 %d 处（改完请同步，否则重跑分类会冲掉）：" % len(hits))
        for ln, table, text in hits:
            print("    绝对行 %-5d [%s] %s" % (ln, table, text))
    else:
        print("⚠ 规则文件里没有 %s 的条目 —— 需要在 CULT_RULE 里新增一行" % eu5)
    print()

    # ---- CSV ----
    if old != target:
        row["target"] = target
        if note:
            row["note"] = note
        if apply:
            C.backup(C.CLASSIF, "remap")
            C.save_classif(rows, header)
        print("CSV  1 行  %s: %s -> %s" % (eu5, old, target))
    else:
        print("CSV  无需改动（已是 %s）" % target)

    # ---- 省份 ----
    if scope in ("all", "prov"):
        hit_cty = C.counties_for_eu5_cultures([eu5])
        _, pids = C.county_structure()
        want = sorted({p for c in hit_cty for p in pids.get(c, [])})
        n, det = C.rewrite_provinces(want, target, apply=apply)
        print("省份 %d 行（%d 个 county / %d 个 province，EU5 province: %s）"
              % (n, len(hit_cty), len(want), sorted(set(hit_cty.values()))))
        for (a, b), v in det.most_common(10):
            print("      %-24s -> %-24s %4d" % (a, b, v))

    # ---- 人物 ----
    if scope in ("all", "people"):
        res = C.rewrite_people({eu5: target}, apply=apply)
        tot = 0
        for rel, (n, det) in res.items():
            if n:
                print("人物 %-52s %6d" % (rel, n))
                tot += n
        print("人物合计 %d 行" % tot)

    if not apply:
        print("\nDRY RUN：未写入。加 --apply 执行。")


if __name__ == "__main__":
    main()
