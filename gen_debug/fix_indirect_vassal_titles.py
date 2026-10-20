# -*- coding: utf-8 -*-
"""Reconcile history/titles/zz_eu5_titles.txt against the vanilla EU5 politics model.

Reads ONLY the vanilla export (Global_modern_map/eu5_export). The modern-borders
mod's own export (eu5_export_modern) is a different mod's data and must never be
read here (its extra counties are not declared in this mod's landed_titles).

Phases (so today's work lands in the user's order, one reviewable step at a time):

  --heirs         seat the heirs: only the titles and counties of the countries the
                  model rules through an heir rather than a regent
  --rest          the remaining counties: the corrected Rule A (a vassal takes his
                  lord's OWN county; tusi never claim; the claimant's own seat and a
                  superior's primary-title seat are protected) plus every other
                  holder/liege/government the model has an opinion about
  --baronies      b_ block reconciliation only: a barony the model no longer seats
                  loses its stale block, a model barony with no block gets one

Ghost blocks (titles the mod's landed_titles never declares) are removed in every
phase: a history block for an undeclared title makes CK3 reject the whole file.
No dry-run mode: run it and it writes (with a timestamped backup), printing what
changed. Surgical by construction -- only TARGET blocks are rewritten.
"""
import argparse, bisect, datetime, io, json, os, re, shutil, sys

