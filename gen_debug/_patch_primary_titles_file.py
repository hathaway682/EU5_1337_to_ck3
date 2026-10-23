# -*- coding: utf-8 -*-
"""Surgical patch of common/on_action/zz_eu5_primary_titles.txt, in the file's own format.

The generator's county tier now seats the shugo daimyo (the `for ... else` added to
_fix_politics_output.py), but the file it wrote was not regenerated — the generator rewrites
dozens of other files and must not be run for this. This writes the entries by hand instead,
and is safe to re-run: an entry already present with the right title is left alone.

Round one (2026-10-23, applied): the shugo daimyo wear no seat the generic loop could find —
every county they govern answers to the shogun, so the only owner among their holdings is JAP
and its capital is Kyoto. Twelve are seated on the county of their own kokufu — the seat their
house is written on — and Hosokawa, whose kokufu county Settsu was taken from him by Akamatsu,
wears the county his own capital stands in. Two stale entries went with them: eu5_regent_mci
pointed at c_yazhou, which is yua_togon_temur's and which mci never held, and
hhb_margaretha_hohenberg_rotenburg pointed at c_swabian_alb, which she does not hold in 1337.

Round two (2026-10-23): the file predates the current export data by two days, so twelve
entries are left over from rulers who now hold a single county — the tier settles those and the
entry is redundant — and three picks the unchanged loop makes were never written. All fifteen
verified against history/titles/zz_eu5_titles.txt at 1337.4.1: each deletion candidate holds
fewer than two counties and no duchy or better, each addition holds the county named beside at
least one other and no duchy or better.

Round three (2026-10-23, user decisions): four rulers whose EU5 capital stands in a county
another lord holds — the loop leaves those alone by design, and the user chose their seat by
hand rather than move anybody's land. Each wears a county he already holds:
  - bds_jalal_al_dawla_iskandar -> c_qazvin: his capital kojur sits in c_rustamdar, which
    mzn_hasan holds; qazvin is his own integrated territory in EU5 (own_control_integrated).
  - gel_reinoud_ii_van_gelre -> c_gelderland: geldern sits in c_niederrhein, brg_adolf_ix_berg's.
  - rig_friedrich_von_pernstein -> c_inner_livonia: limbazi sits in c_south_livonia, whose seat
    is riga and stays autonomous as the user asked.
  - utr_jan_van_diest -> c_overijssel: verden sits in c_aller, lun_otto_iii_luneburg's.
These four the generator cannot derive — no capital of theirs stands in a county they hold — so
they live here and nowhere else: a rerun of the generator loses them, and this script writes
them back.

After rounds one and two the file held exactly what the generator's logic produces; round three
adds the four manual seats on top.

Usage: python _patch_primary_titles_file.py [--apply]
"""
import argparse, io, os, re, shutil, sys

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true")
args = ap.parse_args()

path = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "common", "on_action", "zz_eu5_primary_titles.txt")

