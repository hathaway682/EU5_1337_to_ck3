# -*- coding: utf-8 -*-
"""校验：每个文化的 gfx 四件套是否成套（同一组合），以及所有 key 是否为 CK3 原版合法 key。只读。"""
import io, os, re, sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _restore_eu5_aesthetics as A

SRC = os.path.join(A.MOD, "common", "culture", "cultures", "00_generated_cultures.txt")
CK3 = r"E:\SteamLibrary\steamapps\common\Crusader Keys III\game"
CK3 = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"
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
        yield path, m.group(1), text[m.end():j - 1]
        yield from walk(text[m.end():j - 1], path + (m.group(1),))
        i = j


# 原版合法 key（文化四件套词表）
valid = set()
for fn in sorted(os.listdir(os.path.join(CK3, "common", "culture", "cultures"))):
    if not fn.endswith(".txt"):
        continue
    for path, key, body in walk(read(os.path.join(CK3, "common", "culture", "cultures", fn))):
        if path:
            continue
        for f in A.FIELDS:
            m = re.search(f + r"\s*=\s*\{([^}]*)\}", body)
            if m:
                valid |= set(m.group(1).split())

# 组合是否成套：每个文化的四件套必须能对应到某个已登记组合（heritage/tag 表里的），
# 或整体保持原样（美洲）
registered = set(A.HERITAGE_GFX.values()) | {A.PAPUAN, A.MALAY, A.WEST_AFRICAN}

raw = read(SRC)
# 单行块（gen_culture_unsettled）特殊处理：整行取出
m = re.search(r"(?m)^gen_culture_unsettled = \{(.*)\}\s*$", raw)
oneline = m.group(0) if m else ""

text = raw
quad_re = re.compile(r"coa_gfx\s*=\s*\{([^}]*)\}\s*building_gfx\s*=\s*\{([^}]*)\}\s*"
                     r"clothing_gfx\s*=\s*\{([^}]*)\}\s*unit_gfx\s*=\s*\{([^}]*)\}")

bad_key = Counter()
not成套 = []
n = 0
for path, key, body in walk(text):
    if path or key == "gen_culture_unsettled":
        continue
    q = quad_re.search(body)
    if not q:
        continue
    n += 1
    vals = [" ".join(q.group(i).split()) for i in range(1, 5)]
    for v in vals:
        for k in v.split():
            if k not in valid:
                bad_key[k] += 1
    combo = tuple(vals)
    if combo not in registered:
        not成套.append((key, combo))

print("检查文化块: %d" % n)
print("非法 gfx key: %d %s" % (len(bad_key), dict(bad_key)))
print("四件套未登记组合（= 保持原样的美洲文化）: %d" % len(not成套))
for k, c in not成套[:10]:
    print("   %-26s %s" % (k, " | ".join(c)))
# 单行块
if oneline:
    q = quad_re.search(oneline)
    vals = [" ".join(q.group(i).split()) for i in range(1, 5)]
    print("gen_culture_unsettled: %s" % " | ".join(vals))
    for v in vals:
        for k in v.split():
            if k not in valid:
                print("   ILLEGAL KEY: %s" % k)
