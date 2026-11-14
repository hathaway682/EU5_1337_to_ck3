# -*- coding: utf-8 -*-
"""SBL（巴利奥尔）改挂 d_scottish_lowlands，并作为苏格兰（k_scotland）的封臣。

依据（用户 2026-11-14 下令「k_eu5_sbl改挂d_scottish_lowlands，并且做成苏格兰的封臣，反应其实际上是内战」）：
- SBL = Balliol，EU5 setup 里 type = monarchy、无 country_rank（= 伯国），
  ruler_term 从 1332.9.24 起是 sco_edward_balliol —— 即爱德华·巴利奥尔 1332 年入侵苏格兰、
  自称国王，与布鲁斯派的大卫二世（k_scotland）打内战。
- 原挂 k_eu5_sbl（自铸 titular 王国），现降为 d_scottish_lowlands（k_scotland 的 de jure 公国，
  de jure 县 = c_aberdeenshire / c_angus / c_fife / c_galloway，capital = c_lothian），
  并写 liege = k_scotland，让他在游戏里是苏格兰的封臣、实际占据低地 —— 内战格局。
- 大卫二世（sco_david_ii）原持有 d_scottish_lowlands，改由巴利奥尔持有；他仍是 k_scotland 国王。

改动六处（幂等）：
1. history/titles/zz_eu5_titles.txt
   - d_scottish_lowlands 的 1337.4.1：holder -> sco_edward_balliol，加 liege = k_scotland
   - 删 k_eu5_sbl 块
   - c_outer_hebrides 的 liege = k_eu5_sbl -> liege = d_scottish_lowlands
2. common/landed_titles/zz_eu5_titular.txt：删 k_eu5_sbl 声明块
3. localization/<11 语言>/zz_eu5_politics_l_*.yml：删 k_eu5_sbl 条目
4. gen_debug/eu5_ck3_title_map.csv：country,SBL 行改为 d_scottish_lowlands/d，liege = k_scotland，eu5_tier 改 c
5. gen_debug/_title_overrides.csv：追加 SBL -> d_scottish_lowlands
6. gen_debug/eu5_titles_dropped.txt：追加 k_eu5_sbl
"""
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P_TITLES = os.path.join(ROOT, "history", "titles", "zz_eu5_titles.txt")
P_TITULAR = os.path.join(ROOT, "common", "landed_titles", "zz_eu5_titular.txt")
P_CSV = os.path.join(ROOT, "gen_debug", "eu5_ck3_title_map.csv")
P_OVR = os.path.join(ROOT, "gen_debug", "_title_overrides.csv")
P_DROP = os.path.join(ROOT, "gen_debug", "eu5_titles_dropped.txt")


def load(p):
    b = open(p, "rb").read()
    bom = b[:3] == b"\xef\xbb\xbf"
    s = b.decode("utf-8-sig")
    nl = "\r\n" if b.count(b"\r\n") > b.count(b"\n") // 2 else "\n"
    return s, bom, nl


def save(p, s, bom):
    d = s.encode("utf-8")
    if bom:
        d = b"\xef\xbb\xbf" + d
    open(p, "wb").write(d)


def top_blocks(s):
    tops = [(m.group(1), m.start()) for m in re.finditer(r"(?m)^([a-z0-9_]+) = \{", s)]
    tops.append(("__END__", len(s)))
    return tops


log = []

# ---------- 1. history/titles ----------
s, bom, nl = load(P_TITLES)

tops = top_blocks(s)
done = False
for i in range(len(tops) - 1):
    if tops[i][0] == "d_scottish_lowlands":
        a, b = tops[i][1], tops[i + 1][1]
        blk = s[a:b]
        if "holder = sco_david_ii" in blk:
            blk = blk.replace("holder = sco_david_ii", "holder = sco_edward_balliol", 1)
            log.append("titles: d_scottish_lowlands holder -> sco_edward_balliol")
        if "liege = k_scotland" not in blk:
            blk = blk.replace(
                "holder = sco_edward_balliol",
                "holder = sco_edward_balliol" + nl + "\t\tliege = k_scotland", 1)
            log.append("titles: d_scottish_lowlands + liege = k_scotland")
        s = s[:a] + blk + s[b:]
        done = True
        break
