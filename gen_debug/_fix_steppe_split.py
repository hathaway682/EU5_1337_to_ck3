# -*- coding: utf-8 -*-
"""草原东西支最终分法：带 steppe_group 的归 cuman（西支），不带的归 kipchak（东支）。

用户 2026-10-22 定：
  - 带 EU5 草原族群文化组（steppe_group）→ CK3 cuman（库曼，西支）
  - 不带 steppe_group 的钦察语 → CK3 kipchak（钦察，东支）
  - **能自己独立的保留**：CK3 00_turkic.txt 里有独立文化的，不并入上面两支。

当前 kipchak_language 的成员与落点：
  astrakhani / crimean / nogai       带 steppe_group → cuman
  kazani / mishar                    带 steppe_group，但伏尔加保加尔底子 → bolghar
  bashkir                            → bashkir（独立）
  cuman_culture                      → cuman（独立，匈牙利那支）
  kyrgyz_culture                     → kirghiz（独立，黠戛斯）
  uzbek / kumyk / balkar / karachay
  / telengit / teleut / yerle_qaliq  → kipchak（CK3 无对应，东支）

本脚本只处理「上一轮已经改成 kipchak、现在要改回/改走」的四个：
  crimean / nogai / astrakhani : kipchak → cuman
  kyrgyz_culture               : kipchak → kirghiz

做法：从「第一次落地之前」的备份里扫出这些 key 所属的块 id，
再在当前文件里只改这些块的 culture 行。默认 dry run，--apply 才写。
"""
import os
import re
import sys
import shutil
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAMP = "20261022_223413"
PAIRS = [
    "history/provinces/00_generated_provinces.txt",
    "history/characters/00_generated_characters.txt",
    "history/characters/zz_eu5_characters.txt",
    "history/characters/zz_eu5_regents.txt",
    "history/characters/zz_gen_adventurers.txt",
    "common/dynasties/00_generated_dynasties.txt",
    "common/dynasties/zz_eu5_dynasties.txt",
    "common/dynasties/zz_gen_adventurers.txt",
    "common/dynasty_houses/zz_eu5_merged_houses.txt",
]

# (源 key 集合, 当前值, 目标值)
RULES = [
    ({"crimean", "nogai", "astrakhani"}, "kipchak", "cuman"),
    ({"kyrgyz_culture"}, "kipchak", "kirghiz"),
]

RE_BLOCK = re.compile(r"^([A-Za-z0-9_]+)\s*=\s*\{\s*$")
RE_CULT = re.compile(r'^([ \t]*)culture([ \t]*=[ \t]*)"?([A-Za-z0-9_]+)"?([ \t]*)$')


def scan(path, src_keys):
    ids = set()
    cur = None
    for line in open(path, encoding="utf-8-sig", errors="replace"):
        b = line.rstrip("\r\n")
        m = RE_BLOCK.match(b)
        if m:
            cur = m.group(1)
            continue
        m2 = RE_CULT.match(b)
        if m2 and m2.group(3) in src_keys and cur:
            ids.add(cur)
    return ids


def rewrite(path, plan):
    """plan: {block_id: (old, new)}"""
    raw = open(path, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    lines = raw.decode("utf-8-sig").split("\n")
    cur = None
    n = 0
    for i, line in enumerate(lines):
        b = line[:-1] if line.endswith("\r") else line
        m = RE_BLOCK.match(b)
        if m:
            cur = m.group(1)
            continue
        m2 = RE_CULT.match(b)
        if not m2 or cur not in plan:
            continue
        old, new = plan[cur]
        if m2.group(3) != old:
            continue
        ind, mid, _key, tail = m2.groups()
        q = '"' if '"' in b else ""
        lines[i] = (ind + "culture" + mid + q + new + q + tail
                    + ("\r" if line.endswith("\r") else ""))
        n += 1
    if n and APPLY:
        shutil.copy2(path, path + ".bak_steppesplit_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
        data = "\n".join(lines).encode("utf-8")
        if bom:
            data = b"\xef\xbb\xbf" + data
        open(path, "wb").write(data)
    return n


APPLY = "--apply" in sys.argv
print("模式：%s" % ("APPLY 落盘" if APPLY else "DRY RUN"))
print("%-52s %6s %6s" % ("文件", "块数", "改动行"))
total = 0
for rel in PAIRS:
    p = os.path.join(ROOT, rel)
    bak = p + ".bak_v2cult_" + STAMP
    if not os.path.exists(p) or not os.path.exists(bak):
        continue
    plan = {}
    for keys, old, new in RULES:
        for bid in scan(bak, keys):
            plan[bid] = (old, new)
    n = rewrite(p, plan)
    total += n
    if plan or n:
        print("  %-50s %6d %6d" % (rel, len(plan), n))
print("\n合计改动 %d 行" % total)
