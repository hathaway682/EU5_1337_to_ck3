# -*- coding: utf-8 -*-
"""按 EU5 文化组（eu5_groups 首位组）批量归并还没落点的文化。

用于「某个大洲还剩一堆 NEW:，按文化组合并掉」这种批量活。美洲/大洋洲那次
（983 -> 129）就是这个流程。

用法：
    python culture_group_merge.py --continents 北美洲,南美洲,大洋洲
    python culture_group_merge.py --continents 大洋洲 --apply

做的事（默认 dry run）：
  1. 挑出这些大洲里 target 还是 NEW: 的 CSV 行
  2. 按 eu5_groups 首位组分组；没有 culture_groups 的按 eu5_language 反推
  3. 每组建一个文化：key = 组名去掉 _group，中文名取 EU5 的组名
     定义体（ethos/traditions/name_list/gfx/ethnicities）克隆组内 barony 最多的成员，
     heritage = <group>_group，language = eu5_heritage_<group>_group
  4. 写定义文件 + 本地化文件，更新 CSV target

本脚本**不写省份、不写人物**。跑完按提示再执行：
    python ../../../gen_debug/_apply_province_pop_culture.py --cats <cat> \\
        --continents <大洲> --only-selected --apply
    然后跑 culture_remap.py 的 people 环节，或直接用
    gen_debug/_apply_people_culture.py --apply
"""
import collections
import io
import os
import re
import sys

import _common as C

GEN_CULT = os.path.join(C.MOD, "common/culture/cultures/00_generated_cultures.txt")
PILLARS = os.path.join(C.MOD, "common/culture/pillars/00_generated_pillars.txt")
DEFS_OUT = os.path.join(C.MOD, "common/culture/cultures/zz_eu5_culture_group.txt")
LOC_OUT = os.path.join(C.MOD, "localization/simp_chinese/zz_eu5_culture_group_l_simp_chinese.yml")


def opt(name, default=""):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


