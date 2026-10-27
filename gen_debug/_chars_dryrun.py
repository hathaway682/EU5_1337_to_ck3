# -*- coding: utf-8 -*-
"""dry-run：模拟 _apply_christian_rites_chars.py（CRLF 安全版）会改哪些人物，只统计不写盘"""
import io, os, re, json, glob
from collections import Counter

GEN = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
CHDIR = os.path.join(MOD, "history", "characters")
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"

pol = json.load(open(os.path.join(GEN, "eu5_politics.json"), encoding="utf-8"))
ct = pol["countries"]
lower_tags = {tag.lower(): tag for tag in ct}

_mapping = json.load(open(os.path.join(GEN, "mapping.json"), encoding="utf-8"))
_yemen_counties = set("c_" + l["county"] for l in _mapping["locations"]
                      if l.get("kind") == "land" and l.get("duchy") == "north_yemen")
ZAIDI_FORCE_TAGS = set()
for _c in _yemen_counties:
    _o = pol["counties"].get(_c, {}).get("owner")
    if _o:
        ZAIDI_FORCE_TAGS.add(_o)
_ny_locs = set(l["name"] for l in _mapping["locations"]
               if l.get("kind") == "land" and l.get("duchy") == "north_yemen")


def blocks(text):
    out = {}
    for m in re.finditer(r'(?m)^\t([A-Z][A-Z0-9_]{1,6})\s*=\s*\{', text):
        k = m.group(1); i = m.end() - 1; d = 0
        for j in range(i, len(text)):
            if text[j] == '{':
                d += 1
            elif text[j] == '}':
                d -= 1
                if d == 0:
                    out[k] = text[i:j + 1]; break
    return out


t = io.open(os.path.join(EU5, "main_menu/setup/start/10_countries.txt"),
            encoding="utf-8-sig", errors="ignore").read()
tag_ll, tag_school, tag_sharia = {}, {}, {}
for k, b in blocks(t).items():
    ll = re.search(r'(?m)^\s*liturgical_language\s*=\s*([a-z0-9_]+)', b)
    if ll: tag_ll[k] = ll.group(1)
    sc = re.search(r'(?m)^\s*religious_school\s*=\s*([a-z0-9_]+)', b)
    if sc: tag_school[k] = sc.group(1)
    sl = re.search(r'(?m)^\s*sharia_law\s*=\s*([a-z0-9_]+)', b)
    if sl: tag_sharia[k] = sl.group(1)

# 与正式脚本同步：男爵级国家纳入栽德派覆盖，然后剔除 QHT/YAM
for _tag, _body in blocks(t).items():
    _held = set()
    for _om in re.finditer(r'(?m)^\s*(own_[a-z_]+|control[a-z_]*)\s*=\s*\{([^}]*)\}', _body):
        _held.update(_om.group(2).split())
    if _held & _ny_locs:
        ZAIDI_FORCE_TAGS.add(_tag)
ZAIDI_FORCE_TAGS.discard("QHT")
ZAIDI_FORCE_TAGS.discard("YAM")

# 与正式脚本同步的 LCK/HLL 学派补丁
for _tag, (_sc, _sl) in {"LCK": ("jafari_school", "jafari_policy"),
                         "HLL": ("jafari_school", "jafari_policy")}.items():
    tag_school[_tag] = _sc
    tag_sharia[_tag] = _sl

