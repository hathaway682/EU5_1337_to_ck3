# -*- coding: utf-8 -*-
"""只读：把我们用到的 EU5 language 全部列出来，带男爵领权重和 CK3 同名候选。"""
import io, os, re, csv
from collections import Counter, defaultdict

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
CK3 = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game\in_game"
OUTDIR = os.path.join(MOD, "gen_debug")

BLOCK = re.compile(r"([A-Za-z0-9_]+)\s*=\s*\{")


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


def walk(text, path=()):
    i, n = 0, len(text)
    while i < n:
        m = BLOCK.search(text, i)
        if not m:
            return
        j, d = m.end(), 1
        while j < n and d:
            c = text[j]
            if c == "{":
                d += 1
            elif c == "}":
                d -= 1
            j += 1
        body = text[m.end():j - 1]
        yield path, m.group(1), body
        yield from walk(body, path + (m.group(1),))
        i = j


# EU5 culture -> language
eu5_lang = {}
for fn in os.listdir(os.path.join(EU5, "common", "cultures")):
    if not fn.endswith(".txt"):
        continue
    for path, key, body in walk(read(os.path.join(EU5, "common", "cultures", fn))):
        if path:
            continue
        lg = re.search(r"(?m)^\s*language\s*=\s*(\S+)", body)
        if lg:
            eu5_lang[key] = lg.group(1)

# 我们的 culture -> 男爵领
raw = read(os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt"))
cnt = Counter(re.findall(r"(?m)^\s*culture\s*=\s*(\S+)", raw))

# CK3 language 清单
ck3_lang = []
for path, key, body in walk(read(os.path.join(CK3, "common", "culture", "pillars", "00_language.txt"))):
    if not path:
        ck3_lang.append(key)


def norm(s):
    s = re.sub(r"^language_", "", s)
    s = re.sub(r"_(language|dialect|group)$", "", s)
    return s


ck3_norm = {norm(x): x for x in ck3_lang}

stat = defaultdict(lambda: {"cultures": 0, "baronies": 0})
no_lang = []
for c, n in cnt.items():
    lg = eu5_lang.get(c)
    if not lg:
        no_lang.append(c)
        continue
    stat[lg]["cultures"] += 1
    stat[lg]["baronies"] += n

rows = sorted(stat.items(), key=lambda kv: -kv[1]["baronies"])
tot = sum(v["baronies"] for _, v in rows)
acc = 0
L = []
L.append("EU5 language 用到: %d 个；男爵领合计 %d；没有 language 的文化: %d 个"
         % (len(rows), tot, len(no_lang)))
L.append("%-40s %5s %6s %7s %-24s" % ("eu5_language", "文化", "男爵领", "累计%", "CK3同名候选"))
for lg, s in rows:
    acc += s["baronies"]
    cand = ck3_norm.get(norm(lg), "")
    L.append("%-40s %5d %6d %7.1f %-24s"
             % (lg, s["cultures"], s["baronies"], 100.0 * acc / tot, cand or "-"))
if no_lang:
    L.append("")
    L.append("没有 language 的文化: " + " ".join(no_lang[:50]))

io.open(os.path.join(OUTDIR, "_eu5_language_list.log"), "w",
        encoding="utf-8", newline="\n").write("\n".join(L))

with io.open(os.path.join(OUTDIR, "_eu5_language_list.csv"), "w",
             encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["eu5_language", "cultures", "baronies", "ck3_auto_candidate"])
    for lg, s in rows:
        w.writerow([lg, s["cultures"], s["baronies"], ck3_norm.get(norm(lg), "")])
print("ok")
