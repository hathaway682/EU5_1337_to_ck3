# -*- coding: utf-8 -*-
"""只读探查：EU5 有 language 的文化，在我们文件里 language 行写成什么。

重点：language = eu5_heritage_<group>（组级自造 key）但却有 EU5 自有 language 字段的文化
——这些是「语言信息被组级键抹掉」的。
"""
import io, os, re, collections

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game\in_game"

BLOCK = re.compile(r"([A-Za-z0-9_]+)\s*=\s*\{")
DEF = re.compile(r"(?ms)^\t?([a-z0-9_]+)\s*=\s*\{")


def rd(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


def top_keys(text):
    """顶层 key -> body（只一层括号）"""
    out = {}
    i, n = 0, len(text)
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


# --- EU5: culture -> language / group ---
eu5_lang, eu5_grp = {}, {}
cd = os.path.join(EU5, "common", "cultures")
for fn in sorted(os.listdir(cd)):
    if not fn.endswith(".txt"):
        continue
    t = rd(os.path.join(cd, fn))
    for k, body in top_keys(t).items():
        m = re.search(r"(?m)^\s*language\s*=\s*([a-z0-9_]+)", body)
        g = re.search(r"(?m)^\s*culture_groups?\s*=\s*([a-z0-9_]+)", body)
        if not m and not g:
            continue
        if m:
            eu5_lang[k] = m.group(1)
        if g:
            eu5_grp[k] = g.group(1)

# --- 我们: culture -> language 行 ---
ours = {}
t = rd(os.path.join(MOD, "common", "culture", "cultures", "00_generated_cultures.txt"))
for k, body in top_keys(t).items():
    m = re.search(r"(?m)^\s*language\s*=\s*([a-z0-9_]+)", body)
    ours[k] = m.group(1) if m else ""

print("EU5 cultures: %d | with language: %d" % (len(eu5_lang), len(eu5_lang)))
print("ours cultures: %d | with language line: %d"
      % (len(ours), sum(1 for v in ours.values() if v)))
print()

custom = [c for c, v in ours.items() if v.startswith("eu5_heritage_")]
ck3 = [c for c, v in ours.items() if v.startswith("language_")]
print("language 行 = eu5_heritage_* (自造组级): %d" % len(custom))
print("language 行 = CK3 language_*        : %d" % len(ck3))
print()

# 有 EU5 language 但被写成组级 key 的
lost = [(c, ours[c], eu5_lang.get(c, ""), eu5_grp.get(c, "")) for c in custom
        if eu5_lang.get(c)]
print("== 有 EU5 language 却写成 eu5_heritage_<group> 的文化: %d ==" % len(lost))
by = collections.defaultdict(list)
for c, cur, lg, grp in lost:
    by[(lg, grp)].append(c)
for (lg, grp), cs in sorted(by.items(), key=lambda kv: -len(kv[1])):
    print("  %-34s group=%-32s n=%-4d 例: %s"
          % (lg, grp, len(cs), cs[0]))
print()

# 完全没有 EU5 language 的
nol = [c for c in custom if not eu5_lang.get(c)]
print("== EU5 里也没有 language 字段的文化: %d ==" % len(nol))
print("  " + ", ".join(sorted(nol)[:20]))
print()

# 地区分布：按 EU5 culture_groups 的 group 统计丢失规模
grpn = collections.Counter()
for c, cur, lg, grp in lost:
    grpn[grp] += 1
print("== 丢失语言信息的 group（按 n 排序，前 25） ==")
for g, n in grpn.most_common(25):
    print("  %-36s %d" % (g, n))
