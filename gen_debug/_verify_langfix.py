# -*- coding: utf-8 -*-
"""校验 language 修复：引用完整性 / 括号平衡 / 行数 / 编码 / 新旧值分布 / 抽查。"""
import io, os, re, collections

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
CULT = os.path.join(MOD, "common", "culture", "cultures", "00_generated_cultures.txt")
PILL = os.path.join(MOD, "common", "culture", "pillars", "00_generated_pillars.txt")
BAK = os.path.join(os.path.dirname(CULT),
                   "00_generated_cultures.txt.bak_langfix_20261020_011406")

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


new = rd(CULT)
old = rd(BAK)

# 结构
print("大括号: %d / %d %s" % (new.count("{"), new.count("}"),
                             "平衡" if new.count("{") == new.count("}") else "不平衡!"))
print("行数: new=%d old=%d %s" % (new.count("\n"), old.count("\n"),
                                 "一致" if new.count("\n") == old.count("\n") else "不一致!"))
b = open(CULT, "rb").read()
print("cultures 编码: BOM=%s CRLF行=%d 纯LF=%d" %
      (b[:3] == b"\xef\xbb\xbf", b.count(b"\r\n"), b.count(b"\n") - b.count(b"\r\n")))
b = open(PILL, "rb").read()
print("pillars   编码: BOM=%s CRLF行=%d 纯LF=%d" %
      (b[:3] == b"\xef\xbb\xbf", b.count(b"\r\n"), b.count(b"\n") - b.count(b"\r\n")))

# pillars 重复 key
tk = list(top_keys(new))
pk = list(top_keys(rd(PILL)))
print("pillars key 数: %d | 重复: %s" % (len(pk), [k for k, c in collections.Counter(pk).items() if c > 1] or "无"))

# 引用完整性
cult_lang = {k: field(b, "language") for k, b in top_keys(new).items()}
pillars_def = set(top_keys(rd(PILL)))
vanilla = set()
for fn in sorted(os.listdir(r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game\common\culture\pillars")):
    if fn.endswith(".txt"):
        vanilla |= set(top_keys(rd(os.path.join(
            r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game\common\culture\pillars", fn))))
undef = sorted(v for v in set(cult_lang.values())
               if v and v not in pillars_def and v not in vanilla)
print("language 引用未定义: %s" % (undef or "无"))

# 分布
dist = collections.Counter()
for v in cult_lang.values():
    dist["eu5_language_*" if v.startswith("eu5_language_") else
         ("CK3 language_*" if v.startswith("language_") else "eu5_heritage_*")] += 1
print("language 行分布: %s" % dict(dist))

# 与备份 diff：只应有 language 行变化
nl, ol = new.split("\n"), old.split("\n")
diffs = [(i, ol[i], nl[i]) for i in range(min(len(nl), len(ol))) if nl[i] != ol[i]]
fields = collections.Counter()
for i, o, n in diffs:
    m = re.match(r"^\s*([a-z_]+)\s*=", n)
    fields[m.group(1) if m else "?"] += 1
print("相对备份变化行数: %d | 涉及字段: %s" % (len(diffs), dict(fields)))
bad = [d for d in diffs if not re.match(r"^\s*language\s*=", d[2])]
print("非 language 行的变化: %s" % (bad or "无"))

# 抽查美洲文化
print()
print("== 抽查 ==")
for c in ["ache_culture", "anccara_culture", "chol_culture", "amarak_culture",
          "dorset_culture", "het_culture", "irritila_culture", "amonraq_culture"]:
    if c in cult_lang:
        print("  %-24s language = %s" % (c, cult_lang[c]))
