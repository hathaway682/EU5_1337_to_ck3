# -*- coding: utf-8 -*-
"""只读：用 CrusaderUniversalis（工坊 3811443965）给非洲 + 东南亚推导「EU5 宗教 -> CK3 faith/rite」映射。

步骤：
 1. 从 CU 抽 county 级 rite（求值到 1178.1.1，CK3 原版数据的天花板；CU 里 >1178 的块是作者自造，不用）
 2. 本 mod：province -> county -> kingdom，按王国名划分 非洲 / 东南亚
 3. 本 mod：province -> EU5 religion（pops 多数）
 4. 交叉表 eu5_religion x cu_rite（按省计数），取每个 EU5 宗教的多数 rite
 5. 输出建议映射 + 现有 faith_map 对照
不写任何游戏文件。
"""
import io, os, re, csv, glob
from collections import Counter, defaultdict

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
CU = r"E:\SteamLibrary\steamapps\workshop\content\1158310\3811443965"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"
FAITHMAP = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export\eu5_ck3_faith_map.csv"
OUTDIR = os.path.join(MOD, "gen_debug")
START = (1178, 1, 1)

AFRICA = {"maghreb", "egypt", "nubia", "somalia", "ethiopia", "sahel", "guinea",
          "central_africa", "kongo", "southern_africa", "zimbabwe", "swahili_coast",
          "madagascar", "macaronesia"}
SEA = {"indochina", "indonesia"}
MELANESIA = {"melanesia"}

BLOCK = re.compile(r"([A-Za-z0-9_]+)\s*=\s*\{")


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


def walk(text, path=()):
    i, n = 0, len(text)
    while i < n:
        m = BLOCK.search(text, i)
        if not m:
            return
        j, d = m.end(), 1
        while j < n and d:
            c = text[j]
            if c == "{":
                d += 1
            elif c == "}":
                d -= 1
            j += 1
        body = text[m.end():j - 1]
        yield path, m.group(1), body
        yield from walk(body, path + (m.group(1),))
        i = j


def cu_county_rite():
    """county -> rite（CU 的首府值 + province_mapping 继承，求值到 1178.1.1）"""
    hist = {}
    for p in glob.glob(os.path.join(CU, "history", "provinces", "*.txt")):
        t = read(p)
        for m in re.finditer(r"(?m)^(\d+)\s*=\s*\{", t):
            pid = int(m.group(1))
            body = t[m.end() - 1:]
            d = 0
            for j, ch in enumerate(body):
                if ch == "{":
                    d += 1
                elif ch == "}":
                    d -= 1
                    if d == 0:
                        body = body[1:j]
                        break
            base = None
            dated = []
            depth = 0
            cur = None
            for line in body.split("\n"):
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                md = re.match(r"(\d{1,4})\.(\d{1,2})\.(\d{1,2})\s*=\s*\{", s)
                if md:
                    cur = (int(md.group(1)), int(md.group(2)), int(md.group(3)))
                mf = re.match(r"(?:rite|faith)\s*=\s*(\S+)", s)
                if mf:
                    if depth == 1 and cur:
                        dated.append((cur, mf.group(1)))
                    elif depth == 0:
                        base = mf.group(1)
                depth += line.count("{") - line.count("}")
            v = base
            for dt, val in sorted(dated):
                if dt <= START:
                    v = val
            if v:
                hist[pid] = v

    mapping = {}
    for p in glob.glob(os.path.join(CU, "history", "province_mapping", "*.txt")):
        for line in read(p).split("\n"):
            m = re.match(r"\s*(\d+)\s*=\s*(\d+)\s*(?:#.*)?$", line)
            if m:
                mapping[int(m.group(1))] = int(m.group(2))

    def resolve(pid, seen=None):
        seen = seen or set()
        if pid in hist:
            return hist[pid]
        if pid in mapping and pid not in seen:
            seen.add(pid)
            return resolve(mapping[pid], seen)
        return None

    cu_b = {}
    for p in glob.glob(os.path.join(CU, "common", "landed_titles", "*.txt")):
        for path, key, body in walk(read(p)):
            if not key.startswith("b_"):
                continue
            m = re.search(r"\bprovince\s*=\s*(\d+)", body)
            if not m:
                continue
            c = next((x for x in reversed(path) if x.startswith("c_")), None)
            r = resolve(int(m.group(1)))
            if c and r and c not in cu_b:
                cu_b[c] = r
    return cu_b


