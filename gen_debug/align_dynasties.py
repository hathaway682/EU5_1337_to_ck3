# -*- coding: ascii -*-
import io, re, os, datetime

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
DYN = os.path.join(MOD, r"common\dynasties\zz_eu5_dynasties.txt")
ALIAS = os.path.join(MOD, r"common\coat_of_arms\coat_of_arms\95_zz_eu5_dynasty_aliases.txt")

NAME_MAP = {
    "kudou_dynasty": "dynn_KudO_",
    "uda_genji_dynasty": "dynn_Minamoto",
    "saga_genji_dynasty": "dynn_Minamoto",
    "murakami_genji_dynasty": "dynn_Minamoto",
    "ooe_dynasty": "dynn_O_e",
    "saitou_dynasty": "dynn_SaitO_",
    "takashina_dynasty": "dynn_Takashina",
    "hatano_dynasty": "dynn_Hatano",
    "yamato_dynasty": "dynn_Yamato",
    "aleramici_dynasty": "dynn_Aleramicci",
    "angelos_dynasty": "dynn_Angelos",
    "blois_dynasty": "dynn_Blois",
    "hohenzollern_dynasty": "dynn_Hohenzollern",
    "de_brienne_dynasty": "dynn_Brienne",
    "kondou_dynasty": "dynn_KondO_",
    "tatara_dynasty": "dynn_Tatara",
    "oyama_dynasty": "dynn_Oyama",
    "antelminelli_dynasty": "dynn_Antelminelli",
    "lomagne_dynasty": "dynn_Lomagne",
    "taira_dynasty": "dynn_Taira",
    "fujiwara_dynasty": "dynn_Fujiwara",
    "orsini_dynasty": "dynn_Orsini",
    "barcelona_dynasty": "dynn_Barcelona",
    "subic_dynasty": "dynn_S_ubiC_",
}

COA_MAP = {
    "kudou_dynasty": "japanese_kudo",
    "uda_genji_dynasty": "japanese_minamoto_uda",
    "saga_genji_dynasty": "japanese_minamoto_saga",
    "murakami_genji_dynasty": "japanese_minamoto_murakami",
    "ooe_dynasty": "japanese_oe",
    "saitou_dynasty": "japanese_saito",
    "takashina_dynasty": "japanese_takashina",
    "hatano_dynasty": "japanese_hatano",
    "yamato_dynasty": "japanese_yamato",
    "aleramici_dynasty": "206",
    "angelos_dynasty": "195",
    "blois_dynasty": "721",
    "hohenzollern_dynasty": "12476",
    "de_brienne_dynasty": "80",
    "taira_dynasty": "japanese_taira_kanmu",
    "fujiwara_dynasty": "japanese_fujiwara",
    "orsini_dynasty": "2",
    "barcelona_dynasty": "100204",
}

def read_bom(path):
    with open(path, "rb") as f:
        raw = f.read()
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig"), True
    return raw.decode("utf-8"), False

def detect_nl(text):
    return "\r\n" if "\r\n" in text else "\n"

def write_bom(path, text, had_bom):
    with open(path, "w", encoding="utf-8-sig" if had_bom else "utf-8", newline="") as f:
        f.write(text)

text, bom = read_bom(DYN)
nl = detect_nl(text)
orig = text
changed = []
for key, vname in NAME_MAP.items():
    pat = re.compile(re.escape(key) + r' = \{' + nl + r'[ \t]*name = "' + re.escape(key) + r'"' + nl)
    m = pat.findall(text)
    if len(m) != 1:
        raise SystemExit("ABORT: key %s matched %d times (expected 1)" % (key, len(m)))
    repl = key + ' = {' + nl + '\tname = "' + vname + '"' + nl
    text = pat.sub(repl, text, count=1)
    changed.append((key, vname))

if text != orig:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = DYN + "." + ts + ".bak"
    with open(backup, "wb") as f:
        f.write(orig.encode("utf-8-sig" if bom else "utf-8"))
    write_bom(DYN, text, bom)
    print("DYNASTIES: edited %d name fields; backup -> %s" % (len(changed), backup))
else:
    print("DYNASTIES: no change")

atext, abom = read_bom(ALIAS)
anl = detect_nl(atext)
aorig = atext
added = []
for key, target in COA_MAP.items():
    line = "%s = %s" % (key, target)
    if re.search(re.escape(line) + r"\s*(#.*)?$", atext, re.M):
        continue
    added.append(line)
if added:
    block = ("" if atext.endswith(nl) else nl) + "# --- batch aligned (B-path) ---" + nl + nl.join(added) + nl
    atext = atext.rstrip("\r\n") + nl + block
    write_bom(ALIAS, atext, abom)
    print("ALIASES: appended %d COA alias lines" % len(added))
else:
    print("ALIASES: no change")

print("DONE name=%d coa=%d" % (len(NAME_MAP), len(COA_MAP)))
