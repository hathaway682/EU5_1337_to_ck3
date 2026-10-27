# -*- coding: utf-8 -*-
"""外科手术式改省份的 faith / rite。默认 dry-run。

只改目标省的 `faith =` / `rite =` 行，其它字节一个不动（culture / holding / 注释原样），
BOM 与 CRLF 按原文件保留。内容无变化就不写盘（连 mtime 都不动）。

用法：
    # 看会发生什么（不写盘）
    python religion_set.py --prov 8839 --rite quanzhen
    # 真写
    python religion_set.py --prov 8839 --rite quanzhen --apply

    # 整个伯爵领
    python religion_set.py --county c_ninghai --rite shangqing --apply

    # 一批省 id（文件里一行一个，或用空格/逗号分隔）
    python religion_set.py --prov-file ids.txt --rite dhyana --apply
    python religion_set.py --provs "7364 7384 7418" --rite daoxue --apply

    # 同时改 faith
    python religion_set.py --prov 8839 --faith mahayana_faith --rite dhyana --apply

    # 删掉 faith 行，只留 rite（CK3 里「有 rite 就不写 faith」的写法）
    python religion_set.py --prov 9368 --rite acharya --drop-faith --apply

    # 把某个值整体换成另一个（全库替换，慎用）
    python religion_set.py --rename-rite shangqing=quanzhen --apply

校验（不加 --force 时生效）：
  * rite 必须在 rite_types 里有定义；
  * 写的 rite 的父 faith 必须等于该省的 faith（省没有 faith 行时跳过这条）；
  * 要写的 faith 必须在 faith_types 里有定义。
"""
import argparse
import os
import re
import shutil
import sys
import time

import _common as C


def parse_ids(s):
    return {int(x) for x in re.split(r"[\s,]+", s.strip()) if x.isdigit()}


