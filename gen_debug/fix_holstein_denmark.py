# -*- coding: utf-8 -*-
"""Denmark/Holstein surgical patch (user decision 2026-10-20):

1. landed_titles: b_rendsburg becomes the first barony of c_holstein (capital).
2. zz_eu5_titles.txt:
   - c_holstein 1337.1.1: holder -> Gerhard III (HTR), liege -> k_eu5_dan
     (Holstein becomes Denmark's vassal; the HRE liege line on the 1337.1.1
     entry only is replaced -- historical entries untouched).
   - b_kiel: new block, holder Johann III of Holstein-Kiel (demoted to baron).
3. zz_eu5_regents.txt: Dan Valdemar designates Gerhard as regent at start.

Provinces 608/611 are already castle_holding -- nothing to do there.
"""
import datetime, io, re, shutil

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
GERHARD = "shl_gerhard_iii_holstein_rendsburg"
JOHANN = "shl_johann_iii_holstein_kiel"


def read(p):
    return io.open(p, encoding="utf-8-sig", newline="").read()


def write(p, t):
    io.open(p, "w", encoding="utf-8-sig", newline="").write(t)


def backup(p, stamp):
    shutil.copy2(p, p + ".bak_" + stamp)


def eol_of(t):
    return "\r\n" if "\r\n" in t else "\n"


stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
wrote = []

# ---- 1. landed_titles ----
lp = MOD + r"\common\landed_titles\00_landed_titles.txt"
lt = read(lp)
cm = re.search(r"(?ms)^(\t+)c_holstein = \{.*?^\1\}", lt)
assert cm, "c_holstein block not found"
indent = cm.group(1)
rm = re.search(r"(?ms)^" + indent + r"\tb_rendsburg = \{.*?^" + indent + r"\t\}\r?\n", cm.group(0))
assert rm, "b_rendsburg not found in c_holstein"
rblock = rm.group(0)
km = re.search(r"(?ms)^" + indent + r"\tb_kiel = \{", cm.group(0))
assert km, "b_kiel not found in c_holstein"
newblk = cm.group(0).replace(rblock, "", 1)
ki = newblk.find(km.group(0))
newblk = newblk[:ki] + rblock + newblk[ki:]
lt2 = lt[:cm.start()] + newblk + lt[cm.end():]
first_bar = re.search(r"(?m)^" + indent + r"\t(b_[A-Za-z0-9_]+) = \{", newblk)
if first_bar and first_bar.group(1) == "b_rendsburg" and lt2 == lt:
    print("landed_titles: b_rendsburg already the first barony, skipped")
else:
    assert lt2 != lt and lt2.count("{") == lt2.count("}")
    # b_rendsburg must now be the first barony of the block
    assert first_bar and first_bar.group(1) == "b_rendsburg", "capital reorder failed"
    backup(lp, stamp)
    write(lp, lt2)
    wrote.append("00_landed_titles.txt")
    print("landed_titles: b_rendsburg is now the first barony of c_holstein")

# ---- 2. titles ----
tp = MOD + r"\history\titles\zz_eu5_titles.txt"
t = read(tp)
eol = eol_of(t)
cm = re.search(r"(?ms)^c_holstein = \{.*?^\}", t)
assert cm, "c_holstein history block not found"
em = re.search(r"(?ms)^\t1337\.1\.1 = \{.*?^\t\}", cm.group(0))
assert em, "c_holstein has no 1337.1.1 entry"
seg = em.group(0)
seg2 = seg.replace("holder = " + JOHANN, "holder = " + GERHARD)
seg2 = re.sub(r"(\t\tliege = )e_hre(\r?\n)", r"\g<1>k_eu5_dan\2", seg2, count=1)
assert "holder = " + GERHARD in seg2 and "liege = k_eu5_dan" in seg2, "c_holstein rewrite failed"
blk2 = cm.group(0)[:em.start()] + seg2 + cm.group(0)[em.end():]
t2 = t[:cm.start()] + blk2 + t[cm.end():]

assert not re.search(r"(?m)^b_kiel = \{", t2), "b_kiel block already exists?"
marks = [(m.group(1), m.start()) for m in re.finditer(r"(?m)^(b_[A-Za-z0-9_]+) = \{", t2)]
block = eol.join(["b_kiel = {", "\t1337.1.1 = {",
                  "\t\tholder = " + JOHANN, "\t}", "}", ""])
after = sorted(k for k, _ in marks if k > "b_kiel")
at = next(m[1] for m in marks if m[0] == after[0]) if after else len(t2)
t3 = t2[:at] + block + t2[at:]
assert t3.count("{") == t3.count("}")
backup(tp, stamp)
write(tp, t3)
wrote.append("zz_eu5_titles.txt")
print("titles: c_holstein -> Gerhard / liege k_eu5_dan; b_kiel block inserted for Johann")

# ---- 3. regents ----
rp = MOD + r"\history\characters\zz_eu5_regents.txt"
r = read(rp)
if re.search(r"(?m)^dan_valdemar_atterdag = \{", r):
    print("regents: DAN block already there, skipped")
else:
    eol = eol_of(r)
    nb = eol.join(["# regent of DAN", "dan_valdemar_atterdag = {",
                   "\t1337.1.1 = {", "\t\teffect = {",
                   "\t\t\tdesignate_diarch = " + GERHARD,
                   "\t\t\ttry_start_diarchy = regency",
                   "\t\t}", "\t}", "}", ""])
    # insert alphabetically: before the first block key greater than dan_
    keys = [(m.group(1), m.start()) for m in re.finditer(r"(?m)^# regent of .*\r?\n([A-Za-z0-9_]+) = \{", r)]
    later = [k for k, _ in keys if k > "dan_valdemar_atterdag"]
    if later:
        first = min(later)
        at = next(s for k, s in keys if k == first) - len("# regent of " + first) - len(eol) - len(eol)
        # simpler: find the comment line start for that block
        cm = re.search(r"(?ms)^# regent of [^\n]*\r?\n" + re.escape(first) + r" = \{", r)
        at = cm.start()
    else:
        at = len(r)
    r2 = r[:at] + nb + eol + r[at:]
    assert r2.count("{") == r2.count("}")
    backup(rp, stamp)
    write(rp, r2)
    wrote.append("zz_eu5_regents.txt")
    print("regents: dan_valdemar_atterdag -> designate_diarch", GERHARD)

print("written:", ", ".join(wrote))
