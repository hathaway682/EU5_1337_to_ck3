# -*- coding: utf-8 -*-
"""CU mod 的 CK3 rite 与本 mod 的 EU5 宗教，在【男爵领】层面的重合度对照（只读，不写任何文件）。

口径：
  - 我们的每个男爵领(b_xxx = province) 有：所属县、EU5 pops 多数宗教
  - CU 只写县首府，所以 CU 的 rite 是【县级】数据；一个县下所有男爵领共用该县的 CU rite
  - "重合度" = 该 EU5 宗教的男爵领里，有多少个落在 CU 有 rite 数据的县里
  - CU rite 求值到 1173.1.1（用户口径：原版数据最多到 1173；>1173 的块是 CU 作者自造）

输出：
  gen_debug/_cu_barony_overlap.csv    逐 (区域, EU5宗教) 汇总
  gen_debug/_cu_barony_detail.csv     逐男爵领明细（供抽查）
"""
import io, os, re, csv, glob
from collections import Counter, defaultdict

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
CU = r"E:\SteamLibrary\steamapps\workshop\content\1158310\3811443965"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"
OUTDIR = os.path.join(MOD, "gen_debug")
START = (1173, 1, 1)

AFRICA = {"maghreb", "egypt", "nubia", "somalia", "ethiopia", "sahel", "guinea",
          "central_africa", "kongo", "southern_africa", "zimbabwe", "swahili_coast",
          "madagascar", "macronesia"}
SEA = {"indochina", "indonesia"}

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


def religion_tables():
    """faith -> main_rite  (rite -> faith 反查用)"""
    faith_main = {}
    d = os.path.join(MOD, "common", "religion", "faith_types")
    for fn in os.listdir(d):
        if not fn.endswith(".txt"):
            continue
        for path, key, body in walk(read(os.path.join(d, fn))):
            if path:
                continue
            m = re.search(r"(?m)^\s*main_rite\s*=\s*(\S+)", body)
            if m:
                faith_main[key] = m.group(1)
    return faith_main


def cu_county_rite():
    """CU 县 -> rite（≤ START），以及县集合"""
    hist, comment_county = {}, {}
    for p in glob.glob(os.path.join(CU, "history", "provinces", "*.txt")):
        t = read(p)
        for m in re.finditer(r"(?m)^(\d+)\s*=\s*\{([^\n]*)", t):
            pid = int(m.group(1))
            mc = re.search(r"#\s*b_[a-z0-9_]+,\s*(c_[a-z0-9_\-]+)", m.group(2))
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

    out = {}
    for p in glob.glob(os.path.join(CU, "common", "landed_titles", "*.txt")):
        for path, key, body in walk(read(p)):
            if not key.startswith("b_"):
                continue
            m = re.search(r"\bprovince\s*=\s*(\d+)", body)
            if not m:
                continue
            c = next((x for x in reversed(path) if x.startswith("c_")), None)
            r = resolve(int(m.group(1)))
            if c and r and c not in out:
                out[c] = r
    for pid, c in comment_county.items():
        r = resolve(pid)
        if r and c not in out:
            out[c] = r
    return out, set(comment_county.values()), hist, comment_county


