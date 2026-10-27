# -*- coding: utf-8 -*-
"""只读：文化传承 = heritage_iberian 的男爵领，按 王国/公国 汇总（括号平衡解析）。"""
import io, os, re, collections

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
LT = os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt")
PROV = os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt")
CULT = os.path.join(MOD, "common", "culture", "cultures", "00_generated_cultures.txt")


def rd(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


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
    pc.setdefault(m.group(1), mc.group(1) if mc else "")

t = rd(LT)
tok = re.compile(r"([a-z0-9_]+)\s*=\s*\{|\{|\}")
stack = []
rec = {}
for m in tok.finditer(t):
    s = m.group(0)
    if s == "}":
        if stack:
            stack.pop()
        continue
    if s == "{":
        stack.append("?")
        continue
    key = m.group(1)
    stack.append(key)
    if key.startswith("b_"):
        mp = re.search(r"\bprovince\s*=\s*(\d+)", t[m.end():m.end() + 400])
        if mp:
            d = next((x for x in reversed(stack[:-1]) if x.startswith("d_")), "")
            kk = next((x for x in reversed(stack[:-1]) if x.startswith("k_")), "")
            rec.setdefault(mp.group(1), (key, d, kk))

rows = collections.Counter()
detail = collections.defaultdict(list)
for pid, cult in pc.items():
    if her.get(cult) != "heritage_iberian":
        continue
    b, d, k = rec.get(pid, ("?", "?", "?"))
    key = (k[2:] if k else "(no k)", d[2:] if d else "(no d)", cult)
    rows[key] += 1
    detail[key].append("%s(%s)" % (b[2:], pid))

print("heritage_iberian 男爵领总计: %d" % sum(rows.values()))
print()
print("%-16s %-24s %-12s %4s  %s" % ("kingdom", "duchy", "culture", "n", "样例"))
for (k, d, c), n in sorted(rows.items(), key=lambda kv: (-kv[1], kv[0])):
    if n >= 5:
        print("%-16s %-24s %-12s %4d  %s" % (k, d, c, n, ",".join(detail[(k, d, c)][:5])))
print()
print("== 法国系王国下的全部（含 n<5）==")
for (k, d, c), n in sorted(rows.items()):
    if k in ("france", "aquitaine", "burgundy", "arles", "frisia", "lotharingia"):
        print("  %-12s %-22s %-12s %2d  %s"
              % (k, d, c, n, ",".join(detail[(k, d, c)])))