SCHOOL_RITE = {
    "jafari_school": ("imami", "shia"), "imamiya_school": ("imami", "shia"),
    "ismaili_school": ("ismaili", "shia"), "zaidi_school": ("zayidi", "shia"),
    "nizari_school": ("nizari", "shia"), "mustali_school": ("hafizi", "shia"),
    "alevism_school": ("alevi", "shia"), "alawi_school": ("alawite", "shia"),
    "hanafi_school": ("hanafi", "sunni"), "hanbali_school": ("hanbali", "sunni"),
    "maliki_school": ("maliki", "sunni"), "shafii_school": ("shafii", "sunni"),
    "maturidi_school": ("hanafi", "sunni"), "qadiri_school": ("shafii", "sunni"),
    "chishti_school": ("hanafi", "sunni"), "ibadi_school": ("ibadi", "kharijite"),
}
SHARIA_POLICY_RITE = {
    "hanafi_policy": ("hanafi", "sunni"), "maliki_policy": ("maliki", "sunni"),
    "shafii_policy": ("shafii", "sunni"), "hanbali_policy": ("hanbali", "sunni"),
    "jafari_policy": ("imami", "shia"), "ismaili_policy": ("ismaili", "shia"),
    "zaidi_policy": ("zayidi", "shia"), "ibadi_policy": ("ibadi", "kharijite"),
}
LL_RITE = {"church_slavonic_language": "slavic_rite", "geez_language": "ethiopian_rite",
           "armenian_language": "armenian_rite"}
GEORGIAN_TAGS = set()


def tag_of(char_id):
    if char_id.startswith("eu5_regent_") or char_id.startswith("eu5_rep_"):
        seg = char_id.split("_")
        return lower_tags.get(seg[2]) if len(seg) >= 3 else None
    return lower_tags.get(char_id.split("_")[0])


def plan_rite(char_id, culture, religion):
    tag = tag_of(char_id)
    if religion in ("sunni", "shia", "kharijite", "ibadi"):
        if tag and tag in ZAIDI_FORCE_TAGS and religion == "shia":
            return "zayidi", True
        if tag:
            sl = tag_sharia.get(tag)
            if sl and sl in SHARIA_POLICY_RITE:
                rite, faith = SHARIA_POLICY_RITE[sl]
                if religion == faith: return rite, True
                return None, False
            sc = tag_school.get(tag)
            if sc and sc in SCHOOL_RITE:
                rite, faith = SCHOOL_RITE[sc]
                if religion == faith: return rite, True
                return None, False
        return None, False
    if religion == "orthodox":
        if tag and tag in tag_ll:
            ll = tag_ll[tag]
            if ll == "church_slavonic_language": return "slavic_rite", True
            if ll == "koine_dialect": return None, True
        if tag in GEORGIAN_TAGS: return "georgian_rite", True
        return None, False
    return None, False


out = io.open(os.path.join(MOD, "gen_debug", "_chars_dryrun.out"), "w", encoding="utf-8")
def w(s=""):
    out.write(str(s) + "\n")

tot = Counter()
changes = []
for cp in sorted(glob.glob(os.path.join(CHDIR, "*.txt"))):
    if ".bak" in cp:
        continue
    txt = io.open(cp, encoding="utf-8-sig", errors="ignore").read()
    if not re.search(r"religion = (orthodox|miaphysitism|armenian_apostolic|sunni|shia|kharijite|ibadi)", txt):
        continue
    parts = re.split(r"(?m)^([a-z0-9_]+) = \{", txt)
    for i in range(1, len(parts), 2):
        head, body = parts[i], parts[i + 1]
        cm = re.search(r"culture = (\S+)", body)
        rm = re.search(r"religion = (\S+)", body)
        if not cm or not rm:
            continue
        culture, religion = cm.group(1), rm.group(1)
        if religion == "catholic":
            continue
        rite, write = plan_rite(head, culture, religion)
        if not write:
            continue
        cur = re.search(r"(?m)^\s*rite = ([a-z_]+)", body)
        cur_rite = cur.group(1) if cur else None
        if cur_rite != rite:
            changes.append((os.path.basename(cp), head, religion, cur_rite, rite))
            tot["%s -> %s" % (cur_rite, rite)] += 1

w("会变化的人物数: %d" % len(changes))
w("\n按变化类型:")
for k, v in tot.most_common():
    w("  %-28s %d" % (k, v))
w("\n前 80 条明细:")
for f, h, rel, a, b in changes[:80]:
    w("  %-28s %-32s rel=%-8s %s -> %s" % (f, h, rel, a, b))
out.close()
print("done")
