# -*- coding: utf-8 -*-
"""欧洲 + 已定融合文化的「不建新文化」落地脚本。

与上一版（_apply_eu_culture_merge.py）的区别：
  1. 一个新文化都不建，全部落到 CK3 原版已有的文化上；
  2. 省份、角色、宗族、支系四层一次改完；
  3. 省份是 EU5 原始 key（宗教重跑后已复原），角色/宗族是上一轮「建新文化」
     的产物（anglo_irish / norse_gael / walloon / pomeranian / teutonic），
     所以角色层要叠一层补丁映射。

映射来源：gen_debug/_culture_classification.csv
  范围 = 欧洲全部 + 用户拍过落点的 12 个非欧洲 key（EXTRA）。
  只取 target 不是 NEW: 开头、且 target != culture 的条目。

★ prussian 在角色/宗族层不动：EU5 的 prussian（德意志）已在上一轮改成 teutonic，
  现在角色里的 prussian 是 pruthenian/sudovian/curonian 改过来的波罗的普鲁士人。
  省份层则相反，prussian 还是 EU5 德意志普鲁士，要改成 saxon。

默认 dry run，--apply 才写盘。
"""
import csv
import os
import re
import sys
import shutil
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(ROOT, "gen_debug", "_culture_classification.csv")

PROV = "history/provinces/00_generated_provinces.txt"

# 角色 / 宗族 / 支系层要改的文件
PEOPLE = [
    "history/characters/00_generated_characters.txt",
    "history/characters/zz_eu5_characters.txt",
    "history/characters/zz_eu5_missing_characters.txt",
    "history/characters/zz_eu5_regents.txt",
    "history/characters/zz_gen_adventurers.txt",
    "common/dynasties/00_generated_dynasties.txt",
    "common/dynasties/zz_eu5_dynasties.txt",
    "common/dynasties/zz_gen_adventurers.txt",
    "common/dynasty_houses/zz_eu5_merged_houses.txt",
]

# 非欧洲、但用户已经拍过落点的文化
EXTRA = {
    "algerian", "moroccan", "tunisian", "sudanese_arab",
    "astrakhani", "crimean", "mishar", "nogai",
    "turkish_culture", "azeri_culture", "gyalrong_culture",
}

# 落点范围：CK3 原版地图内（cat1-cat9）。cat10/cat11 是图外自创，不碰。
INSIDE_CATS = set("123456789")

# 上一轮建的新文化 → 现在并入的已有文化（不在 CSV 里，需单独补）
PATCH = {
    "pomeranian": "saxon",   # western/eastern_pomeranian 的融合产物
    "teutonic":   "saxon",   # EU5 德意志普鲁士的分离产物
}

# 角色层不能碰的 key（这里的 prussian 是波罗的普鲁士人）
KEEP_IN_PEOPLE = {"prussian"}

# 省份层也不能碰 prussian：EU5 的德意志普鲁士（11 省）在上一轮已并入 saxon，
# 现在省份里的 30 个 prussian 是 pruthenian/sudovian/curonian 改过来的
# 波罗的普鲁士人。再扫一次 prussian->saxon 会把他们误改成萨克森。
KEEP_IN_PROV = {"prussian"}

RE_CULT = re.compile(r'^([ \t]*)culture([ \t]*=[ \t]*)"?([A-Za-z0-9_]+)"?([ \t]*)$')


def load_map():
    rows = list(csv.DictReader(open(CSV, encoding="utf-8-sig")))
    # CK3 原版地图内的文化（cat1-cat9）全部参与映射；图外自创（cat10/cat11）不动。
    keep = [r for r in rows if r["category"] in INSIDE_CATS]
    m = {}
    for r in keep:
        c, t = r["culture"], r["target"]
        if not t or t.startswith("NEW:"):
            continue
        if t == c:
            continue
        m[c] = t
    return m, len(rows), len(keep)


def rewrite(path, mapping, skip=()):
    """逐行替换 culture = <key>，保留缩进、引号、行尾。返回 (改动数, 明细Counter)"""
    raw = open(path, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    crlf = "\r\n" in text
    lines = text.split("\n")
    hits = {}
    n = 0
    for i, line in enumerate(lines):
        body = line[:-1] if line.endswith("\r") else line
        mm = RE_CULT.match(body)
        if not mm:
            continue
        ind, mid, key, tail = mm.groups()
        if key in skip:
            continue
        new = mapping.get(key)
        if not new or new == key:
            continue
        lines[i] = "%s%s%s%s%s%s" % (ind, "culture", mid, '"%s"' % new if '"' in body else new,
                                     tail, "\r" if line.endswith("\r") else "")
        hits[key] = hits.get(key, 0) + 1
        n += 1
    if n and APPLY:
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(path, path + ".bak_v2cult_" + stamp)
        out = "\n".join(lines)
        data = out.encode("utf-8")
        if bom:
            data = b"\xef\xbb\xbf" + data
        open(path, "wb").write(data)
    return n, hits


APPLY = "--apply" in sys.argv

mapping, total, inscope = load_map()
print("CSV %d 条，范围内 %d 条，映射 %d 条" % (total, inscope, len(mapping)))
print("模式：%s" % ("APPLY 落盘" if APPLY else "DRY RUN"))
print()

# 省份：全表
if os.path.exists(os.path.join(ROOT, PROV)):
    n, hits = rewrite(os.path.join(ROOT, PROV), mapping, skip=KEEP_IN_PROV)
    print("省份  %-46s %6d 行 / %d 组" % (PROV, n, len(hits)))
    for k in sorted(hits, key=lambda x: -hits[x])[:20]:
        print("        %-24s %5d -> %s" % (k, hits[k], mapping[k]))
else:
    print("省份文件缺失")

print()
# 角色 / 宗族 / 支系：全表 + 补丁，但 prussian 不动
pmap = dict(mapping)
pmap.update(PATCH)
for k in KEEP_IN_PEOPLE:
    pmap.pop(k, None)
print("角色层补丁：%s；保留不动：%s" % (PATCH, sorted(KEEP_IN_PEOPLE)))
print()
tot = 0
for rel in PEOPLE:
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        print("  %-52s 不存在" % rel)
        continue
    n, hits = rewrite(p, pmap)
    tot += n
    print("  %-52s %6d 行 / %2d 组" % (rel, n, len(hits)))
print()
print("角色/宗族/支系 合计 %d 行" % tot)
