# -*- coding: utf-8 -*-
"""Denmark/Holstein surgical patch (user decision 2026-10-20):

1. landed_titles: b_rendsburg becomes the first barony of c_holstein (capital).
2. zz_eu5_titles.txt:
   - c_holstein 1337.4.1: holder -> Gerhard III (HTR), liege -> k_eu5_dan
     (Holstein becomes Denmark's vassal; the HRE liege line on the 1337.4.1
     entry only is replaced -- historical entries untouched).
   - b_kiel: new block, holder Johann III of Holstein-Kiel (demoted to baron).

This script writes special counties and nothing else. The Danish regency itself --
Valdemar with Gerhard as his diarch from 1332.8.2, swing and all -- lives in
zz_eu5_diarchy_regencies.txt and is not touched here: dan_valdemar_atterdag is
already a character in zz_eu5_characters.txt, and a second block naming him in
zz_eu5_regents.txt would only be a duplicate definition of the same man.

Provinces 608/611 are already castle_holding -- nothing to do there.

3. HRE namesake seats (user decision 2026-10-22, written here with the rest of
   the manual arrangements): inside the Holy Roman Empire a county is led from
   the town it is named for, whoever holds it. The barony whose name is the
   county's own name -- or a piece of it -- becomes the county's first barony,
   and the county's 1337.4.1 holder follows it there. A county counts as inside
   the Empire only when every location in it is held by an HRE member. Five
   counties move:
     c_chrudimsko        caslav -> chrudim           (BOH, holder unchanged)
     c_hanover           hildesheim -> hanover       (HDH -> BRU, theocracy -> feudal)
     c_lippe             soest -> paderborn          (KOL -> PDB)
     c_luneburger_heide  dannenberg -> luneburg      (LUN, holder unchanged)
     c_neuchatel         delemont -> basel           (BAS, holder unchanged; the
                          county reads 巴塞尔 in EU5's localization, so basel is
                          its namesake, not neuchatel)
   c_lippe is the one county rank_state had already picked (soest), so
   RANK_STATE.json is corrected here to keep the pick and the tree in agreement;
   the five counties and their new seats also join eu5_reassign_keep.json.
   NOTE: a later full `_capital_correct.py --barony-order rank_state` run
   re-derives RANK_STATE.json from the rule and would hand c_lippe back to
   soest -- re-run this script after any such run.

4. Armagh seat (user decision 2026-11-01). Outside the HRE, so rule 3 never
   reaches it: EU5's Armagh holds c_oriel and its capital is the town armagh,
   but the county was still led from b_monaghan -- Oriel's own seat, left over
   from when OIL held the county. b_armagh moves to the front of c_oriel, and
   c_oriel + b_armagh join eu5_reassign_keep.json.

5. Elector seats (user decision 2026-11-01). The two secular electors whose county
   was led from the wrong town: c_flaming b_schweinitz -> b_wittenberg
   (Saxe-Wittenberg, d_upper_saxony) and c_palatinate b_kaiserslautern ->
   b_heidelberg (Palatine, d_upper_rhine). Both counties and both new seats join
   eu5_reassign_keep.json.

6. Romagna seat (user decision 2026-11-10). RAV (Ravenna) is a one-location
   country inside the Romagna province; RIM (Rimini) holds the rest of it.
   Lock b_ravenna as c_romagna's first barony and seat Ravenna's ruler on the
   county. The Malatesta, who held c_romagna from b_rimini, drop to that barony
   -- the same shape as the Holstein/Kiel split in section 1. The EU5 title map
   is rebound to match: RAV -> c_romagna, RIM -> b_rimini. All three keys join
   eu5_reassign_keep.json. NOTE: _export_title_map.py derives these two rows
   from seat/barony_of, so a full export writes the old binding back -- re-run
   this script after any such export.

7. Hanseatic seats (user decision 2026-11-10). The same standard workflow, for
   the two Free Cities: HAM owns only the location hamburg in c_elbmarch, BRM
   owns only bremen in c_wesermarch. Lock each town as its county's first barony,
   seat its ruler on the county, rebind the title map's country rows, and add
   every touched key to eu5_reassign_keep.json:
     c_elbmarch    b_harburg   -> b_hamburg     LUN -> HAM
     c_wesermarch  b_oldenburg -> b_bremen      OLD -> BRM
   LUN is a duchy (d_eu5_lun) holding eleven locations, so losing c_elbmarch
   leaves it plenty of land: its country row stays on the duchy and no b_harburg
   block is created. OLD holds only the three locations of c_wesermarch, so its
   country row is rebound to b_oldenburg and that barony takes its holder --
   exactly the RIM/b_rimini case in section 6. Both new rulers are republics,
   so the counties' 1337.4.1 government line changes with the holder.

8. Capital seats (user decision 2026-11-14). Five EU5 national capitals that are
   also flavour locations (except stuttgart) but were not their county's first
   barony, so the county was led from some other town:
     c_gamrun          b_gamrun      -> b_hormuz     ORM (holder already ORM's ruler)
     c_malmohus        b_helsingborg -> b_lund       SKE (was an ecclesiastical holder)
     c_kosovo          b_peja        -> b_prizren    SER (was a local Serbian lord)
     c_main_franconia  b_hassfurt    -> b_wurzburg   WBG (holder already WBG's ruler)
     c_neckar          b_horb        -> b_stuttgart  WUR (Hohenberg held the county;
                                        "霍恩贝格狗运占了第一个地点把符腾堡首府斯图加特抢走了")
   Where the 1337.4.1 holder was not already the capital country's ruler, it and
   the government line follow the new seat. No barony demotions and no title-map
   rebinds here: all five countries are duchy/kingdom/county rank whose country
   rows already sit on d_/k_/c_ titles rather than on b_<capital>, and the
   displaced Hohenberg still holds c_swabian_alb -- the same "LUN has plenty of
   land" call from section 7. county/barony rows likewise stay as they are.

9. Melk seat (user decision 2026-11-14). c_ober_dem_wienerwald was led from
   b_amstetten: Passau holds St. Polten as an outlying town, and rank_state's
   enclave rule handed the county to Austria, picking the town of the winning
   power by population alone. Once rank_state prefers EU5's city/town rank first
   (see _capital_correct.py pick_town), that same pick is b_melk. Both amstetten
   and melk are Austrian and the county's 1337.4.1 holder is already Habsburg
   Austria (hab_albrecht_ii_habsburg, feudal_government), so no holder,
   government or eu5_ck3_title_map.csv row changes. Lock b_melk as the first
   barony in both trees, write melk into RANK_STATE.json, and add c_ober_dem_
   wienerwald + b_melk to eu5_reassign_keep.json. Re-run this script after any
   full export or --barony-order rank_state run, which re-derives those picks.
"""
import csv, datetime, io, json, os, re, shutil
from collections import defaultdict

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
assert em, "c_holstein has no 1337.4.1 entry"
seg = em.group(0)
seg2 = seg.replace("holder = " + JOHANN, "holder = " + GERHARD)
seg2 = re.sub(r"(\t\tliege = )e_hre(\r?\n)", r"\g<1>k_eu5_dan\2", seg2, count=1)
if not ("holder = " + GERHARD in seg2 and "liege = k_eu5_dan" in seg2):
    # Already patched on an earlier run: the holder now lives in a separate
    # 1337.4.1 block and the 1337.1.1 liege line has since been hand-edited
    # (k_denmark). Never rewrite that line -- leave the whole file untouched.
    assert ("holder = " + GERHARD in cm.group(0)
            and re.search(r"(?m)^b_kiel = \{", t)), "c_holstein rewrite failed"
    seg2 = seg
