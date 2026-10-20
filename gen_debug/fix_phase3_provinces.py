# -*- coding: utf-8 -*-
"""Phase 3, province side + character government entries. Surgical only.

Inputs read (never written):
  - Global_modern_map/eu5_export/eu5_politics.json  (the model)
  - history/titles/zz_eu5_titles.txt.bak_20261020_104058  (state just before the
    phase-3 b_ reconciliation: b_ blocks present there but absent from the model
    are the killed baronies; model baronies absent there are the new seats)
  - common/landed_titles/*.txt  (b_ -> province id)
Written (with timestamped backups, only lines touched):
  - history/provinces/00_generated_provinces.txt : holding = none for killed
    baronies, model/tusi holding for new seats. culture/faith never touched.
  - history/characters/zz_eu5_government.txt : additive-only entries for model
    rulers that have no block yet (append at end).
"""
import datetime, io, json, os, re, shutil, sys

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
EXPORT = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
PRE_B = os.path.join(MOD, "history", "titles", "zz_eu5_titles.txt.bak_20261020_104058")
TITLES = os.path.join(MOD, "history", "titles", "zz_eu5_titles.txt")
PROV = os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt")
GOV = os.path.join(MOD, "history", "characters", "zz_eu5_government.txt")

GOVMAP = {"monarchy": "feudal_government", "tribe": "tribal_government",
          "republic": "republic_government", "theocracy": "theocracy_government",
          "steppe_horde": "nomad_government", "clan": "clan_government",
          "administrative": "administrative_government", "celestial": "celestial_government",
          "meritocratic": "meritocratic_government", "japan_feudal": "japan_feudal_government",
          "japan_ritsuryo": "japan_administrative_government", "mandala": "mandala_government",
          "wanua": "wanua_government", "herder": "herder_government"}

BLOCK = re.compile(r"([A-Za-z0-9_]+)\s*=\s*\{")


def read(path):
    return io.open(path, encoding="utf-8-sig", errors="replace", newline="").read()


def close_of(text, start):
    j, depth = start, 1
    while j < len(text) and depth:
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
        j += 1
    return j


def walk(text, path=()):
    i, n = 0, len(text)
    while i < n:
        m = BLOCK.search(text, i)
        if not m:
            return
        j = close_of(text, m.end())
        body = text[m.end():j - 1]
        yield path, m.group(1), body
        yield from walk(body, path + (m.group(1),))
        i = j


def uncommented(text):
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c == "#":
            while i < n and text[i] != "\n":
                i += 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


new = json.load(io.open(os.path.join(EXPORT, "eu5_politics.json"), encoding="utf-8"))
model_baronies = new.get("baronies") or {}
countries = new["countries"]
counties = new["counties"]
relations = new["relations"]
tusi_tags = set()
for rel in relations:
    if rel.get("type") == "tusi":
        tusi_tags.add(rel.get("first")); tusi_tags.add(rel.get("second"))

# ---- killed vs new baronies: diff the pre-reconciliation backup against the model ----
pre = read(PRE_B)
pre_b = {m.group(1) for m in re.finditer(r"(?m)^(b_[A-Za-z0-9_]+) = \{", uncommented(pre))}
model_b = set(model_baronies)
killed = sorted(pre_b - model_b)
new_seats = sorted(model_b - pre_b)
print(f"killed baronies: {len(killed)} | new seats: {len(new_seats)} {new_seats}")

# ---- landed_titles: b_ -> province id ----
barony_prov = {}
lt_dir = os.path.join(MOD, "common", "landed_titles")
for f in sorted(os.listdir(lt_dir)):
    if not f.endswith(".txt") or ".bak" in f:
        continue
    for _, key, body in walk(read(os.path.join(lt_dir, f))):
        if key.startswith("b_"):
            p = re.search(r"(?m)^\s*province\s*=\s*(\d+)", body)
            if p:
                barony_prov[key] = int(p.group(1))

# ---- patch province holdings (holding line only) ----
ptext = read(PROV)
n_kill = n_seat = 0
for b in killed:
    pid = barony_prov.get(b)
    if pid is None:
        print(f"  WARN killed {b}: no province id in landed_titles, skipped")
        continue
    m = re.search(r"(?m)^" + str(pid) + r"[ \t]*=[ \t]*\{[ \t]*\r?\n([\s\S]*?)^\}", ptext)
    if not m:
        print(f"  WARN killed {b}: province {pid} has no history entry, skipped")
        continue
    seg = m.group(1)
    cur = re.search(r"(?m)^[ \t]*holding[ \t]*=[ \t]*([a-z_]+)", seg)
    if not cur or cur.group(1) == "none":
        continue
    ptext = ptext[:m.start(1)] + seg[:cur.start(1)] + "none" + seg[cur.end(1):] + ptext[m.end(1):]
    n_kill += 1
