# -*- coding: utf-8 -*-
"""只读诊断：mod 省文件 culture/faith 的粒度 + pops 覆盖率 + 键是否对得上 EU5。
输出 gen_debug/_diag_culture_source.txt
"""
import io, os, re, json, csv
from collections import Counter, defaultdict

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
GEN = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"
OUT = os.path.join(MOD, "gen_debug", "_diag_culture_source.txt")


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


def block_body(txt, start):
    d = 0
    for j in range(start, len(txt)):
        c = txt[j]
        if c == "{":
            d += 1
        elif c == "}":
            d -= 1
            if d == 0:
                return txt[start:j + 1]
    return txt[start:]


L = []
# A. province file: pid -> culture/faith
ptxt = read(os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt"))
prov_cult, prov_faith = {}, {}
for m in re.finditer(r"(?m)^(\d+)\s*=\s*\{", ptxt):
    pid = int(m.group(1))
    body = block_body(ptxt, m.end() - 1)
    c = re.search(r"(?m)^\s*culture\s*=\s*(\S+)", body)
    f = re.search(r"(?m)^\s*faith\s*=\s*(\S+)", body)
    if c:
        prov_cult[pid] = c.group(1)
    if f:
        prov_faith[pid] = f.group(1)
L.append("province file: %d blocks, %d culture, %d faith" % (len(prov_cult), len(prov_cult), len(prov_faith)))

# B. definition.csv (EXPORT: p0=tool id, p4=location name)
pid_loc = {}
for line in read(os.path.join(GEN, "csv", "definition.csv")).splitlines():
    p = line.split(";")
    if len(p) >= 5 and p[0].isdigit() and int(p[0]) != 0:
        pid_loc[int(p[0])] = p[4]
L.append("definition.csv: %d pid->location" % len(pid_loc))

# C. landed_titles: county -> [pid]
lt = read(os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt"))
county_provs = defaultdict(list)
cur_county = None
depth = 0
for line in lt.splitlines():
    s = line.strip()
    mc = re.match(r"^(c_[A-Za-z0-9_]+)\s*=\s*\{", s)
    if mc:
        cur_county = mc.group(1)
        depth = 1
        continue
    if cur_county is not None:
        depth += s.count("{") - s.count("}")
        mp = re.match(r"^province\s*=\s*(\d+)", s)
        if mp:
            county_provs[cur_county].append(int(mp.group(1)))
        if depth <= 0:
            cur_county = None
L.append("landed_titles: %d counties, %d provinces total" % (len(county_provs), sum(len(v) for v in county_provs.values())))

# D. pops: location -> culture sizes / religion sizes
pop_cult, pop_rel = defaultdict(Counter), defaultdict(Counter)
ptxt2 = read(os.path.join(EU5, "main_menu", "setup", "start", "06_pops.txt"))
for m in re.finditer(r"(?ms)^[ \t]*([a-z0-9_']+)[ \t]*=[ \t]*\{\n(.*?)^[ \t]*\}", ptxt2):
    loc = m.group(1)
    for pm in re.finditer(r"define_pop\s*=\s*\{([^}]*)\}", m.group(2)):
        pb = pm.group(1)
        sz = re.search(r"\bsize\s*=\s*([0-9.]+)", pb)
        cu = re.search(r"\bculture\s*=\s*([a-z0-9_]+)", pb)
        rl = re.search(r"\breligion\s*=\s*([a-z0-9_]+)", pb)
        if sz:
            v = float(sz.group(1))
            if cu:
                pop_cult[loc][cu.group(1)] += v
            if rl:
                pop_rel[loc][rl.group(1)] += v
L.append("pops: %d locations with culture pops, %d with religion pops" % (len(pop_cult), len(pop_rel)))

# E. key overlap
peoples = json.load(io.open(os.path.join(GEN, "eu5_peoples.json"), encoding="utf-8"))
eu5_cult = set(peoples["cultures"].keys())
eu5_rel = set(peoples["religions"].keys())
pc = set(prov_cult.values())
pf = set(prov_faith.values())
L.append("")
L.append("== key overlap ==")
L.append("province culture distinct=%d | eu5 cultures=%d | intersect=%d" % (len(pc), len(eu5_cult), len(pc & eu5_cult)))
L.append("  province-culture NOT in eu5 (%d): %s" % (len(pc - eu5_cult), sorted(pc - eu5_cult)[:25]))
L.append("province faith distinct=%d | eu5 religions=%d | intersect=%d" % (len(pf), len(eu5_rel), len(pf & eu5_rel)))
L.append("  province-faith NOT in eu5 (%d): %s" % (len(pf - eu5_rel), sorted(pf - eu5_rel)[:25]))

# F. granularity: per county distinct culture/faith among baronies
multi_c = multi_f = 0
for c, pids in county_provs.items():
    cs = set(prov_cult.get(p, None) for p in pids)
    fs = set(prov_faith.get(p, None) for p in pids)
    if len(cs) > 1:
        multi_c += 1
    if len(fs) > 1:
        multi_f += 1
L.append("")
L.append("== granularity ==")
L.append("counties with >1 distinct culture among baronies: %d / %d" % (multi_c, len(county_provs)))
L.append("counties with >1 distinct faith among baronies: %d / %d" % (multi_f, len(county_provs)))

# G. sample county
for c in list(county_provs)[:3]:
    pids = county_provs[c]
    L.append("  %s: %s" % (c, [(p, prov_cult.get(p), prov_faith.get(p), pid_loc.get(p)) for p in pids[:5]]))

# H. pops coverage over all locations referenced by mod provinces
locs = set(pid_loc.values())
have = [l for l in locs if l in pop_cult]
L.append("")
L.append("== pops coverage ==")
L.append("mod locations: %d | with pops: %d (%.1f%%)" % (len(locs), len(have), 100.0 * len(have) / len(locs) if locs else 0))
missing = [l for l in locs if l not in pop_cult]
L.append("  no pops (%d) sample: %s" % (len(missing), missing[:30]))

io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("OK wrote", OUT)
