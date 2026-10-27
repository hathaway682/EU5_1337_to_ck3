# -*- coding: utf-8 -*-
"""只读探查：CU 的 province 文化字段形态 + 我们 mod 的 landed_titles 层级 + province 文化样例"""
import io, os, re, glob
from collections import Counter

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
CU = r"E:\SteamLibrary\steamapps\workshop\content\1158310\3811443965"
OUT = os.path.join(MOD, "gen_debug", "_probe_cu_culture.log")


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


lines = []
files = sorted(glob.glob(os.path.join(CU, "history", "provinces", "*.txt")))
lines.append("CU province history files: %d" % len(files))
for p in files[:40]:
    lines.append("  %s (%d bytes)" % (os.path.basename(p), os.path.getsize(p)))

# 统计 culture= 出现次数 & 值分布
cult = Counter()
pat = re.compile(r"(?m)^\s*culture\s*=\s*(\S+)")
n_files_with = 0
for p in files:
    t = read(p)
    ms = pat.findall(t)
    if ms:
        n_files_with += 1
    for v in ms:
        cult[v] += 1
lines.append("files containing culture=: %d / %d" % (n_files_with, len(files)))
lines.append("distinct culture values: %d" % len(cult))
lines.append("top 40: %s" % cult.most_common(40))

# 看一个样例块
for p in files:
    t = read(p)
    m = pat.search(t)
    if m:
        s = max(0, m.start() - 400)
        lines.append("\n--- sample from %s ---" % os.path.basename(p))
        lines.append(t[s:m.end() + 600])
        break

# 我们 mod landed_titles 层级
lt = read(os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt"))
lines.append("\n== our landed_titles ==")
lines.append("len=%d  e_=%d k_=%d d_=%d c_=%d b_=%d"
             % (len(lt),
                len(re.findall(r"(?m)^\s*e_[a-z0-9_\-]+\s*=\s*\{", lt)),
                len(re.findall(r"(?m)^\s*k_[a-z0-9_\-]+\s*=\s*\{", lt)),
                len(re.findall(r"(?m)^\s*d_[a-z0-9_\-]+\s*=\s*\{", lt)),
                len(re.findall(r"(?m)^\s*c_[a-z0-9_\-]+\s*=\s*\{", lt)),
                len(re.findall(r"(?m)^\s*b_[a-z0-9_\-]+\s*=\s*\{", lt))))

# 我们 province 文件样例
gp = read(os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt"))
m = re.search(r"(?ms)^1\s*=\s*\{.*?^\}", gp)
lines.append("\n== our province 1 ==")
lines.append(m.group(0) if m else "(none)")
our_cult = Counter(re.findall(r"(?m)^\s*culture\s*=\s*(\S+)", gp))
lines.append("\nour province-file distinct culture: %d  top20: %s"
             % (len(our_cult), our_cult.most_common(20)))

io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
print("written")
