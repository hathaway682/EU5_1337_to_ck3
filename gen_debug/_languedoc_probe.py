# -*- coding: utf-8 -*-
"""只读：d_languedoc 下每个男爵领（province）实际挂的文化，以及该文化的 heritage。"""
import io, os, re, collections

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
LT = os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt")
PROV = os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt")
CULT = os.path.join(MOD, "common", "culture", "cultures", "00_generated_cultures.txt")


def rd(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


t = rd(LT)
i = t.find("d_languedoc = {")
j, d = i + len("d_languedoc = {"), 1
while j < len(t) and d:
    if t[j] == "{":
        d += 1
    elif t[j] == "}":
        d -= 1
    j += 1
blk = t[i:j]
pairs = re.findall(r"(b_[a-z0-9_]+)\s*=\s*\{\s*province\s*=\s*(\d+)", blk)
print("d_languedoc 男爵领: %d" % len(pairs))

# 文化 heritage
her, lang = {}, {}
cur = None
for line in rd(CULT).split("\n"):
    m = re.match(r"^([a-z0-9_]+)\s*=\s*\{\s*$", line)
    if m:
        cur = m.group(1)
        continue
    mh = re.match(r"^\s*heritage\s*=\s*([a-z0-9_]+)", line)
    if mh and cur:
        her[cur] = mh.group(1)
    ml = re.match(r"^\s*language\s*=\s*([a-z0-9_]+)", line)
    if ml and cur:
        lang[cur] = ml.group(1)

# province -> culture（单文件，按顶层数字块解析）
pt = rd(PROV)
pc = {}
for m in re.finditer(r"(?m)^(\d+)\s*=\s*\{", pt):
    pid = m.group(1)
    k, dd = m.end(), 1
    while k < len(pt) and dd:
        if pt[k] == "{":
            dd += 1
        elif pt[k] == "}":
            dd -= 1
        k += 1
    body = pt[m.end():k - 1]
    mc = re.search(r"(?m)^\s*culture\s*=\s*([a-z0-9_]+)", body)
    if pid not in pc:
        pc[pid] = mc.group(1) if mc else "(none)"

print()
print("%-24s %-6s %-18s %-26s %s" % ("barony", "prov", "culture", "heritage", "language"))
cnt = collections.Counter()
for b, pid in pairs:
    c = pc.get(pid, "(no block)")
    cnt[(c, her.get(c, "?"))] += 1
    print("%-24s %-6s %-18s %-26s %s" % (b, pid, c, her.get(c, "?"), lang.get(c, "")))
print()
print("== 汇总 ==")
for (c, h), n in cnt.most_common():
    print("  %-18s %-26s %d" % (c, h, n))
