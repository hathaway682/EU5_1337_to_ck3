# -*- coding: utf-8 -*-
"""CU mod 的 CK3 文化与本 mod 的 EU5 文化，在【男爵领】层面的重合度对照（只读）。

口径（与 _cu_barony_overlap.py 的宗教版完全一致）：
  - 我们的每个男爵领(b_xxx = province) 有：所属县、所属帝国、EU5 文化（= province 文件 culture）
  - CU 只写县首府，所以 CU 的文化是【县级】数据；一个县下所有男爵领共用该县的 CU 文化
  - "重合度" = 该 EU5 文化分组的男爵领里，有多少个落在 CU 有文化数据的县里
  - CU culture 求值到 1173.1.1（原版数据最多到 1173；>1173 的块是 CU 作者自造）
  - CU 的 gen_wilderness_culture 视为"无有效文化"（作者自造占位）

输出：
  gen_debug/_cu_barony_culture_overlap.csv   按 (帝国, EU5文化组) 汇总
  gen_debug/_cu_barony_culture_detail.csv    逐男爵领明细
"""
import io, os, re, csv, glob
from collections import Counter, defaultdict

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
CU = r"E:\SteamLibrary\steamapps\workshop\content\1158310\3811443965"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game\in_game"
OUTDIR = os.path.join(MOD, "gen_debug")
START = (1173, 1, 1)

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


def eu5_culture_groups():
    """EU5 culture -> (culture_group, language)"""
    out = {}
    d = os.path.join(EU5, "common", "cultures")
    for fn in os.listdir(d):
        if not fn.endswith(".txt"):
            continue
        for path, key, body in walk(read(os.path.join(d, fn))):
            if path:
                continue
            g = re.search(r"culture_groups\s*=\s*\{([^}]*)\}", body)
            lg = re.search(r"(?m)^\s*language\s*=\s*(\S+)", body)
            out[key] = (g.group(1).strip().split()[0] if g and g.group(1).strip() else "",
                        lg.group(1) if lg else "")
    return out


def cu_barony_culture():
    """CU 县 -> culture（≤ START），以及 县首府染色整县后的 男爵领名 -> culture"""
    hist, comment_county = {}, {}
    for p in sorted(glob.glob(os.path.join(CU, "history", "provinces", "*.txt"))):
        t = read(p)
        for m in re.finditer(r"(?m)^(\d+)\s*=\s*\{([^\n]*)", t):
            pid = int(m.group(1))
            mc = re.search(r"#\s*b_[a-z0-9_]+,?\s*(c_[a-z0-9_\-]+)", m.group(2))
            if mc:
                comment_county[pid] = mc.group(1)
            bp = t.index("{", m.end(1))
            body = t[bp:]
            d = 0
            for j, ch in enumerate(body):
                if ch == "{":
                    d += 1
                elif ch == "}":
                    d -= 1
                    if d == 0:
                        body = body[1:j]
                        break
            base, dated, depth, cur = None, [], 0, None
            for line in body.split("\n"):
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                md = re.match(r"(\d{1,4})\.(\d{1,2})\.(\d{1,2})\s*=\s*\{", s)
                if md:
                    cur = (int(md.group(1)), int(md.group(2)), int(md.group(3)))
                mf = re.match(r"culture\s*=\s*(\S+)", s)
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

    out, cbset = {}, defaultdict(set)
    for p in sorted(glob.glob(os.path.join(CU, "common", "landed_titles", "*.txt"))):
        for path, key, body in walk(read(p)):
            if not key.startswith("b_"):
                continue
            m = re.search(r"\bprovince\s*=\s*(\d+)", body)
            if not m:
                continue
            c = next((x for x in reversed(path) if x.startswith("c_")), None)
            if not c:
                continue
            cbset[c].add(key[2:])
            r = resolve(int(m.group(1)))
            if r and c not in out:
                out[c] = r
    for pid, c in comment_county.items():
        r = resolve(pid)
        if r and c not in out:
            out[c] = r

    # 男爵领口径：县首府染色整县后，县下每个 b_ 都拿到该县的 culture
    bcult = {}
    for p in sorted(glob.glob(os.path.join(CU, "common", "landed_titles", "*.txt"))):
        for path, key, body in walk(read(p)):
            if not key.startswith("b_"):
                continue
            c = next((x for x in reversed(path) if x.startswith("c_")), None)
            if c and c in out:
                bcult[key[2:]] = out[c]
    return out, hist, comment_county, cbset, bcult


