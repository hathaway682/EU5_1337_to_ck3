# -*- coding: utf-8 -*-
"""把 culture 定义里的 heritage 从 EU5 culture_group 名换成 CK3 原版 heritage。

规则：
  - 基表：gen_debug/_eu5_to_ck3_pillars.csv（eu5_group -> ck3_heritage，status=mapped 的 83 个组）
  - 文化级覆盖：EU5 的 language 更细的组，按语言拆（celtic -> goidelic/brythonic 等）
  - 没有对应 CK3 heritage 的组（162 个，美洲/澳洲/太平洋/西伯利亚极地等）保持自定义组名，
    pillars/00_generated_pillars.txt 里已有定义，不产生悬空引用

默认 dry-run，--apply 才写（先备份）。BOM/CRLF 安全同 _restore_eu5_language.py。
"""
import io, os, re, csv, sys, shutil, time
from collections import Counter

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game\in_game"
SRC = os.path.join(MOD, "common", "culture", "cultures", "00_generated_cultures.txt")
MAPCSV = os.path.join(MOD, "gen_debug", "_eu5_to_ck3_pillars.csv")
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


# EU5 language -> CK3 heritage（组内混合时按语言拆；都来自 EU5 语言系属 + CK3 原版归类）
LANG_OVERRIDE = {
    # 凯尔特：EU5 celtic_group 混 goidelic/brythonic
    "irish_dialect": "heritage_goidelic",
    "scottish_gaelic_dialect": "heritage_goidelic",
    "manx_dialect": "heritage_goidelic",
    "breton_dialect": "heritage_brythonic",
    "welsh_dialect": "heritage_brythonic",
    "cornish_dialect": "heritage_brythonic",
    # 印度：EU5 indian_group 混印欧/达罗毗荼/南亚语系/藏缅
    "malayalam_language": "heritage_dravidian",
    "tamil_language": "heritage_dravidian",
    "telugu_language": "heritage_dravidian",
    "kannada_language": "heritage_dravidian",
    "gondi_language": "heritage_dravidian",
    "north_dravidian_language": "heritage_dravidian",
    "munda_language": "heritage_mon_khmer",
    "khasi_language": "heritage_mon_khmer",
    "brahmaputran_language": "heritage_burman",
    "meitei_language": "heritage_burman",
    "tibetan_language": "heritage_tibetan",
    # EU5 把这两个文化放进 german_group，CK3 原版另有归类
    "czech_dialect": "heritage_west_slavic",
    "yiddish_dialect": "heritage_israelite",
}

# 文化级硬覆盖（个别 EU5 分组与原版明显冲突的）
CULT_OVERRIDE = {
    # ashkenazi 在 EU5 里挂 german_group，CK3 原版归 israelite
    "ashkenazi": "heritage_israelite",
}


def main():
    # 组级基表
    hmap = {}
    with io.open(MAPCSV, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["status"] == "mapped" and row["ck3_heritage"]:
                hmap[row["eu5_group"]] = row["ck3_heritage"]

    # EU5 culture -> language / groups
    eu5_lang, eu5_grp = {}, {}
    for fn in os.listdir(os.path.join(EU5, "common", "cultures")):
        if not fn.endswith(".txt"):
            continue
        for path, key, body in walk(read(os.path.join(EU5, "common", "cultures", fn))):
            if path:
                continue
            lg = re.search(r"(?m)^\s*language\s*=\s*(\S+)", body)
            gr = re.search(r"(?ms)^\s*culture_groups\s*=\s*\{(.*?)\}", body)
            if lg:
                eu5_lang[key] = lg.group(1)
            if gr:
                eu5_grp[key] = gr.group(1).split()

    raw = read(SRC)
    lines = raw.split("\n")

    cur = None
    changed = 0
    no_eu5 = 0
    kept = 0
    via_lang = 0
    via_grp = 0
    samples = []
    dist = Counter()
    out = []
    for line in lines:
        m = re.match(r"^([a-z0-9_]+)\s*=\s*\{\s*$", line)
        if m:
            cur = m.group(1)
            out.append(line)
            continue
        mh = re.match(r"^(\s*)heritage\s*=\s*(\S+)", line)
        if mh and cur:
            old = mh.group(2)
            dist[old] += 1
            new = old
            lg = eu5_lang.get(cur)
            grps = eu5_grp.get(cur) or []
            if cur in CULT_OVERRIDE:
                new = CULT_OVERRIDE[cur]
                via_lang += 1
            elif lg and lg in LANG_OVERRIDE:
                # 语言覆盖只在该语言确实属于组内少数派时才有意义；
                # 但达罗毗荼/南亚语/藏缅 与 组默认印欧冲突，直接用语言覆盖
                cand = LANG_OVERRIDE[lg]
                grp_default = next((hmap.get(g) for g in grps if g in hmap), None)
                if cand != grp_default:
                    new = cand
                    via_lang += 1
                else:
                    new = grp_default
                    via_grp += 1
            else:
                hit = next((hmap[g] for g in grps if g in hmap), None)
                if hit:
                    new = hit
                    via_grp += 1
                else:
                    kept += 1
            dist[new] += 1
            if new != old:
                changed += 1
                if len(samples) < 24:
                    samples.append((cur, old, new, lg or "", ";".join(grps)))
                out.append("%sheritage = %s" % (mh.group(1), new))
                continue
        out.append(line)

    new_text = "\n".join(out)
    print("heritage lines: %d" % sum(dist.values()))
    print("changed: %d | via group: %d | via language: %d | keep(custom): %d"
          % (changed, via_grp, via_lang, kept))
    print()
    print("samples:")
    for c, o, n, lg, g in samples:
        print("  %-28s %-26s -> %-24s (eu5: %s | %s)" % (c, o, n, lg, g))
    print()
    # 汇总：仍保留自定义组的文化（按新值统计）
    kept_detail = Counter()
    for line in out:
        m = re.match(r"^([a-z0-9_]+)\s*=\s*\{\s*$", line)
        if m:
            cur2 = m.group(1)
            continue
        mh = re.match(r"^(\s*)heritage\s*=\s*(\S+)", line)
        if mh and cur2 and not mh.group(2).startswith("heritage_"):
            kept_detail[mh.group(2)] += 1
    print("kept custom groups (top 20):")
    for g, c in kept_detail.most_common(20):
        print("  %-30s %4d" % (g, c))
    print("kept cultures total: %d" % sum(kept_detail.values()))

    if DRY:
        print("\n[dry-run] 未写文件。加 --apply 才写。")
        return
    if new_text == raw:
        print("\nno change")
        return
    ts = time.strftime("%Y%m%d_%H%M%S")
    shutil.copy2(SRC, SRC + ".bak_heritagerestore_" + ts)
    io.open(SRC, "w", encoding="utf-8-sig", newline="\n").write(new_text)
    print("\nAPPLIED. backup: %s" % (SRC + ".bak_heritagerestore_" + ts))
    print("braces: %d %d" % (new_text.count("{"), new_text.count("}")))


if __name__ == "__main__":
    main()
