# -*- coding: utf-8 -*-
"""只读：文化 -> 各大洲省份数（EU5 definitions.txt 顶层 continent）。

链路：mod province history (id -> culture) + mod landed_titles (id -> b_<location>)
      -> EU5 definitions.txt (location -> continent)
输出 gen_debug/_culture_continents.csv
"""
import io, os, re, csv, collections

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game\in_game"

DEF = os.path.join(EU5, "map_data", "definitions.txt")
PROV = os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt")
LT = os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt")
OUT = os.path.join(MOD, "gen_debug", "_culture_continents.csv")

# ---------- 1. location -> continent ----------
txt = io.open(DEF, encoding="utf-8-sig", errors="replace").read()
loc2cont = {}
stack = []
for line in txt.splitlines():
    s = line.split("#")[0].strip()
    if not s:
        continue
    # 取出本行大括号之外、以及最内层括号之间的 location token
    if "{" in s:
        head, rest = s.split("{", 1)
        key = head.strip()
        if key:
            stack.append(key)
        body = rest
    else:
        body = s
    if "}" in body:
        body = body.split("}", 1)[0]
    cont = stack[0].rstrip(" =").strip() if stack else ""
    for name in body.replace("{", " ").split():
        if name and name != "}":
            loc2cont.setdefault(name, cont)
    if "}" in s:
        for _ in range(s.count("}")):
            if stack:
                stack.pop()
print("location -> continent: %d" % len(loc2cont))
print("大洲分布:", collections.Counter(loc2cont.values()))

# ---------- 2. province id -> culture ----------
pt = io.open(PROV, encoding="utf-8-sig", errors="ignore").read()
pc = {}
for m in re.finditer(r"(?m)^(\d+)\s*=\s*\{", pt):
    k, d = m.end(), 1
    while k < len(pt) and d:
        if pt[k] == "{":
            d += 1
        elif pt[k] == "}":
            d -= 1
        k += 1
    mc = re.search(r"(?m)^\s*culture\s*=\s*([a-z0-9_]+)", pt[m.end():k - 1])
    if mc:
        pc.setdefault(m.group(1), mc.group(1))
print("province -> culture: %d" % len(pc))

# ---------- 3. province id -> barony(location) ----------
t = io.open(LT, encoding="utf-8-sig", errors="ignore").read()
tok = re.compile(r"([a-z0-9_]+)\s*=\s*\{|\{|\}")
st = []
id2loc = {}
for m in tok.finditer(t):
    s = m.group(0)
    if s == "}":
        if st:
            st.pop()
        continue
    if s == "{":
        st.append("?")
        continue
    key = m.group(1)
    st.append(key)
    if key.startswith("b_"):
        mp = re.search(r"\bprovince\s*=\s*(\d+)", t[m.end():m.end() + 400])
        if mp:
            id2loc.setdefault(mp.group(1), key[2:])
print("province id -> barony: %d" % len(id2loc))

# ---------- 4. culture -> continent counts ----------
cult_cont = collections.defaultdict(collections.Counter)
unmatched = 0
for pid, cult in pc.items():
    loc = id2loc.get(pid)
    if not loc:
        unmatched += 1
        continue
    cont = loc2cont.get(loc)
    if not cont:
        unmatched += 1
        continue
    cult_cont[cult][cont] += 1
print("province 未匹配到大洲: %d" % unmatched)

with io.open(OUT, "w", encoding="utf-8-sig", newline="") as fp:
    w = csv.writer(fp)
    w.writerow(["culture", "total"] + ["c_" + c for c in
               ("europe", "asia", "africa", "america", "oceania")] + ["other"])
    for c in sorted(cult_cont):
        cc = cult_cont[c]
        row = [c, sum(cc.values())] + [cc.get(x, 0) for x in
                                       ("europe", "asia", "africa", "america", "oceania")]
        row.append(sum(v for k, v in cc.items() if k not in
                       ("europe", "asia", "africa", "america", "oceania")))
        w.writerow(row)
print("写出", OUT, len(cult_cont), "个文化")
