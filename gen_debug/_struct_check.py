# -*- coding: utf-8 -*-
"""只读：成品文件结构体检（BOM / 换行 / 块数 / rite 位置 / 重复）。"""
import io, os, re
from collections import Counter

SRC = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape\history\provinces\00_generated_provinces.txt"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_struct_check.out")

raw = io.open(SRC, "rb").read()
L = []
L.append("BOM: %s" % (raw[:3] == b"\xef\xbb\xbf"))
L.append("CRLF 行数: %d / 裸 LF 行数: %d" % (raw.count(b"\r\n"), raw.count(b"\n") - raw.count(b"\r\n")))
L.append("文件大小: %d 字节" % len(raw))

txt = raw.decode("utf-8-sig")
blocks = re.findall(r"(?m)^(\d+) = \{\n(.*?)\n\}", txt, re.S)
L.append("province 块: %d" % len(blocks))
L.append("braces: %d %d" % (txt.count("{"), txt.count("}")))

multi, misorder, nofaith = 0, 0, 0
keys = Counter()
for pid, body in blocks:
    lines = body.split("\n")
    rl = [i for i, s in enumerate(lines) if re.match(r"^\s*rite = ", s)]
    fl = [i for i, s in enumerate(lines) if re.match(r"^\s*faith = ", s)]
    if len(rl) > 1:
        multi += 1
    if rl and fl and rl[0] != fl[0] + 1:
        misorder += 1
    if not fl:
        nofaith += 1
    for s in lines:
        m = re.match(r"^\s*(\w+) = ", s)
        if m:
            keys[m.group(1)] += 1
L.append("一个块里多个 rite 行: %d" % multi)
L.append("rite 不在 faith 下一行: %d" % misorder)
L.append("没有 faith 的块: %d" % nofaith)
L.append("块内字段: %s" % dict(keys.most_common(12)))

io.open(OUT, "w", encoding="utf-8-sig", newline="\n").write("\n".join(L))
