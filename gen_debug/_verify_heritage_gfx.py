# -*- coding: utf-8 -*-
"""校验：每个有 heritage_* 的文化，其 gfx 四件套必须精确等于 HERITAGE_GFX 里该 heritage 的组合。只读。"""
import io, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _restore_eu5_aesthetics as A

SRC = os.path.join(A.MOD, "common", "culture", "cultures", "00_generated_cultures.txt")
raw = io.open(SRC, encoding="utf-8-sig", errors="ignore").read()

BLOCK = re.compile(r"([A-Za-z0-9_]+)\s*=\s*\{")


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


bad = []
ok = 0
custom = 0
for path, key, body in walk(raw):
    if path or key == "gen_culture_unsettled":
        continue
    h = re.search(r"(?m)^\s*heritage\s*=\s*(\S+)", body)
    if not h:
        continue
    her = h.group(1)
    if not her.startswith("heritage_"):
        custom += 1
        continue
    want = A.HERITAGE_GFX.get(her)
    if want is None:
        bad.append((key, her, "NO TABLE ENTRY"))
        continue
    got = []
    for f in A.FIELDS:
        m = re.search(f + r"\s*=\s*\{([^}]*)\}", body)
        got.append(" ".join(m.group(1).split()) if m else "")
    if tuple(got) != want:
        bad.append((key, her, " | ".join(got)))
    else:
        ok += 1

print("heritage 文化四件套精确匹配: %d" % ok)
print("自定义 heritage（不检查）: %d" % custom)
print("不匹配: %d" % len(bad))
for k, h, g in bad[:20]:
    print("  %-26s %-24s %s" % (k, h, g))
