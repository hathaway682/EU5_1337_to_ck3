# -*- coding: utf-8 -*-
"""为新增的 eu5_language_<x> pillar key 补本地化（名字取 EU5 自己的词条）。

只补英文，沿用 gen_cultures_l_english.yml 现有约定（` key:0 "Value"`）。
默认 dry-run，--apply 落盘（先备份）。
"""
import io, os, re, shutil, sys, collections
from datetime import datetime

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
EU5LOC = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game\main_menu\localization"
CULT = os.path.join(MOD, "common", "culture", "cultures", "00_generated_cultures.txt")
LOC = os.path.join(MOD, "localization", "english", "gen_cultures_l_english.yml")
APPLY = "--apply" in sys.argv

DEF = re.compile(r"(?ms)^\t?([a-z0-9_]+)\s*=\s*\{")


def rd(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


def top_keys(text):
    out, i, n = {}, 0, len(text)
    while i < n:
        m = DEF.search(text, i)
        if not m:
            break
        j, d = m.end(), 1
        while j < n and d:
            c = text[j]
            if c == "{":
                d += 1
            elif c == "}":
                d -= 1
            j += 1
        out[m.group(1)] = text[m.end():j - 1]
        i = j
    return out


def field(b, k):
    m = re.search(r"(?m)^\s*" + k + r"\s*=\s*([a-z0-9_]+)", b)
    return m.group(1) if m else ""


# 1. 我们文件里实际使用的 eu5_language_* key -> EU5 language 名
used = set()
for k, b in top_keys(rd(CULT)).items():
    v = field(b, "language")
    if v.startswith("eu5_language_"):
        used.add((v, v[len("eu5_language_"):]))
print("使用的 eu5_language_* key: %d" % len(used))

# 2. EU5 英文 localization: language key -> name
en_names = {}
p = os.path.join(EU5LOC, "english", "languages_desc_l_english.yml")
for name in [p] + [os.path.join(EU5LOC, "english", f) for f in
                   ("cultural_and_languages_l_english.yml", "culture_groups_l_english.yml")]:
    if not os.path.exists(name):
        continue
    for line in rd(name).split("\n"):
        m = re.match(r'^\s*([a-z0-9_]+):\d*\s*"([^"]*)"\s*$', line)
        if m:
            en_names.setdefault(m.group(1), m.group(2))
print("EU5 english language 词条: %d" % len(en_names))

# 3. 生成新行
rows = []
noloc = []
for key, lg in sorted(used):
    nm = en_names.get(lg, "")
    if not nm:
        noloc.append(lg)
        nm = lg.replace("_language", "").replace("_dialect", "").replace("_", " ").title()
    rows.append((key + "_name", nm))
print("EU5 无英文词条、用键名美化兜底: %d %s" % (len(noloc), noloc[:10]))

# 4. 合并进 yml（保持排序；已有键不动）
text = rd(LOC)
lines = text.split("\n")
have = set()
for line in lines:
    m = re.match(r"^\s*([a-z0-9_]+):", line)
    if m:
        have.add(m.group(1))
add = [(k, v) for k, v in rows if k not in have]
skip = [(k, v) for k, v in rows if k in have]
print("已存在跳过: %d | 待插入: %d" % (len(skip), len(skip)))
if skip[:3]:
    print("  例:", skip[:3])

# 找插入点：最后一个 eu5_heritage_*_name 之后
insert_at = None
for i, line in enumerate(lines):
    if re.match(r"^\s*eu5_heritage_[a-z0-9_]+_name:", line):
        insert_at = i + 1
if insert_at is None:
    for i, line in enumerate(lines):
        if line.strip() == "l_english:":
            insert_at = i + 1
print("插入位置: 第 %d 行后（该行: %r）" % (insert_at, lines[insert_at - 1][:60] if insert_at else None))

new_lines = lines[:insert_at] + [" %s:0 \"%s\"" % (k, v) for k, v in add] + lines[insert_at:]
print("插入 %d 行，行数 %d -> %d" % (len(add), len(lines), len(new_lines)))

if APPLY:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = LOC + ".bak_langloc_" + ts
    shutil.copy2(LOC, bak)
    out = "\n".join(new_lines)
    # 保持 BOM + CRLF
    raw = io.open(LOC, "rb").read()
    bom = raw[:3] == b"\xef\xbb\xbf"
    crlf = raw.count(b"\r\n") > (raw.count(b"\n") - raw.count(b"\r\n"))
    if crlf:
        out = out.replace("\r\n", "\n").replace("\n", "\r\n")
    io.open(LOC, "w", encoding="utf-8-sig" if bom else "utf-8", newline="").write(out)
    print("已写回 %s (备份 %s)" % (LOC, bak))
else:
    print("dry-run：未写盘。加 --apply 执行。")
print()
print("== 样例 ==")
for k, v in add[:12]:
    print("  %-46s \"%s\"" % (k, v))
