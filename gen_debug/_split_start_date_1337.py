#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
把 mod 里的 1337.1.1 拆成两类（2026-10-23）：

  A. 来自 EU5 原始记录的日期 —— EU5 setup 里字面就写着 1337.1.1 → 保留
  B. 我们自己钉的「开局触发」基线 → 改成 1337.4.1

判定依据（查证 EU5/game/main_menu/setup/start/）：
  * 10_countries.txt：14 个 ruler_term 的 start_date = 1337.1.1（角色见 RULERS_1337_1_1）
    → 这些角色作为 holder 的 title 块保留
  * 10_countries.txt：全库只有 MRI 的 start_regency_date = 1337.1.1
    → 该摄政块保留，其余摄政块是基线
  * 05_characters.txt：birth_date ×46 / death_date ×7 = 1337.1.1 → 保留；
    全库没有 marriage_date，所以 add_spouse 的 1337.1.1 是基线
  * government / 世族头衔 / 其余 title 基线 → 全部改 4.1

默认 dry run，加 --apply 落盘。保持 BOM + CRLF。
"""
import os
import re
import sys

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPLY = "--apply" in sys.argv

D_OLD = b"1337.1.1"
D_NEW = b"1337.4.1"

# EU5 10_countries.txt 里 start_date = 1337.1.1 的 ruler_term 角色（14 个）
RULERS_1337_1_1 = {
    "asc_angelo_del_signor_bartolomeo_di_rieti",
    "bud_heinrich_ii_isenburg",
    "cev_bonifacio_ii_di_ceva",
    "dul_karaca",
    "eng_hugh_le_despenser",
    "erm_hermann_of_prague",
    "feo_demetrios_gabras",
    "fer_obizzo_iii_este",
    "gen_galeotto_spinola",
    "jaw_henryk_i_javorski",
    "nmd_boleslaw_elder",
    "nur_rappold_von_kulsheim",
    "rag_filippo_belegno",
    "tes_kazimir_piast",
}

# EU5 里 start_regency_date = 1337.1.1 的摄政块（只有毛利）
REGENT_BLOCKS_1337_1_1 = {"jap_mori_motoharu"}

DATE_LINE = re.compile(rb"^\t1337\.1\.1 = \{")
TOP_KEY = re.compile(rb"^([A-Za-z0-9_]+) = \{")
HOLDER = re.compile(rb"holder = ([A-Za-z0-9_]+)")


def load(path):
    with open(path, "rb") as f:
        return f.read().split(b"\r\n")


def save(path, lines):
    with open(path, "wb") as f:
        f.write(b"\r\n".join(lines))


def block_holder(lines, i):
    """从 1337.1.1 行往下找 holder，遇到块结束就停。"""
    for k in range(i + 1, min(i + 8, len(lines))):
        m = HOLDER.search(lines[k])
        if m:
            return m.group(1).decode()
        if lines[k].rstrip() in (b"\t}", b"}"):
            break
    return None


def process_titles(rel):
    """title 块：holder 属于 EU5 里 1337.1.1 即位的 14 人则保留，其余改 4.1。"""
    path = os.path.join(MOD, rel)
    lines = load(path)
    keep = change = 0
    kept_holders = []
    for i, line in enumerate(lines):
        if not DATE_LINE.match(line):
            continue
        holder = block_holder(lines, i)
        if holder in RULERS_1337_1_1:
            keep += 1
            kept_holders.append(holder)
        else:
            lines[i] = line.replace(D_OLD, D_NEW)
            change += 1
    if APPLY:
        save(path, lines)
    return keep, change, kept_holders


def process_all(rel):
    """整个文件里的 1337.1.1 全部当基线改掉。"""
    path = os.path.join(MOD, rel)
    lines = load(path)
    change = 0
    for i, line in enumerate(lines):
        if DATE_LINE.match(line) or b"1337.1.1" in line:
            if b"1337.1.1" in line:
                lines[i] = line.replace(D_OLD, D_NEW)
                change += 1
    if APPLY:
        save(path, lines)
    return change


def process_diarchy(rel):
    """摄政块：只有毛利那块保留，其余改 4.1。"""
    path = os.path.join(MOD, rel)
    lines = load(path)
    keep = change = 0
    current = None
    for i, line in enumerate(lines):
        m = TOP_KEY.match(line)
        if m:
            current = m.group(1).decode()
        if b"1337.1.1" not in line:
            continue
        if current in REGENT_BLOCKS_1337_1_1:
            keep += 1
        else:
            lines[i] = line.replace(D_OLD, D_NEW)
            change += 1
    if APPLY:
        save(path, lines)
    return keep, change


def process_characters(rel):
    """人物：birth/death 来自 EU5 的 birth_date/death_date，保留；add_spouse 与多行块是基线。"""
    path = os.path.join(MOD, rel)
    lines = load(path)
    keep = change = 0
    for i, line in enumerate(lines):
        if b"1337.1.1" not in line:
            continue
        if line == b"\t1337.1.1 = { birth = yes }" or line == b"\t1337.1.1 = { death = yes }":
            keep += 1
        else:
            lines[i] = line.replace(D_OLD, D_NEW)
            change += 1
    if APPLY:
        save(path, lines)
    return keep, change


def main():
    print("mode:", "APPLY" if APPLY else "DRY RUN")
    print()
    total_keep = total_change = 0

    for rel in ("history/titles/zz_eu5_titles.txt",
                "history/characters/zz_eu5_titles.txt"):
        keep, change, holders = process_titles(rel)
        total_keep += keep
        total_change += change
        print(f"{rel}")
        print(f"    保留(EU5 1337.1.1 即位) {keep:5d}   改 4.1 {change:5d}")
        if holders:
            uniq = sorted(set(holders))
            print(f"    保留的 holder: {len(uniq)} 人 -> {', '.join(uniq[:6])}{' ...' if len(uniq) > 6 else ''}")

    for rel in ("history/characters/zz_eu5_government.txt",
                "history/titles/zzz_eu5_japan_noble_families.txt"):
        change = process_all(rel)
        total_change += change
        print(f"{rel}")
        print(f"    改 4.1 {change:5d}")

    keep, change = process_diarchy("history/characters/zz_eu5_diarchy_regencies.txt")
    total_keep += keep
    total_change += change
    print("history/characters/zz_eu5_diarchy_regencies.txt")
    print(f"    保留(毛利) {keep:5d}   改 4.1 {change:5d}")

    keep, change = process_characters("history/characters/zz_eu5_characters.txt")
    total_keep += keep
    total_change += change
    print("history/characters/zz_eu5_characters.txt")
    print(f"    保留(birth/death) {keep:5d}   改 4.1 {change:5d}")

    print()
    print(f"合计：保留 {total_keep}   改 4.1 {total_change}")


if __name__ == "__main__":
    main()
