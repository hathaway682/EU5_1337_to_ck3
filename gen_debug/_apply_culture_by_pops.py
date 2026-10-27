# -*- coding: utf-8 -*-
"""按 EU5 pops 人口多数，重算 mod 每个 province（男爵领）的文化/宗教，写回 province 历史。

映射链：CK3 barony 名 b_XXX  ==  EU5 location 名 XXX
  （已核实：b_yola -> yola -> culture=adamawa_culture / religion=adamawa_religion，与 province 文件一致）
  - culture : pops 的 culture 键 = province 文件 culture 键（同名，直接用）
  - religion: pops 的 religion 键(EU5) -> eu5_ck3_faith_map.csv -> CK3 faith

口径（默认 --per-province）：
  每个 province 用它自己那个 EU5 location 的 pops，按 size 累加，取最大的 culture / religion。
  这就是 CK3 原生粒度（history/provinces 一条 = 一个男爵领），县内混合是正常的。

  --county 才改成县级聚合（把一个 county 下所有 location 的 pops 合并后取多数，整县同值）。
  --apply  才写文件（先备份）；默认 dry-run。
"""
import io, os, re, csv, sys, shutil, time
from collections import defaultdict, Counter

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
GEN = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"
SRC = os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt")
FAITHMAP = os.path.join(GEN, "eu5_ck3_faith_map.csv")
OUTDIR = os.path.join(MOD, "gen_debug")
DRY = "--apply" not in sys.argv
BY_COUNTY = "--county" in sys.argv

# --fallback <file>: 无 pops 的 province 用该文件里已有的值兜底（默认用 location 标注版 = git HEAD）
FALLBACK = None
if "--fallback" in sys.argv:
    FALLBACK = sys.argv[sys.argv.index("--fallback") + 1]

BLOCK = re.compile(r"([A-Za-z0-9_]+)\s*=\s*\{")


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


def walk_blocks(text, path=()):
    i, n = 0, len(text)
    while i < n:
        m = BLOCK.search(text, i)
        if not m:
            return
        j, depth = m.end(), 1
        while j < n and depth:
            c = text[j]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            j += 1
        body = text[m.end():j - 1]
        yield path, m.group(1), body
        yield from walk_blocks(body, path + (m.group(1),))
        i = j


def majority(counter):
    return min(counter.items(), key=lambda kv: (-kv[1], kv[0]))[0]


