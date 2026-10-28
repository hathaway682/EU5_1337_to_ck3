# -*- coding: utf-8 -*-
"""删除 zz_eu5_tributaries.txt / zz_eu5_primary_titles.txt 里指向 herder 摄政的 character 块。"""
import json, os, re, shutil, sys, time

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
EXPORT = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
APPLY = "--apply" in sys.argv

d = json.load(open(os.path.join(EXPORT, "eu5_politics.json"), encoding="utf-8"))
HERD = {t for t, v in d["countries"].items() if v.get("government") == "herder"}
REG = "|".join(sorted("eu5_regent_" + t.lower() for t in HERD))
PAT = re.compile(r"character:(" + REG + r")\s*=\s*\{")

for rel in ["common/on_action/zz_eu5_tributaries.txt", "common/on_action/zz_eu5_primary_titles.txt"]:
    p = os.path.join(MOD, rel)
    text = open(p, encoding="utf-8-sig").read()
    out, last, n = [], 0, 0
    for m in PAT.finditer(text):
        if m.start() < last:
            continue
        i, depth = m.end(), 1
        while i < len(text) and depth:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        end = i
        while end < len(text) and text[end] in "\r\n\t ":
            if text[end] == "\n" and end + 1 < len(text) and text[end + 1] not in "\r\n\t ":
                break
            end += 1
        out.append(text[last:m.start()])
        last = end
        n += 1
    out.append(text[last:])
    new = "".join(out)
    print(f"{rel}: 删除 {n} 块 | 变化 {new != text} | 花括号 {new.count('{')}/{new.count('}')}")
    if APPLY and new != text:
        open(p, "w", encoding="utf-8-sig", newline="").write(new)
