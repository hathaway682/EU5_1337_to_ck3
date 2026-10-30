# -*- coding: utf-8 -*-
"""只读分析：伯爵领 -> 最高归属头衔 的层级分布。"""
import re, collections, json, os

P = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape\history\titles\zz_eu5_titles.txt"
txt = open(P, encoding="utf-8-sig").read()

blocks = {}
lines = txt.splitlines()
cur = None; depth = 0; buf = []
for ln in lines:
    if depth == 0:
        m = re.match(r"^([A-Za-z0-9_.-]+)\s*=\s*\{", ln)
        if m:
            cur = m.group(1); buf = [ln]; depth = 1; continue
    else:
        buf.append(ln); depth += ln.count("{") - ln.count("}")
        if depth == 0:
            blocks[cur] = "\n".join(buf); cur = None


def field(block, name):
    vals = re.findall(rf"(?<![a-z_]){name}\s*=\s*([A-Za-z0-9_-]+)", block)
    return vals[-1] if vals else None


holder = {}
liege = {}
for k, b in blocks.items():
    h = field(b, "holder"); lg = field(b, "liege")
    if h: holder[k] = h
    if lg: liege[k] = lg

# holder -> 持有的最高头衔
held = collections.defaultdict(list)
for k, h in holder.items():
    if k[0] in "ekdh":
        held[h].append(k)
rank = {"h": 5, "e": 4, "k": 3, "d": 2, "c": 1, "b": 0}
top_of = {}
for h, ks in held.items():
    top_of[h] = max(ks, key=lambda x: rank[x[0]])

# 从 c_ 出发沿 liege 爬到顶
def climb(k):
    seen = set()
    while k in liege and k not in seen:
        seen.add(k); k = liege[k]
    return k

top_liege = {}
for k in blocks:
    if k.startswith("c_"):
        if k in liege:
            top_liege[k] = climb(k)
        else:
            # 无 liege：看 holder 的最高头衔
            h = holder.get(k)
            t = top_of.get(h) if h else None
            top_liege[k] = t if t else "NONE"

c = collections.Counter()
for k, t in top_liege.items():
    if t == "NONE": c["NONE"] += 1
    elif t is None: c["NONE"] += 1
    else:
        c[t[0] + ("_eu5" if "_eu5_" in t else "_real")] += 1
print("c_ 最高归属头衔类别：")
for k, v in sorted(c.items()):
    print(f"  {k:12s} {v}")

print("\n无 liege 的 c_ 中，holder 最高头衔层级：")
c2 = collections.Counter()
for k in blocks:
    if k.startswith("c_") and k not in liege:
        h = holder.get(k); t = top_of.get(h)
        c2[t[0] if t else "NONE"] += 1
print(" ", dict(c2))

print("\nh_ 层的 c_ 数：", sum(1 for t in top_liege.values() if t and t.startswith("h_")))
print("h 头衔：", [k for k in blocks if k.startswith("h_")])

# 顶层头衔清单（被爬到的）
topkeys = collections.Counter(t for t in top_liege.values() if t and t != "NONE")
print("\n被爬到的顶层头衔数：", len(topkeys))
for k, v in sorted(topkeys.items(), key=lambda x: -x[1])[:20]:
    print(f"  {k:24s} {v}")
