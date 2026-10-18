# -*- coding: utf-8 -*-
"""按 EU5 pops 人口多数，重算 mod 每个 county 的文化/宗教，写回 province 历史。

映射链：CK3 barony 名 b_XXX  ==  EU5 location 名 XXX（已核实：b_yola->yola->adamawa_culture）
  - culture: pops 的 culture 键 = province 文件 culture 键（同名，直接用）
  - religion: pops 的 religion 键(EU5) -> eu5_ck3_faith_map.csv -> CK3 faith
口径：每个 county 内，把它的所有 location 的 pops 按 size 累加，取 size 最大的 culture / religion。
      文化/宗教本就是 county 统一（3819 县 0 个内部有差异），所以整县写成同一个值。
默认 dry-run；--apply 才写（先备份）。
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


def main():
    # 1) barony -> county, province, location
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
    print("provinces mapped:", len(prov_county), "counties:", len(set(prov_county.values())))

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

    # 3) faith map: eu5 religion -> ck3 faith
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
        # take up to matching brace
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

    # 5) per county: aggregate pops
    county_provs = defaultdict(list)
    for pid, c in prov_county.items():
        county_provs[c].append(pid)

    plan = {}
    no_data = []
    no_pops_loc = 0
    for county, pids in county_provs.items():
        csize, rsize = Counter(), Counter()
        locs = 0
        for pid in pids:
            loc = prov_loc.get(pid)
            if not loc:
                continue
            if loc in pop_cult:
                locs += 1
            for k, v in pop_cult.get(loc, {}).items():
                csize[k] += v
            for k, v in pop_rel.get(loc, {}).items():
                rsize[k] += v
        if not csize:
            no_data.append(county)
            continue
        maj_cult = min(csize.items(), key=lambda kv: (-kv[1], kv[0]))[0]
        maj_rel = min(rsize.items(), key=lambda kv: (-kv[1], kv[0]))[0]
        maj_faith = fmap.get(maj_rel, "pagan")
        plan[county] = (maj_cult, maj_faith, maj_rel, sum(csize.values()), locs, len(pids))

    # 6) compare
    chg_c = chg_f = both = 0
    samples = []
    unk_rel = Counter()
    for county, (mc, mf, mr, tot, locs, nb) in plan.items():
        pids = county_provs[county]
        cc, cf = cur.get(pids[0], (None, None))
        dc = cc != mc
        df = cf != mf
        if dc:
            chg_c += 1
        if df:
            chg_f += 1
        if dc and df:
            both += 1
        if mr not in fmap:
            unk_rel[mr] += 1
        if (dc or df) and len(samples) < 30:
            samples.append((county, cc, cf, mc, mf, mr, round(tot, 1), locs, nb))

    print()
    print("== result ==")
    print("counties with pop data: %d / %d | no pop data: %d" % (len(plan), len(county_provs), len(no_data)))
    print("culture changed: %d | faith changed: %d | both changed: %d" % (chg_c, chg_f, both))
    if unk_rel:
        print("religions not in faith map (-> pagan):", dict(unk_rel.most_common(10)))
    print()
    print("samples (county: cur_cult/cur_faith -> new_cult/new_faith  [eu5_rel, pop, locs, baronies]):")
    for s in samples:
        county, cc, cf, mc, mf, mr, tot, locs, nb = s
        print("  %-26s %s/%s -> %s/%s  [%s, %s, %d, %d]" %
              (county, cc, cf, mc, mf, mr, tot, locs, nb))

    if DRY:
        print("\n[dry-run] 未写文件。加 --apply 才写。")
        # write report
        rep = os.path.join(OUTDIR, "_culture_by_pops_report.txt")
        io.open(rep, "w", encoding="utf-8", newline="\n").write(
            "counties=%d plan=%d no_data=%d\nchg_culture=%d chg_faith=%d both=%d\n" %
            (len(county_provs), len(plan), len(no_data), chg_c, chg_f, both))
        # full diff csv
        csvp = os.path.join(OUTDIR, "_culture_by_pops_diff.csv")
        with io.open(csvp, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["county", "baronies", "cur_culture", "new_culture",
                        "cur_faith", "new_faith", "eu5_religion", "pop_total", "locs_with_pops"])
            for county in sorted(plan):
                mc, mf, mr, tot, locs, nb = plan[county]
                pids = county_provs[county]
                cc, cf = cur.get(pids[0], (None, None))
                if cc != mc or cf != mf:
                    w.writerow([county, nb, cc, mc, cf, mf, mr, round(tot, 1), locs])
        print("report:", rep)
        print("diff csv:", csvp)
        if no_data:
            print("no-pop-data counties (%d): %s" % (len(no_data), ", ".join(sorted(no_data)[:40])))
        return

    # 7) apply
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
        pid = cur_pid
        if pid is not None and pid in prov_county:
            county = prov_county[pid]
            if county in plan:
                mc, mf, mr, tot, locs, nb = plan[county]
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
        print("\nAPPLIED. changed_lines=%d backup=%s" % (changed_lines, SRC + ".bak_popsmajority_" + ts))
        print("braces:", new.count("{"), new.count("}"))
    else:
        print("\nno change")


if __name__ == "__main__":
    main()
