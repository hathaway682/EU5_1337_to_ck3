# -*- coding: utf-8 -*-
"""只读：194 个「多组冲突」文化，最终传承到底由谁决定。"""
import io, os, re, csv, collections

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\EUV"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game\in_game"
MAPCSV = os.path.join(MOD, "gen_debug", "_eu5_to_ck3_pillars.csv")
CULT = os.path.join(MOD, "common", "culture", "cultures", "00_generated_cultures.txt")

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


def field(b, k):
    m = re.search(r"(?m)^\s*" + k + r"\s*=\s*([a-z0-9_]+)", b)
    return m.group(1) if m else ""


hmap = {}
with io.open(MAPCSV, encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        if row["status"] == "mapped" and row["ck3_heritage"]:
            hmap[row["eu5_group"]] = row["ck3_heritage"]

grps = {}
cd = os.path.join(EU5, "common", "cultures")
for fn in sorted(os.listdir(cd)):
    if fn.endswith(".txt"):
        for k, b in top_keys(rd(os.path.join(cd, fn))).items():
            m = re.search(r"(?ms)^\s*culture_groups\s*=\s*\{(.*?)\}", b)
            if m:
                grps[k] = m.group(1).split()

cur_her = {k: field(b, "heritage") for k, b in top_keys(rd(CULT)).items()}

multi = {k: v for k, v in grps.items() if len(v) > 1}
same = [k for k, gs in multi.items()
        if len({hmap[g] for g in gs if g in hmap}) == 1 and any(g in hmap for g in gs)]
none = [k for k, gs in multi.items() if not any(g in hmap for g in gs)]
conf = [k for k, gs in multi.items() if len({hmap[g] for g in gs if g in hmap}) > 1]

print("多组文化 %d = 各组同解 %d + 全无映射 %d + 真冲突 %d"
      % (len(multi), len(same), len(none), len(conf)))
print()

by_first, by_lang, by_other, keep = [], [], [], []
for k in conf:
    gs = multi[k]
    first = next((hmap[g] for g in gs if g in hmap), None)
    got = cur_her.get(k, "")
    if got == first:
        by_first.append(k)
    elif got.startswith("heritage_"):
        by_lang.append((k, gs, first, got))
    elif got in gs:
        keep.append(k)
    else:
        by_other.append((k, gs, first, got))

print("最终值 = 第一个有映射的组 : %d" % len(by_first))
print("最终值 = 语言覆盖表纠正    : %d" % len(by_lang))
print("最终值 = 保留 EU5 组名     : %d" % len(keep))
print("其他                        : %d" % len(by_other))
print()
print("== 被语言覆盖改掉「第一个组」结论的 ==")
for k, gs, first, got in by_lang:
    print("  %-24s 组顺序 %s | 第一组给 %-24s -> 实际 %s"
          % (k, ",".join(gs), first, got))
print()
print("== 其他 ==")
for k, gs, first, got in by_other[:10]:
    print("  %-24s %s | 第一组给 %s -> 实际 %s" % (k, ",".join(gs), first, got))
