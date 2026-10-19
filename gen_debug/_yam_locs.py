# -*- coding: utf-8 -*-
"""只读：YAM 的 7 个 location 在 CK3 里落在哪个县 / 哪个省 / 当前礼"""
import io, re, os, json, collections

GEN = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
SRC = os.path.join(MOD, "history/provinces/00_generated_provinces.txt")
LT = os.path.join(MOD, "common/landed_titles/00_landed_titles.txt")
LOC = os.path.join(MOD, "localization/simp_chinese")
MAP = os.path.join(GEN, "mapping.json")

out = io.open(os.path.join(MOD, "gen_debug", "_yam_locs.out"), "w", encoding="utf-8")
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
bar = {}   # b_key -> (pid, county, duchy, kingdom)
stack = []; cur_c = None; cur_d = None; cur_k = None
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
        elif key.startswith("b_"):
            cur_b = key
            bar.setdefault(key, {"pid": None, "county": cur_c})
        continue
    mp = re.match(r"\s*province\s*=\s*(\d+)", line)
    if mp:
        bb = [s[1] for s in stack if s[1].startswith("b_")]
        if bb:
            bar.setdefault(bb[-1], {"pid": None, "county": cur_c})["pid"] = int(mp.group(1))

loc = {}
for fn in os.listdir(LOC):
    if not fn.endswith(".yml"):
        continue
    try:
        t = io.open(os.path.join(LOC, fn), encoding="utf-8-sig", errors="ignore").read()
    except Exception:
        continue
    for m in re.finditer(r'(?m)^\s*([A-Za-z0-9_.\-]+):\d*\s*"([^"]*)"', t):
        loc.setdefault(m.group(1), m.group(2))

pol = json.load(open(os.path.join(GEN, "eu5_politics.json"), encoding="utf-8"))
cs = pol["counties"]
pe = json.load(open(os.path.join(GEN, "eu5_peoples.json"), encoding="utf-8"))
cr = pe["county_religion"]

YAM_LOCS = ["al_mahjal", "dhahran", "huth", "main", "najran", "sadah", "suq_al_ghinan"]

w("==== YAM 的 location -> b_ / 县 / 省 / 礼 ====")
for nm in YAM_LOCS:
    bk = "b_" + nm
    info = bar.get(bk)
    if not info or info["pid"] is None:
        w("  %-16s -> 没有对应的 b_%s" % (nm, nm))
        continue
    pid = info["pid"]; c = info["county"]
    f, r = prov.get(pid, (None, None))
    w("  %-16s -> %-18s p%-6d county=%-16s(%s) faith=%-10s rite=%-8s  EU5县宗教=%s owner=%s" %
      (nm, bk, pid, c, loc.get(c, ""), f, r, cr.get(c), cs.get(c, {}).get("owner")))

w("\n==== 这些县的全部省 ====")
seen = set()
for nm in YAM_LOCS:
    info = bar.get("b_" + nm)
    if not info or info["pid"] is None:
        continue
    c = info["county"]
    if c in seen:
        continue
    seen.add(c)
    w("\n-- %s (%s) owner=%s EU5县宗教=%s" % (c, loc.get(c, ""), cs.get(c, {}).get("owner"), cr.get(c)))
    for bk, bi in bar.items():
        if bi["county"] == c and bi["pid"]:
            f, r = prov.get(bi["pid"], (None, None))
            w("   %-24s p%-6d faith=%-10s rite=%s" % (bk, bi["pid"], f, r))

# 也门 d_north_yemen 里 shia 无 rite 的那个省
w("\n==== d_north_yemen / d_south_yemen 里 shia 无 rite 的省 ====")
for bk, bi in bar.items():
    pid = bi["pid"]
    if not pid:
        continue
    f, r = prov.get(pid, (None, None))
    if f == "shia" and not r:
        w("   %-24s p%-6d county=%s (%s)" % (bk, pid, bi["county"], loc.get(bi["county"], "")))

out.close()
print("done")
