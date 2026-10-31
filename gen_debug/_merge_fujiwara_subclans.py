# -*- coding: utf-8 -*-
"""
把藤原系 8 个「中间层」dynasty 降级并入 fujiwara_dynasty（2026-10-31）

用户定：臣籍降下的源/平/大和系不并入大和（不动）；藤原的子系要并入藤原。
本脚本只处理 fujiwara_subclans 里的 8 个：
  hatano / kondou / kudou / nakamura / oyama / saitou / sanjou / utsunomiya

动作：
 1) zz_eu5_dynasties.txt：删除这 8 个独立 dynasty 定义块
 2) zz_eu5_merged_houses.txt：
    a) 26 个子 house 的 `dynasty = X` -> `dynasty = fujiwara_dynasty`
    b) 新增 8 个 `house_<name>`（dynasty = fujiwara_dynasty，name 沿用原 dynasty 的 name）
 3) history/characters/zz_eu5_characters.txt：88 个角色
    `dynasty = X` -> `dynasty = fujiwara_dynasty` + `dynasty_house = house_<name>`
 4) 95_zz_eu5_dynasty_aliases.txt：3 条 `X_dynasty = target` -> `house_<name> = target`

用法：
  python _merge_fujiwara_subclans.py --dry-run
  python _merge_fujiwara_subclans.py
"""
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DYN = os.path.join(ROOT, "common", "dynasties", "zz_eu5_dynasties.txt")
HOU = os.path.join(ROOT, "common", "dynasty_houses", "zz_eu5_merged_houses.txt")
CHR = os.path.join(ROOT, "history", "characters", "zz_eu5_characters.txt")
ALIAS = os.path.join(ROOT, "common", "coat_of_arms", "coat_of_arms", "95_zz_eu5_dynasty_aliases.txt")

KEYS = ["hatano_dynasty", "kondou_dynasty", "kudou_dynasty", "nakamura_dynasty",
        "oyama_dynasty", "saitou_dynasty", "sanjou_dynasty", "utsunomiya_dynasty"]
NEW_HOUSE = {x: "house_" + x[:-8] for x in KEYS}
ALIAS_MAP = {"kudou_dynasty": "house_kudou", "saitou_dynasty": "house_saitou",
             "hatano_dynasty": "house_hatano"}
PAT = re.compile(r'^([ \t]*)dynasty[ \t]*=[ \t]*(%s)[ \t]*$' % "|".join(KEYS))


def read(path):
    raw = open(path, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    nl = "\r\n" if "\r\n" in text else "\n"
    return raw, bom, nl, text.split(nl)


def write(path, lines, nl, bom):
    data = nl.join(lines).encode("utf-8")
    if bom:
        data = b"\xef\xbb\xbf" + data
    open(path, "wb").write(data)


def main():
    dry = "--dry-run" in sys.argv

    # ---- 1. dynasties: 删除 8 个块，顺手抓 name/culture ----
    raw_d, bom_d, nl_d, lines = read(DYN)
    dyninfo = {}
    out = []
    i = 0
    removed = []
    while i < len(lines):
        m = re.match(r'^([A-Za-z0-9_\-]+)\s*=\s*\{\s*$', lines[i])
        if m and m.group(1) in KEYS:
            k = m.group(1)
            depth = 1
            j = i + 1
            nm = cu = None
            while j < len(lines) and depth > 0:
                depth += lines[j].count("{") - lines[j].count("}")
                if depth > 0:
                    mm = re.match(r'\s*name\s*=\s*"([^"]*)"', lines[j])
                    if mm:
                        nm = mm.group(1)
                    mc = re.match(r'\s*culture\s*=\s*"([^"]*)"', lines[j])
                    if mc:
                        cu = mc.group(1)
                j += 1
            dyninfo[k] = (nm, cu)
            removed.append(k)
            i = j
            if i < len(lines) and lines[i].strip() == "":
                i += 1
        else:
            out.append(lines[i])
            i += 1
    lines_dyn = out

    # ---- 2. houses: 子 house 改挂 fujiwara + 新增 8 个 house ----
    raw_h, bom_h, nl_h, lines = read(HOU)
    nsub = 0
    for idx, l in enumerate(lines):
        m = PAT.match(l)
        if m:
            lines[idx] = m.group(1) + "dynasty = fujiwara_dynasty"
            nsub += 1
    while lines and lines[-1].strip() == "":
        lines.pop()
    lines.append("")
    for x in KEYS:
        hk = NEW_HOUSE[x]
        nm, cu = dyninfo.get(x, (None, None))
        lines.append("%s = {" % hk)
        lines.append('\tname = "%s"' % nm)
        lines.append('\tculture = "%s"' % (cu or "japanese"))
        lines.append("\tdynasty = fujiwara_dynasty")
        lines.append("}")
        lines.append("")
    lines_hou = lines

    # ---- 3. characters: dynasty = X -> fujiwara + dynasty_house ----
    raw_c, bom_c, nl_c, lines = read(CHR)
    out = []
    nchr = 0
    for l in lines:
        m = PAT.match(l)
        if m:
            indent = m.group(1)
            hk = NEW_HOUSE[m.group(2)]
            out.append(indent + "dynasty = fujiwara_dynasty")
            out.append(indent + "dynasty_house = " + hk)
            nchr += 1
        else:
            out.append(l)
    lines_chr = out

    # ---- 4. alias: X_dynasty -> house_X ----
    raw_a, bom_a, nl_a, lines = read(ALIAS)
    nalias = 0
    for idx, l in enumerate(lines):
        m = re.match(r'^([A-Za-z0-9_\-]+)\s*=\s*(.+)$', l)
        if m and m.group(1) in ALIAS_MAP:
            lines[idx] = "%s = %s" % (ALIAS_MAP[m.group(1)], m.group(2))
            nalias += 1
    lines_alias = lines

    print("删除 dynasty 定义: %d %s" % (len(removed), removed))
    print("子 house 改挂 fujiwara: %d" % nsub)
    print("新增 house: %d %s" % (len(KEYS), [NEW_HOUSE[x] for x in KEYS]))
    print("角色改挂: %d" % nchr)
    print("COA 别名改键: %d" % nalias)

    if dry:
        print("（dry-run，未落盘）")
        return

    stamp = time.strftime("%Y%m%d_%H%M%S")
    for path, raw in [(DYN, raw_d), (HOU, raw_h), (CHR, raw_c), (ALIAS, raw_a)]:
        open(path + ".bak_fuji_" + stamp, "wb").write(raw)
    write(DYN, lines_dyn, nl_d, bom_d)
    write(HOU, lines_hou, nl_h, bom_h)
    write(CHR, lines_chr, nl_c, bom_c)
    write(ALIAS, lines_alias, nl_a, bom_a)
    print("已落盘，备份 .bak_fuji_%s" % stamp)


if __name__ == "__main__":
    main()
