# -*- coding: utf-8 -*-
"""把 mod 全部圣地整理成 CSV，并标注「是否已确认落点」。

已确认的判据（按优先级，取第一个命中的）：
  1. 用户手改      — USER_CONFIRMED 里列的 key
  2. 已修          — 在 _apply_holy_site_knowledge_map.py 的 MAP 里（按知识/原版/EU5 判定改过）
  3. EU5 一致      — EU5 common/holy_sites 的 location 与当前 barony 相同
  4. 原版一致      — CK3 原版圣地指向的 county 与当前 county 相同
  5. 同名          — 圣地中文名 == barony 中文名，或 barony key == 圣地 key，或二者互为前缀
  其余一律「未确认」。

输出 gen_debug/holy_sites_table.csv（UTF-8 BOM，Excel 直接开）
"""
import io
import os
import re
import glob
import csv
import importlib.util

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game\in_game"
GAME = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"
SRC = os.path.join(MOD, "common", "religion", "holy_site_types", "00_holy_site_types.txt")
OUT = os.path.join(MOD, "gen_debug", "holy_sites_table.csv")

# 用户手动确认过的
USER_CONFIRMED = {
    "sanchi": "用户手改：桑吉大塔→比尔沙（Bhilsa=Vidisha 旧称）",
    # 2026-11-14 用户逐条确认
    "tinmallal": "用户确认：廷马拉尔=tinmal 廷梅勒，同一个词",
    "gerizim": "用户确认：基利心山就在纳布卢斯",
    "panticapaeum": "用户确认：潘提卡派翁=刻赤=沃斯波罗，同一城市不同时期称呼",
    "kerch": "用户确认：刻赤=沃斯波罗，同一城市不同时期称呼",
    "olympus": "用户确认：EU5 olympos 圣地 location=hatera（哈泰拉）",
    # 2026-11-14 第二轮「同一个词 / 一城异名」普查，用户批准 10 条一起改
    "ellora": "用户批准：埃洛拉石窟→道拉塔巴德（=德瓦吉里），原版 c_devagiri 下有 b_jalna，与 mod 的上马拉特瓦达对应",
    "khao_khlang_nai": "用户批准：考克朗奈是西贴古城内建筑→西贴（b_sri_thep）",
    "ranakpur": "用户批准：罗拿迦补罗在帕利县境内→帕利（b_pali）",
    "ranaheim": "用户批准：拉纳海姆=Ranheim，特隆赫姆东郊；尼达罗斯=特隆赫姆旧称→b_nidaros",
    "mizdahqan": "用户批准：米兹达赫甘墓地在火者里（Xojeli）城边→b_xojeli",
    "takht-e_soleyman": "用户批准：同一个词→b_takht_e_soleyman（c_barza，含布坎/米扬多阿布）",
    "udabhanda": "用户批准：同一个词→b_udabhanda（乌达班达=洪德）",
    "gyaitang": "用户批准：建塘=中甸藏语名，元代汉文作大旦当→b_dadandang",
    "kilimanjaro": "用户批准：莫希在乞力马扎罗南麓；原版该县另一 barony 为 b_kwa_mgogo（莫希乡下）→b_moshi",
    "gangganegara": "用户批准：刚迦尼国遗址定在木威（Beruas）→b_beruas",
}


def load_loc(d):
    out = {}
    for fn in glob.glob(os.path.join(d, "**", "*.yml"), recursive=True):
        s = io.open(fn, encoding="utf-8-sig", errors="ignore").read()
        for x in re.finditer(r'(?m)^\s*([A-Za-z0-9_.\-]+):\d*\s*"((?:[^"]|"")*)"', s):
            out.setdefault(x.group(1), x.group(2))
    return out


lm = load_loc(os.path.join(MOD, "localization", "simp_chinese"))
lg = load_loc(os.path.join(GAME, "localization", "simp_chinese"))
zh = lambda k: (lm.get(k) or lg.get(k) or "").strip()


