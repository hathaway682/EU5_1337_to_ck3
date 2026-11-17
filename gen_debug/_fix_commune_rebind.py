# -*- coding: utf-8 -*-
"""d_commune_ 系列全部改挂（用户 2026-11-17 指令）。

用户原话：「我说的是 d_commune_ 这一系列头衔，全都改挂」「共和国的历史都在
zzz_eu5_communes.txt，改挂也包括米兰」「以及你没发现帕多瓦共和国开局没有持有人吗，
我就没想让他独立」。

现状：
- common/landed_titles/zz_eu5_communes.txt 有 12 个 d_commune_* 声明（titular）。
- history/titles/zzz_eu5_communes.txt 有 11 个 history 块（缺 d_commune_padua），
  各县的 liege 也在这里写。
- 12 国仍挂在旧键上：FLO=d_eu5_flo、MLO=d_lombardy、VER=d_eu5_ver，
  其余 9 国挂 c_*（ANC/SIE/MAN/PAV/BLG/FER/RAG 的 liege 已是 d_commune_*，但缺 holder）。
- 帕多瓦：c_padua 的 1337.4.1 holder 是 ver_alberto_ii_scala（维罗纳人），
  PAD 自己的 pad_marsiglio_carrara 一个头衔都没有 → 用户要它作为维罗纳封臣存在，不独立。

做法：
1 zzz_eu5_communes.txt
   - d_commune_firenze / d_commune_verona / d_commune_milan 的块整块换成
     d_eu5_flo / d_eu5_ver / d_lombardy 的 history（世系跟着国家走）
   - 新建 d_commune_padua：holder pad_marsiglio_carrara，liege d_commune_verona
2 zz_eu5_titles.txt
   - 删 d_eu5_flo / d_eu5_ver / d_lombardy 三个块（已迁走）
   - c_padua：1337.4.1 holder 改 pad_marsiglio_carrara，删 liege = d_eu5_ver
3 zz_eu5_republic_families.txt
   - liege 替换：d_eu5_flo→d_commune_firenze、d_eu5_ver→d_commune_verona、
     d_lombardy→d_commune_milan
4 common/landed_titles/zz_eu5_titular.txt  删 d_eu5_flo / d_eu5_ver 声明
5 localization/*/zz_eu5_politics_l_*.yml   删两个旧键、补 12 个 d_commune_* 名字
6 gen_debug/eu5_titles_dropped.txt         +d_eu5_flo / d_eu5_ver
7 gen_debug/eu5_ck3_title_map.csv          12 行 country 改 key/tier/名字/liege
8 gen_debug/_title_overrides.csv           12 行

写入：读全文 -> 替换 -> 临时文件 -> os.replace，绝不对原文件开 wb。
"""
import glob
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def P(*a):
    return os.path.join(ROOT, *a)

def read(p):
    with io.open(p, "r", encoding="utf-8-sig", newline="") as f:
        return f.read()

def write(p, text):
    tmp = p + ".tmp_commune"
    with io.open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        f.write(text)
    os.replace(tmp, p)

def block_of(t, key):
    """取顶层块（含键名到匹配的 }），找不到返回 None。"""
    m = re.search(r"(?m)^" + re.escape(key) + r" = \{", t)
    if not m:
        return None
    i = t.index("{", m.start())
    lvl = 0
    k = i
    while k < len(t):
        if t[k] == "{":
            lvl += 1
        elif t[k] == "}":
            lvl -= 1
            if lvl == 0:
                break
        k += 1
    return t[m.start():k + 1]

def rename_block(blk, old, new):
    return re.sub(r"(?m)^" + re.escape(old) + r" = \{", new + " = {", blk, count=1)

changed = []

# ---------- 读三个旧块 ----------
p_titles = P("history", "titles", "zz_eu5_titles.txt")
t_titles = read(p_titles)
MOVES = [
    ("d_eu5_flo", "d_commune_firenze"),
    ("d_eu5_ver", "d_commune_verona"),
    ("d_lombardy", "d_commune_milan"),
]
moved = {}
for old, new in MOVES:
    blk = block_of(t_titles, old)
    if blk is None:
        raise SystemExit("找不到 %s 块，中止" % old)
    moved[new] = rename_block(blk, old, new)

# ---------- 1. zzz_eu5_communes.txt ----------
p_comm = P("history", "titles", "zzz_eu5_communes.txt")
t_comm = read(p_comm)
for new, blk in moved.items():
    cur = block_of(t_comm, new)
    if cur is None:
        raise SystemExit("zzz 里找不到 %s 块，中止" % new)
    t_comm = t_comm.replace(cur, blk, 1)
    changed.append("zzz: %s 换成完整世系" % new)

