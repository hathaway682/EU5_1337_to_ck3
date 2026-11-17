# -*- coding: utf-8 -*-
"""撤销上一脚本对帕多瓦的多余改动（用户 2026-11-17 指出）。

用户原话：「帕多瓦根本不在任务范围内，在你小脑萎缩的世界里公国是能臣属于公国的吗，
显然不可能」。

问题：
- d_commune_padua 不在 zzz_eu5_communes.txt 的 11 个历史块里，本就不该动。
- 我给它写了 liege = d_commune_verona，公国臣属公国，CK3 里不成立。
- 顺手把 c_padua 的 1329.7.22 holder 也误改成 pad_marsiglio_carrara。

回滚四处：
1 zzz_eu5_communes.txt  删 d_commune_padua 块
2 zz_eu5_titles.txt     c_padua 整块恢复成 git HEAD 原样
3 CSV                   country,PAD 行恢复成 git HEAD 原样
4 _title_overrides.csv  删 country,PAD 行
5 本地化 11 语言        删 d_commune_padua 条目
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
    tmp = p + ".tmp_padroll"
    with io.open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        f.write(text)
    os.replace(tmp, p)

def block_of(t, key):
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

changed = []

# ---------- 1. zzz 删 d_commune_padua ----------
p = P("history", "titles", "zzz_eu5_communes.txt")
t = read(p)
blk = block_of(t, "d_commune_padua")
if blk:
    t = t.replace("\n\n" + blk, "", 1)
    if blk in t:
        t = t.replace(blk, "", 1)
    write(p, t)
    changed.append("zzz: 删 d_commune_padua")
else:
    print(" - zzz: 无 d_commune_padua，跳过")

# ---------- 2. c_padua 恢复 ----------
p = P("history", "titles", "zz_eu5_titles.txt")
t = read(p)
cur = block_of(t, "c_padua")
ORIG = """c_padua = {
	1265.7.1 = {
		holder = ven_lorenzo_tiepolo
	}
	1318.7.25 = {
		holder = pad_giacomo_carrara
	}
	1324.11.23 = {
		holder = pad_marsiglio_carrara
	}
	1328.9.10 = {
		holder = ver_cangrande_scala
	}
	1329.7.22 = {
		holder = ver_alberto_ii_scala
	}
	1337.1.1 = {
		liege = d_eu5_ver
	}
	1337.4.1 = {
		change_prosperity_level = 34
	}
	1337.4.1 = {
		holder = ver_alberto_ii_scala
		government = republic_government
	}
}"""
if cur and cur != ORIG:
    t = t.replace(cur, ORIG, 1)
    write(p, t)
    changed.append("titles: c_padua 恢复原样")
else:
    print(" - titles: c_padua 已是原样，跳过")

# ---------- 3. CSV PAD 恢复 ----------
p = P("gen_debug", "eu5_ck3_title_map.csv")
t = read(p)
lines = t.split("\r\n")
ORIG_CSV = 'country,PAD,c,Padua,帕多瓦,,,c_padua,c,Patávion,帕多瓦,eu5_rep_pad,pad_marsiglio_carrara,d_eu5_ver,republic_government,yes,"consul,vassal,consul-holds,country-below-county-rank: its land is its counties"'
n = 0
for i, ln in enumerate(lines):
    if ln.startswith("country,PAD,"):
        if ln != ORIG_CSV:
            lines[i] = ORIG_CSV
            n += 1
if n:
    write(p, "\r\n".join(lines))
    changed.append("csv: PAD 行恢复原样")
else:
    print(" - csv: PAD 行已是原样，跳过")

# ---------- 4. overrides 删 PAD ----------
p = P("gen_debug", "_title_overrides.csv")
t = read(p)
NL = "\r\n" if "\r\n" in t else "\n"
lines = t.split(NL)
keep = [ln for ln in lines if not ln.startswith("country,PAD,title_key,")]
if len(keep) != len(lines):
    write(p, NL.join(keep))
    changed.append("overrides: 删 PAD 行")
else:
    print(" - overrides: 无 PAD 行，跳过")

# ---------- 5. 本地化删 d_commune_padua ----------
n_loc = 0
for f in sorted(glob.glob(P("localization", "*", "zz_eu5_politics_l_*.yml"))):
    t = read(f)
    NLOC = "\r\n" if "\r\n" in t else "\n"
    lines = t.split(NLOC)
    keep = [ln for ln in lines if not ln.lstrip().startswith("d_commune_padua:")]
    if len(keep) != len(lines):
        write(f, NLOC.join(keep))
        n_loc += 1
if n_loc:
    changed.append("本地化: %d 个语言删 d_commune_padua" % n_loc)
else:
    print(" - 本地化: 无 d_commune_padua，跳过")

print("完成:")
for c in changed:
    print(" -", c)
