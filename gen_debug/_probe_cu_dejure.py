# -*- coding: utf-8 -*-
"""只读探查：本 mod 的每个公国，其地在 CU 里归属的法理王国分布。
输出统计与候选映射，不写任何文件（除本脚本外的 _probe_cu_dejure.out）。"""
import glob, io, os, re, csv, sys
from collections import Counter, defaultdict

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
CU = r"E:\SteamLibrary\steamapps\workshop\content\1158310\3811443965"


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


PAT = re.compile(r"([A-Za-z0-9_]+)\s*=\s*\{")


def parse_tree(text, parents=()):
    """返回 [(key, parents_tuple, body)]，按花括号栈解析。"""
    out = []
    i, n = 0, len(text)
    while True:
        m = PAT.search(text, i)
        if not m:
            break
        key = m.group(1)
        j = m.end()
        depth = 1
        while j < n and depth:
            c = text[j]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            j += 1
        body = text[m.end():j - 1]
        out.append((key, parents, body))
        out.extend(parse_tree(body, parents + (key,)))
        i = j
    return out


def cu_map():
    b2c = {}
    c2d = {}
    d2k = {}
    k2e = {}
    e2h = {}
    for p in glob.glob(os.path.join(CU, "common", "landed_titles", "*.txt")):
        t = read(p)
        for key, parents, body in parse_tree(t):
            if key.startswith("b_"):
                c = next((x for x in reversed(parents) if x.startswith("c_")), None)
                if c:
                    b2c[key] = c
            elif key.startswith("c_"):
                d = next((x for x in reversed(parents) if x.startswith("d_")), None)
                if d:
                    c2d[key] = d
            elif key.startswith("d_"):
                k = next((x for x in reversed(parents) if x.startswith("k_")), None)
                if k:
                    d2k[key] = k
            elif key.startswith("k_"):
                e = next((x for x in reversed(parents) if x.startswith("e_")), None)
                if e:
                    k2e[key] = e
            elif key.startswith("e_"):
                h = next((x for x in reversed(parents) if x.startswith("h_")), None)
                if h:
                    e2h[key] = h
    return b2c, c2d, d2k, k2e, e2h


def mod_duchies():
    t = read(os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt"))
    res = {}
    for key, parents, body in parse_tree(t):
        if key.startswith("d_"):
            provs = [int(x) for x in re.findall(r"(?m)^\s*province\s*=\s*(\d+)", body)]
            # 只取本 d_ 直接下的（body 已含子块，这里会把子 c_ 的 province 也算进来，正确）
            res[key] = set(provs)
    return res


def main():
    b2c, c2d, d2k, k2e, e2h = cu_map()
    print("CU: b2c=%d c2d=%d d2k=%d k2e=%d e2h=%d" % (len(b2c), len(c2d), len(d2k), len(k2e), len(e2h)))

    rows = list(csv.DictReader(io.open(os.path.join(MOD, "gen_debug", "_cu_vs_ours.csv"), encoding="utf-8-sig")))
    prov2county = {int(r["our_province"]): r["cu_county"] for r in rows}
    print("csv rows=%d uniq prov=%d" % (len(rows), len(prov2county)))

    # cu_county -> cu_kingdom
    cty2k = {}
    for c, d in c2d.items():
        k = d2k.get(d)
        if k:
            cty2k[c] = k
    print("cu county with kingdom=%d / %d" % (len(cty2k), len(set(c2d))))

    duchies = mod_duchies()
    print("mod duchies=%d" % len(duchies))

    covered, uncovered = 0, 0
    out_rows = []
    for d, provs in sorted(duchies.items()):
        hit = [p for p in provs if p in prov2county]
        if not hit:
            uncovered += 1
            out_rows.append((d, 0, len(provs), "", 0, ""))
            continue
        covered += 1
        cnt = Counter()
        for p in hit:
            k = cty2k.get(prov2county[p])
            if k:
                cnt[k] += 1
        if cnt:
            top, num = cnt.most_common(1)[0]
            out_rows.append((d, len(hit), len(provs), top, num, round(num / float(len(hit)), 3)))
        else:
            out_rows.append((d, len(hit), len(provs), "", 0, "no_kingdom"))

    print("covered duchies=%d uncovered=%d" % (covered, uncovered))
    no_k = sum(1 for r in out_rows if r[5] == "no_kingdom")
    print("covered but no CU kingdom=%d" % no_k)

    # 目标王国分布
    kc = Counter(r[3] for r in out_rows if r[3])
    print("distinct target kingdoms=%d" % len(kc))
    print("top 20:", kc.most_common(20))

    # 一致性：单一王国占比
    strong = sum(1 for r in out_rows if r[5] and isinstance(r[5], float) and r[5] >= 0.5)
    print("duchies with top kingdom >=50%%: %d" % strong)

    with io.open(os.path.join(MOD, "gen_debug", "_probe_cu_dejure.out"), "w", encoding="utf-8") as f:
        f.write("duchy,cov_prov,total_prov,top_kingdom,top_n,ratio\n")
        for r in out_rows:
            f.write(",".join(str(x) for x in r) + "\n")
    print("wrote _probe_cu_dejure.out")


if __name__ == "__main__":
    main()
