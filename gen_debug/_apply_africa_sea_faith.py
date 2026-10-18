# -*- coding: utf-8 -*-
"""用 CrusaderUniversalis 的 county 级 rite，给本 mod 的非洲 + 东南亚省份写 faith / rite。

依据：
  - CU 的 rite 求值到 1178.1.1（CK3 原版数据上限；>1178 的块是 CU 作者自造，不用）
  - 只对 非洲 / 东南亚 两个区域生效，不动全球其他地区
  - 映射按区域分别统计：eu5_religion -> CU 多数 rite（要求 n>=2 且 share>=0.5）
  - faith 由 rite 反查：优先 faith.main_rite == rite，其次 rite 块里声明的 faith
默认 dry-run；--apply 才写（先备份）。
"""
import io, os, re, csv, glob, sys, shutil, time
from collections import Counter, defaultdict

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
CU = r"E:\SteamLibrary\steamapps\workshop\content\1158310\3811443965"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"
SRC = os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt")
if "--src" in sys.argv:
    SRC = sys.argv[sys.argv.index("--src") + 1]
OUTDIR = os.path.join(MOD, "gen_debug")
START = (1178, 1, 1)
DRY = "--apply" not in sys.argv

AFRICA = {"maghreb", "egypt", "nubia", "somalia", "ethiopia", "sahel", "guinea",
          "central_africa", "kongo", "southern_africa", "zimbabwe", "swahili_coast",
          "madagascar", "macaronesia"}
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
    faith_main = {}
    for fn in os.listdir(os.path.join(MOD, "common", "religion", "faith_types")):
        if not fn.endswith(".txt"):
            continue
        for path, key, body in walk(read(os.path.join(MOD, "common", "religion", "faith_types", fn))):
            if path:
                continue
            m = re.search(r"(?m)^\s*main_rite\s*=\s*(\S+)", body)
            if m:
                faith_main[key] = m.group(1)
    rite2faith = {v: k for k, v in faith_main.items()}
    rite_decl = {}
    for fn in os.listdir(os.path.join(MOD, "common", "religion", "rite_types")):
        if not fn.endswith(".txt"):
            continue
        for path, key, body in walk(read(os.path.join(MOD, "common", "religion", "rite_types", fn))):
            if path:
                continue
            m = re.search(r"(?m)^\s*faith\s*=\s*(\S+)", body)
            if m:
                rite_decl[key] = m.group(1)
    return rite2faith, rite_decl


def cu_county_rite():
    hist = {}
    comment_county = {}     # pid -> county（CU 块头注释 # b_xxx, c_yyy 里写的县名）
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
    # 再用 CU 块头注释里的县名补一遍（landed_titles 归类与注释不一致时兜住）
    for pid, c in comment_county.items():
        r = resolve(pid)
        if r and c not in out:
            out[c] = r
    return out, set(comment_county.values())


