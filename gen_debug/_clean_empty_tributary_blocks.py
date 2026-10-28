# -*- coding: utf-8 -*-
"""清理朝贡文件里因删掉牧民朝贡者而只剩 save_scope_as 的空壳 character 块。"""
import re, sys

P = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape\common\on_action\zz_eu5_tributaries.txt"
APPLY = "--apply" in sys.argv

text = open(P, encoding="utf-8-sig").read()
pat = re.compile(r"\n(\t+)character:([A-Za-z0-9_]+) = \{")
spans = []
for m in pat.finditer(text):
    i, depth = m.end(), 1
    while i < len(text) and depth:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    body = text[m.end():i - 1]
    if not body.strip() or ("character:" not in body and "set_" not in body
                            and "break_" not in body and "add_" not in body):
        spans.append((m.start(), i, m.group(2)))
spans.sort()
print("空壳块:", len(spans), [s[2] for s in spans])
out, last = [], 0
for s, e, name in spans:
    out.append(text[last:s])
    last = e
out.append(text[last:])
new = "".join(out)
print("括号:", new.count("{"), new.count("}"))
if APPLY and new != text:
    open(P, "w", encoding="utf-8-sig", newline="").write(new)
    print("已写盘")
