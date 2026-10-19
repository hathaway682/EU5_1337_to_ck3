# -*- coding: utf-8 -*-
"""校验本地化插入结果：编码/重复键/格式/边界。"""
import io, re, collections, sys

LOC = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape\localization\english\gen_cultures_l_english.yml"
BAK = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape\localization\english\gen_cultures_l_english.yml.bak_langloc_20261020_011702"

raw = open(LOC, "rb").read()
t = io.open(LOC, encoding="utf-8-sig").read()
print("BOM: %s | CRLF: %d | LF-only: %d"
      % (raw[:3] == b"\xef\xbb\xbf", raw.count(b"\r\n"),
         raw.count(b"\n") - raw.count(b"\r\n")))
lines = t.split("\n")
keys = [m.group(1) for m in re.finditer(r"(?m)^\s*([a-z0-9_]+):\d+", t)]
dup = [k for k, c in collections.Counter(keys).items() if c > 1]
print("keys: %d | dup: %s" % (len(keys), dup or "none"))
print("eu5_language_* entries: %d" % sum(1 for k in keys if k.startswith("eu5_language_")))
bad = [l for l in lines
       if l.strip() and not l.startswith("#") and l.strip() != "l_english:"
       and not re.match(r'^\s*[a-z0-9_]+:\d+\s+".*"$', l)]
print("格式异常行: %s" % (bad[:3] if bad else "none"))

o = io.open(BAK, encoding="utf-8-sig").read()
ol = o.split("\n")
print("行数: %d -> %d (+%d)" % (len(ol), len(lines), len(lines) - len(ol)))
# 除了插入块之外，原有内容应逐行一致（去掉插入的 313 行）
new_entries = set(re.findall(r"(?m)^\s*(eu5_language_[a-z0-9_]+_name):\d+", t))
stripped = [l for l in lines if not re.match(r"^\s*eu5_language_[a-z0-9_]+_name:\d+", l)]
print("去掉新条目后与原备份一致: %s" % (stripped == ol))
# 边界
for i, l in enumerate(lines):
    if l.startswith(" eu5_language_abenakian_language_name"):
        print("插入块起点在第 %d 行" % (i + 1))
        for j in range(i - 2, i + 3):
            print("   %d: %s" % (j + 1, lines[j]))
        break