# (ruler, county) — entries to write where the sort puts them.
ADD = [
    # round one: the shugo daimyo
    ("jap_akamatsu_norimura", "c_settsu"),
    ("jap_hosokawa_kazuuji", "c_awa"),
    ("jap_ishidou_yoshifusa", "c_suruga"),
    ("jap_kitabatake_chikafusa", "c_ise"),
    ("jap_kou_no_moronao", "c_yamato"),
    ("jap_kyougoku_douyo", "c_oumi"),
    ("jap_ootomo_ujiyasu", "c_bungo"),
    ("jap_shiba_takatsune", "c_kazusa"),
    ("jap_shimazu_sadahisa", "c_oosumi"),
    ("jap_shouni_yorihisa", "c_chikuzen"),
    ("jap_takeda_nobutake", "c_kai"),
    ("jap_uesugi_noriaki", "c_kouzuke"),
    ("jap_yoshimi_yoritaka", "c_noto_japan"),
    # round two: picks the unchanged loop makes that the older file never wrote
    ("bru_otto_i_braunschweig_gottingen", "c_brunswick"),
    ("hhb_rudolf_iii_hohenberg_rotenburg", "c_swabian_alb"),
    ("uls_elizabeth_de_burgh_4th_countess_ulster", "c_antrim"),
    # round three: seats the user picked by hand for the four whose EU5 capital stands in
    # another lord's county — no land moves, each wears a county he already holds
    ("bds_jalal_al_dawla_iskandar", "c_qazvin"),
    ("gel_reinoud_ii_van_gelre", "c_gelderland"),
    ("rig_friedrich_von_pernstein", "c_inner_livonia"),
    ("utr_jan_van_diest", "c_overijssel"),
]
# entries to drop: the two stale ones, and the twelve left from single-county holders.
DROP = ["eu5_regent_mci", "hhb_margaretha_hohenberg_rotenburg",
        "eu5_regent_hur", "eu5_regent_kke", "eu5_regent_nlg", "eu5_regent_snp",
        "eu5_regent_sui", "eu5_regent_sul", "eu5_regent_toh",
        "hdh_heinrich_iii_von_braunschweig_luneburg", "hes_heinrich_ii_hesse",
        "kol_walram_von_julich", "mun_ludwig_ii_hessen", "urb_sighinolfo_montefeltro"]

data = open(path, "rb").read()
assert data[:3] == b"\xef\xbb\xbf", "no BOM: refusing to touch the file"
text = data.decode("utf-8-sig")
lines = text.split("\r\n")
assert lines[-1] == "" and lines[-2] == "}", "unexpected tail"


def entry_at(ls, i):
    """The (ruler, title) of the six-line entry starting at line i, or None."""
    head = ls[i].strip()
    if not head.startswith("character:") or not head.endswith(" = {"):
        return None
    m = re.search(r"set_primary_title_to = title:(\w+)", ls[i + 3])
    return (head.split(":", 1)[1].split(" ", 1)[0],
            m.group(1) if m else None)


# ---- drop
out, dropped = [], []
i = 0
while i < len(lines):
    e = entry_at(lines, i)
    if e and e[0] in DROP:
        assert lines[i + 5].strip() == "}", lines[i:i + 6]
        dropped.append(e)
        i += 6
        continue
    out.append(lines[i])
    i += 1

# ---- add where the sort puts them
names = [e[0] for e in (entry_at(out, k) for k in range(len(out))) if e]
added = []
for ruler, title in ADD:
    if ruler in names:
        have = next(e[1] for e in (entry_at(out, k) for k in range(len(out)))
                    if e and e[0] == ruler)
        assert have == title, "%s already holds %s, wanted %s" % (ruler, have, title)
        continue
    after = max([n for n in names if n < ruler], default=None)
    if after is not None:
        k = next(k for k, l in enumerate(out) if l.strip() == "character:%s = {" % after)
        idx = k + 6
    else:
        idx = next(k for k, l in enumerate(out) if l.strip().startswith("character:"))
    out[idx:idx] = ["\t\tcharacter:%s = {" % ruler,
                    "\t\t\tif = {",
                    "\t\t\t\tlimit = { is_alive = yes }",
                    "\t\t\t\tset_primary_title_to = title:%s" % title,
                    "\t\t\t}",
                    "\t\t}"]
    names.append(ruler)
    added.append((ruler, title))

body = "\r\n".join(out)
print("dropped %d: %s" % (len(dropped), [d[0] for d in dropped]))
print("added %d: %s" % (len(added), [a[0] for a in added]))
if not args.apply:
    sys.exit(0)
if body != text:
    shutil.copy2(path, path + ".bak_primarysync_apply")
    io.open(path, "w", encoding="utf-8-sig", newline="").write(body)
    print("written (backup .bak_primarysync_apply)")
else:
    print("no change: file already holds exactly this")
