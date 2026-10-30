"""Rebind a country's title: rewrite its binding in eu5_ck3_title_map.csv, re-hang the
reign history onto the new key, and keep _title_overrides.csv in step.

改绑 = three things that must move together:

  1. eu5_ck3_title_map.csv — the country row's `ck3_key` (the tag -> title binding the COA
     generator and other tools read). _export_title_map.py computes `ck3_key` from
     `{rank}_eu5_{tag}` and never consults the override table, so a binding that is not
     plain rank-derived (a country re-bound to the duchy its capital sits in) has to be
     written here by hand. Editing the CSV is the only way those tools see it.

  2. history/titles/*.txt — the old block's whole reign list is merged into the new key's
     block (chronologically, keeping the new block's opening entry), and the old block is
     deleted. Dropping the old block without merging would lose the lineage.

  3. _title_overrides.csv — `country,<tag>,title_key,<new>` so _patch_title_history.py's
     ckey() answers the new key; without it the next patch run mints the old shell again.

The old key is read from the CSV's current `ck3_key`, not from ckey(), so the operation is
idempotent: run it twice and the second run finds the CSV already points at the new key.

Usage:
  python rebind.py --mod "<mod>" --export "<export>" --tag MLO [--to d_lombardy] [--dry-run]
  python rebind.py --mod "<mod>" --export "<export>" --all-capital-duchy [--dry-run]
"""
import argparse, csv, io, os, re, shutil, sys, datetime, importlib.util

BLOCK = re.compile(r"(?ms)^([A-Za-z0-9_]+) = \{\n(.*?)^\}\n")
ENTRY = re.compile(r"(?ms)^(\t\d+\.\d+\.\d+) = \{\n(.*?)^\t\}\n")
START = "1337.4.1"


def dkey(s):
    try:
        return tuple(int(x) for x in s.split("."))
    except Exception:
        return (0, 0, 0)


def insert_reigns(body, to_add):
    entries = [(e.start(), e.group(1).strip()) for e in ENTRY.finditer(body)]
    inserts = []
    for date, char in to_add:
        seg = f"\t{date} = {{\n\t\tholder = {char}\n\t}}\n"
        pos = None
        for est, edate in entries:
            if dkey(edate) >= dkey(date):
                pos = est
                break
        inserts.append((pos, date, seg))
    inserts.sort(key=lambda x: (x[0] if x[0] is not None else 10 ** 9, dkey(x[1])))
    out, cursor = [], 0
    for pos, _date, seg in inserts:
        if pos is None:
            out.append(body[cursor:])
            cursor = len(body)
            if out and not out[-1].endswith("\n"):
                out[-1] += "\n"
            out.append(seg)
        else:
            out.append(body[cursor:pos])
            out.append(seg)
            cursor = pos
    out.append(body[cursor:])
    return "".join(out)


def load_grant(export_dir=None):
    here = os.path.dirname(os.path.abspath(__file__))
    cands = [export_dir, os.environ.get("EU5_EXPORT_DIR"),
             os.path.join(here, "..", "..", "..", "..", "Global_modern_map", "eu5_export")]
    for cand in cands:
        if not cand:
            continue
        p = os.path.join(cand, "_grant_landed_duchies.py")
        if os.path.exists(p):
            if cand not in sys.path:
                sys.path.insert(0, cand)
            spec = importlib.util.spec_from_file_location("_grant_landed_duchies", p)
            g = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(g)
            return g
    raise SystemExit("cannot locate _grant_landed_duchies.py (set EU5_EXPORT_DIR)")


def read_norm(path):
    return io.open(path, encoding="utf-8-sig", errors="ignore").read() \
             .replace("\r\n", "\n").replace("\r", "\n")


