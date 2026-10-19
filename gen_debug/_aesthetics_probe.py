# -*- coding: utf-8 -*-
"""探查：原版 gfx 四件套完整词表 + 我们文化的 EU5 tags 分布 + 当前 gfx 使用情况。只读。"""
import io, os, re
from collections import Counter, defaultdict

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
CK3 = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game\in_game"

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


def top_blocks(text):
    """顶层块。"""
    for path, key, body in walk(text):
        if not path:
            yield key, body


def gfx_quad(body):
    c = re.search(r"coa_gfx\s*=\s*\{([^}]*)\}", body)
    b = re.search(r"building_gfx\s*=\s*\{([^}]*)\}", body)
    l = re.search(r"clothing_gfx\s*=\s*\{([^}]*)\}", body)
    u = re.search(r"unit_gfx\s*=\s*\{([^}]*)\}", body)
    if not (c and b and l and u):
        return None
    return (tuple(c.group(1).split()), tuple(b.group(1).split()),
            tuple(l.group(1).split()), tuple(u.group(1).split()))


# 1. 原版完整词表
van = {}
for fn in sorted(os.listdir(os.path.join(CK3, "common", "culture", "cultures"))):
    if not fn.endswith(".txt"):
        continue
    for key, body in top_blocks(read(os.path.join(CK3, "common", "culture", "cultures", fn))):
        q = gfx_quad(body)
        if q:
            van[key] = q

coa, bld, clo, uni = Counter(), Counter(), Counter(), Counter()
for q in van.values():
    coa.update(q[0]); bld.update(q[1]); clo.update(q[2]); uni.update(q[3])
print("== 原版 culture gfx 词表（%d 个文化）==" % len(van))
print("coa:      ", " ".join(sorted(coa)))
print("building: ", " ".join(sorted(bld)))
print("clothing: ", " ".join(sorted(clo)))
print("unit:     ", " ".join(sorted(uni)))

# 用 walk 方式再扫 buildings/activities 里出现的 key，补全词表
extra = set()
for sub in ("common/buildings", "common/activities"):
    for root, _, files in os.walk(os.path.join(CK3, sub)):
        for fn in files:
            if not fn.endswith(".txt"):
                continue
            t = read(os.path.join(root, fn))
            extra |= set(re.findall(r"\b([a-z0-9_]+_gfx)\b", t))
print("\n== buildings/activities 里出现但我们 culture 词表没有的 ==")
known = set(coa) | set(bld) | set(clo) | set(uni)
print(" ".join(sorted(extra - known)))

# 2. EU5 culture -> tags/language/groups
eu5 = {}
for fn in sorted(os.listdir(os.path.join(EU5, "common", "cultures"))):
    if not fn.endswith(".txt"):
        continue
    for key, body in top_blocks(read(os.path.join(EU5, "common", "cultures", fn))):
        tags = re.search(r"(?m)^\s*tags\s*=\s*\{([^}]*)\}", body)
        lg = re.search(r"(?m)^\s*language\s*=\s*(\S+)", body)
        gr = re.search(r"(?ms)^\s*culture_groups\s*=\s*\{(.*?)\}", body)
        eu5[key] = {
            "tags": set(tags.group(1).split()) if tags else set(),
            "language": lg.group(1) if lg else "",
            "groups": set(gr.group(1).split()) if gr else set(),
        }
print("\nEU5 cultures parsed: %d" % len(eu5))

# 3. 我们的文化 -> 当前 gfx + EU5 tags
ours = {}
for key, body in top_blocks(read(os.path.join(MOD, "common", "culture", "cultures", "00_generated_cultures.txt"))):
    q = gfx_quad(body)
    if q:
        ours[key] = q
print("our cultures: %d" % len(ours))

# 4. EU5 tags 在我们文化里的分布
tagcnt = Counter()
for k in ours:
    e = eu5.get(k)
    if e:
        tagcnt.update(e["tags"])
print("\n== EU5 tags 在我们文化里的分布 ==")
for t, c in tagcnt.most_common():
    print("  %-32s %5d" % (t, c))

# 5. 当前 gfx 使用
qcnt = Counter(ours.values())
print("\n== 我们当前 gfx 组合 top20 ==")
for q, c in qcnt.most_common(20):
    print("  %5d %s" % (c, q))
print("distinct quads: %d" % len(qcnt))

# 6. 每个文化的 tag 数分布
ncnt = Counter(len(eu5.get(k, {}).get("tags", ())) for k in ours)
print("\ntag 数分布:", dict(sorted(ncnt.items())))
noeu5 = [k for k in ours if k not in eu5]
print("无 EU5 来源: %d %s" % (len(noeu5), noeu5))