for b in new_seats:
    info = model_baronies[b]
    pid = barony_prov.get(b)
    if pid is None:
        pid = info.get("province")
    if pid is None:
        print(f"  WARN seat {b}: no province id, skipped")
        continue
    want = info.get("holding")
    if info.get("tag") in tusi_tags:
        want = "tribal_holding"  # tusi rule: tribal on every built holding
    if not want:
        print(f"  WARN seat {b}: model gives no holding, skipped")
        continue
    m = re.search(r"(?m)^" + str(pid) + r"[ \t]*=[ \t]*\{[ \t]*\r?\n([\s\S]*?)^\}", ptext)
    if not m:
        print(f"  WARN seat {b}: province {pid} has no history entry, skipped")
        continue
    seg = m.group(1)
    cur = re.search(r"(?m)^[ \t]*holding[ \t]*=[ \t]*([a-z_]+)", seg)
    if cur and cur.group(1) == want:
        continue
    if cur:
        seg2 = seg[:cur.start(1)] + want + seg[cur.end(1):]
    else:
        seg2 = seg.rstrip("\r\n") + "\n    holding = " + want + "\n"
    ptext = ptext[:m.start(1)] + seg2 + ptext[m.end(1):]
    n_seat += 1
if ptext.count("{") != ptext.count("}"):
    raise SystemExit("provinces: braces unbalanced -- NOT WRITTEN")
print(f"province holdings: {n_kill} set none | {n_seat} seats set")

# ---- additive government entries for seated rulers with no block ----
gtext = read(GOV)
have = set(re.findall(r"(?m)^([A-Za-z0-9_]+) = \{", gtext))
rulers = set()
for c in countries.values():
    if c.get("ruler"):
        rulers.add(c["ruler"])
for info in counties.values():
    if info.get("ruler"):
        rulers.add(info["ruler"])
missing = sorted(rulers - have)

# each missing ruler's government: the government line on the highest-rank title
# they hold in the CURRENT titles file; else their country's model government.
tcur = read(TITLES)
title_gov = {}
for path, key, body in walk(uncommented(tcur)):
    if key.split("_")[0] in ("c", "d", "k", "e") and len(path) == 1:
        h = re.search(r"(?m)^\s*1337\.1\.1 = \{.*?holder\s*=\s*([A-Za-z0-9_]+)", body, re.S)
        g = re.search(r"(?m)^\s*1337\.1\.1 = \{.*?government\s*=\s*([a-z_]+)", body, re.S)
        if h:
            rank = {"c": 0, "d": 1, "k": 2, "e": 3}[key[0]]
            gv = g.group(1) if g else None
            old = title_gov.get(h.group(1))
            if gv and (old is None or rank >= old[0]):
                title_gov[h.group(1)] = (rank, gv)
entry_eol = "\r\n" if "\r\n" in gtext else "\n"
added = []
for ch in missing:
    gv = title_gov.get(ch, (None, None))[1]
    if not gv:
        # fall back to the model country government(s) this ruler runs
        gvs = {GOVMAP.get(c.get("government") or "") for c in countries.values()
               if c.get("ruler") == ch and c.get("government")}
        gvs.discard(None)
        if len(gvs) == 1:
            gv = gvs.pop()
    if not gv:
        print(f"  WARN {ch}: no government resolvable, no entry written")
        continue
    added.append((ch, gv))
    block = (f"{ch} = {{{entry_eol}"
             f"\t1337.1.1 = {{{entry_eol}"
             f"\t\teffect = {{{entry_eol}"
             f"\t\t\tchange_government = {gv}{entry_eol}"
             f"\t\t}}{entry_eol}"
             f"\t}}{entry_eol}"
             f"}}{entry_eol}")
    if not gtext.endswith("\n"):
        gtext += entry_eol
    gtext += block
if gtext.count("{") != gtext.count("}"):
    raise SystemExit("zz_eu5_government.txt: braces unbalanced -- NOT WRITTEN")
print(f"government entries added: {len(added)}")
for ch, gv in added:
    print(f"  {ch} -> {gv}")

# ---- write only what changed ----
stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
wrote = []
for path, text in ((PROV, ptext), (GOV, gtext)):
    if text != read(path):
        shutil.copy2(path, path + f".bak_{stamp}")
        io.open(path, "w", encoding="utf-8-sig", newline="").write(text)
        wrote.append(os.path.basename(path))
print("written:", ", ".join(wrote) if wrote else "nothing changed")
