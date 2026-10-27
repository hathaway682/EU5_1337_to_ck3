# -*- coding: utf-8 -*-
"""只读：QHT/YAM 全部 location 对应的男爵领现状"""
import io, re, os, collections

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
SRC = os.path.join(MOD, "history/provinces/00_generated_provinces.txt")
LT = os.path.join(MOD, "common/landed_titles/00_landed_titles.txt")
LOC = os.path.join(MOD, "localization/simp_chinese")

out = io.open(os.path.join(MOD, "gen_debug", "_qht_yam_locs.out"), "w", encoding="utf-8")
def w(s=""):
    out.write(str(s) + "\n")

txt = io.open(SRC, encoding="utf-8-sig", errors="ignore").read()
prov = {}
for m in re.finditer(r"(?m)^(\d+) = \{(.*?)\n\}", txt, re.S):
    pid = int(m.group(1)); body = m.group(2)
    f = re.search(r"(?m)^\s*faith = (\S+)", body)
    r = re.search(r"(?m)^\s*rite = (\S+)", body)
    prov[pid] = (f.group(1) if f else None, r.group(1) if r else None)

lt = io.open(LT, encoding="utf-8-sig", errors="ignore").read().replace("\r\n", "\n")
bar = {}
stack = []; cur_c = None
for line in lt.split("\n"):
    if not line.strip() or line.lstrip().startswith("#"):
        continue
    depth = len(line) - len(line.lstrip("\t"))
    m = re.match(r"\s*([a-z]_[A-Za-z0-9_]+)\s*=\s*\{", line)
    if m:
        key = m.group(1)
        while stack and stack[-1][0] >= depth:
            stack.pop()
        stack.append((depth, key))
        if key.startswith("c_"):
            cur_c = key
        continue
    mp = re.match(r"\s*province\s*=\s*(\d+)", line)
    if mp:
        bb = [s[1] for s in stack if s[1].startswith("b_")]
        if bb:
            bar.setdefault(bb[-1], {"pid": None, "county": cur_c})
            bar[bb[-1]]["pid"] = int(mp.group(1))

QHT = ["abha", "abil", "samakh", "tanomah", "tathlith", "al_amwah", "al_harjah",
       "al_maddah", "khaybar_janoub", "yadamah", "al_husayniyah"]
YAM = ["al_mahjal", "dhahran", "huth", "main", "najran", "sadah", "suq_al_ghinan"]

for name, lst in (("QHT", QHT), ("YAM", YAM)):
    w("==== %s ====" % name)
    for nm in lst:
        bk = "b_" + nm
        info = bar.get(bk)
        if not info or not info["pid"]:
            w("  %-18s -> 无对应男爵领" % nm)
            continue
        pid = info["pid"]
        f, r = prov.get(pid, (None, None))
        flag = "" if r == "ismaili" else "   <<< 还不是 ismaili"
        w("  %-18s p%-6d county=%-12s faith=%-8s rite=%-10s%s" %
          (nm, pid, info["county"], f, r, flag))
    w("")

w("==== c_sana 全部省（对照）====")
for bk, info in bar.items():
    if info["county"] == "c_sana" and info["pid"]:
        f, r = prov.get(info["pid"], (None, None))
        w("  %-22s p%-6d faith=%-8s rite=%s" % (bk, info["pid"], f, r))

out.close()
print("done")
