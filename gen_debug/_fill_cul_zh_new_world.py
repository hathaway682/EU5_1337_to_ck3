# -*- coding: utf-8 -*-
"""补中文：美洲 / 大洋洲 / 非洲有地的新文化所用 cul_ 人名键。

范围：gen_debug/_culture_classification.csv 里 continent ∈ {北美洲,南美洲,大洋洲,非洲}
      且 baronies > 0，并且文化块仍在 common/culture/cultures/00_generated_cultures.txt。

值来源：
  1) EU5 官方中文（character_names_dynamic / character_names 的 name_<slug>）
  2) 查不到时用英文原值（gen_cultures_l_english.yml 的 cul_ 值），不自己音译。

纪律：只补缺失 key，已有行原样保留；BOM + CRLF；无变化不写盘。
"""
import io, os, re, csv, sys

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"

CLS = os.path.join(MOD, "gen_debug", "_culture_classification.csv")
CULT = os.path.join(MOD, "common", "culture", "cultures", "00_generated_cultures.txt")
NL = os.path.join(MOD, "common", "culture", "name_lists", "00_generated_name_lists.txt")
EN = os.path.join(MOD, "localization", "english", "gen_cultures_l_english.yml")
ZH = os.path.join(MOD, "localization", "simp_chinese", "gen_cultures_l_simp_chinese.yml")

TARGET_CONT = {"北美洲", "南美洲", "大洋洲", "非洲"}

# ---------- 1. 范围 ----------
cur_cult = set(re.findall(r'(?m)^([A-Za-z0-9_]+)\s*=\s*\{',
                          io.open(CULT, encoding="utf-8-sig").read()))
scope = []
for r in csv.DictReader(io.open(CLS, encoding="utf-8-sig")):
    if r["continent"] in TARGET_CONT and int(r["baronies"] or 0) > 0 and r["culture"] in cur_cult:
        scope.append(r["culture"])
scope = sorted(set(scope))
print("范围内文化: %d（北美洲/南美洲/大洋洲/非洲且有地）" % len(scope))

# ---------- 2. 这些文化的 name_list -> cul_ 键 ----------
raw = io.open(NL, encoding="utf-8-sig").read()
blocks = dict(re.findall(r'(?ms)^(name_list_[A-Za-z0-9_-]+)\s*=\s*\{(.*?)^\}', raw))
keys = set()
for c in scope:
    keys |= set(re.findall(r'\bcul_[A-Za-z0-9_-]+', blocks.get("name_list_" + c, "")))
print("涉及 cul_ 键: %d" % len(keys))
if not keys:
    sys.exit(0)

# ---------- 3. 英文原值 ----------
def load_mod(path):
    d = {}
    for ln in io.open(path, encoding="utf-8-sig", errors="replace"):
        m = re.match(r'^\s*([A-Za-z0-9_.\-]+):\d*\s*"([^"]*)"', ln)
        if m:
            d.setdefault(m.group(1), m.group(2))
    return d

en = load_mod(EN)
# ---------- 4. EU5 中文 ----------
zh_src = {}
base = os.path.join(EU5, "main_menu", "localization", "simp_chinese")
for fn in ("character_names_dynamic_l_simp_chinese.yml", "character_names_l_simp_chinese.yml"):
    p = os.path.join(base, fn)
    if os.path.exists(p):
        for ln in io.open(p, encoding="utf-8-sig", errors="replace"):
            m = re.match(r'^\s*([A-Za-z0-9_.\-]+):\s*"([^"]*)"', ln)
            if m:
                zh_src.setdefault(m.group(1), m.group(2))

def zh_of(key):
    slug = key[4:]
    for cand in ("name_" + slug, slug):
        if cand in zh_src:
            return zh_src[cand], "EU5"
    return en.get(key, ""), "EN"

want, stat = {}, {"EU5": 0, "EN": 0, "空": 0}
for k in keys:
    v, src = zh_of(k)
    if not v:
        stat["空"] += 1
        continue
    want[k] = v
    stat[src] += 1
print("可写 %d 条：EU5 中文 %d / 英文原值 %d / 空 %d"
      % (len(want), stat["EU5"], stat["EN"], stat["空"]))

# ---------- 5. 只补缺失 ----------
existing = {}
lines_zh = io.open(ZH, encoding="utf-8-sig").read().split("\n")
for ln in lines_zh:
    m = re.match(r'^\s*([A-Za-z0-9_.\-]+):\d*\s*"([^"]*)"', ln)
    if m:
        existing[m.group(1)] = m.group(2)
added = [k for k in want if k not in existing]
print("中文文件已有 %d 条；本次新增 %d 条" % (len(existing), len(added)))
if not added:
    print("无需要写入的改动。")
    sys.exit(0)

for k in sorted(added):
    lines_zh.append(' %s: "%s"' % (k, want[k]))

out = "\r\n".join(lines_zh).rstrip("\r\n") + "\r\n"
with io.open(ZH, "w", encoding="utf-8", newline="") as fp:
    fp.write("\ufeff" + out)
print("已写回", ZH)
