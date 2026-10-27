# -*- coding: utf-8 -*-
"""只读：QHT / YAM 部落的县、奈季兰位置、也门 shia 省的礼分布"""
import io, re, os, json, collections

GEN = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
SRC = os.path.join(MOD, "history/provinces/00_generated_provinces.txt")
LT = os.path.join(MOD, "common/landed_titles/00_landed_titles.txt")
LOC = os.path.join(MOD, "localization/simp_chinese")
ADJ = os.path.join(GEN, "_ck3_province_adjacency.json")
MAP = os.path.join(GEN, "mapping.json")

out = io.open(os.path.join(MOD, "gen_debug", "_yemen_ismaili.out"), "w", encoding="utf-8")
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
county = collections.OrderedDict(); stack = []; cur = None
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
            kk = [s[1] for s in stack if s[1].startswith("k_")]
            dd = [s[1] for s in stack if s[1].startswith("d_")]
            cur = key
            county[key] = {"baronies": [], "duchy": dd[-1] if dd else None,
                           "kingdom": kk[-1] if kk else None}
        continue
    mp = re.match(r"\s*province\s*=\s*(\d+)", line)
    if mp and cur:
        bb = [s[1] for s in stack if s[1].startswith("b_")]
        if bb:
            county[cur]["baronies"].append((bb[-1], int(mp.group(1))))

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

# QHT / YAM 的县
w("==== owner = QHT / YAM 的县 ====")
for c, d in sorted(cs.items()):
    if d.get("owner") in ("QHT", "YAM"):
        info = county.get(c, {})
        w("\n-- %-24s %-12s owner=%-4s duchy=%-18s kingdom=%-12s EU5县宗教=%s" %
          (c, loc.get(c, ""), d.get("owner"), info.get("duchy"), info.get("kingdom"), cr.get(c)))
        for bn, pid in info.get("baronies", []):
            f, r = prov.get(pid, (None, None))
            w("   %-24s p%-6d faith=%-12s rite=%s" % (bn, pid, f, r))

# 奈季兰
w("\n==== 名字含 奈季兰 / 纳季兰 的县 ====")
for c in county:
    n = loc.get(c, "")
    if "奈季兰" in n or "纳季兰" in n or "纳吉兰" in n:
        info = county[c]
        w("\n-- %-24s %-12s duchy=%-18s kingdom=%-12s EU5县宗教=%s owner=%s" %
          (c, n, info["duchy"], info["kingdom"], cr.get(c), cs.get(c, {}).get("owner")))
        for bn, pid in info["baronies"]:
            f, r = prov.get(pid, (None, None))
            w("   %-24s p%-6d faith=%-12s rite=%s" % (bn, pid, f, r))

# 也门周边（north_yemen / south_yemen / asir）shia 省的礼分布
w("\n==== 也门/阿西尔一带 shia 省的礼分布 ====")
cnt = collections.Counter()
byc = collections.defaultdict(list)
pid2c = {}
for c, info in county.items():
    for bn, pid in info["baronies"]:
        pid2c[pid] = c
for pid, (f, r) in prov.items():
    if f != "shia":
        continue
    c = pid2c.get(pid)
    if not c:
        continue
    du = county[c]["duchy"]
    if du in ("d_north_yemen", "d_south_yemen", "d_asir", "d_hijaz", "d_tihama",
              "d_hadramawt", "d_mahra", "d_dhofar", "d_najran", "d_jizan"):
        cnt[(du, r)] += 1
        byc[du].append((pid, c, r))
for (du, r), k in sorted(cnt.items(), key=lambda x: (str(x[0][0]), str(x[0][1]))):
    w("  %-20s %-10s %d" % (du, str(r), k))

w("\n==== 也门各 duchy 的县清单（含 duchy 名）====")
dset = collections.defaultdict(list)
for c, info in county.items():
    if info["kingdom"] in ("k_yemen", "k_arabia"):
        dset[info["duchy"]].append(c)
for du in sorted(dset):
    w("  %-22s %-10s %s" % (du, loc.get(du, ""), " ".join(sorted(dset[du])[:14])))

out.close()
print("done")
