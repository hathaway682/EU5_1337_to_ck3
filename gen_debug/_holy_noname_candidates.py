# -*- coding: utf-8 -*-
"""只读：为「无中文本地化」的圣地找落点候选。
对每个 key 输出：当前 barony(county,中文) / mod 里同名 key 的 barony 与 county /
以及 key 里各词根能命中的 barony（按 key 字符串包含）。
"""
import io
import os
import re

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(MOD, "common", "religion", "holy_site_types", "00_holy_site_types.txt")
LT = os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt")
GAME = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"

KEYS = """napata colonea armagh yamama qom puri badrinath shringeri prambanan
preah_vihear lejre zeeland sparta suzhou mount_kunyu ishizuchi haku koya haguro
shaolin hangzhou jiuhua putuo shicheng jianchang bulguksa donggang danai magadha
tate awa quanzhou turpan quzhou linzi zhuolu dongting wehale cheongju goseong
nanhua sarasvati mogao gaeseong hiei heiankyo""".split()


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


def load_loc(root):
    out = {}
    for dp, _, fs in os.walk(root):
        for f in fs:
            if not f.endswith(".yml"):
                continue
            try:
                t = io.open(os.path.join(dp, f), encoding="utf-8-sig", errors="ignore").read()
            except Exception:
                continue
            for m in re.finditer(r'(?m)^\s*([A-Za-z0-9_.\-]+):\d*\s*"((?:[^"]|"")*)"', t):
                out.setdefault(m.group(1), m.group(2).replace('""', '"'))
    return out


locm = load_loc(os.path.join(MOD, "localization", "simp_chinese"))
locg = load_loc(os.path.join(GAME, "localization", "simp_chinese"))
loc = lambda k: locm.get(k) or locg.get(k)

# landed_titles：barony -> county，county -> 中文
lt = read(LT)
bar2c, cty_order, cur_c = {}, [], None
for ln in lt.split("\n"):
    s = ln.strip()
    m = re.match(r"^(c_[A-Za-z0-9_]+)\s*=\s*\{", s)
    if m:
        cur_c = m.group(1)
        cty_order.append(cur_c)
        continue
    m = re.match(r"^(b_[A-Za-z0-9_]+)\s*=\s*\{", s)
    if m and cur_c:
        bar2c[m.group(1)] = cur_c

bars = sorted(bar2c)
ctys = sorted(set(bar2c.values()))

# 圣地文件：key -> barony / county
lines = io.open(SRC, "rb").read().decode("utf-8-sig").split("\r\n")
depth, cur, hs = 0, None, {}
for ln in lines:
    m = re.match(r"^([A-Za-z0-9_\-]+)\s*=\s*\{", ln)
    if depth == 0 and m:
        cur = m.group(1)
        hs[cur] = {"c": None, "b": None}
    if depth == 1 and cur:
        mc = re.match(r"^\s*county\s*=\s*(\S+)", ln)
        mb = re.match(r"^\s*barony\s*=\s*(\S+)", ln)
        if mc:
            hs[cur]["c"] = mc.group(1)
        if mb:
            hs[cur]["b"] = mb.group(1)
    depth += ln.count("{") - ln.count("}")

for k in KEYS:
    h = hs.get(k, {})
    cb, cc = h.get("b"), h.get("c")
    print("=" * 74)
    print("%-18s 现指 %-22s %-10s (县 %s %s)"
          % (k, cb or "-", loc(cb) or "", cc or "-", loc(cc) or ""))
    # 1) key 完全同名
    exact = [b for b in bars if b == "b_" + k]
    for b in exact:
        print("   [同名barony] %-24s %-12s 县 %-22s %s"
              % (b, loc(b) or "", bar2c[b], loc(bar2c[b]) or ""))
    ce = [c for c in ctys if c == "c_" + k]
    for c in ce:
        print("   [同名county] %-24s %-12s" % (c, loc(c) or ""))
    # 2) key 词根命中（长度>=4 的词根）
    roots = [w for w in k.split("_") if len(w) >= 4]
    hit = []
    for b in bars:
        nm = b[2:]
        for r in roots:
            if r in nm and b != "b_" + k:
                hit.append((b, r))
                break
    if hit:
        print("   [词根命中 %s]" % ",".join(roots))
        for b, r in hit[:12]:
            print("      %-26s %-12s 县 %-22s %s" % (b, loc(b) or "", bar2c[b], loc(bar2c[b]) or ""))
    # 3) 当前所在县的全部 barony
    if cb and cb in bar2c:
        c0 = bar2c[cb]
        sib = [b for b in bars if bar2c[b] == c0]
        print("   [同县 %s %s 的 barony]" % (c0, loc(c0) or ""))
        print("      " + " ".join("%s=%s" % (b, loc(b) or "?") for b in sib[:24]))