def main():
    # 1) barony -> county, location
    lt = read(os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt"))
    prov_county, prov_loc = {}, {}
    for path, key, body in walk_blocks(lt):
        if not key.startswith("b_"):
            continue
        m = re.search(r"\bprovince\s*=\s*(\d+)", body)
        if not m:
            continue
        pid = int(m.group(1))
        county = next((p for p in reversed(path) if p.startswith("c_")), None)
        if county:
            prov_county[pid] = county
            prov_loc[pid] = key[2:]
    print("provinces mapped: %d counties: %d" % (len(prov_county), len(set(prov_county.values()))))

    # 2) pops: location -> culture sizes / religion sizes
    pop_cult, pop_rel = defaultdict(Counter), defaultdict(Counter)
    pt = read(os.path.join(EU5, "main_menu", "setup", "start", "06_pops.txt"))
    for m in re.finditer(r"(?ms)^[ \t]*([a-z0-9_']+)[ \t]*=[ \t]*\{\n(.*?)^[ \t]*\}", pt):
        loc = m.group(1)
        for pm in re.finditer(r"define_pop\s*=\s*\{([^}]*)\}", m.group(2)):
            pb = pm.group(1)
            sz = re.search(r"\bsize\s*=\s*([0-9.]+)", pb)
            cu = re.search(r"\bculture\s*=\s*([a-z0-9_]+)", pb)
            rl = re.search(r"\breligion\s*=\s*([a-z0-9_]+)", pb)
            if not sz:
                continue
            v = float(sz.group(1))
            if cu:
                pop_cult[loc][cu.group(1)] += v
            if rl:
                pop_rel[loc][rl.group(1)] += v
    print("locations with pops:", len(pop_cult))

    # 3) faith map
    fmap = {}
    with io.open(FAITHMAP, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            fmap[row["eu5_religion"]] = row["ck3_faith"] or "pagan"

    # 4) current province file
    raw = read(SRC)
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
        f = re.search(r"(?m)^\s*faith\s*=\s*(\S+)", body)
        cur[pid] = (c.group(1) if c else None, f.group(1) if f else None)

    # 5) build plan
    plan = {}          # pid -> (culture, faith, eu5_rel, pop_total, n_candidates)
    no_pops = []
    if BY_COUNTY:
        county_provs = defaultdict(list)
        for pid, c in prov_county.items():
            county_provs[c].append(pid)
        county_plan = {}
        for county, pids in county_provs.items():
            cs, rs = Counter(), Counter()
            for pid in pids:
                loc = prov_loc.get(pid)
                if loc:
                    for k, v in pop_cult.get(loc, {}).items():
                        cs[k] += v
                    for k, v in pop_rel.get(loc, {}).items():
                        rs[k] += v
            if not cs:
                continue
            county_plan[county] = (majority(cs), fmap.get(majority(rs), "pagan"),
                                   majority(rs), sum(cs.values()), len(cs))
        for pid in prov_county:
            county = prov_county[pid]
            if county in county_plan:
                plan[pid] = county_plan[county]
            else:
                no_pops.append(pid)
    else:
        for pid, loc in prov_loc.items():
            cs = pop_cult.get(loc)
            if not cs:
                no_pops.append(pid)
                continue
            rs = pop_rel.get(loc) or Counter()
            plan[pid] = (majority(cs), fmap.get(majority(rs), "pagan"),
                         majority(rs) if rs else "", sum(cs.values()), len(cs))

    # 5b) 无 pops 的 province 兜底：用 --fallback 文件里已有的值（默认 location 标注版）
    fb_plan = {}
    if FALLBACK and os.path.exists(FALLBACK):
        fbt = read(FALLBACK)
        fb = {}
        for m in re.finditer(r"(?m)^(\d+)\s*=\s*\{", fbt):
            pid = int(m.group(1))
            body = fbt[m.end() - 1:]
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
            f = re.search(r"(?m)^\s*faith\s*=\s*(\S+)", body)
            if c and f:
                fb[pid] = (c.group(1), f.group(1))
        n_same = 0
        for pid in no_pops:
            if pid in fb:
                fb_plan[pid] = fb[pid]
                if fb[pid] == cur.get(pid):
                    n_same += 1
        no_pops = [p for p in no_pops if p not in fb_plan]
        print("fallback (%s): %d provinces, %d 与现值相同, %d 会被改回标注值"
              % (os.path.basename(FALLBACK), len(fb_plan), n_same, len(fb_plan) - n_same))

    # 6) compare
    chg_c = chg_f = both = 0
    samples = []
    unk_rel = Counter()
    for pid, (mc, mf, mr, tot, ncand) in plan.items():
        cc, cf = cur.get(pid, (None, None))
        dc = cc != mc
        df = cf != mf
        chg_c += dc
        chg_f += df
        both += (dc and df)
        if mr and mr not in fmap:
            unk_rel[mr] += 1
        if (dc or df) and len(samples) < 25:
            samples.append((pid, cc, cf, mc, mf, mr, round(tot, 1), ncand))

    mode = "county" if BY_COUNTY else "per-province"
    print()
    print("== result (%s) ==" % mode)
    print("provinces with pop data: %d / %d | no pop data: %d"
          % (len(plan), len(prov_county), len(no_pops)))
    print("culture changed: %d | faith changed: %d | both changed: %d" % (chg_c, chg_f, both))
    if unk_rel:
        print("religions not in faith map (-> pagan):", dict(unk_rel.most_common(10)))
    print()
    print("samples (province: cur_cult/cur_faith -> new_cult/new_faith  [eu5_rel, pop, #cand]):")
    for pid, cc, cf, mc, mf, mr, tot, ncand in samples:
        print("  %-7d %-22s/%-20s -> %-22s/%-20s [%s, %s, %d]"
              % (pid, cc, cf, mc, mf, mr, tot, ncand))

    # 7) report
    rep = os.path.join(OUTDIR, "_culture_by_pops_report.txt")
    io.open(rep, "w", encoding="utf-8", newline="\n").write(
        "mode=%s provinces=%d plan=%d no_pops=%d\nchg_culture=%d chg_faith=%d both=%d\n"
        % (mode, len(prov_county), len(plan), len(no_pops), chg_c, chg_f, both))
    csvp = os.path.join(OUTDIR, "_culture_by_pops_diff.csv")
    with io.open(csvp, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["province", "county", "cur_culture", "new_culture",
                    "cur_faith", "new_faith", "eu5_religion", "pop_total", "n_candidates"])
        for pid in sorted(plan):
            mc, mf, mr, tot, ncand = plan[pid]
            cc, cf = cur.get(pid, (None, None))
            if cc != mc or cf != mf:
                w.writerow([pid, prov_county.get(pid, ""), cc, mc, cf, mf, mr,
                            round(tot, 1), ncand])
        for pid in sorted(fb_plan):
            mc, mf = fb_plan[pid]
            cc, cf = cur.get(pid, (None, None))
            if cc != mc or cf != mf:
                w.writerow([pid, prov_county.get(pid, ""), cc, mc, cf, mf,
                            "(fallback:location-label)", 0, 0])
    print()
    print("report:", rep)
    print("diff csv:", csvp)

    if DRY:
        print("\n[dry-run] 未写文件。加 --apply 才写。")
        if no_pops:
            print("no-pop provinces: %d (保持原值)" % len(no_pops))
        return

    # 8) apply
    ts = time.strftime("%Y%m%d_%H%M%S")
    out = []
    cur_pid = None
    changed_lines = 0
    for line in raw.split("\n"):
        m = re.match(r"^(\d+) = \{$", line)
        if m:
            cur_pid = int(m.group(1))
            out.append(line)
            continue
        if line.strip() == "}":
            out.append(line)
            continue
        if cur_pid is not None and (cur_pid in plan or cur_pid in fb_plan):
            if cur_pid in plan:
                mc, mf = plan[cur_pid][0], plan[cur_pid][1]
            else:
                mc, mf = fb_plan[cur_pid]
            mc2 = re.match(r"^(\s*)culture\s*=\s*(\S+)", line)
            mf2 = re.match(r"^(\s*)faith\s*=\s*(\S+)", line)
            if mc2:
                out.append("%sculture = %s" % (mc2.group(1), mc))
                if mc2.group(2) != mc:
                    changed_lines += 1
                continue
            if mf2:
                out.append("%sfaith = %s" % (mf2.group(1), mf))
                if mf2.group(2) != mf:
                    changed_lines += 1
                continue
        out.append(line)
    new = "\n".join(out)
    if new != raw:
        shutil.copy2(SRC, SRC + ".bak_popsmajority_" + ts)
        io.open(SRC, "w", encoding="utf-8-sig", newline="\n").write(new)
        print("\nAPPLIED (%s). changed_lines=%d" % (mode, changed_lines))
        print("backup:", SRC + ".bak_popsmajority_" + ts)
        print("braces:", new.count("{"), new.count("}"))
    else:
        print("\nno change")


if __name__ == "__main__":
    main()