def do_sync(mod, export, rows, fields, by_tag, dry_run, vassals_of=()):
    """Recompute every country's true binding and fix the title-map rows (history untouched).

    true binding, in order:
      1. the override table (`_title_overrides.csv`) — a kingdom/empire/duchy decision that
         outranks anything derived from rank;
      2. rank-d countries only: the same-name duchy, else the duchy its capital sits in;
      3. a rank-d country listed under `--vassals-of`: the duchy of its own rank, i.e. the
         one a vassal that was demoted to a county takes back;
      4. rank-k / rank-e: `{rank}_eu5_{tag}` (the Papal States keep k_papal_state).

    A landless d/k/e country (0 counties) keeps whatever seat/barony the map gives it — its
    rank title was dropped, and forcing the duchy back would invent a shell. A target key
    that is not declared in common/landed_titles is never written either: binding a row to
    a dropped title makes the map point at nothing.
    """
    import json
    from collections import defaultdict
    g = load_grant(export)
    grants, why, _b, _u, countries, _p = g.compute(mod, export)
    cd = g.capital_duchy(mod, export)
    pol = json.load(io.open(os.path.join(export, "eu5_politics.json"), encoding="utf-8"))
    vassals = set()
    for dep in pol.get("dependencies") or []:
        if dep.get("type") == "vassal" and dep.get("first") in vassals_of:
            vassals.add(dep.get("second"))
    import _herders
    pol, _h, _bk = _herders.apply(pol, export)
    held = defaultdict(int)
    for v in pol["counties"].values():
        o = (v or {}).get("owner")
        if o:
            held[o] += 1
    ov = {}
    for row in csv.reader(io.open(os.path.join(mod, "gen_debug", "_title_overrides.csv"),
                                  encoding="utf-8-sig")):
        if len(row) >= 4 and row[0] == "country" and row[2] == "title_key":
            ov[row[1]] = row[3]
    declared = set()
    ltd = os.path.join(mod, "common", "landed_titles")
    for fn in os.listdir(ltd):
        if fn.endswith(".txt"):
            declared |= set(re.findall(
                r"(?m)^\s*([a-z]_[A-Za-z0-9_]+)\s*=\s*\{",
                io.open(os.path.join(ltd, fn), encoding="utf-8-sig", errors="ignore").read()))
    bodies = {m.group(1): m.group(2)
              for m in BLOCK.finditer(read_norm(os.path.join(mod, "history", "titles", "zz_eu5_titles.txt")))}

    def true_key(tag):
        rank = (countries.get(tag) or {}).get("rank")
        if tag in ov:
            return ov[tag]
        if rank not in ("d", "k", "e"):
            return None
        if held.get(tag, 0) == 0:
            return None
        if rank == "d":
            for d, t in grants.items():
                if t == tag and why.get(d) == "same name":
                    return d
            if cd.get(tag) and grants.get(cd[tag]) == tag:
                return cd[tag]
            if tag in vassals:
                return f"d_eu5_{tag.lower()}"
            return None
        if tag == "PAP":
            return "k_papal_state"
        return f"{rank}_eu5_{tag.lower()}"

    changes, undeclared = [], []
    for tag, r in by_tag.items():
        t = true_key(tag)
        cur = (r["ck3_key"] or "").strip()
        if not t or t == cur:
            continue
        if t not in declared:
            undeclared.append((tag, cur, t))
            continue
        changes.append((tag, cur, t))
        r["ck3_key"] = t
        r["ck3_tier"] = t.split("_")[0]
        b = bodies.get(t, "")
        op = re.search(r"(?ms)^\t" + re.escape(START) + r" = \{\n(.*?)^\t\}", b)
        got = {}
        if op:
            for line in op.group(1).splitlines():
                m = re.match(r"\s*(holder|liege|government)\s*=\s*([A-Za-z0-9_]+)", line)
                if m:
                    got[m.group(1)] = m.group(2)
        r["ck3_holder"] = got.get("holder", "")
        r["ck3_liege"] = got.get("liege", "")
        r["ck3_government"] = got.get("government", "")
        r["ck3_declared"] = "yes" if t in declared else "no"

    print(f"title map rows to change: {len(changes)}")
    for c in sorted(changes):
        print("   ", c)
    if undeclared:
        print(f"skipped, target key not declared: {len(undeclared)}")
        for c in sorted(undeclared):
            print("   ", c)
    if dry_run or not changes:
        return
    with io.open(os.path.join(mod, "gen_debug", "eu5_ck3_title_map.csv"),
                 "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("title map written")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mod", required=True)
    ap.add_argument("--export", required=True)
    ap.add_argument("--tag", action="append", default=[])
    ap.add_argument("--map", action="append", default=[], metavar="TAG=KEY",
                    help="per-country target, repeatable (TUN=k_africa TLE=k_tahert)")
    ap.add_argument("--all-capital-duchy", action="store_true")
    ap.add_argument("--to", help="explicit target key for every --tag given")
    ap.add_argument("--sync", action="store_true",
                    help="recompute every country's ck3_key from its true binding and fix "
                         "the title map rows only (history untouched)")
    ap.add_argument("--vassals-of", action="append", default=[], metavar="TAG",
                    help="with --sync: also give back the duchy of their own rank to this "
                         "tag's vassals that were demoted to a county")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    mod = args.mod

    map_path = os.path.join(mod, "gen_debug", "eu5_ck3_title_map.csv")
    rows = list(csv.DictReader(io.open(map_path, encoding="utf-8-sig", newline="")))
    fields = list(rows[0].keys())
    by_tag = {r["eu5_tag"]: r for r in rows if r["kind"] == "country"}

    if args.sync:
        do_sync(mod, args.export, rows, fields, by_tag, args.dry_run, args.vassals_of)
        return

    cd = {}
    explicit = {}
    if args.all_capital_duchy:
        g = load_grant(args.export)
        grants, why, _b, _u, countries, _p = g.compute(mod, args.export)
        cd = g.capital_duchy(mod, args.export)
        # a country already bound to a kingdom/empire by the override table (Majorca ->
        # k_mediterranean_sea, Eretna -> k_eretnid, the Ottomans -> k_ottoman) keeps its
        # kingdom: a stale d_eu5_* row in the title map does not make it a duchy.
        ov_key = {}
        for row in csv.reader(io.open(os.path.join(mod, "gen_debug", "_title_overrides.csv"),
                                      encoding="utf-8-sig")):
            if len(row) >= 4 and row[0] == "country" and row[2] == "title_key":
                ov_key[row[1]] = row[3]
        tags = []
        for d, tag in grants.items():
            if why.get(d) == "same name":
                continue
            if (countries.get(tag) or {}).get("rank") != "d":
                continue
            if cd.get(tag) != d:
                continue
            true_key = ov_key.get(tag) or f"d_eu5_{tag.lower()}"
            if not true_key.startswith("d_"):
                continue
            if not (by_tag.get(tag) or {}).get("ck3_key", "").startswith("d_eu5_"):
                continue
            tags.append(tag)
    else:
        for m in args.map:
            t, _, k = m.partition("=")
            if not t.strip() or not k.strip():
                raise SystemExit(f"--map wants TAG=KEY, got {m!r}")
            explicit[t.strip()] = k.strip()
        tags = sorted(set(args.tag) | set(explicit))
        if not tags:
            raise SystemExit("give --tag, --map or --all-capital-duchy")
        if not args.to and not explicit:
            g = load_grant(args.export)
            cd = g.capital_duchy(mod, args.export)

    def target_of(tag):
        if tag in explicit:
            return explicit[tag]
        return (args.to or cd.get(tag) or "").strip()

    # history + declarations
    hist = os.path.join(mod, "history", "titles", "zz_eu5_titles.txt")
    htext = read_norm(hist)
    bodies = {m.group(1): m.group(2) for m in BLOCK.finditer(htext)}
    tit_path = os.path.join(mod, "common", "landed_titles", "zz_eu5_titular.txt")
    ttext = read_norm(tit_path)
    declared = set(re.findall(r"(?m)^\s*([a-z]_[A-Za-z0-9_]+)\s*=\s*\{", ttext))
    for fn in os.listdir(os.path.join(mod, "common", "landed_titles")):
        if fn.endswith(".txt"):
            declared |= set(re.findall(
                r"(?m)^\s*([a-z]_[A-Za-z0-9_]+)\s*=\s*\{",
                io.open(os.path.join(mod, "common", "landed_titles", fn),
                        encoding="utf-8-sig", errors="ignore").read()))
    # the CU 1337 de jure tree: a key declared there is a real title of the world, not a shell
    # this mod minted. Its block and its declaration are never removed when a country walks
    # away from it — the title keeps existing for whoever else holds it.
    cu_tree = set(re.findall(
        r"(?m)^\s*([a-z]_[A-Za-z0-9_]+)\s*=\s*\{",
        read_norm(os.path.join(mod, "common", "landed_titles", "00_landed_titles.txt"))))

    replace, rename, delete, decl_del, plan = {}, {}, set(), [], []
    old_of = {}
    liege_map = {}
    for tag in sorted(tags):
        r = by_tag.get(tag)
        if not r:
            print(f"  !! {tag}: no country row in title map")
            continue
        old = (r["ck3_key"] or "").strip()
        old_of[tag] = old
        new = target_of(tag)
        if not new:
            print(f"  !! {tag}: no target key")
            continue
        if old == new:
            plan.append((tag, old, new, "already bound"))
            continue
        if new not in declared:
            plan.append((tag, old, new, "target key NOT declared - skipped"))
            continue
        merged = 0
        if old in cu_tree:
            plan.append((tag, old, new, "old key is a CU de jure title: binding only"))
            continue
        if old and old in bodies and new not in bodies:
            # the new key is a de jure title with no history yet (nobody has worn it): the old
            # block moves over whole, name and all, keeping its chronology and its 1337 entry.
            rename[old] = (new, bodies[old])
            delete.add(old)
            decl_del.append(old)
            liege_map[old] = new
            merged = len(ENTRY.findall(bodies[old]))
            plan.append((tag, old, new, f"carry the whole block over ({merged} reigns)"))
            continue
        if old and old in bodies and new in bodies:
            duchy_existing = set()
            for e in ENTRY.finditer(bodies[new]):
                dd = e.group(1).strip()
                for h in re.findall(r"(?m)^\t\tholder = ([A-Za-z0-9_]+)$", e.group(2)):
                    duchy_existing.add((dd, h))
            old_reigns = [(e.group(1).strip(), h) for e in ENTRY.finditer(bodies[old])
                          for h in re.findall(r"(?m)^\t\tholder = ([A-Za-z0-9_]+)$", e.group(2))]
            to_add = [(d, c) for (d, c) in old_reigns if (d, c) not in duchy_existing]
            replace[new] = insert_reigns(bodies[new], to_add)
            delete.add(old)
            decl_del.append(old)
            liege_map[old] = new
            merged = len(to_add)
        plan.append((tag, old, new, f"merge {merged} reigns"))

    print(f"rebind targets: {len(plan)}")
    for p in plan:
        print("   ", p)
    if args.dry_run:
        return

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. history: replace new bodies, drop old blocks
    if replace or delete or rename:
        # a vassal's county history says `liege = d_eu5_teu`. Once that shell is gone the line
        # points at nothing and the vassalage silently breaks (Samland under the Teutons was
        # the visible case), so every reference to a dropped key moves to the new one.
        for o, n in liege_map.items():
            htext = re.sub(r"(?m)^(\s*)liege = " + re.escape(o) + r"$",
                           lambda m, n=n: f"{m.group(1)}liege = {n}", htext)
        for k in list(rename):
            nk, body = rename[k]
            for o, n in liege_map.items():
                body = re.sub(r"(?m)^(\s*)liege = " + re.escape(o) + r"$",
                              lambda m, n=n: f"{m.group(1)}liege = {n}", body)
            rename[k] = (nk, body)
        out, last = [], 0
        for m in BLOCK.finditer(htext):
            key = m.group(1)
            out.append(htext[last:m.start()])
            if key in rename:
                nk, body = rename[key]
                out.append(f"{nk} = {{\n{body.rstrip(chr(10))}\n}}\n")
            elif key in delete:
                pass
            elif key in replace:
                out.append(f"{key} = {{\n{replace[key].rstrip(chr(10))}\n}}\n")
            else:
                out.append(m.group(0))
            last = m.end()
        out.append(htext[last:])
        shutil.copy2(hist, hist + f".bak_{stamp}")
        io.open(hist, "w", encoding="utf-8-sig", newline="").write(
            "".join(out).replace("\n", "\r\n"))
        print(f"history rewritten: {os.path.relpath(hist, mod)}")

    # 2. declarations of the old keys
    if decl_del:
        tt = ttext
        removed = 0
        for old in decl_del:
            tt, n = re.subn(r"(?ms)^" + re.escape(old) + r" = \{\n(?:\t[^\n]*\n)*\}\n", "", tt)
            removed += n
        if removed:
            shutil.copy2(tit_path, tit_path + f".bak_{stamp}")
            io.open(tit_path, "w", encoding="utf-8-sig", newline="").write(
                tt.replace("\n", "\r\n"))
        print(f"declarations removed: {removed}")

    # 3. title map rows
    for k, v in replace.items():
        bodies[k] = v
    for _old, (nk, body) in rename.items():
        bodies[nk] = body
    for tag in sorted(tags):
        r = by_tag.get(tag)
        if not r:
            continue
        new = target_of(tag)
        if not new or r["ck3_key"] == new or new not in declared:
            continue
        r["ck3_key"] = new
        r["ck3_tier"] = new.split("_")[0]
        b = bodies.get(new, "")
        op = re.search(r"(?ms)^\t" + re.escape(START) + r" = \{\n(.*?)^\t\}", b)
        got = {}
        if op:
            for line in op.group(1).splitlines():
                m = re.match(r"\s*(holder|liege|government)\s*=\s*([A-Za-z0-9_]+)", line)
                if m:
                    got[m.group(1)] = m.group(2)
        # a landless title nobody has worn yet has no history block, so these fields stay as
        # they were: the country did not change, only the key it is worn under.
        r["ck3_holder"] = got.get("holder") or r["ck3_holder"]
        r["ck3_liege"] = got.get("liege") or r["ck3_liege"]
        r["ck3_government"] = got.get("government") or r["ck3_government"]
        r["ck3_declared"] = "yes" if new in declared else "no"
    with io.open(map_path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"title map updated: {os.path.relpath(map_path, mod)}")

    # 4. overrides (durable binding for the patch)
    ovp = os.path.join(mod, "gen_debug", "_title_overrides.csv")
    ovt = io.open(ovp, encoding="utf-8-sig", newline="").read()
    nl = "\r\n" if "\r\n" in ovt else "\n"
    if not ovt.endswith(nl):
        ovt += nl
    lines = ovt.split(nl)
    have, n_upd = set(), 0
    for i, line in enumerate(lines):
        try:
            row = next(csv.reader([line]))
        except Exception:
            continue
        if len(row) < 4 or row[0] != "country" or row[2] != "title_key":
            continue
        have.add(row[1])
        new = target_of(row[1]) if row[1] in tags else ""
        # a tag that already carries a title_key row keeps it — but when this run moves the
        # binding again (d_liguria -> k_genoa), the old row has to be rewritten, not skipped:
        # a stale override drags the country back on the next patch run.
        if not new or new == row[3] or new not in declared:
            continue
        tier = new.split("_")[0]
        kind = "帝国" if tier == "e" else "王国" if tier == "k" else "公国"
        why = f"改绑到{kind} {new}（原 {row[3]}）"
        row[3] = new
        if len(row) > 4:
            row[4] = why
        else:
            row.append(why)
        buf = io.StringIO()
        csv.writer(buf, lineterminator="").writerow(row)
        lines[i] = buf.getvalue()
        n_upd += 1
    add, n_add = "", 0
    for tag in sorted(tags):
        new = target_of(tag)
        old = old_of.get(tag, "")
        if not new or tag in have or new not in declared:
            continue
        tier = new.split("_")[0]
        kind = "帝国" if tier == "e" else "王国" if tier == "k" else "公国"
        add += f"country,{tag},title_key,{new},改绑到{kind} {new}（原 {old or '空'}）{nl}"
        n_add += 1
    io.open(ovp, "w", encoding="utf-8-sig", newline="").write(nl.join(lines) + add)
    print(f"overrides updated: {n_upd}, appended: {n_add}")


if __name__ == "__main__":
    main()
