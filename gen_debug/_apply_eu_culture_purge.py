# -*- coding: utf-8 -*-
"""欧洲文化归并第二步：改角色 culture + 统计旧 key 残留引用。

阶段 1（--chars）：history/characters/*.txt 里欧洲文化的 culture 改成新 key
阶段 2（--purge）：删掉不再被任何地方引用的旧文化定义与 history/cultures 文件
默认只统计不写。
"""
import csv
import glob
import io
import os
import re
import sys
from collections import Counter

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
GEN = os.path.join(MOD, "gen_debug")
CSV = os.path.join(GEN, "_culture_classification.csv")

DO_CHARS = "--chars" in sys.argv
DO_PURGE = "--purge" in sys.argv

SKIP = {"kazani"}


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


def fk(t):
    return t[4:] if t.startswith("NEW:") else t


rows = list(csv.DictReader(io.open(CSV, encoding="utf-8-sig")))
EU = {r["culture"]: r for r in rows if r.get("continent") == "欧洲"}
MAP = {}
for c, r in EU.items():
    if c in SKIP:
        continue
    t = fk(r["target"])
    if t and t != c:
        MAP[c] = t

print("欧洲文化 %d，映射 %d 条" % (len(EU), len(MAP)))

# ---------- 阶段 1：改角色 ----------
RE_CULT = re.compile(r"(?<![a-z_])culture(\s*=\s*)([A-Za-z0-9_]+)")

char_files = [f for f in glob.glob(os.path.join(MOD, "history", "characters", "*.txt")) if ".bak" not in f]
n_chars = 0
n_files = 0
pairs = Counter()
for f in char_files:
    txt = read(f)
    hit = [0]

    def repl(m):
        old = m.group(2)
        new = MAP.get(old)
        if new and new != old:
            hit[0] += 1
            pairs[(old, new)] += 1
            return m.group(1) + new
        return m.group(0)

    new = RE_CULT.sub(repl, txt)
    if hit[0]:
        n_chars += hit[0]
        n_files += 1
        if DO_CHARS:
            io.open(f, "w", encoding="utf-8-sig", newline="\n").write(new)

print("角色 culture 需改 %d 处，涉及 %d 个文件%s"
      % (n_chars, n_files, "（已写入）" if DO_CHARS else "（未写入）"))
print()
print("== 角色改动 Top 15 ==")
for (o, n), c in pairs.most_common(15):
    print("   %-24s -> %-22s %d" % (o, n, c))

# ---------- 阶段 2：统计旧 key 残留引用 ----------
print()
print("== 旧 key 残留引用统计（provinces / characters / titles / landed_titles / dynasties）==")
scan_dirs = [
    os.path.join(MOD, "history", "provinces"),
    os.path.join(MOD, "history", "characters"),
    os.path.join(MOD, "history", "titles"),
    os.path.join(MOD, "common", "landed_titles"),
    os.path.join(MOD, "common", "dynasties"),
    os.path.join(MOD, "common", "dynasty_houses"),
]
blob = []
for d in scan_dirs:
    for f in glob.glob(os.path.join(d, "**", "*.txt"), recursive=True):
        if ".bak" in f:
            continue
        blob.append(read(f))
big = "\n".join(blob)
print("扫描文本 %d MB" % (len(big) // 1048576))

ref = Counter()
for m in RE_CULT.finditer(big):
    ref[m.group(2)] += 1

left = {k: ref.get(k, 0) for k in MAP}
zero = [k for k, v in left.items() if v == 0]
nonzero = {k: v for k, v in left.items() if v}
print("旧 key %d 个：引用已归零 %d 个，仍有引用 %d 个" % (len(left), len(zero), len(nonzero)))
if nonzero:
    print("仍有引用的（不能删）:")
    for k, v in sorted(nonzero.items(), key=lambda kv: -kv[1])[:30]:
        print("   %-26s %d" % (k, v))

# ---------- 阶段 3：删定义 ----------
CULT_FILE = os.path.join(MOD, "common", "culture", "cultures", "00_generated_cultures.txt")
ctxt = read(CULT_FILE)
HEAD_END = ctxt.find("\n\n")
head = ctxt[:HEAD_END + 2]

blocks = {}
order = []
for m in re.finditer(r"(?m)^([a-z_0-9]+)\s*=\s*\{", ctxt):
    k = m.group(1)
    s = m.start()
    d = 0
    j = ctxt.find("{", s)
    while j < len(ctxt):
        if ctxt[j] == "{":
            d += 1
        elif ctxt[j] == "}":
            d -= 1
            if d == 0:
                break
        j += 1
    blocks[k] = ctxt[s:j + 1]
    order.append(k)

print()
print("生成物文化定义块 %d 个" % len(blocks))
to_del = [k for k in zero if k in blocks]
print("可删定义块 %d 个" % len(to_del))

if DO_PURGE:
    keep = [k for k in order if k not in set(to_del)]
    out = head + "\n\n".join(blocks[k] for k in keep) + "\n"
    io.open(CULT_FILE, "w", encoding="utf-8-sig", newline="\n").write(out)
    print("已重写定义文件，保留 %d 块，花括号 %d/%d" % (len(keep), out.count("{"), out.count("}")))

    # 删 history/cultures/<key>.txt
    removed = 0
    for k in to_del:
        p = os.path.join(MOD, "history", "cultures", k + ".txt")
        if os.path.exists(p):
            os.remove(p)
            removed += 1
    print("已删 history/cultures 文件 %d 个" % removed)
else:
    print("[未写入] 加 --purge 才删。")
