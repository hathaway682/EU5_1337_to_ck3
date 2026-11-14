# -*- coding: utf-8 -*-
"""对 81 个未确认圣地，用 key 里的显著词干在 mod 全部男爵领 key 里做子串搜索，
列出「同名/近名」候选（不在当前县也算），供判定同一个词 / 同一城市不同时期称呼。"""
import csv, io, os, re

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LT = os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt")

def read(p):
    return io.open(p, encoding="utf-8-sig").read()

# 法理树
stack, county_of, bar_of = [], {}, {}
for ln in read(LT).split("\n"):
    s = ln.strip()
    ind = len(ln) - len(ln.lstrip("\t "))
    if s.startswith("}"):
        while stack and stack[-1][0] >= ind:
            stack.pop()
        continue
    m = re.match(r'^([a-z])_([A-Za-z0-9_\-]+)\s*=\s*\{', s)
    if not m:
        continue
    rank, key = m.group(1), m.group(1) + "_" + m.group(2)
    while stack and stack[-1][0] >= ind:
        stack.pop()
    if rank == "c":
        county_of.setdefault(key, [])
    elif rank == "b":
        for sind, skey in reversed(stack):
            if skey.startswith("c_"):
                county_of.setdefault(skey, []).append(key)
                bar_of[key] = skey
                break
    stack.append((ind, key))

# 中文名（CSV 里已有的对照）
cnmap = {}
p = os.path.join(MOD, "gen_debug", "holy_sites_table.csv")
for r in csv.DictReader(io.open(p, encoding="utf-8-sig")):
    if r["男爵领"]:
        cnmap[r["男爵领"]] = r["男爵领中文"]

rows = list(csv.DictReader(io.open(p, encoding="utf-8-sig")))
un = [r for r in rows if r["状态"] != "已确认"]

keys = list(bar_of)

def norm(s):
    return s.replace("_", "").replace("-", "").lower()

nmap = {k: norm(k[2:]) for k in keys}

out = []
for r in un:
    k = r["圣地key"]
    stem = norm(k)
    hits = []
    for bk, nb in nmap.items():
        if len(nb) < 4:
            continue
        # 全名包含 / 被包含
        if stem in nb or (len(nb) >= 5 and nb in stem):
            hits.append(bk)
            continue
        # 前缀 6 字母相同
        if len(nb) >= 6 and len(stem) >= 6 and nb[:6] == stem[:6]:
            hits.append(bk)
    hits = [h for h in hits if h != r["男爵领"]]
    if hits:
        out.append("%-22s (%s) 现值 %s/%s" % (k, r["圣地中文名"], r["县"], r["男爵领"]))
        for h in hits[:12]:
            out.append("        -> %-30s %s  (县 %s)" % (h, cnmap.get(h, ""), bar_of.get(h, "")))

io.open(os.path.join(MOD, "gen_debug", "_unconf_samename.out"), "w", encoding="utf-8").write("\n".join(out))
print("命中", sum(1 for x in out if not x.startswith("        ")), "个圣地有近名候选")
print("\n".join(out))
