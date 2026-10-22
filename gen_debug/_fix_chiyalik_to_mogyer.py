# -*- coding: utf-8 -*-
"""把 EU5 chiyalik_culture（奇亚利克，马札尔文化组仅存文化）从 hungarian 改到 mogyer。

背景：分类表原先把 chiyalik_culture 归 cat6 → hungarian，但 CK3 里
`mogyer`（马扎尔）才是 hungarian 的父文化（00_magyar.txt: `hungarian.created = 1000.1.1`,
`parents = { mogyer }`），比匈牙利更早。用户 2026-10-22 指出应落 mogyer。

做法：上一轮已经把 chiyalik_culture 全改成 hungarian，无法从当前文件区分。
所以从「第二次落地之前」的备份里找出 chiyalik_culture 所属的块 id，
再在当前文件里只改这些块的 culture 行。外科手术式，不动其它行。

默认 dry run，--apply 才写。
"""
import os
import re
import sys
import shutil
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAMP = "20261022_223413"
PAIRS = [
    ("history/provinces/00_generated_provinces.txt",),
    ("history/characters/00_generated_characters.txt",),
    ("history/characters/zz_eu5_characters.txt",),
    ("history/characters/zz_eu5_missing_characters.txt",),
    ("history/characters/zz_eu5_regents.txt",),
    ("history/characters/zz_gen_adventurers.txt",),
    ("common/dynasties/00_generated_dynasties.txt",),
    ("common/dynasties/zz_eu5_dynasties.txt",),
    ("common/dynasties/zz_gen_adventurers.txt",),
    ("common/dynasty_houses/zz_eu5_merged_houses.txt",),
]

SRC = "chiyalik_culture"
OLD = "hungarian"
NEW = "mogyer"

RE_BLOCK = re.compile(r"^([A-Za-z0-9_]+)\s*=\s*\{\s*$")
RE_CULT = re.compile(r'^([ \t]*)culture([ \t]*=[ \t]*)"?([A-Za-z0-9_]+)"?([ \t]*)$')


def scan(path):
    """返回 culture == SRC 的顶层块 id 集合。"""
    ids = set()
    cur = None
    for line in open(path, encoding="utf-8-sig", errors="replace"):
        b = line.rstrip("\r\n")
        m = RE_BLOCK.match(b)
        if m:
            cur = m.group(1)
            continue
        m2 = RE_CULT.match(b)
        if m2 and m2.group(3) == SRC and cur:
            ids.add(cur)
    return ids


def rewrite(path, ids):
    raw = open(path, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    lines = text.split("\n")
    cur = None
    n = 0
    for i, line in enumerate(lines):
        b = line[:-1] if line.endswith("\r") else line
        m = RE_BLOCK.match(b)
        if m:
            cur = m.group(1)
            continue
        m2 = RE_CULT.match(b)
        if not m2 or cur not in ids or m2.group(3) != OLD:
            continue
        ind, mid, _key, tail = m2.groups()
        q = '"' if '"' in b else ""
        lines[i] = (ind + "culture" + mid + q + NEW + q + tail
                    + ("\r" if line.endswith("\r") else ""))
        n += 1
    if n and APPLY:
        shutil.copy2(path, path + ".bak_mogyer_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
        data = "\n".join(lines).encode("utf-8")
        if bom:
            data = b"\xef\xbb\xbf" + data
        open(path, "wb").write(data)
    return n


APPLY = "--apply" in sys.argv
print("模式：%s" % ("APPLY 落盘" if APPLY else "DRY RUN"))
print("%-56s %6s %6s" % ("文件", "块数", "改动行"))
total = 0
for (rel,) in PAIRS:
    p = os.path.join(ROOT, rel)
    bak = p + ".bak_v2cult_" + STAMP
    if not os.path.exists(p) or not os.path.exists(bak):
        print("  %-54s 跳过（缺文件或备份）" % rel)
        continue
    ids = scan(bak)
    n = rewrite(p, ids)
    total += n
    print("  %-54s %6d %6d" % (rel, len(ids), n))
print("\n合计改动 %d 行" % total)
