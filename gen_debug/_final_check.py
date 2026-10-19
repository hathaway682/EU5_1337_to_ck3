# -*- coding: utf-8 -*-
"""只读：最终结构 + 残余缺口校验"""
import io, re, os, collections

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
SRC = os.path.join(MOD, "history/provinces/00_generated_provinces.txt")
LT = os.path.join(MOD, "common/landed_titles/00_landed_titles.txt")
LOC = os.path.join(MOD, "localization/simp_chinese")

out = io.open(os.path.join(MOD, "gen_debug", "_final_check.out"), "w", encoding="utf-8")
def w(s=""):
    out.write(str(s) + "\n")

raw = open(SRC, "rb").read()
w("BOM: %s" % raw.startswith(b"\xef\xbb\xbf"))
w("CRLF: %d   LF: %d" % (raw.count(b"\r\n"), raw.count(b"\n")))
txt = raw.decode("utf-8-sig")

blocks = re.findall(r"(?m)^(\d+) = \{", txt)
w("province 块: %d" % len(blocks))
w("braces: { %d  } %d" % (txt.count("{"), txt.count("}")))
rites = re.findall(r"(?m)^\s*rite = (\S+)", txt)
w("rite 行: %d" % len(rites))
dup = [k for k, v in collections.Counter(blocks).items() if v > 1]
w("重复 province id: %d" % len(dup))

# rite 紧跟 faith
lines = txt.split("\n")
bad_adj = 0
cur_id = None
for i, ln in enumerate(lines):
    m = re.match(r"^(\d+) = \{$", ln)
    if m:
        cur_id = int(m.group(1))
    if re.match(r"^\s*rite = ", ln):
        if i == 0 or not re.match(r"^\s*faith = ", lines[i-1]):
            bad_adj += 1
w("rite 未紧跟 faith 的: %d" % bad_adj)

# 逐块解析
prov = {}
for m in re.finditer(r"(?m)^(\d+) = \{(.*?)\n\}", txt, re.S):
    pid = int(m.group(1)); body = m.group(2)
    f = re.search(r"(?m)^\s*faith = (\S+)", body)
    r = re.search(r"(?m)^\s*rite = (\S+)", body)
    prov[pid] = (f.group(1) if f else None, r.group(1) if r else None)

w("\n==== 仍然 faith=sunni 但无 rite（会回落成哈乃斐）====")
rest = [(p, prov[p][0]) for p in sorted(prov) if prov[p][0] == "sunni" and not prov[p][1]]
w("共 %d 个: %s" % (len(rest), rest))

# 名称
lt = io.open(LT, encoding="utf-8-sig", errors="ignore").read().replace("\r\n", "\n")
pid2b = {}
stack = []
for line in lt.split("\n"):
    if not line.strip() or line.lstrip().startswith("#"):
        continue
    depth = len(line) - len(line.lstrip("\t"))
    m = re.match(r"\s*([a-z]_[A-Za-z0-9_]+)\s*=\s*\{", line)
    if m:
        while stack and stack[-1][0] >= depth:
            stack.pop()
        stack.append((depth, m.group(1)))
        continue
    mp = re.match(r"\s*province\s*=\s*(\d+)", line)
    if mp:
        bb = [s[1] for s in stack if s[1].startswith("b_")]
        cc = [s[1] for s in stack if s[1].startswith("c_")]
        if bb:
            pid2b[int(mp.group(1))] = (bb[-1], cc[-1] if cc else None)

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

for p, f in rest:
    b, c = pid2b.get(p, ("?", "?"))
    w("   p%-6d %-22s %-20s %s" % (p, b, c, loc.get(c, "")))

w("\n==== 马达加斯加 5 省确认 ====")
for p in (14381, 14386, 14388, 14427, 14435):
    f, r = prov.get(p, (None, None))
    b, c = pid2b.get(p, ("?", "?"))
    w("   p%-6d %-22s %-18s faith=%-8s rite=%s" % (p, b, c, f, r))

out.close()
print("done")
