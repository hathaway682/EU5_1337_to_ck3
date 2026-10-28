# -*- coding: utf-8 -*-
"""把 _culture_classification.csv 的落点同步到「人物层」：角色 / 宗族 / 支系。

范围：
  * 全部有真实 target 的行（不区分 category，cat10/11 的美洲、大洋洲组文化也算），
    只跳过 target 为空 / NEW: 开头 / target == culture。
  * 不动省份文件（省份由 _apply_province_pop_culture.py 负责）。

不能碰的 key：
  prussian —— 人物层里的 prussian 是上一轮 pruthenian/sudovian/curonian 改过来的
  波罗的普鲁士人，再按 CSV 扫一次会误改成萨克森。

默认 dry run，--apply 才写盘（每个文件先备份 .bak_peoplecult_<时间戳>）。
"""
import collections
import csv
import datetime
import glob
import io
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(ROOT, "gen_debug", "_culture_classification.csv")
CK3 = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"

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

KEEP_IN_PEOPLE = {"prussian"}

RE_CULT = re.compile(r'^([ \t]*)culture([ \t]*=[ \t]*)"?([A-Za-z0-9_]+)"?([ \t]*)$')


def load_map():
    m = {}
    for r in csv.DictReader(io.open(CSV, encoding="utf-8-sig")):
        c, t = r["culture"], r["target"]
        if not t or t.startswith("NEW:") or t == c:
            continue
        m[c] = t
    for k in KEEP_IN_PEOPLE:
        m.pop(k, None)
    return m


def defined_cultures():
    keys = set()
    for pat in (os.path.join(ROOT, "common/culture/cultures/*.txt"),
                os.path.join(CK3, "common/culture/cultures/*.txt")):
        for f in glob.glob(pat):
            keys |= set(re.findall(r'(?m)^([a-z0-9_]+)\s*=\s*\{',
                                   io.open(f, encoding="utf-8-sig", errors="ignore").read()))
    return keys


def rewrite(path, mapping, apply):
    raw = open(path, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    lines = text.split("\n")
    hits = collections.Counter()
    n = 0
    for i, line in enumerate(lines):
        body = line[:-1] if line.endswith("\r") else line
        mm = RE_CULT.match(body)
        if not mm:
            continue
        ind, mid, key, tail = mm.groups()
        new = mapping.get(key)
        if not new or new == key:
            continue
        lines[i] = "%s%s%s%s%s%s" % (
            ind, "culture", mid,
            '"%s"' % new if '"' in body else new,
            tail, "\r" if line.endswith("\r") else "")
        hits[key] += 1
        n += 1
    if n and apply:
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(path, path + ".bak_peoplecult_" + stamp)
        data = "\n".join(lines).encode("utf-8")
        if bom:
            data = b"\xef\xbb\xbf" + data
        open(path, "wb").write(data)
    return n, hits


def main():
    apply = "--apply" in sys.argv
    mapping = load_map()
    defined = defined_cultures()
    bad = sorted({v for v in mapping.values() if v not in defined})
    print("映射 %d 条 | 目标文化未定义 %d 个 %s" % (len(mapping), len(bad), bad[:10]))
    print("模式：%s\n" % ("APPLY 落盘" if apply else "DRY RUN"))

    grand = 0
    per_key = collections.Counter()
    for rel in PEOPLE:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            print("  %-52s 不存在" % rel)
            continue
        n, hits = rewrite(p, mapping, apply)
        grand += n
        per_key.update(hits)
        print("  %-52s %6d 行 / %2d 组" % (rel, n, len(hits)))
    print("\n合计 %d 行" % grand)
    print("涉及 %d 个 EU5 culture，前 25：" % len(per_key))
    for k in sorted(per_key, key=lambda x: -per_key[x])[:25]:
        print("   %-26s %5d -> %s" % (k, per_key[k], mapping[k]))
    if not apply:
        print("\nDRY RUN：未写入。加 --apply 执行。")


if __name__ == "__main__":
    main()
