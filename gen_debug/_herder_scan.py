# -*- coding: utf-8 -*-
"""只读盘点：448 个 herder(人群国家) tag 在成品 mod 里的全部落点。"""
import json, os, re, collections

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
EXPORT = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"

d = json.load(open(os.path.join(EXPORT, "eu5_politics.json"), encoding="utf-8"))
cs, cts = d["countries"], d["counties"]
herd = {t for t, v in cs.items() if v.get("government") == "herder"}
herd_cts = {c for c, v in cts.items() if v.get("owner") in herd}

print("herder tags:", len(herd), "herder counties:", len(herd_cts))

# 角色 key 候选
chars = set()
for t in herd:
    v = cs[t]
    if v.get("ruler"):
        chars.add(v["ruler"])
    chars.add("eu5_regent_" + t.lower())
    for r in v.get("rulers") or []:
        if r.get("character"):
            chars.add(r["character"])

pats = [("tag_lower", re.compile(r"\b(?:eu5_regent_)?(" + "|".join(sorted(x.lower() for x in herd)) + r")\b"))]
char_re = re.compile(r"\b(" + "|".join(sorted(re.escape(c) for c in chars)) + r")\b")

hits = collections.Counter()
examples = collections.defaultdict(list)
for root, dirs, files in os.walk(MOD):
    if ".git" in root or ".workbuddy-ai" in root:
        continue
    for fn in files:
        if not fn.endswith((".txt", ".yml")):
            continue
        p = os.path.join(root, fn)
        try:
            txt = open(p, encoding="utf-8-sig", errors="ignore").read()
        except Exception:
            continue
        n_tag = len(pats[0][1].findall(txt))
        n_char = len(char_re.findall(txt))
        if n_tag or n_char:
            rel = os.path.relpath(p, MOD)
            hits[rel] = n_tag + n_char
            examples[rel].append((n_tag, n_char))

for rel, n in hits.most_common(40):
    print(f"{n:7d}  {rel}  tag/char={examples[rel][0]}")
