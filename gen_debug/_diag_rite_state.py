# -*- coding: utf-8 -*-
"""只读体检：当前 province history 里的 rite 与 faith 是否还自洽。

不写任何文件（除了 stdout）。
"""
import io, os, re, sys
from collections import Counter, defaultdict

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
REL = os.path.join(MOD, "common/religion")
SRC = os.path.join(MOD, "history/provinces/00_generated_provinces.txt")

_OUT = []


def print(*a):
    _OUT.append(" ".join(str(x) for x in a))


def blocks(text):
    out = {}
    for m in re.finditer(r"(?m)^([A-Za-z0-9_\-]+)\s*=\s*\{", text):
        k = m.group(1); i = m.end() - 1; d = 0
        for j in range(i, len(text)):
            if text[j] == "{":
                d += 1
            elif text[j] == "}":
                d -= 1
                if d == 0:
                    out[k] = text[i:j + 1]
                    break
    return out


def read_dir(sub):
    d = os.path.join(REL, sub)
    txt = []
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".txt"):
            txt.append(io.open(os.path.join(d, fn), encoding="utf-8-sig", errors="ignore").read())
    return "\n".join(txt)


# rite -> faith（rite_types 里自己的 faith =）
rite2faith = {}
for k, b in blocks(read_dir("rite_types")).items():
    m = re.search(r"(?m)^\s*faith\s*=\s*([A-Za-z0-9_]+)", b)
    if m:
        rite2faith[k] = m.group(1)

# faith -> (main_rite, origin)
faith_main = {}
faith_origin = {}
for k, b in blocks(read_dir("faith_types")).items():
    m = re.search(r"(?m)^\s*main_rite\s*=\s*([A-Za-z0-9_]+)", b)
    if m:
        faith_main[k] = m.group(1)
    m = re.search(r"(?m)^\s*origin\s*=\s*([A-Za-z0-9_]+)", b)
    if m:
        faith_origin[k] = m.group(1)

print("rite_types: %d 个（有 faith 指向 %d）" % (len(blocks(read_dir("rite_types"))), len(rite2faith)))
print("faith_types: %d 个（有 main_rite %d，有 origin %d）"
      % (len(blocks(read_dir("faith_types"))), len(faith_main), len(faith_origin)))

# rite 的 faith 字段 = faith 的 origin（信仰家族），不是某个具体 faith
rite_parents = defaultdict(set)
for r, f in rite2faith.items():
    rite_parents[r].add(f)

hist = io.open(SRC, encoding="utf-8-sig").read()
prov = {}
for m in re.finditer(r"(?m)^(\d+) = \{(.*?)\n\}", hist, re.S):
    pid = int(m.group(1)); body = m.group(2)
    f = re.search(r"(?m)^\s*faith\s*=\s*(\S+)", body)
    r = re.search(r"(?m)^\s*rite\s*=\s*(\S+)", body)
    prov[pid] = (f.group(1) if f else None, r.group(1) if r else None)

tot = len(prov)
with_rite = sum(1 for v in prov.values() if v[1])
print("\nprovince 块 %d | 带 rite %d" % (tot, with_rite))

bad = []
bad_unknown_rite = []
for pid, (f, r) in prov.items():
    if not r:
        continue
    if r not in rite_parents:
        bad_unknown_rite.append((pid, f, r))
        continue
    if faith_origin.get(f) not in rite_parents[r]:
        bad.append((pid, f, r))

print("rite 键在 rite_types 里找不到的: %d" % len(bad_unknown_rite))
for x in bad_unknown_rite[:20]:
    print("   ", x)

print("rite 的家族 != 块内 faith 的 origin 的: %d" % len(bad))
c = Counter((f, r) for _, f, r in bad)
for (f, r), n in c.most_common(30):
    print("    faith=%-24s rite=%-16s  %d   (faith.origin=%s / rite.faith=%s)"
          % (f, r, n, faith_origin.get(f), "/".join(sorted(rite_parents.get(r, {"?"})))))

# faith 没有 main_rite 却也没写 rite 的块（会落空）
no_main = [pid for pid, (f, r) in prov.items() if f and f not in faith_main and not r]
print("\nfaith 本身没有 main_rite 且块内没写 rite 的: %d" % len(no_main))
print("   按 faith 统计:", dict(Counter(prov[p][0] for p in no_main).most_common(20)))

# rite 分布
print("\n当前 rite 分布 top30:")
for r, n in Counter(v[1] for v in prov.values() if v[1]).most_common(30):
    print("   %-22s %d" % (r, n))

io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_diag_rite_state.out"),
        "w", encoding="utf-8-sig", newline="\n").write("\n".join(_OUT))
