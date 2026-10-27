# -*- coding: utf-8 -*-
"""只读：对比本次运行前后的 rite 变化，确认只有马达加斯加动了"""
import io, re, os, collections

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
NEW = os.path.join(MOD, "history/provinces/00_generated_provinces.txt")
OLD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\_backup_20261019_194855_before_islamic_geo_spread\history\provinces\00_generated_provinces.txt"

out = io.open(os.path.join(MOD, "gen_debug", "_madagascar_diff.out"), "w", encoding="utf-8")
def w(s=""):
    out.write(str(s) + "\n")

def parse(path):
    txt = io.open(path, encoding="utf-8-sig", errors="ignore").read()
    d = {}
    for m in re.finditer(r"(?m)^(\d+) = \{(.*?)\n\}", txt, re.S):
        pid = int(m.group(1)); body = m.group(2)
        f = re.search(r"(?m)^\s*faith = (\S+)", body)
        r = re.search(r"(?m)^\s*rite = (\S+)", body)
        d[pid] = (f.group(1) if f else None, r.group(1) if r else None)
    return d

new = parse(NEW); old = parse(OLD)
w("blocks old=%d new=%d" % (len(old), len(new)))

w("\n==== faith 变化 ====")
fdiff = [(p, old[p][0], new[p][0]) for p in old if p in new and old[p][0] != new[p][0]]
w("共 %d 处" % len(fdiff))
for p, a, b in fdiff[:30]:
    w("  p%-6d %s -> %s" % (p, a, b))

w("\n==== rite 变化 ====")
rdiff = [(p, old[p][1], new[p][1]) for p in old if p in new and old[p][1] != new[p][1]]
w("共 %d 处" % len(rdiff))
for p, a, b in rdiff:
    w("  p%-6d %s -> %s" % (p, a, b))

w("\n==== rite 计数 ====")
co = collections.Counter(v[1] for v in old.values())
cn = collections.Counter(v[1] for v in new.values())
keys = set(co) | set(cn)
for k in sorted(keys, key=lambda x: -(cn.get(x, 0))):
    a, b = co.get(k, 0), cn.get(k, 0)
    flag = "" if a == b else "   <<< %+d" % (b - a)
    w("  %-22s %5d -> %5d%s" % (str(k), a, b, flag))
w("总 rite 行: %d -> %d" % (sum(v for k, v in co.items() if k), sum(v for k, v in cn.items() if k)))

out.close()
print("done")