if not done:
    log.append("titles: 找不到 d_scottish_lowlands 块")

if "liege = k_eu5_sbl" in s:
    s = s.replace("liege = k_eu5_sbl", "liege = d_scottish_lowlands")
    log.append("titles: c_outer_hebrides liege -> d_scottish_lowlands")

tops = top_blocks(s)
for i in range(len(tops) - 1):
    if tops[i][0] == "k_eu5_sbl":
        s = s[:tops[i][1]] + s[tops[i + 1][1]:]
        log.append("titles: 删除 k_eu5_sbl 块")
        break

save(P_TITLES, s, bom)

# ---------- 2. zz_eu5_titular 声明 ----------
s2, bom2, nl2 = load(P_TITULAR)
tops = top_blocks(s2)
removed = False
for i in range(len(tops) - 1):
    if tops[i][0] == "k_eu5_sbl":
        s2 = s2[:tops[i][1]] + s2[tops[i + 1][1]:]
        removed = True
        break
if removed:
    save(P_TITULAR, s2, bom2)
    log.append("titular: 删除 k_eu5_sbl 声明")
else:
    log.append("titular: k_eu5_sbl 声明已不存在（跳过）")

# ---------- 3. 本地化 ----------
nloc = 0
for f in sorted(glob.glob(os.path.join(ROOT, "localization", "*", "zz_eu5_politics_l_*.yml"))):
    s3, bom3, nl3 = load(f)
    lines = s3.split(nl3)
    kept = [ln for ln in lines if not re.match(r"^\s*k_eu5_sbl:0\s", ln)]
    if len(kept) != len(lines):
        save(f, nl3.join(kept), bom3)
        nloc += 1
log.append("localization: %d 个文件删除 k_eu5_sbl 条目" % nloc)

# ---------- 4. CSV ----------
OLD_ROW = ("country,SBL,k,Balliol,巴利奥尔,,,k_eu5_sbl,k,Balliol,巴利奥尔,"
           "sco_edward_balliol,sco_edward_balliol,,feudal_government,yes,")
NEW_ROW = ("country,SBL,c,Balliol,巴利奥尔,,,d_scottish_lowlands,d,Scottish Lowlands,"
           "苏格兰低地,sco_edward_balliol,sco_edward_balliol,k_scotland,feudal_government,yes,")
c, bomc, nlc = load(P_CSV)
if OLD_ROW + nlc in c:
    c = c.replace(OLD_ROW + nlc, NEW_ROW + nlc, 1)
    save(P_CSV, c, bomc)
    log.append("csv: country,SBL -> d_scottish_lowlands/d，liege = k_scotland")
elif NEW_ROW + nlc in c:
    log.append("csv: country,SBL 已是新值（跳过）")
else:
    log.append("csv: ! country,SBL 行未匹配")

# ---------- 5. overrides ----------
NEW_OVR = "country,SBL,title_key,d_scottish_lowlands,降为苏格兰封臣公国（原 k_eu5_sbl），反映巴利奥尔派内战"
o, bomo, nlo = load(P_OVR)
if NEW_OVR not in o:
    if not o.endswith(nlo):
        o += nlo
    o += NEW_OVR + nlo
    save(P_OVR, o, bomo)
    log.append("overrides: 追加 SBL -> d_scottish_lowlands")
else:
    log.append("overrides: SBL 行已存在（跳过）")

# ---------- 6. dropped 清单 ----------
d, bomd, nld = load(P_DROP)
if not re.search(r"(?m)^k_eu5_sbl\s*$", d):
    if not d.endswith(nld):
        d += nld
    d += "k_eu5_sbl" + nld
    save(P_DROP, d, bomd)
    log.append("dropped: 追加 k_eu5_sbl")
else:
    log.append("dropped: k_eu5_sbl 已存在（跳过）")

for x in log:
    print(" -", x)
