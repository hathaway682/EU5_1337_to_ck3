# -*- coding: utf-8 -*-
"""把「组级兜底 language」恢复成 EU5 文化的真实 language。

背景：上一轮 `_restore_eu5_language.py` 只覆盖了映射表里的 591 个 EU5 language
（284 exact + 307 keep），剩下 2 个（yiddish_dialect / ladino_dialect）根本不在表里，
导致凡是没有 CK3 对应语系的文化，language 一律退化成 `eu5_heritage_<group>`——
EU5 里明确的 nahuatl / tupi / quechuan / maya / pama_nyungan 等语言信息被抹平。

本脚本：凡 language 行 = eu5_heritage_* 且该文化在 EU5 有 language 字段的，
改写成 `eu5_language_<eu5_language>`（新 key 保持 EU5 原名，可追溯），
并在 00_generated_pillars.txt 里补上对应 pillar 定义。

EU5 里没有 language 字段的文化（4 个）保持原样。

用法：默认 dry-run，--apply 才落盘（落盘前备份）。
"""
import io, os, re, shutil, sys, collections
from datetime import datetime

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game\in_game"
CK3 = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"

CULT = os.path.join(MOD, "common", "culture", "cultures", "00_generated_cultures.txt")
PILL = os.path.join(MOD, "common", "culture", "pillars", "00_generated_pillars.txt")
APPLY = "--apply" in sys.argv

DEF = re.compile(r"(?ms)^\t?([a-z0-9_]+)\s*=\s*\{")


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


def write_bom_crlf(p, text):
    """按原格式写回：BOM + CRLF（以原文件实际换行为准）"""
    raw = io.open(p, "rb").read()
    bom = raw[:3] == b"\xef\xbb\xbf"
    crlf = raw.count(b"\r\n") > raw.count(b"\n") - raw.count(b"\r\n")
    if crlf:
        text = text.replace("\r\n", "\n").replace("\n", "\r\n")
    enc = "utf-8-sig" if bom else "utf-8"
    io.open(p, "w", encoding=enc, newline="").write(text)


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


def field(body, k):
    m = re.search(r"(?m)^\s*" + k + r"\s*=\s*([a-z0-9_]+)", body)
    return m.group(1) if m else ""


# ---------- 1. EU5: culture -> language ----------
eu5_lang = {}
cd = os.path.join(EU5, "common", "cultures")
for fn in sorted(os.listdir(cd)):
    if not fn.endswith(".txt"):
        continue
    for k, b in top_keys(read(os.path.join(cd, fn))).items():
        lg = field(b, "language")
        if lg:
            eu5_lang[k] = lg
print("EU5 cultures with language: %d" % len(eu5_lang))

# ---------- 2. 原版 language 键（避免造出与原版同名的 key） ----------
vanilla_lang = set()
for fn in sorted(os.listdir(os.path.join(CK3, "common", "culture", "pillars"))):
    if fn.endswith(".txt"):
        vanilla_lang |= set(top_keys(read(os.path.join(CK3, "common", "culture", "pillars", fn))))
print("CK3 vanilla pillar keys: %d" % len(vanilla_lang))

# ---------- 3. 改 cultures 文件 ----------
raw = read(CULT)
lines = raw.split("\n")
cur = None
changed = 0
new_keys = {}                     # eu5_language_x -> [cultures]
no_eu5_lang = []                  # EU5 里没有 language 的
samples = []
for idx, line in enumerate(lines):
    m = re.match(r"^([a-z0-9_]+)\s*=\s*\{\s*$", line)
    if m:
        cur = m.group(1)
        continue
    ml = re.match(r"^(\s*)language\s*=\s*([a-z0-9_]+)\s*$", line)
    if ml and cur:
        val = ml.group(2)
        if val.startswith("eu5_heritage_"):
            lg = eu5_lang.get(cur, "")
            if not lg:
                no_eu5_lang.append(cur)
                continue
            newkey = "eu5_language_" + lg
            assert newkey not in vanilla_lang, "与原版 key 冲突: %s" % newkey
            term = "\r" if line.endswith("\r") else ""
            lines[idx] = "%slanguage = %s%s" % (ml.group(1), newkey, term)
            changed += 1
            new_keys.setdefault(newkey, []).append(cur)
            if len(samples) < 8:
                samples.append((cur, val, newkey, lg))

print()
print("language 行改写: %d" % changed)
print("EU5 无 language 字段、保持组级: %d -> %s" % (len(no_eu5_lang), sorted(no_eu5_lang)))
print("新增 language pillar key: %d 个" % len(new_keys))
print()
print("样例:")
for c, o, n, lg in samples:
    print("  %-30s %-34s -> %-38s (EU5: %s)" % (c, o, n, lg))

print()
print("== 新 key 覆盖文化数 top 15 ==")
for k, cs in sorted(new_keys.items(), key=lambda kv: -len(kv[1]))[:15]:
    print("  %-40s %d" % (k, len(cs)))

# ---------- 4. 补 pillars 定义 ----------
pill_raw = read(PILL)
have = set(top_keys(pill_raw))
missing = sorted(k for k in new_keys if k not in have)
dup = [k for k in new_keys if k in have]
print()
print("pillars 已存在(跳过): %d | 需新增: %d" % (len(dup), len(missing)))
assert not dup, "意外重复 key: %s" % dup[:5]

if APPLY:
    if changed:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = CULT + ".bak_langfix_" + ts
        shutil.copy2(CULT, bak)
        write_bom_crlf(CULT, "\n".join(lines))
        print("已写回 %s (备份 %s)" % (CULT, bak))
    if missing:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = PILL + ".bak_langfix_" + ts
        shutil.copy2(PILL, bak)
        # 末尾追加新块（文件以 "}\n\n" 结尾）
        text = read(PILL)
        if not text.endswith("\n"):
            text += "\n"
        add = []
        for k in missing:
            add.append(
                "%s = {\n"
                "\ttype = language\n"
                "\tis_shown = {\n"
                "\t\tlanguage_is_shown_trigger = { LANGUAGE = %s }\n"
                "\t}\n"
                "\tai_will_do = {\n"
                "\t\tvalue = 10\n"
                "\t\tif = {\n"
                "\t\t\tlimit = { has_cultural_pillar = %s }\n"
                "\t\t\tmultiply = 10\n"
                "\t\t}\n"
                "\t}\n"
                "}\n" % (k, k, k))
        text = text + "\n" + "\n".join(add)
        write_bom_crlf(PILL, text)
        print("已追加 %d 个 language pillar 到 %s (备份 %s)" % (len(add), PILL, bak))
    print("APPLIED")
else:
    print("dry-run：未写盘。加 --apply 执行。")
