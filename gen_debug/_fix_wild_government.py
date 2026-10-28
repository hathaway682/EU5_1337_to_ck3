# -*- coding: utf-8 -*-
"""修补：已经变荒野的县，块里不该留 government 行（SEA 覆盖留下的 wanua_government）。"""
import json, os, re, sys

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
EXPORT = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
APPLY = "--apply" in sys.argv

d = json.load(open(os.path.join(EXPORT, "eu5_politics.json"), encoding="utf-8"))
HERD = {t for t, v in d["countries"].items() if v.get("government") == "herder"}
CTS = {c for c, v in d["counties"].items() if v.get("owner") in HERD}

for rel in ["history/titles/zz_eu5_titles.txt", "history/characters/zz_eu5_titles.txt"]:
    p = os.path.join(MOD, rel)
    text = open(p, encoding="utf-8-sig").read()
    spans = []
    for c in CTS:
        for m in re.finditer(r"^" + re.escape(c) + r" = \{", text, re.M):
            i, depth = m.end(), 1
            while i < len(text) and depth:
                if text[i] == "{":
                    depth += 1
                elif text[i] == "}":
                    depth -= 1
                i += 1
            body = text[m.start():i]
            if "holder = gen_wilderness_holder" in body and re.search(r"government\s*=", body):
                spans.append((m.start(), i, body))
    spans.sort()
    out, last, n = [], 0, 0
    for s, e, body in spans:
        new = re.sub(r"\n[ \t]*government\s*=\s*\w+", "", body)
        out.append(text[last:s])
        out.append(new)
        last = e
        n += 1
    out.append(text[last:])
    new_text = "".join(out)
    print(f"{rel}: 删 government 行 {n} 处 | 变化 {new_text != text}")
    if APPLY and new_text != text:
        open(p, "w", encoding="utf-8-sig", newline="").write(new_text)