def parse_holy(p):
    lines = io.open(p, "rb").read().decode("utf-8-sig").split("\r\n")
    depth = 0
    cur = None
    out = []
    for i, ln in enumerate(lines):
        code = ln.split("#")[0]
        if depth == 0:
            m = re.match(r"^([A-Za-z0-9_\-]+)\s*=\s*\{", code)
            if m:
                cur = {"key": m.group(1), "b": None, "c": None, "ln": i + 1}
                out.append(cur)
        if depth == 1 and cur:
            mb = re.match(r"^\s*barony\s*=\s*([A-Za-z0-9_]+)", code)
            mc = re.match(r"^\s*county\s*=\s*([A-Za-z0-9_]+)", code)
            if mb:
                cur["b"] = mb.group(1)
            if mc:
                cur["c"] = mc.group(1)
        depth += code.count("{") - code.count("}")
    return out


# 原版圣地
van = {}
for x in parse_holy(os.path.join(GAME, "common", "religion", "holy_site_types", "00_holy_site_types.txt")):
    van[x["key"]] = x

# EU5 圣地 -> location
eu5_loc = {}
for fn in sorted(glob.glob(os.path.join(EU5, "common", "holy_sites", "*.txt"))):
    if os.path.basename(fn).lower() == "readme.txt":
        continue
    txt = io.open(fn, encoding="utf-8-sig", errors="ignore").read()
    depth = 0
    cur = None
    for ln in txt.split("\n"):
        code = ln.split("#")[0]
        if depth == 0:
            m = re.match(r"^([A-Za-z0-9_\-]+)\s*=\s*\{", code)
            if m:
                cur = {"key": m.group(1), "loc": None}
        if cur is not None and depth <= 1:
            ml = re.match(r"^\s*location\s*=\s*([A-Za-z0-9_\-]+)", code)
            if ml:
                cur["loc"] = ml.group(1)
        depth += code.count("{") - code.count("}")
        if cur is not None and depth == 0:
            eu5_loc[cur["key"]] = cur["loc"]
            cur = None

# barony -> county
t = io.open(os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt"),
            encoding="utf-8-sig", errors="ignore").read()
bar2c = {}
counties = {}
cur_c = None
for ln in t.split("\n"):
    s = ln.strip()
    m = re.match(r"^(c_[A-Za-z0-9_]+)\s*=\s*\{", s)
    if m:
        cur_c = m.group(1)
        counties[cur_c] = []
        continue
    m = re.match(r"^(b_[A-Za-z0-9_]+)\s*=\s*\{", s)
    if m and cur_c:
        bar2c[m.group(1)] = cur_c
        counties[cur_c].append(m.group(1))

# MAP
spec = importlib.util.spec_from_file_location("km", os.path.join(MOD, "gen_debug", "_apply_holy_site_knowledge_map.py"))
km = importlib.util.module_from_spec(spec)
import sys
_argv = sys.argv
sys.argv = ["x"]
spec.loader.exec_module(km)
sys.argv = _argv
MAP = km.MAP

# EU5 归一化匹配（同 _eu5_key_match.py）
ck_keys = set(x["key"] for x in parse_holy(SRC))


def norm_match(ek):
    cands = []
    if ek in ck_keys:
        cands.append(ek)
    if ek.startswith("mount_") and ek[6:] in ck_keys:
        cands.append(ek[6:])
    for suf in ("_holy_city_gnostic", "_holy_site", "_temple", "_shrine", "_taisha",
                "_jinguuji", "_sanzan", "_mandir", "_mosque", "_mela", "_ji"):
        if ek.endswith(suf) and ek[:-len(suf)] in ck_keys:
            cands.append(ek[:-len(suf)])
    if "_" in ek:
        head = ek.split("_")[0]
        if head in ck_keys:
            cands.append(head)
    return list(dict.fromkeys(cands))


eu5_hit = {}   # ck3 key -> (eu5 key, location)
for ek, L in eu5_loc.items():
    if not L:
        continue
    for k in norm_match(ek):
        eu5_hit.setdefault(k, (ek, L))