# 新建 d_commune_padua，插在 d_commune_verona 块之后
if block_of(t_comm, "d_commune_padua") is None:
    padua = (
        "d_commune_padua = {\n"
        "\t1337.4.1 = {\n"
        "\t\tholder = pad_marsiglio_carrara\n"
        "\t\tgovernment = republic_government\n"
        "\t\tliege = d_commune_verona\n"
        "\t}\n"
        "}"
    )
    anchor = block_of(t_comm, "d_commune_verona")
    t_comm = t_comm.replace(anchor, anchor + "\n\n" + padua, 1)
    changed.append("zzz: 新建 d_commune_padua（维罗纳封臣）")
else:
    print(" - zzz: d_commune_padua 已存在，跳过")
write(p_comm, t_comm)

# ---------- 2. zz_eu5_titles.txt 删三个块 + 改 c_padua ----------
for old, _ in MOVES:
    blk = block_of(t_titles, old)
    t_titles = t_titles.replace(blk, "", 1)
changed.append("titles: 删 d_eu5_flo / d_eu5_ver / d_lombardy")

c_pad = block_of(t_titles, "c_padua")
if c_pad:
    new_pad = c_pad.replace(
        "\t1337.1.1 = {\n\t\tliege = d_eu5_ver\n\t}\n", ""
    )
    new_pad = new_pad.replace(
        "holder = ver_alberto_ii_scala", "holder = pad_marsiglio_carrara"
    )
    if new_pad != c_pad:
        t_titles = t_titles.replace(c_pad, new_pad, 1)
        changed.append("titles: c_padua holder -> pad_marsiglio_carrara，删 liege")
write(p_titles, t_titles)

# ---------- 3. republic_families liege ----------
p_fam = P("history", "titles", "zz_eu5_republic_families.txt")
t_fam = read(p_fam)
n_fam = 0
for old, new in (("d_eu5_flo", "d_commune_firenze"),
                 ("d_eu5_ver", "d_commune_verona"),
                 ("d_lombardy", "d_commune_milan")):
    c = t_fam.count("liege = " + old)
    if c:
        t_fam = t_fam.replace("liege = " + old, "liege = " + new)
        n_fam += c
if n_fam:
    write(p_fam, t_fam)
    changed.append("families: %d 处 liege 改挂" % n_fam)
else:
    print(" - families: 无 liege 需改，跳过")

# ---------- 4. titular 删两个声明 ----------
p_tit = P("common", "landed_titles", "zz_eu5_titular.txt")
t_tit = read(p_tit)
NL = "\r\n" if "\r\n" in t_tit else "\n"
n_tit = 0
for old, _ in MOVES[:2]:
    pat = re.compile(
        r"(?m)^" + re.escape(old) +
        r" = \{\r?\n\tlandless = yes\r?\n\tcolor = \{[^}]*\}\r?\n\tcapital = \S+\r?\n\}\r?\n(\r?\n)?"
    )
    t_tit, n = pat.subn("", t_tit)
    n_tit += n
if n_tit:
    write(p_tit, t_tit)
    changed.append("titular: 删 %d 个声明" % n_tit)
else:
    print(" - titular: 无声明，跳过")

# ---------- 5. 本地化 ----------
LOC_NAMES = {
    "d_commune_firenze": ("Firenze", "佛罗伦萨"),
    "d_commune_milan": ("Milan", "米兰"),
    "d_commune_verona": ("Verona", "维罗纳"),
    "d_commune_padua": ("Padua", "帕多瓦"),
    "d_commune_ancona": ("Ancona", "安科纳"),
    "d_commune_siena": ("Siena", "锡耶纳"),
    "d_commune_mantua": ("Mantua", "曼托瓦"),
    "d_commune_pavia": ("Pavia", "帕维亚"),
    "d_commune_bologna": ("Bologna", "博洛尼亚"),
    "d_commune_ferrara": ("Ferrara", "费拉拉"),
    "d_commune_ragusa": ("Ragusa", "拉古萨"),
    "d_commune_ravenna": ("Ravenna", "拉文纳"),
}
n_loc = 0
for f in sorted(glob.glob(P("localization", "*", "zz_eu5_politics_l_*.yml"))):
    t = read(f)
    lang = os.path.basename(f).replace("zz_eu5_politics_l_", "").replace(".yml", "")
    NLOC = "\r\n" if "\r\n" in t else "\n"
    lines = t.split(NLOC)
    keep = [ln for ln in lines if not any(ln.lstrip().startswith(k + ":") for k in ("d_eu5_flo", "d_eu5_ver"))]
    dropped = len(lines) - len(keep)
    add = []
    for k, (en, zh) in LOC_NAMES.items():
        if any(ln.lstrip().startswith(k + ":") for ln in keep):
            continue
        add.append(' %s:0 "%s"' % (k, zh if lang == "simp_chinese" else en))
    if dropped or add:
        while keep and keep[-1].strip() == "":
            keep.pop()
        if add:
            keep.extend(add)
        write(f, NLOC.join(keep) + NLOC)
        n_loc += 1
