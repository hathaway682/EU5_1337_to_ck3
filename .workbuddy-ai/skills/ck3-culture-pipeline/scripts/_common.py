# -*- coding: utf-8 -*-
"""文化流水线公共层：路径、数据源加载、BOM/CRLF 读写、county/province 结构。

所有脚本都从这里取东西，避免各自重写一遍解析逻辑。
路径可用环境变量覆盖：EU5_GAME / CK3_GAME / MOD_ROOT。
"""
import collections
import csv
import glob
import io
import os
import re

# ---------- 路径 ----------
_here = os.path.dirname(os.path.abspath(__file__))
# <MOD>/.workbuddy-ai/skills/ck3-culture-pipeline/scripts -> 上四级
_DEFAULT_MOD = os.path.abspath(os.path.join(_here, "..", "..", "..", ".."))
MOD = os.environ.get("MOD_ROOT", _DEFAULT_MOD)
EU5 = os.environ.get("EU5_GAME",
                     r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game")
CK3 = os.environ.get("CK3_GAME",
                     r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game")

POPS = os.path.join(EU5, "main_menu", "setup", "start", "06_pops.txt")
DEFS = os.path.join(EU5, "in_game", "map_data", "definitions.txt")
EU5_CULT_DIR = os.path.join(EU5, "in_game", "common", "cultures")
EU5_GROUP_LOC = os.path.join(EU5, "main_menu", "localization", "simp_chinese",
                             "culture_groups_l_simp_chinese.yml")

CLASSIF = os.path.join(MOD, "gen_debug", "_culture_classification.csv")
RULES = os.path.join(MOD, "gen_debug", "_classify_cultures.py")
PROV = os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt")
LANDED = os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt")

PEOPLE = [
    "history/characters/00_generated_characters.txt",
    "history/characters/zz_eu5_characters.txt",
    "history/characters/zz_eu5_missing_characters.txt",
    "history/characters/zz_eu5_regents.txt",
    "history/characters/zz_gen_adventurers.txt",
    "common/dynasties/00_generated_dynasties.txt",
    "common/dynasties/zz_eu5_dynasties.txt",
    "common/dynasties/zz_gen_adventurers.txt",
    "common/dynasty_houses/zz_eu5_merged_houses.txt",
]

# 人物层不能动的 key：这里的 prussian 是波罗的普鲁士人，再扫会误改成萨克森
KEEP_IN_PEOPLE = {"prussian"}

RE_CULT = re.compile(r'^([ \t]*)culture([ \t]*=[ \t]*)"?([A-Za-z0-9_]+)"?([ \t]*)$')


# ---------- BOM / CRLF 读写 ----------
def read_text(path):
    raw = open(path, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    return raw.decode("utf-8-sig"), bom


def write_text(path, text, bom=True):
    data = text.encode("utf-8")
    if bom:
        data = b"\xef\xbb\xbf" + data
    open(path, "wb").write(data)


def split_keep(text):
    """按 \n 切，保留行尾 \\r（调用方自己处理）。"""
    return text.split("\n")


def join_crlf(lines):
    return "\r\n".join(l[:-1] if l.endswith("\r") else l for l in lines)


# ---------- CSV ----------
def load_classif():
    with io.open(CLASSIF, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def save_classif(rows, header=None):
    header = header or list(rows[0].keys())
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=header, lineterminator="\r\n")
    w.writeheader()
    w.writerows(rows)
    open(CLASSIF, "wb").write(b"\xef\xbb\xbf" + out.getvalue().encode("utf-8"))


# ---------- 文化定义 ----------
def defined_cultures():
    keys = set()
    for pat in (os.path.join(MOD, "common/culture/cultures/*.txt"),
                os.path.join(CK3, "common/culture/cultures/*.txt")):
        for f in glob.glob(pat):
            keys |= set(re.findall(r"(?m)^([a-z0-9_]+)\s*=\s*\{",
                                   io.open(f, encoding="utf-8-sig", errors="ignore").read()))
    return keys


# ---------- EU5 数据 ----------
def eu5_language():
    """EU5 culture key -> language（文化块里没有 culture_groups 时用来推组）。"""
    out = {}
    if not os.path.isdir(EU5_CULT_DIR):
        return out
    for fn in os.listdir(EU5_CULT_DIR):
        if not fn.endswith(".txt"):
            continue
        s = io.open(os.path.join(EU5_CULT_DIR, fn), encoding="utf-8-sig",
                    errors="ignore").read()
        for m in re.finditer(r"(?m)^[ \t]*([a-z0-9_]+)[ \t]*=[ \t]*\{", s):
            i, d = m.end(), 1
            while i < len(s) and d:
                if s[i] == "{":
                    d += 1
                elif s[i] == "}":
                    d -= 1
                i += 1
            body = s[m.end():i - 1]
            lg = re.search(r"(?m)^[ \t]*language[ \t]*=[ \t]*([a-z0-9_]+)", body)
            if lg:
                out[m.group(1)] = lg.group(1)
    return out


def province_majority():
    """EU5 province -> 人口最多的 culture（size 累加，不是 location 个数）。"""
    loc = collections.defaultdict(collections.Counter)
    cur = None
    re_loc = re.compile(r"^\s*([a-z0-9_]+)\s*=\s*\{\s*$")
    re_pop = re.compile(r"define_pop\s*=\s*\{[^}]*?size\s*=\s*([0-9.]+)[^}]*?culture\s*=\s*([a-z0-9_]+)")
    for line in io.open(POPS, encoding="utf-8-sig", errors="ignore"):
        m = re_loc.match(line.rstrip("\n"))
        if m:
            cur = m.group(1)
            continue
        if "define_pop" in line:
            mm = re_pop.search(line)
            if mm and cur:
                loc[cur][mm.group(2)] += float(mm.group(1))
    prov_locs = province_locations()
    out = {}
    for pv, locs in prov_locs.items():
        tot = collections.Counter()
        for l in locs:
            tot.update(loc.get(l, {}))
        if tot:
            out[pv] = min(tot.items(), key=lambda kv: (-kv[1], kv[0]))[0]
    return out


def province_locations():
    """EU5 province -> [location]"""
    d = io.open(DEFS, encoding="utf-8-sig", errors="ignore").read()
    return {m.group(1): [x for x in m.group(2).split() if not x.startswith("#")]
            for m in re.finditer(r"(?m)^\s*([a-z0-9_]+)_province\s*=\s*\{([^}]*)\}", d)}


def barony_province():
    """barony 名（去掉 b_）-> EU5 province"""
    return {l: pv for pv, locs in province_locations().items() for l in locs}


# ---------- CK3 头衔结构 ----------
def county_structure():
    """返回 (county -> [barony 名], county -> [CK3 province id])"""
    bars = collections.defaultdict(list)
    pids = collections.defaultdict(list)
    cur = None
    stack = []
    for line in io.open(LANDED, encoding="utf-8-sig", errors="ignore"):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = re.match(r"^(c_[a-z0-9_]+)\s*=\s*\{", s)
        if m:
            cur = m.group(1)
            stack.append("c")
            continue
        m = re.match(r"^(b_[a-z0-9_]+)\s*=\s*\{", s)
        if m:
            bars[cur].append(m.group(1)[2:])
            stack.append("b")
            continue
        m = re.match(r"^province\s*=\s*(\d+)", s)
        if m and "b" in stack and cur:
            pids[cur].append(int(m.group(1)))
        if s == "}":
            if stack:
                stack.pop()
            if not any(x == "c" for x in stack):
                cur = None
    return bars, pids


def province_cultures():
    """CK3 province id -> 当前 culture 值"""
    text, _ = read_text(PROV)
    out = {}
    cid = None
    for line in text.split("\n"):
        s = line.rstrip("\r")
        m = re.match(r"^(\d+) = \{$", s)
        if m:
            cid = int(m.group(1))
            continue
        if s == "}":
            cid = None
            continue
        m = re.match(r'^[ \t]*culture[ \t]*=[ \t]*"?([A-Za-z0-9_]+)"?', s)
        if m and cid is not None:
            out[cid] = m.group(1)
    return out


def counties_for_eu5_cultures(eu5_cultures):
    """哪些 county 的 EU5 province 人口多数落在给定 EU5 culture 集合里 -> {county: pv}"""
    pc = province_majority()
    bp = barony_province()
    bars, _ = county_structure()
    want = set(eu5_cultures)
    hit = {}
    for cty, names in bars.items():
        pvs = {bp[b] for b in names if b in bp}
        if len(pvs) == 1:
            pv = pvs.pop()
            if pc.get(pv) in want:
                hit[cty] = pv
    return hit


# ---------- 改写器 ----------
def rewrite_provinces(pids, target, apply=True):
    """把给定 CK3 province id 的 culture 行改成 target。返回 (改动数, Counter)"""
    pids = set(pids)
    text, bom = read_text(PROV)
    lines = text.split("\n")
    re_b = re.compile(r"^(\d+) = \{$")
    cid = None
    hits = collections.Counter()
    n = 0
    for i, line in enumerate(lines):
        s = line.rstrip("\r")
        m = re_b.match(s)
        if m:
            cid = int(m.group(1))
            continue
        if s == "}":
            cid = None
            continue
        m = RE_CULT.match(s)
        if m and cid is not None and cid in pids:
            ind, mid, old, tail = m.groups()
            if old == target:
                continue
            hits[(old, target)] += 1
            lines[i] = "%sculture%s%s%s%s" % (ind, mid, target, tail,
                                             "\r" if line.endswith("\r") else "")
            n += 1
    if n and apply:
        write_text(PROV, "\n".join(lines), bom)
    return n, hits


def rewrite_people(mapping, apply=True, skip=None):
    """人物层按 mapping 改写。返回 {文件: (行数, Counter)}"""
    skip = KEEP_IN_PEOPLE if skip is None else set(skip)
    m = {k: v for k, v in mapping.items() if k not in skip}
    result = {}
    for rel in PEOPLE:
        p = os.path.join(MOD, rel)
        if not os.path.exists(p):
            result[rel] = (0, collections.Counter())
            continue
        text, bom = read_text(p)
        lines = text.split("\n")
        hits = collections.Counter()
        n = 0
        for i, line in enumerate(lines):
            body = line[:-1] if line.endswith("\r") else line
            mm = RE_CULT.match(body)
            if not mm:
                continue
            ind, mid, key, tail = mm.groups()
            new = m.get(key)
            if not new or new == key:
                continue
            lines[i] = "%sculture%s%s%s%s" % (
                ind, mid, '"%s"' % new if '"' in body else new, tail,
                "\r" if line.endswith("\r") else "")
            hits[key] += 1
            n += 1
        if n and apply:
            write_text(p, "\n".join(lines), bom)
        result[rel] = (n, hits)
    return result


def backup(path, tag):
    import datetime
    import shutil
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = "%s.bak_%s_%s" % (path, tag, stamp)
    shutil.copy2(path, dst)
    return dst


def check_format(path):
    raw = open(path, "rb").read()
    return {
        "bom": raw.startswith(b"\xef\xbb\xbf"),
        "crlf": raw.count(b"\r\n"),
        "bare_lf": raw.count(b"\n") - raw.count(b"\r\n"),
    }
