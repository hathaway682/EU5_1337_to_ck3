# -*- coding: utf-8 -*-
"""只读校验：rite 重算后的结果。

1. faith 与快照逐条比对（必须 0 差异）
2. rite 行数 / 分布
3. rite 家族与 faith 不匹配的清单（armenian_rite 走 miaphysitism 是既定合并约定，单列）
4. 戈尔甘各县状态
"""
import io, os, re, json
from collections import Counter, defaultdict

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
GEN = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
REL = os.path.join(MOD, "common/religion")
SRC = os.path.join(MOD, "history/provinces/00_generated_provinces.txt")
SNAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_faith_snapshot.json")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_verify_rite_regen.out")

L = []


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
    return "\n".join(io.open(os.path.join(d, fn), encoding="utf-8-sig", errors="ignore").read()
                     for fn in sorted(os.listdir(d)) if fn.endswith(".txt"))


rite_family = {}
for k, b in blocks(read_dir("rite_types")).items():
    m = re.search(r"(?m)^\s*faith\s*=\s*([A-Za-z0-9_]+)", b)
    if m:
        rite_family[k] = m.group(1)
faith_origin = {}
for k, b in blocks(read_dir("faith_types")).items():
    m = re.search(r"(?m)^\s*origin\s*=\s*([A-Za-z0-9_]+)", b)
    if m:
        faith_origin[k] = m.group(1)

txt = io.open(SRC, encoding="utf-8-sig", newline="").read()
prov = {}
for m in re.finditer(r"(?m)^(\d+) = \{(.*?)\n\}", txt, re.S):
    body = m.group(2)
    f = re.search(r"(?m)^\s*faith\s*=\s*(\S+)", body)
    r = re.search(r"(?m)^\s*rite\s*=\s*(\S+)", body)
    prov[int(m.group(1))] = (f.group(1) if f else None, r.group(1) if r else None)

# 1) faith vs snapshot
snap = {int(k): v for k, v in json.load(io.open(SNAP, encoding="utf-8")).items()}
diff = [(p, snap[p], prov[p][0]) for p in snap if p in prov and prov[p][0] != snap[p]]
L.append("province 块: %d" % len(prov))
L.append("faith 与快照的差异: %d" % len(diff))
for d in diff[:10]:
    L.append("    %s" % (d,))
L.append("faith 分布（应与重算前一致）: %s" % dict(Counter(v[0] for v in prov.values()).most_common(12)))

# 2) rite 统计
L.append("")
L.append("rite 行数: %d（重算前 4468）" % sum(1 for v in prov.values() if v[1]))
for r, n in Counter(v[1] for v in prov.values() if v[1]).most_common(40):
    L.append("   %-24s %d" % (r, n))

# 3) 家族不匹配
bad = []
for pid, (f, r) in prov.items():
    if not r:
        continue
    fam = faith_origin.get(f, f)
    if rite_family.get(r) != fam:
        bad.append((pid, f, r, rite_family.get(r)))
L.append("")
L.append("rite 家族与 faith 不匹配: %d" % len(bad))
for (f, r, rf), n in Counter((f, r, rf) for _, f, r, rf in bad).most_common(20):
    L.append("   faith=%-26s rite=%-16s (%d)  rite.faith=%s" % (f, r, n, rf))

# 4) 戈尔甘
L.append("")
L.append("戈尔甘 c_gorgan 的 9 个 province:")
for pid in range(6883, 6892):
    if pid in prov:
        L.append("   p%d faith=%-12s rite=%s" % (pid, prov[pid][0], prov[pid][1]))

# 5) ismaili / imami 全局
L.append("")
for tgt in ("ismaili", "imami", "zayidi", "ibadi"):
    ps = [p for p, v in prov.items() if v[1] == tgt]
    L.append("%-8s province %d 个，faith 分布: %s"
             % (tgt, len(ps), dict(Counter(prov[p][0] for p in ps).most_common(5))))

L.append("")
L.append("braces: %d %d" % (txt.count("{"), txt.count("}")))
io.open(OUT, "w", encoding="utf-8-sig", newline="\n").write("\n".join(L))