blk2 = cm.group(0)[:em.start()] + seg2 + cm.group(0)[em.end():]
t2 = t[:cm.start()] + blk2 + t[cm.end():]

if re.search(r"(?m)^b_kiel = \{", t2):
    # already patched on an earlier run: keep whatever the rewrite above produced
    t3 = t2
else:
    marks = [(m.group(1), m.start()) for m in re.finditer(r"(?m)^(b_[A-Za-z0-9_]+) = \{", t2)]
    block = eol.join(["b_kiel = {", "\t1337.4.1 = {",
                      "\t\tholder = " + JOHANN, "\t}", "}", ""])
    after = sorted(k for k, _ in marks if k > "b_kiel")
    at = next(m[1] for m in marks if m[0] == after[0]) if after else len(t2)
    t3 = t2[:at] + block + t2[at:]
assert t3.count("{") == t3.count("}")
if t3 != t:
    backup(tp, stamp)
    write(tp, t3)
    wrote.append("zz_eu5_titles.txt")
    print("titles: c_holstein -> Gerhard / liege k_eu5_dan; b_kiel block for Johann")
else:
    print("titles: c_holstein already Gerhard / liege k_eu5_dan and b_kiel already there, skipped")

# ---- 3. HRE namesake seats ----
EXPORT = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
GAME = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"
LT_MOD = MOD + r"\common\landed_titles\00_landed_titles.txt"
LT_EXP = os.path.join(EXPORT, "landed_titles", "00_eu5_landed_titles.txt")
# EU5 government -> the government line the export writes for a county of that kind.
GOV_OF = {"monarchy": "feudal_government", "theocracy": "theocracy_government",
          "republic": "republic_government", "tribal": "tribal_government"}