if n_loc:
    changed.append("本地化: %d 个语言（删 2 键 + 补 12 键）" % n_loc)
else:
    print(" - 本地化: 无改动，跳过")

# ---------- 6. dropped ----------
p_drop = P("gen_debug", "eu5_titles_dropped.txt")
t_drop = read(p_drop)
have = set(t_drop.split("\n"))
add = [o for o, _ in MOVES[:2] if o not in have]
if add:
    if not t_drop.endswith("\n"):
        t_drop += "\n"
    t_drop += "\n".join(add) + "\n"
    write(p_drop, t_drop)
    changed.append("dropped: +%s" % ",".join(add))
else:
    print(" - dropped: 已存在，跳过")

# ---------- 7. CSV ----------
p_csv = P("gen_debug", "eu5_ck3_title_map.csv")
t_csv = read(p_csv)
CSV_ROWS = {
    "FLO": ("d_eu5_flo", "d_commune_firenze,d,Firenze,佛罗伦萨", "e_hre"),
    "MLO": ("d_lombardy", "d_commune_milan,d,Milan,米兰", "e_hre"),
    "VER": ("d_eu5_ver", "d_commune_verona,d,Verona,维罗纳", "e_hre"),
    "PAD": ("c_padua", "d_commune_padua,d,Padua,帕多瓦", "d_commune_verona"),
    "ANC": ("c_marche", "d_commune_ancona,d,Ancona,安科纳", ""),
    "SIE": ("c_siena", "d_commune_siena,d,Siena,锡耶纳", "e_hre"),
    "MAN": ("c_mantua", "d_commune_mantua,d,Mantua,曼托瓦", "e_hre"),
    "PAV": ("c_pavia", "d_commune_pavia,d,Pavia,帕维亚", "e_hre"),
    "BLG": ("c_bologna", "d_commune_bologna,d,Bologna,博洛尼亚", ""),
    "FER": ("c_ferrara", "d_commune_ferrara,d,Ferrara,费拉拉", ""),
    "RAG": ("c_south_dalmatia", "d_commune_ragusa,d,Ragusa,拉古萨", "k_venice"),
    "RAV": ("c_romagna", "d_commune_ravenna,d,Ravenna,拉文纳", ""),
}
lines = t_csv.split("\r\n")
n_csv = 0
import csv as _csv
import io as _io
for i, ln in enumerate(lines):
    if not ln.startswith("country,"):
        continue
    tag = ln.split(",")[1]
    if tag not in CSV_ROWS:
        continue
    old_key, new_mid, new_liege = CSV_ROWS[tag]
    rec = next(_csv.reader(_io.StringIO(ln)))
    if len(rec) < 17 or rec[7] != old_key:
        print(" - csv: %s 行已是 %s，跳过" % (tag, rec[7] if len(rec) > 7 else "?"))
        continue
    rec[7:11] = new_mid.split(",")
    rec[13] = new_liege
    rec[16] = "rebind to %s (was %s)" % (new_mid.split(",")[0], old_key)
    buf = _io.StringIO()
    _csv.writer(buf, lineterminator="").writerow(rec)
    lines[i] = buf.getvalue()
    n_csv += 1
if n_csv:
    write(p_csv, "\r\n".join(lines))
    changed.append("csv: %d 行改绑" % n_csv)
else:
    print(" - csv: 无待改行，跳过")

# ---------- 8. overrides ----------
p_ovr = P("gen_debug", "_title_overrides.csv")
t_ovr = read(p_ovr)
n_ovr = 0
for tag, (old_key, new_mid, _) in CSV_ROWS.items():
    new_key = new_mid.split(",")[0]
    if ("\ncountry,%s,title_key," % tag) in t_ovr:
        print(" - overrides: %s 已存在，跳过" % tag)
        continue
    if not t_ovr.endswith("\n"):
        t_ovr += "\n"
    t_ovr += "country,%s,title_key,%s,改挂到公社公国 %s（原 %s）\n" % (tag, new_key, new_key, old_key)
    n_ovr += 1
if n_ovr:
    write(p_ovr, t_ovr)
    changed.append("overrides: +%d 行" % n_ovr)

print("完成:")
for c in changed:
    print(" -", c)
