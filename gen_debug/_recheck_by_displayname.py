# -*- coding: utf-8 -*-
"""按中文显示名重查文化分类。

11 类标准里的「同名」指的是显示名，不是 key。有了
  _eu5_culture_zh.csv  我们 2088 个文化的中文名（取自 EU5）
  _ck3_culture_names.csv CK3 244 个文化的中英文名
就能真正按显示名判定，并反过来检查已分类的结果。
"""
import io, os, re, csv, collections

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
GD = os.path.join(MOD, "gen_debug")

def norm(s):
    s = (s or "").strip()
    for a, b in (("‑", "-"), ("–", "-"), ("—", "-"), ("·", ""), ("・", "")):
        s = s.replace(a, b)
    return re.sub(r"[\s\-'’.]", "", s).lower()

def _pick(*names):
    for n in names:
        p = os.path.join(GD, n)
        if os.path.exists(p):
            return p
    raise SystemExit("找不到分类结果 CSV")

CLS_CSV = _pick("_culture_classification.csv", "_culture_classification.new.csv")

ours = list(csv.DictReader(io.open(os.path.join(GD, "_eu5_culture_zh.csv"), encoding="utf-8-sig")))
cls = {r["culture"]: r for r in csv.DictReader(io.open(CLS_CSV, encoding="utf-8-sig"))}
ck = list(csv.DictReader(io.open(os.path.join(GD, "_ck3_culture_names.csv"), encoding="utf-8-sig")))

ck_by_zh = collections.defaultdict(list)
ck_by_en = collections.defaultdict(list)
for c in ck:
    if c["name_zh"]:
        ck_by_zh[norm(c["name_zh"])].append(c["culture"])
    if c["name_en"]:
        ck_by_en[norm(c["name_en"])].append(c["culture"])

A = []
B = []
C = []
for o in ours:
    c = o["culture"]
    cur = cls.get(c)
    if not cur:
        continue
    zh = norm(o["name_zh"])
    en = norm(o["name_en"])
    hit = ck_by_zh.get(zh) or ck_by_en.get(en)
    cat = int(cur["category"])
    tgt = cur["target"]
    if hit:
        # 显示名能对上 CK3 的某个文化
        if cat == 1 and tgt not in hit:
            A.append((c, o["name_zh"], cat, tgt, "/".join(hit), "cat1 但目标不是同名那个"))
        elif cat != 1 and tgt not in hit:
            B.append((c, o["name_zh"], cat, tgt, "/".join(hit), "显示名同名却判成 cat%d" % cat))
    else:
        if cat == 1:
            C.append((c, o["name_zh"], cat, tgt, "", "cat1 但显示名对不上"))

print("== A. 已判 cat1，但中文名对应的 CK3 文化不是当前目标 ==")
for r in A:
    print("  %-26s %-12s cat%s → %-20s 显示名对上 %s | %s" % r)
print("  共 %d\n" % len(A))

print("== B. 显示名能对上 CK3，但不是 cat1（漏判） ==")
for r in sorted(B, key=lambda x: -int(cls[x[0]]["baronies"])):
    print("  %-26s %-12s cat%s → %-20s 显示名对上 %-20s | %s" % r)
print("  共 %d\n" % len(B))

print("== C. 判了 cat1，但中文/英文显示名都对不上同名目标 ==")
for r in C:
    print("  %-26s %-12s cat%s → %-20s | 中文/英文都对不上" % (r[0], r[1], r[2], r[3]))
print("  共 %d\n" % len(C))

# 目标文化的显示名 vs 我们文化显示名，看「并入/异名同族」是否合理
print("== D. cat2~7 目标的中文名（抽样，检查是否张冠李戴） ==")
ckzh = {c["culture"]: c["name_zh"] for c in ck}
cnt = collections.Counter()
for c, r in cls.items():
    cat = int(r["category"])
    if cat in (2, 3, 4, 5, 6, 7):
        cnt[(cat, r["target"], ckzh.get(r["target"], "?"))] += 1
for (cat, t, z), n in sorted(cnt.items(), key=lambda x: (x[0][0], -x[1]))[:40]:
    print("  cat%-2s → %-22s %-14s ×%d" % (cat, t, z, n))