def write_raw(p, text, bom, crlf):
    """Write text back with the byte shape it came in: BOM and CRLF as found."""
    if crlf:
        text = text.replace("\r\n", "\n").replace("\n", "\r\n")
    io.open(p, "wb").write((b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8"))


def hre_targets():
    """(county, barony) for every county wholly inside the HRE that has a namesake town.

    Wholly inside: every location of the county is held by an HRE member, read from
    the political export's organization list and ownership. The namesake test reads
    EU5's own localization -- the county 巴塞尔 and the town basel are both 巴塞尔,
    which no spelling of the keys says -- and takes the town whose name is the
    county's whole name or a piece of it, a one-character piece not counting.
    """
    pol = json.load(io.open(os.path.join(EXPORT, "eu5_politics.json"), encoding="utf-8"))
    hre = set()
    for o in pol["organizations"]:
        if o.get("type") == "hre":
            hre = set(o["members"])
    holders = {}
    for tag, cv in pol["countries"].items():
        for cat, ls in (cv.get("holds") or {}).items():
            if cat.startswith("own_"):
                for l in ls:
                    holders[l] = tag
    mp = json.load(io.open(os.path.join(EXPORT, "mapping.json"), encoding="utf-8"))
    county_locs = defaultdict(list)
    for l in mp["locations"]:
        c = l.get("county")
        if c and l.get("kind") not in ("sea", "wasteland"):
            county_locs[c].append(l["name"])

    root = os.path.join(GAME, "main_menu", "localization", "simp_chinese")
    line = re.compile(r'^[ \t]*([A-Za-z0-9_]+)[ \t]*:[ \t]*\d*[ \t]*"(.*)"[ \t]*$', re.M)
    loc_names, prov_names = {}, {}
    for path, sink, drop in (
            (os.path.join(root, "location_names", "location_names_l_simp_chinese.yml"), loc_names, None),
            (os.path.join(root, "province_names_l_simp_chinese.yml"), prov_names, "_province")):
        for m in line.finditer(io.open(path, encoding="utf-8-sig", errors="replace").read()):
            k = m.group(1)
            if drop and k.endswith(drop):
                k = k[:-len(drop)]
            sink[k.lower()] = m.group(2)

    # definitions order, for the rare county with two namesake towns
    dtext = re.sub(r"#[^\n]*", "", io.open(
        os.path.join(GAME, "in_game", "map_data", "definitions.txt"),
        encoding="utf-8", errors="replace").read())
    order = {}
    for m in re.finditer(r"(?m)^\s*([a-z0-9_]+)_province\s*=\s*\{([^}]*)\}", dtext):
        order[m.group(1)] = m.group(2).split()

    def piece(name, whole):
        return name == whole or (len(name) >= 2 and name in whole)

    out = []
    for c, locs in sorted(county_locs.items()):
        hs = [holders.get(l) for l in locs]
        if not locs or any(t is None or t not in hre for t in hs):
            continue
        cname = prov_names.get(c)
        if not cname:
            continue
        hits = [l for l in locs if loc_names.get(l) and piece(loc_names[l], cname)]
        if not hits:
            continue
        seq = order.get(c, locs)
        out.append((c, min(hits, key=lambda l: seq.index(l) if l in seq else len(seq))))
    return out, holders, pol["countries"]


def tree_first_barony(path):
    """county -> the first barony of its block, for the whole file."""
    raw = io.open(path, "rb").read()
    lines = raw.decode("utf-8-sig").replace("\r\n", "\n").split("\n")
    re_c = re.compile(r"^(\s*)c_([A-Za-z0-9_]+)\s*=\s*\{$")
    re_b = re.compile(r"^(\s*)b_([A-Za-z0-9_]+)\s*=\s*\{$")
    out, i, n = {}, 0, len(lines)
    while i < n:
        m = re_c.match(lines[i])
        if not m:
            i += 1
            continue
        depth, j = 0, i
        while j < n:
            depth += lines[j].count("{") - lines[j].count("}")
            j += 1
            if depth == 0:
                break
        bm = None
        for x in lines[i + 1:j]:
            mm = re_b.match(x)
            if mm:
                bm = mm
                break
        if bm:
            out[m.group(2).lower()] = bm.group(2).lower()
        i = j
    return out


def reorder_seat(path, county, barony):
    """Move b_<barony> to the front of c_<county>'s baronies, in place. True when it wrote."""
    raw = io.open(path, "rb").read()
    bom = raw[:3] == b"\xef\xbb\xbf"
    crlf = b"\r\n" in raw
    orig = raw.decode("utf-8-sig")
    lines = orig.replace("\r\n", "\n").split("\n")
    re_c = re.compile(r"^(\s*)c_([A-Za-z0-9_]+)\s*=\s*\{$")
    re_b = re.compile(r"^(\s*)b_([A-Za-z0-9_]+)\s*=\s*\{$")
    out, i, n, moved = [], 0, len(lines), False
    while i < n:
        m = re_c.match(lines[i])
        if not m or m.group(2).lower() != county:
            out.append(lines[i]); i += 1; continue
        depth, j = 0, i
        while j < n:
            depth += lines[j].count("{") - lines[j].count("}")
            j += 1
            if depth == 0:
                break
        block = lines[i:j]
        segs, k, bd, cur = [], 1, 0, None
        while k < len(block):
            bm = re_b.match(block[k])
            if bm and bd == 0:
                if cur is not None:
                    segs.append((cur[0], cur[1], k))
                cur = (bm.group(2).lower(), k)
            bd += block[k].count("{") - block[k].count("}")
            k += 1
            if cur is not None and bd == 0 and k > cur[1]:
                segs.append((cur[0], cur[1], k)); cur = None
        names = [s[0] for s in segs]
        assert names, "c_%s has no baronies in %s" % (county, path)
        assert barony in names, "b_%s is not in c_%s (%s)" % (barony, county, path)
        if names[0] != barony:
            pre = block[1:segs[0][1]]
            texts = {s[0]: block[s[1]:s[2]] for s in segs}
            new_block = [block[0]] + pre
            for nm in [barony] + [x for x in names if x != barony]:
                new_block.extend(texts[nm])
            new_block.extend(block[segs[-1][2]:])
            out.extend(new_block)
            moved = True
        else:
            out.extend(block)
        i = j
    if not moved:
        print("  %s: b_%s already leads c_%s, skipped" % (os.path.basename(path), barony, county))
        return False
    patched = "\n".join(out)
    if patched == orig.replace("\r\n", "\n"):
        return False
    backup(path, stamp)
    write_raw(path, patched, bom, crlf)
    return True


def move_county_holder(county, new_char, new_gov):
    """The county's 1337.4.1 entry follows the seat: holder, and the government with it.

    The character decides it: the county's 1337 holder is the seat-holder's ruler already --
    c_alessandria's is eu5_regent_asd, ASD's own ruler, whose id carries no tag to read --
    and then there is nothing to do."""
    tp = MOD + r"\history\titles\zz_eu5_titles.txt"
    t = read(tp)
    cm = re.search(r"(?ms)^c_%s = \{.*?^\}" % county, t)
    assert cm, "c_%s history block not found" % county
    em = re.search(r"(?ms)^\t1337\.1\.1 = \{.*?^\t\}", cm.group(0))
    assert em, "c_%s has no 1337.4.1 entry" % county
    seg = em.group(0)
    old = re.search(r"holder = (\w+)", seg)
    assert old, "c_%s 1337 entry has no holder" % county
    if old.group(1) == new_char:
        print("  zz_eu5_titles: c_%s 1337 holder already %s, skipped" % (county, new_char))
        return False
    seg2 = seg.replace("holder = " + old.group(1), "holder = " + new_char, 1)
    gm = re.search(r"government = (\w+)", seg2)
    if gm and new_gov and gm.group(1) != new_gov:
        seg2 = seg2.replace("government = " + gm.group(1), "government = " + new_gov, 1)
    blk2 = cm.group(0)[:em.start()] + seg2 + cm.group(0)[em.end():]
    t2 = t[:cm.start()] + blk2 + t[cm.end():]
    assert t2 != t and t2.count("{") == t2.count("}")
    backup(tp, stamp)
    write(tp, t2)
    print("  zz_eu5_titles: c_%s 1337 holder %s -> %s" % (county, old.group(1), new_char))
    return True


def correct_rank_state(picks):
    """RANK_STATE.json carries the rule's picks; c_lippe's soest pick becomes paderborn here."""
    p = os.path.join(EXPORT, "RANK_STATE.json")
    raw = io.open(p, encoding="utf-8").read()
    data = json.loads(raw)
    for c, b in picks:
        data["counties"]["c_" + c] = b
    new = json.dumps(data, indent=1, sort_keys=True, ensure_ascii=False)
    if raw.endswith("\n"):
        new += "\n"
    if raw == new:
        print("  RANK_STATE.json already carries the namesake picks, skipped")
        return False
    backup(p, stamp)
    io.open(p, "w", encoding="utf-8", newline="").write(new)
    return True


def extend_keep(titles):
    """The touched counties and their new seats join the reassign keep-list."""
    kp = MOD + r"\gen_debug\eu5_reassign_keep.json"
    raw = io.open(kp, "rb").read()
    bom = raw[:3] == b"\xef\xbb\xbf"
    crlf = b"\r\n" in raw
    keep = json.loads(raw.decode("utf-8-sig"))
    text = json.dumps(sorted(set(keep) | set(titles)), indent=2, ensure_ascii=False)
    if crlf:
        text = text.replace("\n", "\r\n")
    if raw.endswith(b"\r\n"):
        text += "\r\n"
    elif raw.endswith(b"\n"):
        text += "\n"
    blob = (b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8")
    if blob == raw:
        print("  eu5_reassign_keep.json already lists them, skipped")
        return False
    backup(kp, stamp)
    io.open(kp, "wb").write(blob)
    return True


print("HRE namesake seats:")
targets, holders, countries = hre_targets()
first = tree_first_barony(LT_MOD)
movers = [(c, b) for c, b in targets if first.get(c) != b]
print("  %d HRE counties have a namesake town, %d of them already led from it, %d to move"
      % (len(targets), len(targets) - len(movers), len(movers)))
picks, keep = [], []
for c, b in movers:
    old_seat = first.get(c)
    r1 = reorder_seat(LT_MOD, c, b)
    r2 = reorder_seat(LT_EXP, c, b)
    if r1 or r2:
        wrote.append("00_landed_titles.txt + 00_eu5_landed_titles.txt (c_%s)" % c)
    tag = holders[b]
    cv = countries[tag]
    move_county_holder(c, cv["ruler"], GOV_OF.get(cv.get("government")))
    picks.append((c, b))
    keep += ["c_" + c, "b_" + b]
    print("  c_%s: %s -> %s (%s)" % (c, old_seat, b, tag))
if picks:
    if correct_rank_state(picks):
        wrote.append("RANK_STATE.json")
    if extend_keep(keep):
        wrote.append("eu5_reassign_keep.json")

# ---- 4. Armagh seat (user decision 2026-11-01) ----
# Outside the HRE, so the namesake rule above never reaches it: EU5's Armagh holds
# c_oriel and its capital is the town armagh, but the county is still led from
# b_monaghan -- Oriel's own seat, left over from when OIL held the county. The
# archbishop's town takes the lead, and both keys join the reassign keep-list so a
# later --barony-order rank_state run does not hand the seat back to monaghan.
print("Armagh seat:")
for path in (LT_MOD, LT_EXP):
    if reorder_seat(path, "oriel", "armagh"):
        wrote.append("%s (c_oriel)" % os.path.basename(path))
if extend_keep(["c_oriel", "b_armagh"]):
    wrote.append("eu5_reassign_keep.json")

# ---- 5. Elector seats (user decision 2026-11-01) ----
# The two secular electors whose county was led from the wrong town:
#   c_flaming      b_schweinitz -> b_wittenberg   (Saxe-Wittenberg, d_upper_saxony)
#   c_palatinate   b_kaiserslautern -> b_heidelberg (Palatine, d_upper_rhine)
# Wittenberg and Heidelberg are the towns both the EU5 country and the CK3 duchy are
# read through. Both counties and both new seats join eu5_reassign_keep.json.
print("Elector seats:")
for county, barony in (("flaming", "wittenberg"), ("palatinate", "heidelberg")):
    for path in (LT_MOD, LT_EXP):
        if reorder_seat(path, county, barony):
            wrote.append("%s (c_%s)" % (os.path.basename(path), county))
if extend_keep(["c_flaming", "b_wittenberg", "c_palatinate", "b_heidelberg"]):
    wrote.append("eu5_reassign_keep.json")

# ---- 6. Romagna seat (user decision 2026-11-10) ----
# RAV owns only the location ravenna inside c_romagna; RIM owns the rest. Ravenna's
# ruler takes the county and its seat, Rimini's ruler is demoted to b_rimini.
RAV_RULER = "rav_ostasio_i_polenta"
RIM_RULER = "rim_malatesta_iii_malatesta"


def romagna_county_holder():
    """c_romagna 1337.4.1 -> RAV's ruler; give RIM's ruler a b_rimini barony."""
    p = MOD + r"\history\titles\zz_eu5_titles.txt"
    t = read(p)
    eol = eol_of(t)
    flat = t.replace("\r\n", "\n")
    cm = re.search(r"(?ms)^c_romagna = \{.*?^\}", flat)
    assert cm, "c_romagna history block not found"
    blk = cm.group(0)
    segs = [s for s in re.finditer(r"(?ms)^\t1337\.4\.1 = \{.*?^\t\}", blk)
            if "holder =" in s.group(0)]
    assert len(segs) == 1, "c_romagna: expected one 1337.4.1 holder entry"
    seg = segs[0].group(0)
    changed = False
    if "holder = " + RAV_RULER not in seg:
        old = re.search(r"holder = (\w+)", seg).group(1)
        seg2 = seg.replace("holder = " + old, "holder = " + RAV_RULER, 1)
        assert "government = republic_government" in seg2  # RAV is a republic too
        blk2 = blk[:segs[0].start()] + seg2 + blk[segs[0].end():]
        flat = flat[:cm.start()] + blk2 + flat[cm.end():]
        print("  zz_eu5_titles: c_romagna holder %s -> %s" % (old, RAV_RULER))
        changed = True
    if not re.search(r"(?m)^b_rimini = \{", flat):
        marks = [(m.group(1), m.start()) for m in
                 re.finditer(r"(?m)^(b_[A-Za-z0-9_]+) = \{", flat)]
        after = sorted(k for k, _ in marks if k > "b_rimini")
        at = next(s for k, s in marks if k == after[0]) if after else len(flat)
        block = "\n".join(["b_rimini = {", "\t1337.4.1 = {",
                           "\t\tholder = " + RIM_RULER, "\t}", "}", "", ""])
        flat = flat[:at] + block + flat[at:]  # eol is applied once, at the end
        print("  zz_eu5_titles: new b_rimini block for " + RIM_RULER)
        changed = True
    if changed:
        assert flat.count("{") == flat.count("}"), "brace mismatch in zz_eu5_titles"
        write(p, flat.replace("\n", eol))
    return changed


def romagna_title_map():
    """Rebind the two country rows of eu5_ck3_title_map.csv: RAV -> c_romagna, RIM -> b_rimini."""
    p = MOD + r"\gen_debug\eu5_ck3_title_map.csv"
    raw = io.open(p, "rb").read()
    bom = raw[:3] == b"\xef\xbb\xbf"
    crlf = b"\r\n" in raw
    lines = raw.decode("utf-8-sig").replace("\r\n", "\n").split("\n")
    new = {
        "RAV": {7: "c_romagna", 8: "c", 9: "Rōmanía", 10: "罗马涅",
                14: "republic_government",
                16: "country-below-county-rank: its land is its counties"},
        "RIM": {7: "b_rimini", 8: "b", 9: "Rimine", 10: "里米尼", 14: "",
                16: "country-below-county-rank: its land is a barony"},
    }
    old = {"RAV": "b_ravenna", "RIM": "c_romagna"}
    hit = 0
    for i, ln in enumerate(lines):
        for tag, repl in new.items():
            if not ln.startswith("country," + tag + ","):
                continue
            f = ln.split(",")
            assert len(f) == 17, "title_map line %d has %d columns" % (i + 1, len(f))
            if f[7] == repl[7]:
                continue
            assert f[7] == old[tag], "title_map %s expected %s, found %s" % (tag, old[tag], f[7])
            for idx, val in repl.items():
                f[idx] = val
            lines[i] = ",".join(f)
            hit += 1
    if not hit:
        print("  eu5_ck3_title_map.csv already rebound, skipped")
        return False
    text = "\n".join(lines)
    if crlf:
        text = text.replace("\n", "\r\n")
    io.open(p, "wb").write((b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8"))
    print("  eu5_ck3_title_map.csv: %d rows rebound (RAV -> c_romagna, RIM -> b_rimini)" % hit)
    return True


print("Romagna seat:")
for path in (LT_MOD, LT_EXP):
    if reorder_seat(path, "romagna", "ravenna"):
        wrote.append("%s (c_romagna)" % os.path.basename(path))
if romagna_county_holder():
    wrote.append("zz_eu5_titles.txt (c_romagna / b_rimini)")
if romagna_title_map():
    wrote.append("eu5_ck3_title_map.csv (RAV / RIM)")
if extend_keep(["c_romagna", "b_ravenna", "b_rimini"]):
    wrote.append("eu5_reassign_keep.json")

# ---- 7. Hanseatic seats (user decision 2026-11-10) ----
# HAM and BRM each own a single location inside their county. LUN keeps its
# duchy, so only c_elbmarch's holder changes; OLD has nothing outside
# c_wesermarch, so it is demoted to b_oldenburg like RIM in section 6.
HANSE = [
    dict(county="elbmarch", seat="hamburg", old_seat="harburg",
         new_tag="HAM", new_ruler="eu5_regent_ham", old_ruler="lun_otto_iii_luneburg",
         old_tag=None, old_en="Harburg", old_zh="哈尔堡",
         county_en="Elbe Marshes", county_zh="易北河沼泽"),
    dict(county="wesermarch", seat="bremen", old_seat="oldenburg",
         new_tag="BRM", new_ruler="eu5_regent_brm", old_ruler="old_johann_iii_oldenburg",
         old_tag="OLD", old_en="Oldenburgo", old_zh="奥尔登堡",
         county_en="Weser Marshes", county_zh="威悉河沼泽"),
]


def seat_rebind_history(spec):
    """c_<county> 1337.4.1 holder/government -> the new seat's ruler.

    The old holder only drops to b_<old_seat> when it has no other land, which
    is what old_tag marks."""
    p = MOD + r"\history\titles\zz_eu5_titles.txt"
    t = read(p)
    eol = eol_of(t)
    flat = t.replace("\r\n", "\n")
    county = spec["county"]
    cm = re.search(r"(?ms)^c_%s = \{.*?^\}" % county, flat)
    assert cm, "c_%s history block not found" % county
    blk = cm.group(0)
    segs = [s for s in re.finditer(r"(?ms)^\t1337\.4\.1 = \{.*?^\t\}", blk)
            if "holder =" in s.group(0)]
    assert len(segs) == 1, "c_%s: expected one 1337.4.1 holder entry" % county
    seg = segs[0].group(0)
    changed = False
    if "holder = " + spec["new_ruler"] not in seg:
        old = re.search(r"holder = (\w+)", seg).group(1)
        assert old == spec["old_ruler"], "c_%s holder %s, expected %s" % (
            county, old, spec["old_ruler"])
        seg2 = seg.replace("holder = " + old, "holder = " + spec["new_ruler"], 1)
        gm = re.search(r"government = (\w+)", seg2)
        assert gm, "c_%s 1337 entry has no government" % county
        seg2 = seg2.replace("government = " + gm.group(1),
                            "government = republic_government", 1)
        blk2 = blk[:segs[0].start()] + seg2 + blk[segs[0].end():]
        flat = flat[:cm.start()] + blk2 + flat[cm.end():]
        print("  zz_eu5_titles: c_%s holder %s -> %s, republic" % (
            county, old, spec["new_ruler"]))
        changed = True
    if spec["old_tag"]:
        key = "b_" + spec["old_seat"]
        if not re.search(r"(?m)^" + key + r" = \{", flat):
            marks = [(m.group(1), m.start()) for m in
                     re.finditer(r"(?m)^(b_[A-Za-z0-9_]+) = \{", flat)]
            after = sorted(k for k, _ in marks if k > key)
            at = next(s for k, s in marks if k == after[0]) if after else len(flat)
            block = "\n".join([key + " = {", "\t1337.4.1 = {",
                               "\t\tholder = " + spec["old_ruler"], "\t}", "}", "", ""])
            flat = flat[:at] + block + flat[at:]
            print("  zz_eu5_titles: new %s block for %s" % (key, spec["old_ruler"]))
            changed = True
    if changed:
        assert flat.count("{") == flat.count("}"), "brace mismatch in zz_eu5_titles"
        write(p, flat.replace("\n", eol))
    return changed


def csv_cell(x):
    return ('"' + x.replace('"', '""') + '"') if ("," in x or '"' in x) else x


def seat_rebind_title_map(spec):
    """country rows: new_tag -> c_<county>; old_tag -> b_<old_seat> when applicable."""
    p = MOD + r"\gen_debug\eu5_ck3_title_map.csv"
    raw = io.open(p, "rb").read()
    bom = raw[:3] == b"\xef\xbb\xbf"
    crlf = b"\r\n" in raw
    lines = raw.decode("utf-8-sig").replace("\r\n", "\n").split("\n")
    new = {
        spec["new_tag"]: {7: "c_" + spec["county"], 8: "c",
                          9: spec["county_en"], 10: spec["county_zh"],
                          14: "republic_government",
                          16: "country-below-county-rank: its land is its counties"},
    }
    old = {spec["new_tag"]: "b_" + spec["seat"]}
    if spec["old_tag"]:
        new[spec["old_tag"]] = {7: "b_" + spec["old_seat"], 8: "b",
                                9: spec["old_en"], 10: spec["old_zh"], 14: "",
                                16: "country-below-county-rank: its land is a barony"}
        old[spec["old_tag"]] = "c_" + spec["county"]
    hit = 0
    for i, ln in enumerate(lines):
        for tag, repl in new.items():
            if not ln.startswith("country," + tag + ","):
                continue
            f = next(csv.reader([ln]))
            assert len(f) == 17, "title_map line %d has %d columns" % (i + 1, len(f))
            if f[7] == repl[7]:
                continue
            assert f[7] == old[tag], "title_map %s expected %s, found %s" % (
                tag, old[tag], f[7])
            for idx, val in repl.items():
                f[idx] = val
            lines[i] = ",".join(csv_cell(x) for x in f)
            hit += 1
    if not hit:
        print("  eu5_ck3_title_map.csv already rebound for c_%s, skipped" % spec["county"])
        return False
    text = "\n".join(lines)
    if crlf:
        text = text.replace("\n", "\r\n")
    io.open(p, "wb").write((b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8"))
    print("  eu5_ck3_title_map.csv: %d rows rebound for c_%s" % (hit, spec["county"]))
    return True


print("Hanseatic seats:")
hanse_keep = []
for spec in HANSE:
    for path in (LT_MOD, LT_EXP):
        if reorder_seat(path, spec["county"], spec["seat"]):
            wrote.append("%s (c_%s)" % (os.path.basename(path), spec["county"]))
    if seat_rebind_history(spec):
        wrote.append("zz_eu5_titles.txt (c_%s)" % spec["county"])
    if seat_rebind_title_map(spec):
        wrote.append("eu5_ck3_title_map.csv (c_%s)" % spec["county"])
    hanse_keep += ["c_" + spec["county"], "b_" + spec["seat"]]
    if spec["old_tag"]:
        hanse_keep.append("b_" + spec["old_seat"])
if extend_keep(hanse_keep):
    wrote.append("eu5_reassign_keep.json")

# ---- 8. Capital seats (user decision 2026-11-14) ----
# Five capitals whose county was led from another town. ORM and WBG already hold
# their county, so only the barony order changes there; SKE, SER and WUR also
# take over the 1337.4.1 holder/government line.
CAPITAL_SEATS = [
    dict(county="gamrun",         seat="hormuz",   ruler="orm_kut_al_din_tahamtan",
         gov="clan_government"),
    dict(county="malmohus",       seat="lund",     ruler="swe_magnus_eriksson",
         gov="feudal_government"),
    dict(county="kosovo",         seat="prizren",  ruler="ser_stefan_dusan",
         gov="feudal_government"),
    dict(county="main_franconia", seat="wurzburg", ruler="wbg_otto_ii_von_wolfskeel",
         gov="ecclesiastical_government"),
    dict(county="neckar",         seat="stuttgart", ruler="wur_ulrich_iii_wurttemberg",
         gov="feudal_government"),
]


def capital_seat_history(spec):
    """1337.4.1 holder/government follow the new seat when they are not already right."""
    p = MOD + r"\history\titles\zz_eu5_titles.txt"
    t = read(p)
    eol = eol_of(t)
    flat = t.replace("\r\n", "\n")
    county = spec["county"]
    cm = re.search(r"(?ms)^c_%s = \{.*?^\}" % re.escape(county), flat)
    assert cm, "c_%s history block not found" % county
    blk = cm.group(0)
    segs = [s for s in re.finditer(r"(?ms)^\t1337\.4\.1 = \{.*?^\t\}", blk)
            if "holder =" in s.group(0)]
    assert len(segs) == 1, "c_%s: expected one 1337.4.1 holder entry" % county
    s = segs[0]
    seg = s.group(0)
    if "holder = " + spec["ruler"] in seg:
        return False
    h = re.search(r"holder = (\w+)", seg)
    assert h, "c_%s 1337 entry has no holder" % county
    seg2 = seg.replace("holder = " + h.group(1), "holder = " + spec["ruler"], 1)
    gm = re.search(r"government = (\w+)", seg2)
    if gm and gm.group(1) != spec["gov"]:
        seg2 = seg2.replace("government = " + gm.group(1),
                            "government = " + spec["gov"], 1)
    blk2 = blk[:s.start()] + seg2 + blk[s.end():]
    flat2 = flat[:cm.start()] + blk2 + flat[cm.end():]
    assert flat2.count("{") == flat2.count("}"), "brace mismatch in zz_eu5_titles"
    write(p, flat2.replace("\n", eol))
    print("  zz_eu5_titles: c_%s holder %s -> %s, government -> %s" %
          (county, h.group(1), spec["ruler"], spec["gov"]))
    return True


print("Capital seats:")
cap_keep = []
for spec in CAPITAL_SEATS:
    for path in (LT_MOD, LT_EXP):
        if reorder_seat(path, spec["county"], spec["seat"]):
            wrote.append("%s (c_%s)" % (os.path.basename(path), spec["county"]))
    if capital_seat_history(spec):
        wrote.append("zz_eu5_titles.txt (c_%s)" % spec["county"])
    cap_keep += ["c_" + spec["county"], "b_" + spec["seat"]]
if extend_keep(cap_keep):
    wrote.append("eu5_reassign_keep.json")


# ---- 9. Melk seat (user decision 2026-11-14) ----
# See the module docstring: only the barony order, RANK_STATE.json's pick and the
# keep-list change. Austria already holds the county and both towns.
print("Melk seat:")
melk = ("ober_dem_wienerwald", "melk")
for path in (LT_MOD, LT_EXP):
    if reorder_seat(path, *melk):
        wrote.append("%s (c_ober_dem_wienerwald)" % os.path.basename(path))
if correct_rank_state([melk]):
    wrote.append("RANK_STATE.json")
if extend_keep(["c_ober_dem_wienerwald", "b_melk"]):
    wrote.append("eu5_reassign_keep.json")

print("written:", ", ".join(wrote))