def main():
    lt = read(os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt"))
    prov_county, prov_king, prov_emp, prov_loc = {}, {}, {}, {}
    our_cbset = defaultdict(set)
    for path, key, body in walk(lt):
        if not key.startswith("b_"):
            continue
        m = re.search(r"\bprovince\s*=\s*(\d+)", body)
        if not m:
            continue
        pid = int(m.group(1))
        c = next((x for x in reversed(path) if x.startswith("c_")), None)
        k = next((x for x in reversed(path) if x.startswith("k_")), None)
        e = next((x for x in reversed(path) if x.startswith("e_")), None)
        if c:
            prov_county[pid] = c
            our_cbset[c].add(key[2:])
        if k:
            prov_king[pid] = k
        if e:
            prov_emp[pid] = e
        prov_loc[pid] = key[2:]

    # 我们现状文化（= EU5 文化 key）
    raw = read(os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt"))
    cur = {}
    for m in re.finditer(r"(?m)^(\d+)\s*=\s*\{", raw):
        pid = int(m.group(1))
        body = raw[m.end() - 1:]
        d = 0
        for j, ch in enumerate(body):
            if ch == "{":
                d += 1
            elif ch == "}":
                d -= 1
                if d == 0:
                    body = body[:j + 1]
                    break
        c = re.search(r"(?m)^\s*culture\s*=\s*(\S+)", body)
        cur[pid] = c.group(1) if c else None

    cg = eu5_culture_groups()
    cu_b, cu_hist, cu_cc, cu_cbset, cu_bc = cu_barony_culture()
    print("EU5 cultures: %d | CU 有 culture 的县: %d | CU 有文化的男爵领名: %d | CU 有块头的县: %d"
          % (len(cg), len(cu_b), len(cu_bc), len(cu_cc)))
    print("我们的男爵领: %d" % len(prov_county))

    # 县名交叉验证：我们的县与 CU 同名县，男爵领名是否有交集（仅作参考）
    same_name = set(prov_county.values()) & set(cu_b)
    verified = {c for c in same_name if our_cbset.get(c) and cu_cbset.get(c)
                and (our_cbset[c] & cu_cbset[c])}
    print("同名县 %d 个，其中男爵领名可交叉验证 %d 个（%.1f%%）"
          % (len(same_name), len(verified), 100.0 * len(verified) / len(same_name) if same_name else 0))

    stat = defaultdict(lambda: {"n": 0, "cov": 0, "cults": Counter(), "cur": Counter()})
    by_grp = defaultdict(lambda: {"n": 0, "cov": 0, "cults": Counter()})
    detail = []
    miss_cult = 0
    for pid, county in prov_county.items():
        ec = cur.get(pid)
        if not ec:
            miss_cult += 1
            continue
        grp, lang = cg.get(ec, ("(unknown_group)", ""))
        rg = (prov_emp.get(pid) or "(no empire)")[2:]
        # 主口径：男爵领名同名即匹配（CU 的 culture 仍是县首府染色整县后的值）
        cc = cu_bc.get(prov_loc.get(pid, "")) or ""
        if cc == "gen_wilderness_culture":
            cc = ""
        # 参考口径：县名同名（旧版）
        cc_county = cu_b.get(county) or ""
        if cc_county == "gen_wilderness_culture":
            cc_county = ""
        s = stat[(rg, grp, lang)]
        s["n"] += 1
        s["cur"][ec] += 1
        gg = by_grp[(grp, lang)]
        gg["n"] += 1
        if cc:
            s["cov"] += 1
            s["cults"][cc] += 1
            gg["cov"] += 1
            gg["cults"][cc] += 1
        if cc_county:
            s["cov_c"] = s.get("cov_c", 0) + 1
            gg["cov_c"] = gg.get("cov_c", 0) + 1
        detail.append((rg, grp, lang, pid, prov_loc.get(pid, ""), county, ec, cc,
                       cc_county, prov_king.get(pid, "")))

    rows = []
    for (rg, grp, lang), s in stat.items():
        n, cov = s["n"], s["cov"]
        if s["cults"]:
            cult, hit = s["cults"].most_common(1)[0]
        else:
            cult, hit = "", 0
        rows.append({
            "empire": rg, "eu5_group": grp, "eu5_language": lang,
            "our_baronies": n, "cu_covered": cov,
            "cu_covered_by_county": s.get("cov_c", 0),
            "overlap_pct": round(100.0 * cov / n, 1) if n else 0,
            "cu_majority_culture": cult, "hit": hit,
            "share_in_covered_pct": round(100.0 * hit / cov, 1) if cov else 0,
            "n_cu_cultures": len(s["cults"]),
            "our_cultures_top3": ";".join("%s:%d" % kv for kv in s["cur"].most_common(3)),
        })
    rows.sort(key=lambda r: (r["empire"], -r["our_baronies"]))

    with io.open(os.path.join(OUTDIR, "_cu_barony_culture_overlap.csv"), "w",
                 encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["empire", "eu5_group", "eu5_language",
                                          "our_baronies", "cu_covered", "cu_covered_by_county",
                                          "overlap_pct",
                                          "cu_majority_culture", "hit",
                                          "share_in_covered_pct", "n_cu_cultures",
                                          "our_cultures_top3"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    with io.open(os.path.join(OUTDIR, "_cu_barony_culture_detail.csv"), "w",
                 encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["empire", "eu5_group", "eu5_language", "province", "barony",
                    "county", "our_culture", "cu_culture", "cu_culture_by_county", "kingdom"])
        for d in sorted(detail):
            w.writerow(d)

    # 全局
    tot = sum(r["our_baronies"] for r in rows)
    cov = sum(r["cu_covered"] for r in rows)
    cov_c = sum(r["cu_covered_by_county"] for r in rows)
    print("\n== 全局 ==")
    print("男爵领 %d | 男爵领名匹配有文化 %d (%.1f%%) | 县名匹配有文化 %d (%.1f%%) | 缺 culture 字段 %d"
          % (tot, cov, 100.0 * cov / tot if tot else 0,
             cov_c, 100.0 * cov_c / tot if tot else 0, miss_cult))

    # 按帝国
    print("\n== 按我们的大区(empire) ==")
    print("%-22s %7s %7s %7s" % ("empire", "男爵领", "有CU", "重合%"))
    by_emp = defaultdict(lambda: [0, 0])
    for r in rows:
        by_emp[r["empire"]][0] += r["our_baronies"]
        by_emp[r["empire"]][1] += r["cu_covered"]
    for e, (n, c) in sorted(by_emp.items(), key=lambda kv: -kv[1][0]):
        print("%-22s %7d %7d %7.1f" % (e, n, c, 100.0 * c / n if n else 0))

    # 按 EU5 文化组（全局合并）
    print("\n== 按 EU5 文化组（全局合并，>=20 男爵领）==")
    print("%-26s %-22s %7s %7s %7s  %-22s %6s %5s" %
          ("eu5_group", "language", "男爵领", "有CU", "重合%", "CU多数文化", "占比%", "种类"))
    gl = []
    for (grp, lang), g in by_grp.items():
        n, c = g["n"], g["cov"]
        cult, hit = g["cults"].most_common(1)[0] if g["cults"] else ("", 0)
        gl.append((grp, lang, n, c, 100.0 * c / n if n else 0, cult,
                   100.0 * hit / c if c else 0, len(g["cults"])))
    gl.sort(key=lambda x: -x[2])
    for grp, lang, n, c, p, cult, sh, k in gl:
        if n < 20:
            continue
        print("%-26s %-22s %7d %7d %7.1f  %-22s %6.1f %5d" %
              (grp, lang, n, c, p, cult or "-", sh, k))

    print("\ncsv:", os.path.join(OUTDIR, "_cu_barony_culture_overlap.csv"))


if __name__ == "__main__":
    main()
