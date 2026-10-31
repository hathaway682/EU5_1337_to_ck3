# -*- coding: utf-8 -*-
"""
宗族对齐规则 v2 —— 落地 A/B 层（2026-10-31）

读 dynasty_alignment_candidates.csv，对 tier in (A,B) 的宗族：
  1) 把 zz_eu5_dynasties.txt 里该块的 name 改成 vanilla 的 dynn_* 键；
  2) 若 vanilla 该 dynasty 在 coat_of_arms 里有条目（完整定义或单行别名），
     在 95_zz_eu5_dynasty_aliases.txt 追加 `mod_key = van_key`。
只处理 A/B；C/D/E/N 不动。rurikovich 已在 aligned 集合，不在 CSV，跳过。

用法：
  python _apply_align_v2.py            # 落地
  python _apply_align_v2.py --dry-run  # 只统计
"""
import csv
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(ROOT, "gen_debug", "dynasty_alignment_candidates.csv")
MOD_DYN = os.path.join(ROOT, "common", "dynasties", "zz_eu5_dynasties.txt")
ALIAS = os.path.join(ROOT, "common", "coat_of_arms", "coat_of_arms", "95_zz_eu5_dynasty_aliases.txt")
COA_DIR = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game\common\coat_of_arms\coat_of_arms"

RE_BLOCK = re.compile(r'^([A-Za-z0-9_\-]+)\s*=\s*\{\s*$')


def load_coa():
    coa = set()
    for fn in os.listdir(COA_DIR):
        if fn.endswith(".txt"):
            for l in open(os.path.join(COA_DIR, fn), encoding="utf-8-sig", errors="replace"):
                m = re.match(r'^([A-Za-z0-9_\-]+)\s*=', l)
                if m:
                    coa.add(m.group(1))
    return coa


def main():
    dry = "--dry-run" in sys.argv
    rows = [r for r in csv.DictReader(open(CSV, encoding="utf-8-sig")) if r["tier"] in ("A", "B")]
    targets = {r["mod_key"]: r for r in rows}
    coa = load_coa()

    # ---- 1. 改 name ----
    raw = open(MOD_DYN, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)

    changed = 0
    i = 0
    while i < len(lines):
        m = RE_BLOCK.match(lines[i])
        if m and m.group(1) in targets:
            key = m.group(1)
            van = targets[key]["van_name"]
            depth = 1
            j = i + 1
            while j < len(lines) and depth > 0:
                if depth == 1 and re.match(r'^\s*name\s*=\s*"', lines[j]):
                    lines[j] = re.sub(r'(name\s*=\s*")[^"]*(")',
                                      lambda mm: mm.group(1) + van + mm.group(2),
                                      lines[j], count=1)
                    changed += 1
                depth += lines[j].count("{") - lines[j].count("}")
                j += 1
            i = j
        else:
            i += 1

    # ---- 2. 追加 COA 别名 ----
    alias_raw = open(ALIAS, "rb").read()
    abom = alias_raw.startswith(b"\xef\xbb\xbf")
    atext = alias_raw.decode("utf-8-sig")
    anl = "\r\n" if "\r\n" in atext else "\n"
    alines = atext.split(anl)
    existing = set()
    for l in alines:
        mm = re.match(r'^([A-Za-z0-9_\-]+)\s*=', l)
        if mm:
            existing.add(mm.group(1))
    while alines and alines[-1].strip() == "":
        alines.pop()
    added = []
    no_coa = []
    for r in rows:
        if r["van_key"] in coa:
            if r["mod_key"] not in existing:
                alines.append("%s = %s" % (r["mod_key"], r["van_key"]))
                added.append(r["mod_key"])
                existing.add(r["mod_key"])
        else:
            no_coa.append(r["mod_key"])

    print("A/B 目标: %d" % len(rows))
    print("name 改动: %d" % changed)
    print("COA 别名追加: %d" % len(added))
    print("无原版 COA（只改名）: %d" % len(no_coa))

    if dry:
        print("（dry-run，未落盘）")
        return

    stamp = time.strftime("%Y%m%d_%H%M%S")
    open(MOD_DYN + ".bak_alignv2_" + stamp, "wb").write(raw)
    open(ALIAS + ".bak_alignv2_" + stamp, "wb").write(alias_raw)

    new_mod = nl.join(lines).encode("utf-8")
    if bom:
        new_mod = b"\xef\xbb\xbf" + new_mod
    open(MOD_DYN, "wb").write(new_mod)

    new_alias = anl.join(alines) + anl
    new_alias = new_alias.encode("utf-8")
    if abom:
        new_alias = b"\xef\xbb\xbf" + new_alias
    open(ALIAS, "wb").write(new_alias)
    print("已落盘，备份 .bak_alignv2_%s" % stamp)


if __name__ == "__main__":
    main()