sys.path.insert(0, r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export")
from _faith_heads import country_title_key

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
EXPORT = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
DATE = "1337.1.1"

ap = argparse.ArgumentParser()
g = ap.add_mutually_exclusive_group()
g.add_argument("--heirs", action="store_true", help="phase 1: heir countries only")
g.add_argument("--rest", action="store_true", help="phase 2: all counties except the heir set")
g.add_argument("--baronies", action="store_true", help="phase 3: b_ block reconciliation only")
args = ap.parse_args()

new = json.load(io.open(os.path.join(EXPORT, "eu5_politics.json"), encoding="utf-8"))
countries = new["countries"]; counties = new["counties"]; relations = new["relations"]
model_baronies = new.get("baronies") or {}

def gov(g):
    return {"monarchy":"feudal_government","tribe":"tribal_government","republic":"republic_government",
            "theocracy":"theocracy_government","steppe_horde":"nomad_government","clan":"clan_government",
            "administrative":"administrative_government","celestial":"celestial_government",
            "meritocratic":"meritocratic_government","japan_feudal":"japan_feudal_government",
            "japan_ritsuryo":"japan_administrative_government","mandala":"mandala_government",
            "wanua":"wanua_government","herder":"herder_government"}.get(g or "")

heir_tags = {t for t, c in countries.items()
             if c.get("heir") and c.get("ruler") == c.get("heir")}
heir_titles = {country_title_key(countries[t].get("rank"), t) for t in heir_tags
               if countries[t].get("rank") in ("d", "k", "e")}
heir_counties = {name for name, info in counties.items()
                 if info.get("owner") in heir_tags}

wanted, wanted_gov, wanted_liege = {}, {}, {}
title_of = {tag: country_title_key(c.get("rank"), tag)
            for tag, c in countries.items() if c.get("rank") in ("d","k","e")}
io_titles = {"hre":"e_hre","ilkhanate":"e_ilkhanate","tatar_yoke":"e_golden_horde","middle_kingdom":"h_china"}
resolved = {}
lp = os.path.join(MOD, "gen_debug", "eu5_lieges.json")
if os.path.exists(lp):
    resolved = json.load(io.open(lp, encoding="utf-8-sig"))
dropped = set()
dp = os.path.join(MOD, "gen_debug", "eu5_titles_dropped.txt")
if os.path.exists(dp):
    dropped = set(io.open(dp, encoding="utf-8-sig").read().split())

for tag, country in countries.items():
    key = country_title_key(country.get("rank"), tag)
    if country.get("ruler"):
        wanted[key] = country["ruler"]
    gv = gov(country.get("government"))
    if gv:
        wanted_gov[key] = gv
for name, county in counties.items():
    if county.get("ruler"):
        wanted[name] = county["ruler"]
    owner = countries.get(county.get("owner") or "") or {}
    gv = gov(owner.get("government"))
    if gv:
        wanted_gov[name] = gv
for rel in relations:
    if rel.get("ck3") not in ("vassal","union") or rel["second"] not in countries:
        continue
    liege = (None if rel.get("ck3") == "union"
             else rel.get("liege_title") or io_titles.get(rel.get("type") or "")
             or title_of.get(rel["first"]))
    liege = resolved.get(rel["second"]) or liege
    if not liege or liege in dropped:
        continue
    if title_of.get(rel["second"]):
        wanted_liege.setdefault(title_of[rel["second"]], liege)
    for name, info in counties.items():
        if info.get("owner") == rel["second"]:
            wanted_liege.setdefault(name, liege)

shugo_counties = set()
for _t, provs in (new.get("shugo_provinces") or {}).items():
    shugo_counties.update(provs)

# ---------------------------------------------------------------- the mod's declarations
NT_BLOCK = re.compile(r"([A-Za-z0-9_-]+)\s*=\s*\{")

def collect_keys(text, out):
    i, n = 0, len(text)
    while i < n:
        m = NT_BLOCK.search(text, i)
        if not m:
            return
        j, d = m.end(), 1
        while j < n and d:
            if text[j] == "{":
                d += 1
            elif text[j] == "}":
                d -= 1
            j += 1
        out.add(m.group(1))
        collect_keys(text[m.end():j - 1], out)
        i = j

allowed = set()
lt_dir = os.path.join(MOD, "common", "landed_titles")
for f in sorted(os.listdir(lt_dir)):
    if f.endswith(".txt") and ".bak" not in f:
        collect_keys(io.open(os.path.join(lt_dir, f), encoding="utf-8-sig", errors="ignore").read(), allowed)

# ---------------------------------------------------------------- the file
tp = os.path.join(MOD, "history", "titles", "zz_eu5_titles.txt")
text = io.open(tp, encoding="utf-8-sig", newline="").read()
text = text.replace("\r\n", "\n").replace("\r", "\n")

def mod_state(county, src=None):
    src = text if src is None else src
    m = re.search(r"(?ms)^" + re.escape(county) + r" = \{\n(.*?)^\n?\}", src)
    if not m:
        return (None, None)
    e = re.search(r"(?ms)^\t" + re.escape(DATE) + r" = \{\n(.*?)^\t\}", m.group(1))
    if not e:
        return (None, None)
    h = re.search(r"holder = ([A-Za-z0-9_]+)", e.group(1))
    lg = re.search(r"liege = ([A-Za-z0-9_]+)", e.group(1))
    return (h.group(1) if h else None, lg.group(1) if lg else None)

# ---- phase 3: b_ reconciliation only ----
if args.baronies:
    BLOCK = re.compile(r"(?ms)^([A-Za-z0-9_]+) = \{\n(.*?)^\}\n")
    removed, out, pos = [], [], 0
    for m in BLOCK.finditer(text):
        key = m.group(1)
        if key.startswith("b_") and key not in model_baronies:
            out.append(text[pos:m.start()]); pos = m.end(); removed.append(key)
    out.append(text[pos:])
    patched = "".join(out)
    if removed:
        patched = re.sub("\n{3,}", "\n\n", patched)
    present = {m.group(1) for m in BLOCK.finditer(patched) if m.group(1).startswith("b_")}
    missing = sorted(b for b in model_baronies if b in allowed and b not in present)
    for b in missing:
        info = model_baronies[b]
        gv = gov(countries.get(info.get("tag") or "", {}).get("government"))
        lines = [f"{b} = {{", f"\t{DATE} = {{", f"\t\tholder = {info['holder']}"]
        if gv:
            lines.append(f"\t\tgovernment = {gv}")
        lines += ["\t}", "}", ""]
        block = "\n".join(lines)
        marks = [(mm.group(1), mm.start()) for mm in re.finditer(r"(?m)^(b_[A-Za-z0-9_]+) = \{", patched)]
        idx = bisect.bisect_left([k for k, _ in marks], b)
        at = marks[idx][1] if idx < len(marks) else (marks[-1][1] if marks else len(patched))
        patched = patched[:at] + block + patched[at:]
    print(f"baronies: {len(removed)} stale blocks removed {sorted(removed)}; {len(missing)} inserted {missing}")
    d = 0
    for ch in patched:
        if ch == "{": d += 1
        elif ch == "}": d -= 1
    if d != 0 or patched == text and not removed and not missing:
        print("nothing to write" if d == 0 else "BRACE IMBALANCE -- NOT WRITTEN")
        if d != 0:
            raise SystemExit(1)
        raise SystemExit(0)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(tp, tp + f".bak_{stamp}")
    io.open(tp, "w", encoding="utf-8-sig", newline="").write(patched.replace("\n", "\r\n"))
    print(f"written: {tp} (backup .bak_{stamp})")
    raise SystemExit(0)

# ---- phases 1/2: county reconciliation ----
TARGET = []
for c in counties:
    if c in shugo_counties:
        continue
    th, tl = wanted.get(c), wanted_liege.get(c)
    if th is None and tl is None:
        continue
    if args.heirs and c not in heir_counties:
        continue
    if args.rest and c in heir_counties:
        continue
    mh, ml = mod_state(c)
    if mh != th or ml != tl:
        TARGET.append(c)
# the heir countries' own d/k/e titles ride with phase 1
if args.heirs:
    for t in heir_titles:
        th = wanted.get(t)
        mh, _ = mod_state(t)
        if th and mh != th and t in allowed:
            TARGET.append(t)
TARGET = sorted(set(TARGET))
print(f"titles to rewrite: {len(TARGET)}")

BLOCK = re.compile(r"(?ms)^([A-Za-z0-9_]+) = \{\n(.*?)^\}\n")
ENTRY = re.compile(r"(?ms)^\t(\d+\.\d+\.\d+) = \{\n(.*?)^\t\}\n")
LIEGE = re.compile(r"(?m)^\t\tliege = ([A-Za-z0-9_]+)\n")
TSET = set(TARGET)

def transform(key, body):
    liege = None
    out, pos = [], 0
    for e in ENTRY.finditer(body):
        date, fields = e.group(1), e.group(2)
        found = LIEGE.search(fields)
        if found is None:
            continue
        if date == DATE:
            continue
        liege = found.group(1)
        out.append(body[pos:e.start()])
        rest = LIEGE.sub("", fields, count=1)
        if rest.strip("\n").strip():
            out.append(f"\t{date} = {{\n{rest}\t}}\n")
        pos = e.end()
    if liege is None:
        out.append(body[pos:])
        body = "".join(out)
    else:
        out.append(body[pos:])
        body = "".join(out).rstrip("\n")
        if re.search(r"(?m)^\t" + re.escape(DATE) + r" = \{", body):
            body = re.sub(r"(?m)^(\t" + re.escape(DATE) + r" = \{\n)",
                          rf"\g<1>\t\tliege = {liege}\n", body, count=1)
        else:
            body += f"\n\t{DATE} = {{\n\t\tliege = {liege}\n\t}}"

    want = wanted.get(key)
    holders = re.findall(r"(?m)^\t\tholder = ([A-Za-z0-9_]+)$", body)
    if want and (not holders or holders[-1] != want):
        opening = re.search(r"(?ms)^\t" + re.escape(DATE) + r" = \{\n(.*?)^\t\}\n", body)
        if opening:
            fields = opening.group(1)
            if re.search(r"(?m)^\t\tholder = ", fields):
                fields = re.sub(r"(?m)^(\t\tholder = )[A-Za-z0-9_]+$", rf"\g<1>{want}", fields, count=1)
            else:
                fields = f"\t\tholder = {want}\n" + fields
            body = body[:opening.start()] + f"\t{DATE} = {{\n{fields}\t}}\n" + body[opening.end():]
        else:
            body = body.rstrip("\n") + f"\n\t{DATE} = {{\n\t\tholder = {want}\n\t}}"

    want_gov = wanted_gov.get(key)
    govs = re.findall(r"(?m)^\t\tgovernment = ([a-z_]+)$", body)
    if want_gov and (not govs or govs[-1] != want_gov):
        opening = re.search(r"(?ms)^\t" + re.escape(DATE) + r" = \{\n(.*?)^\t\}\n", body)
        if opening:
            fields = opening.group(1)
            if re.search(r"(?m)^\t\tgovernment = ", fields):
                fields = re.sub(r"(?m)^(\t\tgovernment = )[a-z_]+$", rf"\g<1>{want_gov}", fields, count=1)
            else:
                fields = fields.rstrip("\n") + f"\n\t\tgovernment = {want_gov}\n"
            body = body[:opening.start()] + f"\t{DATE} = {{\n{fields}\t}}\n" + body[opening.end():]
        else:
            body = body.rstrip("\n") + f"\n\t{DATE} = {{\n\t\tgovernment = {want_gov}\n\t}}"

    want_liege = wanted_liege.get(key)
    lieges = re.findall(r"(?m)^\t\tliege = ([A-Za-z0-9_]+)$", body)
    if (not want_liege and lieges and lieges[-1] == "k_gen_wilderness"
            and holders and holders[-1] != "gen_wilderness_holder"):
        body = re.sub(r"(?m)^\t\tliege = k_gen_wilderness\n", "", body, count=1)
        body = re.sub(r"(?ms)^\t" + re.escape(DATE) + r" = \{\n(\t\})", "", body, count=1)
        lieges = []
    if want_liege and (not lieges or lieges[-1] != want_liege):
        opening = re.search(r"(?ms)^\t" + re.escape(DATE) + r" = \{\n(.*?)^\t\}\n", body)
        if opening:
            fields = opening.group(1)
            if re.search(r"(?m)^\t\tliege = ", fields):
                fields = re.sub(r"(?m)^(\t\tliege = )[A-Za-z0-9_]+$", rf"\g<1>{want_liege}", fields, count=1)
            else:
                fields = fields.rstrip("\n") + f"\n\t\tliege = {want_liege}\n"
            body = body[:opening.start()] + f"\t{DATE} = {{\n{fields}\t}}\n" + body[opening.end():]
        else:
            body = body.rstrip("\n") + f"\n\t{DATE} = {{\n\t\tliege = {want_liege}\n\t}}"
    if (not want_liege and lieges and lieges[-1] != "k_gen_wilderness"
            and key not in shugo_counties):
        body = re.sub(r"(?m)^\t\tliege = [A-Za-z0-9_]+\n", "", body)

    body = body.rstrip("\n") + "\n"
    return f"{key} = {{\n{body.rstrip(chr(10))}\n}}\n"

def repl(m):
    if m.group(1) not in TSET:
        return m.group(0)
    return transform(m.group(1), m.group(2))

patched = BLOCK.sub(repl, text)

# ghosts out (every phase)
removed_ghosts, out, pos = [], [], 0
for m in BLOCK.finditer(patched):
    if m.group(1) not in allowed:
        out.append(patched[pos:m.start()]); pos = m.end(); removed_ghosts.append(m.group(1))
out.append(patched[pos:])
patched = "".join(out)
if removed_ghosts:
    patched = re.sub("\n{3,}", "\n\n", patched)

# insert blocks for TARGET titles the file has never heard of (counties a newly seated
# holder brings into existence, e.g. the c_eu5_* seats of the rank-less heirs)
missing = sorted(k for k in TSET
                 if k in allowed and k.split("_")[0] in ("c", "k", "d", "e")
                 and not re.search(r"(?m)^" + re.escape(k) + r" = \{", patched))
for k in missing:
    h, l, gv = wanted.get(k), wanted_liege.get(k), wanted_gov.get(k)
    lines = [f"{k} = {{", f"\t{DATE} = {{", f"\t\tholder = {h}"]
    if gv:
        lines.append(f"\t\tgovernment = {gv}")
    if l:
        lines.append(f"\t\tliege = {l}")
    lines += ["\t}", "}", ""]
    block = "\n".join(lines)
    pre = k.split("_")[0]
    marks = [(mm.group(1), mm.start()) for mm in re.finditer(r"(?m)^([A-Za-z0-9_]+) = \{", patched)
             if mm.group(1).split("_")[0] == pre]
    idx = bisect.bisect_left([kk for kk, _ in marks], k)
    at = marks[idx][1] if idx < len(marks) else (marks[-1][1] if marks else len(patched))
    patched = patched[:at] + block + patched[at:]
if missing:
    print(f"blocks inserted: {len(missing)} {missing}")

def state_in(txt, county):
    m = re.search(r"(?ms)^" + re.escape(county) + r" = \{\n(.*?)^\n?\}", txt)
    if not m:
        return (None, None)
    e = re.search(r"(?ms)^\t" + re.escape(DATE) + r" = \{\n(.*?)^\t\}", m.group(1))
    if not e:
        return (None, None)
    h = re.search(r"holder = ([A-Za-z0-9_]+)", e.group(1))
    lg = re.search(r"liege = ([A-Za-z0-9_]+)", e.group(1))
    return (h.group(1) if h else None, lg.group(1) if lg else None)

ok = True
for c in TARGET:
    mh, ml = state_in(patched, c)
    th, tl = wanted.get(c), wanted_liege.get(c)
    if (mh, ml) != (th, tl):
        ok = False
        print(f"  MISMATCH {c}: {mh}/{ml} want {th}/{tl}")
d = 0
for ch in patched:
    if ch == "{": d += 1
    elif ch == "}": d -= 1
if d != 0:
    ok = False
    print("BRACE IMBALANCE")
if not ok:
    print("VERIFICATION FAILED -- NOTHING WRITTEN")
    raise SystemExit(1)
if patched == text:
    print("already in sync -- nothing written")
    raise SystemExit(0)

stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy2(tp, tp + f".bak_{stamp}")
io.open(tp, "w", encoding="utf-8-sig", newline="").write(patched.replace("\n", "\r\n"))
print(f"written: {tp} (backup .bak_{stamp})")