def main():
    lt = read(os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt"))
    prov_county, county_kingdom, prov_loc = {}, {}, {}
    for path, key, body in walk(lt):
        if not key.startswith("b_"):
            continue
        m = re.search(r"\bprovince\s*=\s*(\d+)", body)
        if not m:
            continue
        pid = int(m.group(1))
        prov_loc[pid] = key[2:]
        c = next((x for x in reversed(path) if x.startswith("c_")), None)
        k = next((x for x in reversed(path) if x.startswith("k_")), None)
        if c:
            prov_county[pid] = c
            if k:
                county_kingdom[c] = k

    def region(county):
        k = county_kingdom.get(county, "")[2:]
        if k in AFRICA:
            return "africa"
        if k in SEA:
            return "sea"
        return None

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

    rite2faith, rite_decl = religion_tables()
    cu_b, CU_COUNTIES = cu_county_rite()
    faith_main_rev = dict(rite2faith)     # faith -> main_rite（rite2faith 是 rite->faith，反向重建）
    faith_main_rev = {f: r for r, f in rite2faith.items()}

    # 区域映射表：region -> eu5_religion -> (rite, faith, n, share)
    agg = defaultdict(lambda: defaultdict(Counter))
    for pid, county in prov_county.items():
        rg = region(county)
        if not rg:
            continue
        loc = prov_loc.get(pid)
        r = cu_b.get(county)
        if not loc or not r or loc not in pop_rel or not pop_rel[loc]:
            continue
        e = min(pop_rel[loc].items(), key=lambda kv: (-kv[1], kv[0]))[0]
        agg[rg][e][r] += 1

    region_map, skipped = {}, []
    for rg, rels in agg.items():
        region_map[rg] = {}
        for e, cc in rels.items():
            tot = sum(cc.values())
            rite, n = cc.most_common(1)[0]
            share = n / tot
            faith = rite2faith.get(rite) or rite_decl.get(rite)
            if n >= 2 and share >= 0.5 and faith:
                region_map[rg][e] = (rite, faith, n, share)
            else:
                skipped.append((rg, e, rite, n, tot, share))

    print("== 区域映射表 ==")
    for rg in sorted(region_map):
        print("  [%s] %d 条" % (rg, len(region_map[rg])))
        for e, (ri, fa, n, sh) in sorted(region_map[rg].items()):
            print("      %-28s -> %-26s (%-22s) %d  %.0f%%" % (e, fa, ri, n, sh * 100))
    print("  跳过（样本不足/不明确/无法定 faith）：", len(skipped))
    for s in skipped:
        print("    %-8s %-24s best=%-24s %d/%d %.0f%%" % (s[0], s[1], s[2], s[3], s[4], s[5] * 100))

    # 现有值
    raw = read(SRC)
    cur = {}
    for m in re.finditer(r"(?m)^(\d+)\s*=\s*\{", raw):
        pid = int(m.group(1))
        b = raw[m.end() - 1:]
        d = 0
        for j, ch in enumerate(b):
            if ch == "{":
                d += 1
            elif ch == "}":
                d -= 1
                if d == 0:
                    b = b[:j + 1]
                    break
        f = re.search(r"(?m)^\s*faith\s*=\s*(\S+)", b)
        r = re.search(r"(?m)^\s*rite\s*=\s*(\S+)", b)
        cur[pid] = (f.group(1) if f else None, r.group(1) if r else None)

    # 同王国多数信仰（排除 pagan），给「CU 只标了 wilderness」的省兜底
    kmod = defaultdict(Counter)
    for pid, v in cur.items():
        if v[0] and v[0] != "pagan":
            kmod[county_kingdom.get(prov_county.get(pid, ""), "")][v[0]] += 1
    king_modal = {k: c.most_common(1)[0][0] for k, c in kmod.items() if c}

    plan, noeu5, unmapped = {}, Counter(), Counter()
    residual = defaultdict(list)
    for pid, county in prov_county.items():
        rg = region(county)
        cf, cr = cur.get(pid, (None, None))
        # 目标：只消灭通用 pagan，其他信仰不动
        if cf != "pagan":
            continue
        loc = prov_loc.get(pid)
        eu5 = None
        if loc and loc in pop_rel and pop_rel[loc]:
            eu5 = min(pop_rel[loc].items(), key=lambda kv: (-kv[1], kv[0]))[0]
        # 1) 非洲 / 东南亚：用区域映射（EU5 宗教 -> CU 多数 rite）
        if rg and eu5:
            t = region_map.get(rg, {}).get(eu5)
            if t:
                plan[pid] = (t[1], t[0], "regionmap")
                continue
        # 2) 原版地图范围内（CU 有该县）：用 CU 的 county rite
        r = cu_b.get(county)
        if r:
            f = rite2faith.get(r) or rite_decl.get(r)
            if f:
                plan[pid] = (f, r, "cu")
                continue
        # 3) 非洲兜底：原版地图不含撒哈拉以南，没有证据可用，统一给非洲通用异教
        #    （尼罗河努比亚单列 kushitism_pagan，那是该地的本土异教）
        if rg == "africa":
            fb = "kushitism_pagan" if county_kingdom.get(county, "")[2:] == "nubia" else "west_african_pagan"
            plan[pid] = (fb, fb, "africa_fallback")
            continue
        # 4) 原版地图范围（CU 有该县）内、CU 只给了 wilderness 没给信仰的：用同王国多数信仰补
        if county in CU_COUNTIES:
            k = county_kingdom.get(county, "")
            fb = king_modal.get(k)
            if fb:
                plan[pid] = (fb, faith_main_rev.get(fb, fb), "kingdom_modal")
                continue
        # 5) 兜底失败
        residual[rg or "other"].append((pid, county, eu5, cf))
        if rg:
            if eu5:
                unmapped[rg] += 1
            else:
                noeu5[rg] += 1

    print()
    print("== 目标：消灭 faith = pagan ==")
    tot_pagan = sum(1 for v in cur.values() if v[0] == "pagan")
    done = Counter(region(prov_county.get(p, "")) or "other" for p in plan)
    print("  当前 pagan 省:", tot_pagan, " 计划处理:", len(plan), " 残留:", tot_pagan - len(plan))
    print()
    print("  %-12s %-10s %-10s" % ("region", "pagan", "处理", ))
    for k in ("africa", "sea", "other"):
        tot = sum(1 for p, v in cur.items() if v[0] == "pagan"
                  and (region(prov_county.get(p, "")) or "other") == k)
        print("    %-12s %-10d %-10d 残留 %d" % (k, tot, done[k], tot - done[k]))
    print()
    print("  残留按 EU5 宗教：")
    rc = Counter()
    for k, lst in residual.items():
        for pid, county, eu5, cf in lst:
            rc[(k, eu5 or "(no pops)")] += 1
    for (k, e), v in rc.most_common(30):
        print("    %-10s %-28s %d" % (k, e, v))

    chg_f = chg_r = both = 0
    tr = Counter()
    by_branch = Counter()
    for pid, (f, r, br) in plan.items():
        cf, cr = cur.get(pid, (None, None))
        df = cf != f
        dr = cr != r
        chg_f += df
        chg_r += dr
        both += df and dr
        by_branch[br] += 1
        if df:
            tr[(cf, f)] += 1
    print()
    print("faith 变 %d | rite 变 %d | 两者都变 %d" % (chg_f, chg_r, both))
    print("按来源分支：", dict(by_branch))
    print()
    print("top faith transitions:")
    for k, v in tr.most_common(25):
        print("  %-26s -> %-26s %d" % (k[0], k[1], v))

    with io.open(os.path.join(OUTDIR, "_africa_sea_faith_plan.csv"), "w",
                 encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["province", "county", "region", "eu5_religion", "cur_faith", "cur_rite",
                    "new_faith", "new_rite", "branch"])
        for pid in sorted(plan):
            cf, cr = cur.get(pid, (None, None))
            f, r, br = plan[pid]
            loc = prov_loc.get(pid)
            e = ""
            if loc and loc in pop_rel and pop_rel[loc]:
                e = min(pop_rel[loc].items(), key=lambda kv: (-kv[1], kv[0]))[0]
            w.writerow([pid, prov_county[pid], region(prov_county[pid]), e, cf, cr, f, r, br])
    print()
    print("plan csv:", os.path.join(OUTDIR, "_africa_sea_faith_plan.csv"))

    if DRY:
        print("\n[dry-run] 未写文件。加 --apply 才写。")
        return

    ts = time.strftime("%Y%m%d_%H%M%S")
    out, cur_pid, lines = [], None, 0
    for line in raw.split("\n"):
        m = re.match(r"^(\d+) = \{$", line)
        if m:
            cur_pid = int(m.group(1))
            out.append(line)
            continue
        if line.strip() == "}":
            out.append(line)
            continue
        if cur_pid is not None and cur_pid in plan:
            f, r = plan[cur_pid][0], plan[cur_pid][1]
            mf = re.match(r"^(\s*)faith\s*=\s*(\S+)", line)
            mr = re.match(r"^(\s*)rite\s*=\s*(\S+)", line)
            if mf:
                out.append("%sfaith = %s" % (mf.group(1), f))
                if mf.group(2) != f:
                    lines += 1
                continue
            if mr:
                out.append("%srite = %s" % (mr.group(1), r))
                if mr.group(2) != r:
                    lines += 1
                continue
        out.append(line)
    new = "\n".join(out)
    if new != raw:
        shutil.copy2(SRC, SRC + ".bak_afrsea_faith_" + ts)
        io.open(SRC, "w", encoding="utf-8-sig", newline="\n").write(new)
        print("\nAPPLIED. changed_lines=%d" % lines)
        print("backup:", SRC + ".bak_afrsea_faith_" + ts)
        print("braces:", new.count("{"), new.count("}"))
    else:
        print("\nno change")


if __name__ == "__main__":
    main()
