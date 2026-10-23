# -*- coding: utf-8 -*-
"""只读：列出圣地文件里所有带行尾注释的圣地块，并带上当前指向 + 中文本地化名。"""
import io, os, re

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(MOD, "common", "religion", "holy_site_types", "00_holy_site_types.txt")
LOCDIR = os.path.join(MOD, "localization", "simp_chinese")

loc = {}
for fn in sorted(os.listdir(LOCDIR)):
    if not fn.endswith(".yml"):
        continue
    t = io.open(os.path.join(LOCDIR, fn), encoding="utf-8-sig", errors="ignore").read()
    for ln in t.split("\n"):
        m = re.match(r'^\s*([A-Za-z0-9_]+):\d*\s*"(.*)"', ln.strip())
        if m:
            loc[m.group(1)] = m.group(2)

lines = io.open(SRC, "rb").read().decode("utf-8-sig").split("\r\n")
depth = 0
rows = []
for i, ln in enumerate(lines):
    if depth == 0:
        m = re.match(r"^([A-Za-z0-9_\-]+)\s*=\s*\{(.*)$", ln)
        if m:
            rest = m.group(2)
            cm = re.search(r"#(.*)$", rest)
            rows.append({"key": m.group(1), "ln": i + 1,
                         "cmt": cm.group(1).strip() if cm else None,
                         "c": None, "b": None})
            depth = 1
            continue
    elif depth == 1:
        mc = re.match(r"^\s*county\s*=\s*(\S+)", ln)
        mb = re.match(r"^\s*barony\s*=\s*(\S+)", ln)
        if mc:
            rows[-1]["c"] = mc.group(1)
        if mb:
            rows[-1]["b"] = mb.group(1)
    depth += ln.count("{") - ln.count("}")

withc = [r for r in rows if r["cmt"]]
print("圣地块总数 = %d；带行尾注释 = %d" % (len(rows), len(withc)))
print()
for r in withc:
    tgt = r["b"] or r["c"] or ""
    zh = loc.get(r["b"] or "", "") or loc.get(r["c"] or "", "")
    print("%-22s L%-5d %-22s %-12s | %s" % (r["key"], r["ln"], tgt, zh, r["cmt"]))