def find_line(body, pattern):
    """-> (index, match) or (None, None)"""
    for i, line in enumerate(body):
        m = pattern.match(line)
        if m:
            return i, m
    return None, None


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_argument_group("目标省")
    g.add_argument("--prov")
    g.add_argument("--provs")
    g.add_argument("--prov-file")
    g.add_argument("--county")
    g.add_argument("--all-faith", help="该 faith 的全部省")
    g.add_argument("--all-rite", help="该 rite 的全部省")
    ap.add_argument("--faith")
    ap.add_argument("--rite")
    ap.add_argument("--drop-faith", action="store_true",
                    help="设 rite 的同时删掉 faith 行")
    ap.add_argument("--force", action="store_true", help="跳过父 faith 校验")
    ap.add_argument("--rename-rite", help="全库替换 rite：old=new")
    ap.add_argument("--rename-faith", help="全库替换 faith：old=new")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    lines, sep = C.read_prov()
    faiths = C.load_faiths()
    rites = C.load_rites()

    # ---------- 全库替换模式 ----------
    if a.rename_rite or a.rename_faith:
        if a.rename_rite:
            old, new = a.rename_rite.split("=", 1)
            if new not in rites:
                sys.exit("★ rite %s 未定义" % new)
            pat, patname = C.RITE_LINE, "rite"
        else:
            old, new = a.rename_faith.split("=", 1)
            if new not in faiths:
                sys.exit("★ faith %s 未定义" % new)
            pat, patname = C.FAITH_LINE, "faith"
        n, out = 0, []
        for pid, body, close in C.iter_blocks(lines):
            if pid is None:
                out.extend(body)
                continue
            nb = []
            for line in body:
                m = pat.match(line)
                if m and m.group(2) == old:
                    nb.append("%s%s = %s" % (m.group(1), patname, new))
                    n += 1
                else:
                    nb.append(line)
            out.append("%d = {" % pid)
            out.extend(nb)
            out.append("}")
        print("替换 %s = %s -> %s：%d 处" % (patname, old, new, n))
        if not a.apply:
            print("（dry run，加 --apply 才写盘）")
            return 0
        if not n:
            print("无变化，不写盘。")
            return 0
        bak = C.PROV + ".bak_religionset_" + time.strftime("%Y%m%d_%H%M%S")
        shutil.copy2(C.PROV, bak)
        C.write_prov(out, sep)
        print("已写入。备份：%s" % bak)
        return 0

    # ---------- 目标省集合 ----------
    faith_now, rite_now = C.parse_state(lines)
    targets = set()
    if a.prov:
        targets |= parse_ids(a.prov)
    if a.provs:
        targets |= parse_ids(a.provs)
    if a.prov_file:
        targets |= parse_ids(io_read(a.prov_file))
    if a.county:
        cp = C.county_provinces()
        if a.county not in cp:
            sys.exit("★ 没找到伯爵领 %s" % a.county)
        targets |= set(cp[a.county])
    if a.all_faith:
        targets |= {p for p, f in faith_now.items() if f == a.all_faith}
    if a.all_rite:
        targets |= {p for p, r in rite_now.items() if r == a.all_rite}

    if not targets:
        sys.exit("★ 没有目标省。用 --prov / --county / --prov-file / --all-faith / --all-rite")
    if not (a.faith or a.rite):
        sys.exit("★ 要给 --faith 或 --rite")

    # ---------- 校验 ----------
    if a.faith and a.faith not in faiths:
        sys.exit("★ faith %s 在 faith_types 里没有定义" % a.faith)
    if a.rite and a.rite not in rites:
        sys.exit("★ rite %s 在 rite_types 里没有定义" % a.rite)
    if a.rite and not a.force and not a.drop_faith:
        parent = rites[a.rite]["faith"]
        rel_par = faiths.get(parent, {}).get("religion")
        clash = []
        for p in targets:
            own = a.faith or faith_now.get(p)     # 同时改 faith 时按新 faith 判
            if own is None:
                continue
            rel_own = faiths.get(own, {}).get("religion")
            if rel_own and rel_par and rel_own != rel_par:
                clash.append((p, own, rel_own))
        if clash:
            print("★ %d 个省的 faith 与 %s 不在同一个 religion（rite 父 faith %s = %s）："
                  % (len(clash), a.rite, parent, rel_par))
            for p, own, rel in sorted(clash)[:8]:
                print("    %-7d faith=%-24s religion=%s" % (p, own, rel))
            print("  如确实要写，加 --force；或者用 --drop-faith 删掉 faith 行只留 rite。")
            return 1

    # ---------- 改块 ----------
    plan = {}
    out = []
    stat = {"faith 改写": 0, "faith 新增": 0, "faith 删除": 0,
            "rite 改写": 0, "rite 新增": 0, "rite 删除": 0}
    for pid, body, _close in C.iter_blocks(lines):
        if pid is None or pid not in targets:
            out.extend(body if pid is None else ["%d = {" % pid] + body + ["}"])
            continue
        nb = list(body)
        fi, fm = find_line(nb, C.FAITH_LINE)
        ri, rm = find_line(nb, C.RITE_LINE)
        cur_f = fm.group(2) if fm else None
        cur_r = rm.group(2) if rm else None

        # faith
        if a.drop_faith:
            if fi is not None:
                nb.pop(fi)
                stat["faith 删除"] += 1
                ri = ri - 1 if ri is not None and ri > fi else ri
                rm = C.RITE_LINE.match(nb[ri]) if ri is not None else None
            want_f = None
        else:
            want_f = a.faith
        if want_f is not None:
            if fi is not None:
                if cur_f != want_f:
                    nb[fi] = "%sfaith = %s" % (fm.group(1), want_f)
                    stat["faith 改写"] += 1
            else:
                indent = rm.group(1) if rm else "\t"
                pos = ri if ri is not None else 0
                nb.insert(pos, "%sfaith = %s" % (indent, want_f))
                stat["faith 新增"] += 1
                ri = ri + 1 if ri is not None else ri

        # rite
        if a.rite is not None:
            ri, rm = find_line(nb, C.RITE_LINE)
            if ri is not None:
                if rm.group(2) != a.rite:
                    nb[ri] = "%srite = %s" % (rm.group(1), a.rite)
                    stat["rite 改写"] += 1
            else:
                fi, fm2 = find_line(nb, C.FAITH_LINE)
                indent = fm2.group(1) if fm2 else "\t"
                pos = (fi + 1) if fi is not None else 0
                nb.insert(pos, "%srite = %s" % (indent, a.rite))
                stat["rite 新增"] += 1

        plan[pid] = (cur_f, cur_r, a.faith if not a.drop_faith else None, a.rite)
        out.append("%d = {" % pid)
        out.extend(nb)
        out.append("}")

    print("目标省 %d 个" % len(targets))
    for k, v in stat.items():
        if v:
            print("  %-10s %d" % (k, v))
    for p in sorted(plan)[:12]:
        cf, cr, wf, wr = plan[p]
        fs = "(删掉)" if a.drop_faith else (wf or "(不改)")
        print("  %-7d faith %-24s -> %-14s | rite %-16s -> %s"
              % (p, cf or "-", fs, cr or "-", wr or "(不改)"))
    if len(plan) > 12:
        print("  ...（共 %d 个）" % len(plan))

    changed = sum(stat.values())
    if not changed:
        print("无变化，不写盘。")
        return 0
    if not a.apply:
        print("（dry run，加 --apply 才写盘）")
        return 0

    bak = C.PROV + ".bak_religionset_" + time.strftime("%Y%m%d_%H%M%S")
    shutil.copy2(C.PROV, bak)
    C.write_prov(out, sep)
    st = C.byte_stats()
    print("已写入。备份：%s" % bak)
    print("校验：BOM %s | 裸 LF %d | 括号 %d/%d"
          % ("有" if st["bom"] else "★缺", st["lone_lf"], st["open"], st["close"]))
    return 0


def io_read(path):
    return open(path, encoding="utf-8").read()


if __name__ == "__main__":
    sys.exit(main())