# 特殊建筑挂载（game_start.txt 里 add_special_district）
bld_by_bar = {}
for i, ln in enumerate(io.open(os.path.join(MOD, "common", "on_action", "game_start.txt"),
                               "rb").read().decode("utf-8-sig").split("\n"), 1):
    for m in re.finditer(r"title:(b_[A-Za-z0-9_\-]+)\.title_province\s*=\s*\{[^}]*?add_special_district(?:_slot)?\s*=\s*([A-Za-z0-9_]+)", ln):
        bld_by_bar.setdefault(m.group(1), []).append(m.group(2))


def bld_match(k, bar):
    """该 barony 上的特殊建筑是否就是这座圣地的建筑"""
    import difflib
    for bld in bld_by_bar.get(bar, []):
        st = re.sub(r"_\d+$", "", bld)
        st = re.sub(r"_district$", "", st)
        for w in st.split("_") + [st]:
            if len(w) >= 4 and difflib.SequenceMatcher(None, w, k).ratio() >= 0.72:
                return bld
    return None


def same_name(k, b, c):
    sn = zh("holy_site_%s_name" % k) or zh("holy_site_%s" % k)
    if not sn:
        return False, ""
    bn = zh(b) if b else ""
    cn = zh(c) if c else ""
    if b and b[2:] == k:
        return True, "barony key 同名"
    if bn and sn == bn:
        return True, "barony 中文名同名"
    if bn and len(sn) >= 2 and (bn.startswith(sn) or sn.startswith(bn)):
        return True, "barony 名互为前缀"
    if cn and sn == cn:
        return True, "县名同名"
    if cn and len(sn) >= 2 and (cn.startswith(sn) or sn.startswith(cn)):
        return True, "县名互为前缀"
    return False, ""


rows = []
for x in parse_holy(SRC):
    k, b, c = x["key"], x["b"], x["c"] or bar2c.get(x["b"] or "")
    sn = zh("holy_site_%s_name" % k) or zh("holy_site_%s" % k)
    status, basis = "未确认", ""
    if k in USER_CONFIRMED:
        status, basis = "已确认", USER_CONFIRMED[k]
    elif k in MAP:
        status, basis = "已确认", "已修 → %s" % MAP[k]
    elif k in eu5_hit:
        ek, L = eu5_hit[k]
        if b == "b_" + L:
            status, basis = "已确认", "EU5 %s→%s 一致" % (ek, L)
    if status == "未确认" and k in van and van[k]["c"]:
        if van[k]["c"] == c:
            status, basis = "已确认", "原版圣地同县 %s" % c
    if status == "未确认" and b:
        bm = bld_match(k, b)
        if bm:
            status, basis = "已确认", "建筑配套 %s" % bm
    if status == "未确认":
        ok, why = same_name(k, b, c)
        if ok:
            status, basis = "已确认", why
    sibs = [y for y in counties.get(c, []) if y != b]
    rows.append({
        "圣地key": k,
        "圣地中文名": sn,
        "县": c or "",
        "县中文": zh(c) if c else "",
        "男爵领": b or "",
        "男爵领中文": zh(b) if b else "",
        "同barony特殊建筑": " ".join(bld_by_bar.get(b, [])) if b else "",
        "同县其他男爵领": " ".join("%s=%s" % (y, zh(y)) for y in sibs[:8]),
        "状态": status,
        "依据": basis,
        "行号": x["ln"],
    })

with io.open(OUT, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

ok = [r for r in rows if r["状态"] == "已确认"]
bad = [r for r in rows if r["状态"] == "未确认"]
print("圣地总数 = %d" % len(rows))
print("已确认   = %d" % len(ok))
print("未确认   = %d" % len(bad))
print("输出 ->", OUT)
print()
print("=== 未确认清单 ===")
for r in bad:
    print("  %-24s %-14s %-24s %-10s 同县: %s" % (
        r["圣地key"], r["圣地中文名"] or "(无中文名)", r["男爵领"] or r["县"],
        r["男爵领中文"] or r["县中文"], r["同县其他男爵领"]))
