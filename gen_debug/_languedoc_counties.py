# -*- coding: utf-8 -*-
"""只读：d_languedoc 各伯爵领的男爵领顺序（CK3 只读首府男爵领的文化）。"""
import io, os, re

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

her = {}
cur = None
for line in rd(CULT).split("\n"):
    m = re.match(r"^([a-z0-9_]+)\s*=\s*\{\s*$", line)
    if m:
        cur = m.group(1)
        continue
    mh = re.match(r"^\s*heritage\s*=\s*([a-z0-9_]+)", line)
    if mh and cur:
        her[cur] = mh.group(1)

pt = rd(PROV)
pc = {}
for m in re.finditer(r"(?m)^(\d+)\s*=\s*\{", pt):
    k, dd = m.end(), 1
    while k < len(pt) and dd:
        if pt[k] == "{":
            dd += 1
        elif pt[k] == "}":
            dd -= 1
        k += 1
    mc = re.search(r"(?m)^\s*culture\s*=\s*([a-z0-9_]+)", pt[m.end():k - 1])
    pc.setdefault(m.group(1), mc.group(1) if mc else "(none)")

# 拆伯爵领
for cm in re.finditer(r"(c_[a-z0-9_]+)\s*=\s*\{", blk):
    name = cm.group(1)
    k, dd = cm.end(), 1
    while k < len(blk) and dd:
        if blk[k] == "{":
            dd += 1
        elif blk[k] == "}":
            dd -= 1
        k += 1
    cblk = blk[cm.end():k - 1]
    bars = re.findall(r"(b_[a-z0-9_]+)\s*=\s*\{\s*province\s*=\s*(\d+)", cblk)
    cap = re.search(r"(?m)^\s*capital\s*=\s*(b_[a-z0-9_]+)", cblk)
    capname = cap.group(1) if cap else (bars[0][0] if bars else "?")
    cappid = dict(bars).get(capname, "")
    ccap = pc.get(cappid, "?")
    mixed = sorted({pc.get(p, "?") for _, p in bars})
    flag = "  <== 首府是 gascon" if ccap == "gascon" else ""
    print("%-18s 首府 %-22s %-14s 传承 %-24s | 领内文化 %s%s"
          % (name, capname, ccap, her.get(ccap, "?"), ",".join(mixed), flag))
