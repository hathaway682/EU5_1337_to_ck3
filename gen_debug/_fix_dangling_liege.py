# -*- coding: utf-8 -*-
"""Rewrite `liege = <dropped key>` to the country's current primary title.

改绑会把旧键（`d_eu5_teu` 这类本 mod 铸的壳）的块和声明一起删掉，但它的附庸——那些
伯爵领的 history 里写着 `liege = d_eu5_teu`——还指着已经不存在的头衔。CK3 里这就是
封臣关系断掉：萨姆兰（SMD）、库尔姆（c_chelmno）这些县会变成无主附庸。

规则：`<rank>_eu5_<tag>` 不在任何 landed_titles 里声明时，改写成该 tag 在
`eu5_ck3_title_map.csv` 里当前的 `ck3_key`。幂等：改完再跑找不到悬空目标。
"""
import csv, glob, io, os, re, shutil, sys, datetime

MOD = sys.argv[1] if len(sys.argv) > 1 else "."
DRY = "--dry-run" in sys.argv


def norm(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read().replace("\r\n", "\n")


decl = set()
for f in glob.glob(os.path.join(MOD, "common", "landed_titles", "*.txt")):
    decl |= set(re.findall(r"(?m)^\s*([a-z]_[A-Za-z0-9_]+)\s*=\s*\{", norm(f)))

primary = {}
for r in csv.DictReader(io.open(os.path.join(MOD, "gen_debug", "eu5_ck3_title_map.csv"),
                                encoding="utf-8-sig", newline="")):
    if r["kind"] == "country" and (r["ck3_key"] or "").strip():
        primary[r["eu5_tag"]] = r["ck3_key"].strip()

# old key -> new key, only for keys nobody declares any more
fix = {}
for f in glob.glob(os.path.join(MOD, "history", "titles", "*.txt")):
    for m in re.finditer(r"(?m)^\s*liege\s*=\s*([a-z]_eu5_[a-z]+)\s*$", norm(f)):
        old = m.group(1)
        if old in decl:
            continue
        tag = old.split("_eu5_", 1)[1].upper()
        new = primary.get(tag)
        if new and new in decl and new != old:
            fix[old] = new
print("dangling liege targets to rewrite:", len(fix))
for k in sorted(fix):
    print(f"   {k:20s} -> {fix[k]}")

if not fix or DRY:
    raise SystemExit(0)

stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
total = 0
for f in sorted(glob.glob(os.path.join(MOD, "history", "titles", "*.txt"))):
    raw = io.open(f, encoding="utf-8-sig", errors="ignore").read()
    t = raw.replace("\r\n", "\n")
    n = 0
    for old, new in fix.items():
        t, k = re.subn(r"(?m)^(\s*)liege = " + re.escape(old) + r"$",
                       lambda m, new=new: f"{m.group(1)}liege = {new}", t)
        n += k
    if n:
        shutil.copy2(f, f + f".bak_{stamp}")
        io.open(f, "w", encoding="utf-8-sig", newline="").write(t.replace("\n", "\r\n"))
        print(f"  {os.path.basename(f)}: {n}")
        total += n

# the title map's descriptive liege column follows, so the ledger stays readable
mp = os.path.join(MOD, "gen_debug", "eu5_ck3_title_map.csv")
rows = list(csv.DictReader(io.open(mp, encoding="utf-8-sig", newline="")))
fields = list(rows[0].keys())
m = 0
for r in rows:
    cur = (r.get("ck3_liege") or "").strip()
    if cur in fix:
        r["ck3_liege"] = fix[cur]
        m += 1
if m:
    shutil.copy2(mp, mp + f".bak_{stamp}")
    with io.open(mp, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)
print(f"liege lines rewritten: {total}; title-map rows: {m}")