def main():
    # --- 本 mod 结构：province -> county -> kingdom
    lt = read(os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt"))
    prov_county, county_kingdom = {}, {}
    for path, key, body in walk(lt):
        if key.startswith("b_"):
            m = re.search(r"\bprovince\s*=\s*(\d+)", body)
            if not m:
                continue
            c = next((x for x in reversed(path) if x.startswith("c_")), None)
            k = next((x for x in reversed(path) if x.startswith("k_")), None)
            if c:
                prov_county[int(m.group(1))] = c
                if k:
                    county_kingdom[c] = k
    print("provinces:", len(prov_county), "counties:", len(set(prov_county.values())))

    def region(county):
        k = county_kingdom.get(county, "")[2:]
        if k in AFRICA:
            return "africa"
        if k in SEA:
            return "sea"
        if k in MELANESIA:
            return "melanesia"
        return None

    # --- EU5 religion per province（pops 多数）
    pop_rel = defaultdict(Counter)
    pt = read(os.path.join(EU5, "main_menu", "setup", "start", "06_pops.txt"))
    for m in re.finditer(r"(?ms)^[ \t]*([a-z0-9_']+)[ \t]*=[ \t]*\{\n(.*?)^[ \t]*\}", pt):
        loc = m.group(1)
        for pm in re.finditer(r"define_pop\s*=\s*\{([^}]*)\}", m.group(2)):
            pb = pm.group(1)
            sz = re.search(r"\bsize\s*=\s*([0-9.]+)", pb)
            rl = re.search(r"\breligion\s*=\s*([a-z0-9_]+)", pb)
            if sz and rl:
                pop_rel[loc][rl.group(1)] += float(sz.group(1))

    prov_loc = {}
    for path, key, body in walk(lt):
        if key.startswith("b_"):
            m = re.search(r"\bprovince\s*=\s*(\d+)", body)
            if m:
                prov_loc[int(m.group(1))] = key[2:]

    # --- CU county -> rite
    cu_b = cu_county_rite()
    print("CU baronies with rite:", len(cu_b))

    # --- 交叉表
    cross = defaultdict(Counter)     # region -> (eu5rel, cu_rite) counts
    per_rel = defaultdict(lambda: defaultdict(Counter))   # eu5rel -> region -> rite
    matched_prov = defaultdict(int)
    for pid, county in prov_county.items():
        rg = region(county)
        if not rg:
            continue
        loc = prov_loc.get(pid)
        if not loc or loc not in pop_rel or not pop_rel[loc]:
            continue
        e = min(pop_rel[loc].items(), key=lambda kv: (-kv[1], kv[0]))[0]
        r = cu_b.get(county)
        if not r:
            continue
        matched_prov[rg] += 1
        cross[rg][(e, r)] += 1
        per_rel[e][rg][r] += 1

    print()
    for rg in ("africa", "sea", "melanesia"):
        n = matched_prov[rg]
        tot = sum(1 for p, c in prov_county.items() if region(c) == rg)
        print("== %s ==  provinces=%d  CU 有数据的=%d (%.0f%%)" % (rg, tot, n, 100.0 * n / max(tot, 1)))

    # --- 建议映射
    print()
    print("== 每个 EU5 宗教的多数 CU rite（非洲 + 东南亚）==")
    rows = []
    for e in sorted(per_rel):
        agg = Counter()
        for rg, cc in per_rel[e].items():
            if rg in ("africa", "sea"):
                agg += cc
        if not agg:
            continue
        tot = sum(agg.values())
        best, bn = agg.most_common(1)[0]
        rows.append([e, best, bn, tot, round(100.0 * bn / tot, 1),
                     "; ".join("%s:%d" % (k, v) for k, v in agg.most_common(4))])
    rows.sort(key=lambda r: -r[3])
    print("  %-26s %-26s %-6s %-6s %s" % ("eu5_religion", "majority_rite", "hit", "tot", "share"))
    for r in rows:
        print("  %-26s %-26s %-6d %-6d %.0f%%   %s" % (r[0], r[1], r[2], r[3], r[4], r[5]))

    # --- 现有 faith map 对照
    fmap = {}
    for row in csv.DictReader(io.open(FAITHMAP, encoding="utf-8-sig")):
        fmap[row["eu5_religion"]] = row["ck3_faith"] or "pagan"
    print()
    print("== 现有 faith map 里这些 EU5 宗教是什么 ==")
    for r in rows:
        print("  %-26s now=%-24s -> suggest=%s" % (r[0], fmap.get(r[0], "(缺失)"), r[1]))

    with io.open(os.path.join(OUTDIR, "_africa_sea_faith_suggest.csv"), "w",
                 encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["eu5_religion", "suggested_rite", "hit", "total", "share_pct",
                    "current_faith_map", "detail"])
        for r in rows:
            w.writerow(r + [fmap.get(r[0], "")])
    print()
    print("csv:", os.path.join(OUTDIR, "_africa_sea_faith_suggest.csv"))


if __name__ == "__main__":
    main()
