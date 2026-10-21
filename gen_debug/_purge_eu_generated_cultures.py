# -*- coding: utf-8 -*-
"""
删除 00_generated_cultures.txt 里残留的欧洲文化定义块。

背景：这些块是按 EU5 文化生成的 CK3 定义，欧洲落地后省份/角色/宗族都已改用
CK3 原版文化 key。凡原版已有同名定义的，本文件的块会**覆盖原版**造成干扰；
凡新文化（anglo_irish / norse_gael / walloon），已由 zz_eu5_culture_merge.txt 定义。
所以这两类一律删除，让原版 / zz 文件接管。

保留：kazani（草原组，按用户方案归亚洲，尚未处理，仍被 118 处引用）。

用法：
  python _purge_eu_generated_cultures.py            # 只统计
  python _purge_eu_generated_cultures.py --apply    # 落盘（带备份）
"""
import csv
import glob
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "common/culture/cultures/00_generated_cultures.txt")
ZZ = os.path.join(ROOT, "common/culture/cultures/zz_eu5_culture_merge.txt")
CSV = os.path.join(ROOT, "gen_debug/_culture_classification.csv")
VAN_DIR = r"E:/SteamLibrary/steamapps/common/Crusader Kings III/game/common/culture/cultures"

# 用户明确保留：草原组按亚洲方案处理，现在不能删
KEEP = {"kazani"}

RE_HEAD = re.compile(r"^([a-z0-9_]+)[ \t]*=[ \t]*\{[ \t]*$")
RE_KEY = re.compile(r"(?m)^([a-z0-9_]+)\s*=\s*\{")


def load_keys(d):
    s = set()
    for f in glob.glob(os.path.join(d, "*.txt")):
        s |= set(RE_KEY.findall(open(f, encoding="utf-8-sig", errors="replace").read()))
    return s


def blocks(lines):
    """返回 [(key, start, end_inclusive)]，块头在第 0 列，块尾是第 0 列的 }"""
    out = []
    i = 0
    while i < len(lines):
        m = RE_HEAD.match(lines[i].rstrip("\r\n"))
        if m:
            key = m.group(1)
            j = i + 1
            while j < len(lines):
                if lines[j].rstrip("\r\n") == "}":
                    break
                j += 1
            out.append((key, i, j))
            i = j + 1
        else:
            i += 1
    return out


def main():
    apply = "--apply" in sys.argv
    rows = list(csv.DictReader(open(CSV, encoding="utf-8-sig")))
    eu = {r["culture"] for r in rows if r.get("continent") == "欧洲"}

    raw = open(GEN, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    lines = text.splitlines(keepends=True)

    van = load_keys(VAN_DIR)
    # 只认 zz 合并文件里的定义，不能扫整个 cultures 目录（否则会把自己的块算成"有人定义"）
    zz = set(RE_KEY.findall(open(ZZ, encoding="utf-8-sig").read()))

    bl = blocks(lines)
    print("文件内块数 %d" % len(bl))

    dele = []
    for key, a, b in bl:
        if key not in eu:
            continue
        if key in KEEP:
            print("  保留 %s（亚洲方案，未处理）" % key)
            continue
        if key not in van and key not in zz:
            print("  ★跳过 %s：删了就没人定义了" % key)
            continue
        dele.append((key, a, b))

    print("\n待删 %d 块：" % len(dele))
    print("  " + " ".join(k for k, _, _ in dele))

    # 检查连续空行现状（确认收尾可以安全折叠）
    runs = sum(1 for i in range(1, len(lines))
               if lines[i].strip() == "" and lines[i - 1].strip() == "")
    print("  文件现有连续空行对：%d" % runs)

    drop = set()
    for key, a, b in dele:
        for i in range(a, b + 1):
            drop.add(i)
    out = [ln for i, ln in enumerate(lines) if i not in drop]

    # 折叠删除造成的连续空行（只折叠 >=2 个连续空行到 1 个）
    fixed = []
    prev_blank = False
    collapsed = 0
    for ln in out:
        blank = ln.strip() == ""
        if blank and prev_blank:
            collapsed += 1
            continue
        fixed.append(ln)
        prev_blank = blank
    print("  折叠多余空行 %d 行" % collapsed)

    if not apply:
        print("\n（只统计，未落盘；加 --apply 生效）")
        return

    stamp = time.strftime("%Y%m%d_%H%M%S")
    bak = GEN + ".bak_eupurge_" + stamp
    open(bak, "wb").write(raw)

    new_raw = "".join(fixed).encode("utf-8")
    if bom:
        new_raw = b"\xef\xbb\xbf" + new_raw
    open(GEN, "wb").write(new_raw)
    print("\n已写入，块数 %d -> %d" % (len(bl), len(bl) - len(dele)))
    print("备份 %s" % os.path.basename(bak))


if __name__ == "__main__":
    main()
