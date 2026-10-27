# -*- coding: utf-8 -*-
"""只读分析：我们 mod 的文化能否把 heritage / language 对到 CK3 原版。

现状：
  - 我们的 culture 定义里 heritage = <EU5 culture_group>，language = eu5_heritage_<EU5 culture_group>
  - 这两个 key 都是 mod 自己生成的（00_generated_pillars.txt），CK3 原版没有
目标：看 EU5 culture_group -> CK3 heritage、EU5 language -> CK3 language 的映射可行性与缺口

输出 gen_debug/_heritage_language_probe.log
"""
import io, os, re, glob
from collections import Counter, defaultdict

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
CK3 = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game\in_game"
OUT = os.path.join(MOD, "gen_debug", "_heritage_language_probe.log")

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


L = []
def p(s=""):
    L.append(s)


# ---- CK3 vanilla heritage / language ----
def vanilla_pillars(fn):
    out = []
    for path, key, body in walk(read(os.path.join(CK3, "common", "culture", "pillars", fn))):
        if path:
            continue
        out.append(key)
    return out

v_her = vanilla_pillars("00_heritage.txt")
v_lang = vanilla_pillars("00_language.txt")
p("CK3 vanilla: heritage %d, language %d" % (len(v_her), len(v_lang)))

# ---- 我们的 cultures ----
ours = {}
for path, key, body in walk(read(os.path.join(MOD, "common", "culture", "cultures", "00_generated_cultures.txt"))):
    if path:
        continue
    h = re.search(r"(?m)^\s*heritage\s*=\s*(\S+)", body)
    lg = re.search(r"(?m)^\s*language\s*=\s*(\S+)", body)
    ours[key] = (h.group(1) if h else "", lg.group(1) if lg else "")
p("our cultures: %d" % len(ours))

# ---- 我们的 province 文化 -> 男爵领数 ----
raw = read(os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt"))
cnt = Counter(re.findall(r"(?m)^\s*culture\s*=\s*(\S+)", raw))
p("our provinces: %d, distinct culture: %d" % (sum(cnt.values()), len(cnt)))

# ---- EU5 culture -> (group, language) ----
eu5 = {}
for fn in os.listdir(os.path.join(EU5, "common", "cultures")):
    if not fn.endswith(".txt"):
        continue
    for path, key, body in walk(read(os.path.join(EU5, "common", "cultures", fn))):
        if path:
            continue
        g = re.search(r"culture_groups\s*=\s*\{([^}]*)\}", body)
        lg = re.search(r"(?m)^\s*language\s*=\s*(\S+)", body)
        eu5[key] = (g.group(1).strip().split()[0] if g and g.group(1).strip() else "",
                    lg.group(1) if lg else "")
p("EU5 cultures: %d" % len(eu5))

# ---- 汇总：heritage 维度 ----
def norm(s):
    s = re.sub(r"^heritage_", "", s)
    s = re.sub(r"^language_", "", s)
    s = re.sub(r"^eu5_heritage_", "", s)
    s = re.sub(r"_(group|language|dialect)$", "", s)
    return s

vher_norm = {norm(x): x for x in v_her}
vlang_norm = {norm(x): x for x in v_lang}

her_stat = defaultdict(lambda: {"cultures": 0, "baronies": 0, "langs": set(), "eu5langs": set()})
for c, (h, lg) in ours.items():
    if not h:
        continue
    s = her_stat[h]
    s["cultures"] += 1
    s["baronies"] += cnt.get(c, 0)
    s["langs"].add(lg)
    s["eu5langs"].add(eu5.get(c, ("", ""))[1])

p()
p("== 我们的 heritage（= EU5 culture_group）%d 个 ==" % len(her_stat))
p("%-34s %6s %7s %5s %-24s %-24s" % ("heritage", "文化", "男爵领", "语种", "CK3候选heritage", "CK3候选language"))
for h, s in sorted(her_stat.items(), key=lambda kv: -kv[1]["baronies"]):
    n = norm(h)
    cand_h = vher_norm.get(n, "")
    cand_l = vlang_norm.get(n, "")
    p("%-34s %6d %7d %5d %-24s %-24s"
      % (h, s["cultures"], s["baronies"], len(s["langs"]), cand_h or "-", cand_l or "-"))

# ---- 汇总：EU5 language 维度 ----
lg_stat = defaultdict(lambda: {"cultures": 0, "baronies": 0, "groups": set()})
for c, (h, lg) in ours.items():
    el = eu5.get(c, ("", ""))[1]
    if not el:
        continue
    s = lg_stat[el]
    s["cultures"] += 1
    s["baronies"] += cnt.get(c, 0)
    s["groups"].add(h)

p()
p("== EU5 language %d 个（我们实际用到的）==" % len(lg_stat))
p("%-34s %6s %7s %-24s" % ("eu5_language", "文化", "男爵领", "CK3候选language"))
for lg, s in sorted(lg_stat.items(), key=lambda kv: -kv[1]["baronies"]):
    n = norm(lg)
    cand = vlang_norm.get(n, "")
    p("%-34s %6d %7d %-24s" % (lg, s["cultures"], s["baronies"], cand or "-"))

# ---- 覆盖率估算 ----
tot_bar = sum(cnt.values())
hit_h = sum(s["baronies"] for h, s in her_stat.items() if norm(h) in vher_norm)
hit_l = sum(s["baronies"] for lg, s in lg_stat.items() if norm(lg) in vlang_norm)
p()
p("== 自动同名匹配的覆盖率（只做名字归一化，未人工校正）==")
p("heritage: %d/%d 男爵领 = %.1f%%" % (hit_h, tot_bar, 100.0 * hit_h / tot_bar))
p("language: %d/%d 男爵领 = %.1f%%" % (hit_l, tot_bar, 100.0 * hit_l / tot_bar))

# 我们的 language 现状
p()
p("== 我们 culture 里的 language 字段形态 ==")
lgvals = Counter(v[1] for v in ours.values())
p("distinct: %d; 样例: %s" % (len(lgvals), list(lgvals.items())[:5]))

io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L))
print("ok")
