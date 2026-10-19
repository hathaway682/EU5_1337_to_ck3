# -*- coding: utf-8 -*-
"""把 culture 定义里的 language 从 eu5_heritage_<group> 换成 EU5 原始 language 映射后的 CK3 key。

规则：
  - 每个 culture 用它在 EU5 里的 language（EU5 culture key 与我们同名）
  - 该 EU5 language 在 _eu5_language_to_ck3.csv 里 mapped -> 写 CK3 原版 language
  - 没映射（CK3 没有这个语系）-> 保持原来的 eu5_heritage_<group>，pillars 里已有定义

默认 dry-run，--apply 才写（先备份）。
"""
import io, os, re, csv, sys, shutil, time
from collections import Counter, defaultdict

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game\in_game"
SRC = os.path.join(MOD, "common", "culture", "cultures", "00_generated_cultures.txt")
MAPCSV = os.path.join(MOD, "gen_debug", "_eu5_language_to_ck3.csv")
OUTDIR = os.path.join(MOD, "gen_debug")
DRY = "--apply" not in sys.argv

BLOCK = re.compile(r"([A-Za-z0-9_]+)\s*=\s*\{")


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


def walk(text, path=()):
    i, n = 0, len(text)
    while i < n:
        m = BLOCK.search(text, i)
        if not m:
            return
        j, d = m.end(), 1
        while j < n and d:
            c = text[j]
            if c == "{":
                d += 1
            elif c == "}":
                d -= 1
            j += 1
        body = text[m.end():j - 1]
        yield path, m.group(1), body
        yield from walk(body, path + (m.group(1),))
        i = j


def main():
    # EU5 culture -> language
    eu5_lang = {}
    for fn in os.listdir(os.path.join(EU5, "common", "cultures")):
        if not fn.endswith(".txt"):
            continue
        for path, key, body in walk(read(os.path.join(EU5, "common", "cultures", fn))):
            if path:
                continue
            lg = re.search(r"(?m)^\s*language\s*=\s*(\S+)", body)
            if lg:
                eu5_lang[key] = lg.group(1)

    # 映射表
    lmap = {}
    with io.open(MAPCSV, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["status"] == "mapped":
                lmap[row["eu5_language"]] = row["ck3_language"]

    raw = read(SRC)
    lines = raw.split("\n")

    cur_culture = None
    changed = 0
    no_eu5 = 0
    kept = 0
    samples = []
    dist_before, dist_after = Counter(), Counter()
    out = []
    for line in lines:
        m = re.match(r"^([a-z0-9_]+)\s*=\s*\{\s*$", line)
        if m:
            cur_culture = m.group(1)
            out.append(line)
            continue
        ml = re.match(r"^(\s*)language\s*=\s*(\S+)", line)
        if ml and cur_culture:
            old = ml.group(2)
            dist_before[old] += 1
            lg = eu5_lang.get(cur_culture)
            new = old
            if not lg:
                no_eu5 += 1
            elif lg in lmap:
                new = lmap[lg]
            else:
                kept += 1
            dist_after[new] += 1
            if new != old:
                changed += 1
                if len(samples) < 20:
                    samples.append((cur_culture, old, new, lg or ""))
                out.append("%slanguage = %s" % (ml.group(1), new))
                continue
        out.append(line)

    new_text = "\n".join(out)
    print("cultures with language line: %d" % sum(dist_before.values()))
    print("changed: %d | keep(custom): %d | no eu5 culture: %d" % (changed, kept, no_eu5))
    print("distinct language before: %d -> after: %d" % (len(dist_before), len(dist_after)))
    print()
    print("top after:")
    for k, v in dist_after.most_common(20):
        print("  %-32s %5d" % (k, v))
    print()
    print("samples:")
    for c, o, n, lg in samples:
        print("  %-30s %-34s -> %-24s  (eu5 lang: %s)" % (c, o, n, lg))

    rep = os.path.join(OUTDIR, "_lang_restore_report.txt")
    io.open(rep, "w", encoding="utf-8", newline="\n").write(
        "changed=%d keep=%d no_eu5=%d\nbefore_distinct=%d after_distinct=%d\n"
        % (changed, kept, no_eu5, len(dist_before), len(dist_after)))

    if DRY:
        print("\n[dry-run] 未写文件。加 --apply 才写。")
        return
    if new_text == raw:
        print("\nno change")
        return
    ts = time.strftime("%Y%m%d_%H%M%S")
    shutil.copy2(SRC, SRC + ".bak_langrestore_" + ts)
    io.open(SRC, "w", encoding="utf-8-sig", newline="\n").write(new_text)
    print("\nAPPLIED. backup: %s" % (SRC + ".bak_langrestore_" + ts))
    print("braces: %d %d" % (new_text.count("{"), new_text.count("}")))


if __name__ == "__main__":
    main()
