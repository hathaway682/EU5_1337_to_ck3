# -*- coding: utf-8 -*-
"""只读探查 v2：本 mod 的每个公国，其地在 CU（1337.4.1 开局）里归属的法理王国。

v2 修了两处：
  1. key 正则允许连字符（k_kabisay-an / k_caspian-pontic_steppe 之前被截断成 "an" 等）；
  2. 应用 history/titles 里的法理变更（de_jure_liege 与 effect 里的
     set_de_jure_liege_title），取 <= 1337.4.1 的最后一个。
"""
import glob
import io
import os
import re
import csv
from collections import Counter

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
CU = r"E:\SteamLibrary\steamapps\workshop\content\1158310\3811443965"
CUTOFF = (1337, 4, 1)

PAT = re.compile(r"([A-Za-z0-9_.-]+)\s*=\s*\{")


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


def parse_tree(text, parents=()):
    out = []
    i, n = 0, len(text)
    while True:
        m = PAT.search(text, i)
        if not m:
            break
        key = m.group(1)
        j = m.end()
        d = 1
        while j < n and d:
            c = text[j]
            if c == "{":
                d += 1
            elif c == "}":
                d -= 1
            j += 1
        body = text[m.end():j - 1]
        out.append((key, parents, body))
        out.extend(parse_tree(body, parents + (key,)))
        i = j
    return out


def cu_static():
    b2c, c2d, d2k, k2e, e2h = {}, {}, {}, {}, {}
    for p in glob.glob(os.path.join(CU, "common", "landed_titles", "*.txt")):
        t = read(p)
        for key, parents, body in parse_tree(t):
            if key.startswith("b_"):
                c = next((x for x in reversed(parents) if x.startswith("c_")), None)
                if c:
                    b2c.setdefault(key, c)
            elif key.startswith("c_"):
                d = next((x for x in reversed(parents) if x.startswith("d_")), None)
                if d:
                    c2d.setdefault(key, d)
            elif key.startswith("d_"):
                k = next((x for x in reversed(parents) if x.startswith("k_")), None)
                if k:
                    d2k.setdefault(key, k)
            elif key.startswith("k_"):
                e = next((x for x in reversed(parents) if x.startswith("e_")), None)
                if e:
                    k2e.setdefault(key, e)
            elif key.startswith("e_"):
                h = next((x for x in reversed(parents) if x.startswith("h_")), None)
                if h:
                    e2h.setdefault(key, h)
    return b2c, c2d, d2k, k2e, e2h


def date_of(s):
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)$", s)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def history_overrides():
    """{title: target}，只收 <= CUTOFF 的最后一个。"""
    res = {}
    for p in glob.glob(os.path.join(CU, "history", "titles", "*.txt")):
        t = read(p)
        t = re.sub(r"(?m)#[^\n]*$", "", t)
        for key, parents, body in parse_tree(t):
            if parents:
                continue
            if key[:2] not in ("d_", "k_", "e_", "h_"):
                continue
            for m in re.finditer(r'(?m)^\tde_jure_liege\s*=\s*"?([A-Za-z0-9_-]+|0)"?', body):
                res.setdefault(key, []).append(((0, 0, 0), m.group(1)))
            for dk, dpar, dbody in parse_tree(body):
                if dpar:
                    continue
                dt = date_of(dk)
                if not dt or dt > CUTOFF:
                    continue
                for m in re.finditer(r'(?m)^\s*de_jure_liege\s*=\s*"?([A-Za-z0-9_-]+|0)"?', dbody):
                    res.setdefault(key, []).append((dt, m.group(1)))
                for m in re.finditer(r"set_de_jure_liege_title\s*=\s*title:([A-Za-z0-9_-]+)", dbody):
                    res.setdefault(key, []).append((dt, m.group(1)))
    return {k: sorted(v)[-1][1] for k, v in res.items()}


def mod_duchies():
    t = read(os.path.join(MOD, "gen_debug", "_dejure_src_20261029.txt"))
    res = {}
    for key, parents, body in parse_tree(t):
        if key.startswith("d_"):
            res[key] = set(int(x) for x in re.findall(r"(?m)^\s*province\s*=\s*(\d+)", body))
    return res


def main():
    b2c, c2d, d2k, k2e, e2h = cu_static()
    ov = history_overrides()
    print("CU static: c2d=%d d2k=%d k2e=%d e2h=%d | history overrides=%d" % (
        len(c2d), len(d2k), len(k2e), len(e2h), len(ov)))

    d_ov = {k: v for k, v in ov.items() if k.startswith("d_")}
    k_ov = {k: v for k, v in ov.items() if k.startswith("k_")}
    e_ov = {k: v for k, v in ov.items() if k.startswith("e_")}
    print("  d overrides=%d k=%d e=%d" % (len(d_ov), len(k_ov), len(e_ov)))

    def resolve_k(d, seen=()):
        if d in seen:
            return None
        v = d_ov.get(d)
        if v is not None:
            if v == "0":
                return None
            if v.startswith("k_"):
                return v
            if v.startswith("d_"):
                return resolve_k(v, seen + (d,))
        return d2k.get(d)

    k2e.update({k: v for k, v in k_ov.items() if v.startswith("e_")})
    e2h.update({k: v for k, v in e_ov.items() if v.startswith("h_")})

    rows = list(csv.DictReader(io.open(os.path.join(MOD, "gen_debug", "_cu_vs_ours.csv"), encoding="utf-8-sig")))
    prov2county = {int(r["our_province"]): r["cu_county"] for r in rows}

    cty2k = {}
    for c, d in c2d.items():
        k = resolve_k(d)
        if k:
            cty2k[c] = k
    print("cu counties with kingdom=%d / %d" % (len(cty2k), len(set(c2d))))

    duchies = mod_duchies()
    print("mod duchies=%d" % len(duchies))

    out_rows = []
    for d, provs in sorted(duchies.items()):
        hit = [p for p in provs if p in prov2county]
        if not hit:
            out_rows.append((d, 0, len(provs), "", 0, ""))
            continue
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

    cov = sum(1 for r in out_rows if r[1])
    print("covered=%d uncovered=%d no_kingdom=%d" % (
        cov, len(out_rows) - cov, sum(1 for r in out_rows if r[5] == "no_kingdom")))
    kc = Counter(r[3] for r in out_rows if r[3])
    print("distinct target kingdoms=%d" % len(kc))
    print("top20:", kc.most_common(20))

    with io.open(os.path.join(MOD, "gen_debug", "_probe_cu_dejure.out"), "w", encoding="utf-8") as f:
        f.write("duchy,cov_prov,total_prov,top_kingdom,top_n,ratio\n")
        for r in out_rows:
            f.write(",".join(str(x) for x in r) + "\n")
    print("wrote _probe_cu_dejure.out")


if __name__ == "__main__":
    main()