def group_zh():
    out = {}
    if not os.path.exists(C.EU5_GROUP_LOC):
        return out
    for line in io.open(C.EU5_GROUP_LOC, encoding="utf-8-sig", errors="ignore"):
        m = re.match(r'^\s*([a-z0-9_]+_group):\d*\s*"([^"]*)"', line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def extract_block(text, key):
    m = re.search(r"(?m)^" + re.escape(key) + r"\s*=\s*\{", text)
    if not m:
        return None
    i, d = m.end(), 1
    while i < len(text) and d:
        if text[i] == "{":
            d += 1
        elif text[i] == "}":
            d -= 1
        i += 1
    return text[m.end():i - 1]


def build_def(group, rep_block):
    lines = rep_block.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    res, did_h, did_l = [], False, False
    for ln in lines:
        st = ln.strip()
        if st.startswith("heritage"):
            if not did_h:
                res.append("\theritage = %s" % group)
                did_h = True
            continue
        if st.startswith("language"):
            if not did_l:
                res.append("\tlanguage = eu5_heritage_%s" % group)
                did_l = True
            continue
        res.append(ln.rstrip("\r"))
    if not (did_h and did_l):
        ins = [x for x, f in (("\theritage = %s" % group, did_h),
                              ("\tlanguage = eu5_heritage_%s" % group, did_l)) if not f]
        idx = next((i for i, l in enumerate(res) if l.strip().startswith("ethos")), -1)
        res = (res[:idx + 1] + [""] + ins + res[idx + 1:]) if idx >= 0 else ins + res
    return res


def main():
    apply = "--apply" in sys.argv
    conts = [x.strip() for x in opt("--continents").split(",") if x.strip()]
    if not conts:
        print(__doc__)
        sys.exit(1)

    rows = C.load_classif()
    header = list(rows[0].keys())
    target_rows = [r for r in rows
                   if r["target"].startswith("NEW:") and r["continent"] in conts]
    print("大洲 %s：待归并 %d 个文化，%d 个 barony\n"
          % ("/".join(conts), len(target_rows),
             sum(int(r["baronies"] or 0) for r in target_rows)))
    if not target_rows:
        print("没有需要归并的文化。")
        return

    # 语言 -> 首位组（用于没有 culture_groups 的文化）
    lang2grp = collections.defaultdict(collections.Counter)
    for r in rows:
        gs = [x for x in r["eu5_groups"].split(";") if x and not x.startswith("#")]
        if gs and r["eu5_language"]:
            lang2grp[r["eu5_language"]][gs[0].strip()] += 1

    def primary_group(r):
        gs = [x for x in r["eu5_groups"].split(";") if x and not x.startswith("#")]
        if gs:
            return gs[0].strip()
        lg = r["eu5_language"].strip()
        if lg and lg in lang2grp:
            return lang2grp[lg].most_common(1)[0][0]
        return None

    groups = collections.defaultdict(list)
    unresolved = []
    for r in target_rows:
        g = primary_group(r)
        if g is None:
            unresolved.append(r["culture"])
        else:
            groups[g].append(r)
    print("分成 %d 个组；未能定组 %d 个 %s\n" % (len(groups), len(unresolved), unresolved[:8]))

    zh = group_zh()
    existing = C.defined_cultures()
    pil = set(re.findall(r"(?m)^([a-z0-9_]+)\s*=\s*\{",
                         io.open(PILLARS, encoding="utf-8-sig", errors="ignore").read()))
    gen_text = io.open(GEN_CULT, encoding="utf-8-sig").read()

    plan = {}
    problems = []
    for g, mem in groups.items():
        key = g[:-6] if g.endswith("_group") else g
        rep = max(mem, key=lambda r: int(r["baronies"] or 0))
        if key in existing:
            problems.append("key 已被占用: %s" % key)
        if g not in pil or ("eu5_heritage_" + g) not in pil:
            problems.append("支柱缺失: %s" % g)
        if g not in zh:
            problems.append("缺中文组名: %s" % g)
        plan[g] = {"key": key, "zh": zh.get(g, ""), "rep": rep["culture"],
                   "members": [r["culture"] for r in mem],
                   "bar": sum(int(r["baronies"] or 0) for r in mem)}
    if problems:
        print("✗ 先修掉这些问题：")
        for p in problems:
            print("   ", p)
        sys.exit(1)

    for g, v in sorted(plan.items(), key=lambda kv: -kv[1]["bar"]):
        print("  %5d bar %4d cult  %-38s -> %-24s %s"
              % (v["bar"], len(v["members"]), g, v["key"], v["zh"]))

    if not apply:
        print("\nDRY RUN：未生成文件、未改 CSV。加 --apply 执行。")
        return

    # ---- 生成定义文件 ----
    out = ["# =========================================================",
           "# 按 EU5 文化组归并后的文化定义（culture_group_merge.py 生成）",
           "# %d 个文化 -> %d 个组文化；heritage = <group>_group，"
           % (len(target_rows), len(plan)),
           "# language = eu5_heritage_<group>_group；定义体克隆组内 barony 最多的成员。",
           "# =========================================================", ""]
    for g, v in sorted(plan.items(), key=lambda kv: kv[1]["key"]):
        blk = extract_block(gen_text, v["rep"])
        if blk is None:
            print("✗ 找不到代表文化定义 %s" % v["rep"])
            sys.exit(1)
        out.append("%s = {" % v["key"])
        out.extend(build_def(g, blk))
        out.append("}")
        out.append("")
    C.write_text(DEFS_OUT, "\r\n".join(out) + "\r\n")
    print("\n写出 %s（%d 个块）" % (os.path.relpath(DEFS_OUT, C.MOD), len(plan)))

    # ---- 生成本地化 ----
    loc = ["l_simp_chinese:"]
    for g, v in sorted(plan.items(), key=lambda kv: kv[1]["key"]):
        for suffix in ("", "_collective_noun", "_prefix"):
            loc.append(' %s%s:0 "%s"' % (v["key"], suffix, v["zh"]))
    C.write_text(LOC_OUT, "\r\n".join(loc) + "\r\n")
    print("写出 %s（%d 条）" % (os.path.relpath(LOC_OUT, C.MOD), len(loc) - 1))

    # ---- 改 CSV ----
    C.backup(C.CLASSIF, "groupmerge")
    for r in rows:
        if r["culture"] in {m for v in plan.values() for m in v["members"]}:
            r["target"] = plan[next(g for g, v in plan.items() if r["culture"] in v["members"])]["key"]
    C.save_classif(rows, header)
    print("CSV 更新 %d 行" % len(target_rows))

    cats = sorted({r["category"] for r in target_rows})
    print("\n下一步（省份）：")
    print("  python gen_debug/_apply_province_pop_culture.py --cats %s "
          "--continents %s --only-selected --apply" % (",".join(cats), ",".join(conts)))
    print("下一步（人物）：")
    print("  python gen_debug/_apply_people_culture.py --apply")


if __name__ == "__main__":
    main()
