# -*- coding: utf-8 -*-
"""Read-only audit of the day-one primary titles.

Replicates the county tier of _fix_politics_output.py's primary calculation against
eu5_politics.json and diffs it with the mod's common/on_action/zz_eu5_primary_titles.txt,
so a ruler EU5 leaves holding several counties whose seat is not worn can be seen.

Writes nothing. Usage:
    python _audit_primary_titles.py [--export DIR] [--mod DIR]
"""
import argparse, io, json, os, re, sys

ap = argparse.ArgumentParser()
_here = os.path.dirname(os.path.abspath(__file__))
ap.add_argument("--export", default=os.path.join(
    os.path.dirname(os.path.dirname(_here)), "Global_modern_map", "eu5_export"))
ap.add_argument("--mod", default=os.path.dirname(_here))
args = ap.parse_args()

p = json.load(io.open(os.path.join(args.export, "eu5_politics.json"), encoding="utf-8-sig"))
mapping = os.path.join(args.export, "mapping.json")
county = p["counties"]
countries = p["countries"]
chars = p["characters"]

county_of_location = {}
if os.path.exists(mapping):
    for loc in json.load(io.open(mapping, encoding="utf-8")).get("locations") or []:
        if loc.get("county"):
            county_of_location.setdefault(loc["name"], "c_" + loc["county"])
for name, info in county.items():
    if info.get("capital"):
        county_of_location.setdefault(info["capital"], name)

dropped = set()
dpath = os.path.join(args.mod, "gen_debug", "eu5_titles_dropped.txt")
if os.path.exists(dpath):
    dropped = {l.strip() for l in io.open(dpath, encoding="utf-8-sig") if l.strip()}


def title_key(rank, tag):
    return "k_papal_state" if tag == "PAP" else f"{rank}_eu5_{tag.lower()}"


# ---- the tier above: a ruler wearing a duchy or better is settled by the tier itself
by_ruler = {}
for tag, c in countries.items():
    if c.get("rank") in ("d", "k", "e") and c.get("ruler") \
            and title_key(c["rank"], tag) not in dropped:
        by_ruler.setdefault(c["ruler"], []).append(tag)

counties_of_ruler = {}
for name, info in county.items():
    if info.get("ruler"):
        counties_of_ruler.setdefault(info["ruler"], []).append(name)

shugo = p.get("shugo_daimyo") or {}
seat_of = {}
for tag, c in countries.items():
    seat_of[(c.get("ruler") or "")] = tag

# ---- the file as it stands
fpath = os.path.join(args.mod, "common", "on_action", "zz_eu5_primary_titles.txt")
cur = {}
if os.path.exists(fpath):
    cur = dict(re.findall(r"character:(\w+) = \{.*?set_primary_title_to = title:(\w+)",
                          io.open(fpath, encoding="utf-8-sig").read(), re.S))

# ---- every ruler the county tier leaves holding several counties
rows = []
for ruler, held in sorted(counties_of_ruler.items()):
    if len(held) < 2:
        continue
    settled = ruler in by_ruler
    tags = sorted({county[n].get("owner") for n in held if county[n].get("owner")})
    own = (chars.get(ruler) or {}).get("tag")
    pick = None
    for t in ([own] if own in tags else []) + [t for t in tags if t != own]:
        s = county_of_location.get((countries.get(t) or {}).get("capital") or "")
        if s and s in held:
            pick = s
            break
    # what the shugo rule would add: the kokufu seat if he holds it, else his own capital's county
    stag = seat_of.get(ruler) or ""
    shugo_pick = None
    if stag in shugo:
        if shugo[stag] in held:
            shugo_pick = shugo[stag]
        else:
            cap = county_of_location.get((countries.get(stag) or {}).get("capital") or "")
            if cap in held:
                shugo_pick = cap
    rows.append((ruler, stag, settled, pick, shugo_pick, sorted(held), cur.get(ruler)))

miss_plain = [r for r in rows if not r[2] and r[3] is None]
miss_shugo = [r for r in rows if not r[2] and r[3] is None and r[4]]
print(f"rulers holding >=2 counties: {len(rows)}  (settled by a higher tier: "
      f"{sum(1 for r in rows if r[2])})")
print(f"current file entries: {len(cur)}")
print(f"\n== county tier with no primary the generic loop can find: {len(miss_plain)} ==")
for ruler, stag, settled, pick, shugo_pick, held, have in miss_plain:
    tag_note = f"shugo:{stag}" if stag in shugo else ""
    print(f"  {ruler:32s} {tag_note:11s} shugo_pick={shugo_pick} held={held} file={have}")
print(f"\n== of those, the shugo rule would seat: {len(miss_shugo)} ==")
for ruler, stag, settled, pick, shugo_pick, held, have in miss_shugo:
    print(f"  {ruler:32s} {stag:4s} -> {shugo_pick:16s} held={held}")

# ---- stale: entries in the file whose ruler no longer holds that county at all
stale = [(r, t) for r, t in cur.items()
         if t not in (counties_of_ruler.get(r) or []) and not r.startswith("c_")]
print(f"\n== entries in the file the ruler does not hold: {len(stale)} ==")
for r, t in stale[:40]:
    print(f"  {r:32s} -> {t}  (holds {sorted(counties_of_ruler.get(r) or [])})")
