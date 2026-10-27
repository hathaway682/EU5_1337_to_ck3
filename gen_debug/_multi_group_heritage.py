# -*- coding: utf-8 -*-
"""只读：EU5 多文化组文化的传承取值分析。

传承脚本用的是 `next((hmap[g] for g in grps if g in hmap), None)`——
即按 EU5 文件里 culture_groups 的书写顺序，取第一个「有 CK3 映射」的组。
本脚本统计这样做的实际影响面。
"""
import io, os, re, csv, collections

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game\in_game"
MAPCSV = os.path.join(MOD, "gen_debug", "_eu5_to_ck3_pillars.csv")

DEF = re.compile(r"(?ms)^\t?([a-z0-9_]+)\s*=\s*\{")


def rd(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


def top_keys(text):
    out, i, n = {}, 0, len(text)
    while i < n:
        m = DEF.search(text, i)
        if not m:
            break
        j, d = m.end(), 1
        while j < n and d:
            c = text[j]
            if c == "{":
                d += 1
            elif c == "}":
                d -= 1
            j += 1
        out[m.group(1)] = text[m.end():j - 1]
        i = j
    return out


hmap = {}
with io.open(MAPCSV, encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        if row["status"] == "mapped" and row["ck3_heritage"]:
            hmap[row["eu5_group"]] = row["ck3_heritage"]

grps = {}
cd = os.path.join(EU5, "common", "cultures")
for fn in sorted(os.listdir(cd)):
    if not fn.endswith(".txt"):
        continue
    for k, b in top_keys(rd(os.path.join(cd, fn))).items():
        m = re.search(r"(?ms)^\s*culture_groups\s*=\s*\{(.*?)\}", b)
        if m:
            grps[k] = m.group(1).split()

print("EU5 有 culture_groups 的文化: %d" % len(grps))
dist = collections.Counter(len(v) for v in grps.values())
print("组数分布: %s" % dict(sorted(dist.items())))
print()

multi = {k: v for k, v in grps.items() if len(v) > 1}
print("多组文化: %d（占 %.1f%%）" % (len(multi), 100.0 * len(multi) / len(grps)))

# 首个有映射的组 vs 后续组给出不同结果的情况
first_mapped = collections.Counter()     # 第几个组被采用
conflict = []                            # 不同组映射到不同 heritage
no_map = []
for k, gs in grps.items():
    idxs = [i for i, g in enumerate(gs) if g in hmap]
    if not idxs:
        no_map.append((k, gs))
        continue
    first_mapped[idxs[0]] += 1
    vals = {hmap[gs[i]] for i in idxs}
    if len(vals) > 1:
        conflict.append((k, gs, [(gs[i], hmap[gs[i]]) for i in idxs]))

print("采用第几个组（0=第一个）: %s" % dict(sorted(first_mapped.items())))
print("  其中第一个组就有映射的: %d" % first_mapped[0])
print("  第一个组无映射、退到后面的: %d" % sum(v for i, v in first_mapped.items() if i > 0))
print("完全无映射（保留组名）: %d" % len(no_map))
print()
print("== 多组且不同组映射到不同 heritage 的文化: %d ==" % len(conflict))
for k, gs, pairs in sorted(conflict, key=lambda x: -len(x[1]))[:15]:
    print("  %-32s %s" % (k, "  ".join("%s→%s" % p for p in pairs)))
print()
print("== 组数最多的 10 个文化 ==")
for k, gs in sorted(multi.items(), key=lambda kv: -len(kv[1]))[:10]:
    print("  %-32s %s" % (k, gs))
