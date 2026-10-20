# -*- coding: utf-8 -*-
"""Regency start = predecessor monarch's DEATH date (user rule 2026-10-20).

For every block in zz_eu5_regents.txt:
  1. each regented country tag's model rulers[] array -> the predecessor is the
     entry right before the current ruler; the new 1337 heirs are usually not in
     the array at all, in which case the predecessor is the last historical
     ruler. Multi-country blocks take the LATEST predecessor death (the regency
     starts when the ruler actually begins to rule his realms).
  2. preferred date = the predecessor's death date from history/characters
     (`<date> = { death = yes }`); falls back to the model `end` (they agree
     everywhere that was checked).
  3. clamp: if the date precedes the ruler's or the regent's birth (posthumous
     succession, e.g. COM), the effect would reference an unborn character --
     clamped to the later birth date and flagged in the output.
  4. only rewritten when earlier than the block's current date.
"""
import datetime, glob, io, json, os, re, shutil

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
EXPORT = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
REG = os.path.join(MOD, "history", "characters", "zz_eu5_regents.txt")


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="replace", newline="").read()


def dk(d):
    return tuple(int(x) for x in d.split("."))


new = json.load(io.open(os.path.join(EXPORT, "eu5_politics.json"), encoding="utf-8"))
countries = new["countries"]

cb = re.compile(r"(?ms)^([A-Za-z0-9_]+) = \{(.*?)^\}")


def scan(pat, agg):
    out = {}
    for f in glob.glob(os.path.join(MOD, "history", "characters", "*.txt")):
        if ".bak" in f:
            continue
        for mm in cb.finditer(read(f)):
            ds = pat.findall(mm.group(2))
            if ds:
                out[mm.group(1)] = agg(ds)
    return out


death = scan(re.compile(r"(?m)^[ \t]*(\d+\.\d+\.\d+) = \{[^}]*death"), lambda ds: max(ds, key=dk))
birth = scan(re.compile(r"(?m)^[ \t]*(\d+\.\d+\.\d+) = \{[^}]*birth"), lambda ds: min(ds, key=dk))

rtext = read(REG)
stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
out, pos, changed = [], 0, 0
for bm in re.finditer(r"(?ms)^# regent of ([^\n]+)\r?\n([A-Za-z0-9_]+) = \{\r?\n\t([\d.]+) = \{", rtext):
    tags = [t.strip() for t in bm.group(1).split(",")]
    ruler, cur_date = bm.group(2), bm.group(3)
    gm = re.search(r"set_diarch = character:([A-Za-z0-9_]+)", rtext[bm.end():bm.end() + 500])
    regent = gm.group(1) if gm else None
    cands = []
    for tag in tags:
        arr = (countries.get(tag) or {}).get("rulers") or []
        if not arr:
            print("  WARN %s: empty rulers array, skipped" % tag)
            continue
        idx = next((i for i, e in enumerate(arr) if e.get("character") == ruler), None)
        if idx is None:
            pi = len(arr) - 1
        elif idx > 0:
            pi = idx - 1
        else:
            continue
        pred = arr[pi]
        if pred.get("character") == ruler or not pred.get("end"):
            continue
        cands.append((death.get(pred.get("character") or "", pred["end"]), tag, pred.get("character")))
    if not cands:
        print("%-40s (%s) keep %s  [no predecessor data]" % (ruler, bm.group(1), cur_date))
        continue
    pick = max(cands, key=lambda c: dk(c[0]))
    want = pick[0]
    note = ""
    floors = [birth[x] for x in (ruler, regent) if x and x in birth]
    if floors and dk(want) < dk(max(floors, key=dk)):
        want = max(floors, key=dk)
        note = "  CLAMPED to %s (predecessor died %s before ruler/regent birth)" % (want, pick[0])
    if dk(want) < dk(cur_date):
        out.append(rtext[pos:bm.start(3)])
        out.append(want)
        pos = bm.end(3)
        changed += 1
        print("%-40s (%s) %s -> %-9s pred=%s of %s%s"
              % (ruler, bm.group(1), cur_date, want, pick[2], pick[1], note))
    else:
        print("%-40s (%s) keep %s  (predecessor died %s)" % (ruler, bm.group(1), cur_date, want))
out.append(rtext[pos:])
t2 = "".join(out)
assert t2.count("{") == t2.count("}")
if t2 != rtext:
    shutil.copy2(REG, REG + ".bak_" + stamp)
    io.open(REG, "w", encoding="utf-8-sig", newline="").write(t2)
    print("changed:", changed, "| written with backup")
else:
    print("changed:", changed, "| nothing written")