def main():
    lt = read(os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt"))
    prov_county, prov_king = {}, {}
    for path, key, body in walk(lt):
        if not key.startswith("b_"):
            continue
        m = re.search(r"\bprovince\s*=\s*(\d+)", body)
        if not m:
            continue
        pid = int(m.group(1))
        c = next((x for x in reversed(path) if x.startswith("c_")), None)
        k = next((x for x in reversed(path) if x.startswith("k_")), None)
        if c:
            prov_county[pid] = c
        if k:
            prov_king[pid] = k

    def region(pid):
        k = (prov_king.get(pid) or "")[2:]
        if k in AFRICA:
            return "africa"
        if k in SEA:
            return "sea"
        return None

    # 我们的现状
    raw = read(os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt"))
    cur = {}
    for m in re.finditer(r"(?m)^(\d+)\s*=\s*\{(.*?)^\}", raw, re.S):
        f = re.search(r"(?m)^\s*faith\s*=\s*(\S+)", m.group(2))
        cur[int(m.group(1))] = f.group(1) if f else None

    # EU5 pops
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

    # 男爵领名 = province 的 b_ 名；用 landed_titles 里的 key
    prov_loc = {}
    for path, key, body in walk(lt):
        if not key.startswith("b_"):
            continue
        m = re.search(r"\bprovince\s*=\s*(\d+)", body)
        if m:
            prov_loc[int(m.group(1))] = key[2:]

    faith_main = religion_tables()
    rite2faith = {v: k for k, v in faith_main.items()}
    cu_b, CU_COUNTIES, cu_hist, cu_cc = cu_county_rite()
    print("CU: 有 rite 的县 %d 个；CU 有块头的县 %d 个" % (len(cu_b), len(CU_COUNTIES)))

    # 聚合： (region, eu5_religion) -> 统计
    stat = defaultdict(lambda: {"n": 0, "cov": 0, "rites": Counter(), "faiths": Counter()})
    detail = []
    for pid, loc in prov_loc.items():
        rg = region(pid)
        if not rg:
            continue
        if loc not in pop_rel or not pop_rel[loc]:
            eu5 = "(no pops)"
        else:
            eu5 = min(pop_rel[loc].items(), key=lambda kv: (-kv[1], kv[0]))[0]
        county = prov_county.get(pid, "")
        cr = cu_b.get(county)
        s = stat[(rg, eu5)]
        s["n"] += 1
        s["faiths"][cur.get(pid) or "(none)"] += 1
        if cr:
            s["cov"] += 1
            s["rites"][cr] += 1
        detail.append((rg, eu5, pid, loc, county, cur.get(pid), cr or "", prov_king.get(pid, "")))

    rows = []
    for (rg, eu5), s in stat.items():
        n, cov = s["n"], s["cov"]
        if s["rites"]:
            rite, hit = s["rites"].most_common(1)[0]
            faith = rite2faith.get(rite, "?")
        else:
            rite, hit, faith = "", 0, ""
        rows.append({
            "region": rg, "eu5_religion": eu5, "our_baronies": n,
            "cu_covered": cov, "overlap_pct": round(100.0 * cov / n, 1) if n else 0,
            "cu_rite": rite, "cu_faith": faith, "hit": hit,
            "share_in_covered_pct": round(100.0 * hit / cov, 1) if cov else 0,
            "our_current_faiths": ";".join("%s:%d" % kv for kv in s["faiths"].most_common(3)),
        })
    rows.sort(key=lambda r: (r["region"], -r["our_baronies"]))

    with io.open(os.path.join(OUTDIR, "_cu_barony_overlap.csv"), "w",
                 encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["region", "eu5_religion", "our_baronies", "cu_covered",
                                          "overlap_pct", "cu_rite", "cu_faith", "hit",
                                          "share_in_covered_pct", "our_current_faiths"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    with io.open(os.path.join(OUTDIR, "_cu_barony_detail.csv"), "w",
                 encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["region", "eu5_religion", "province", "barony", "county",
                    "our_faith", "cu_rite", "kingdom"])
        for d in sorted(detail):
            w.writerow(d)

    for rg in ("africa", "sea"):
        print()
        print("== %s ==" % rg)
        print("%-30s %7s %7s %7s  %-26s %6s  %s" %
              ("eu5_religion", "男爵领", "有CU", "重合%", "CU多数rite", "占比%", "我们现状"))
        for r in rows:
            if r["region"] != rg or r["our_baronies"] < 3:
                continue
            print("%-30s %7d %7d %7.1f  %-26s %6.1f  %s" %
                  (r["eu5_religion"], r["our_baronies"], r["cu_covered"], r["overlap_pct"],
                   r["cu_rite"] or "-", r["share_in_covered_pct"], r["our_current_faiths"]))
    print()
    print("csv:", os.path.join(OUTDIR, "_cu_barony_overlap.csv"))


if __name__ == "__main__":
    main()
