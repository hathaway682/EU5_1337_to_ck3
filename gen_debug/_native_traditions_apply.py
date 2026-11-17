# -*- coding: utf-8 -*-
"""给美洲原住民（北美+南美）与大洋洲文化写入按史实整理的传统，替换 Ck3MapGen 随机抽的传统。

改两个文件：
  1. common/culture/cultures/00_generated_cultures.txt   —— 单文化（1118 个）
  2. common/culture/cultures/zz_eu5_culture_group.txt    —— 组文化（nadene / tupi / papuan / polynesian …）

数据源：gen_debug/_native_traditions_data.py
   GROUP_SETS  按语系组（eu5_groups 首位，如 papuan_group）给默认 4 条
   CULT_SETS   单文化覆盖（著名民族单独指定）

范围：_culture_classification.csv 的 continent ∈ {北美洲, 南美洲, 大洋洲}。

安全闸：
  - 只允许 CK3 基础游戏 00_*.txt 里定义、且不带 has_cultural_pillar 的传统
    （本 mod 的传承是自建 *_group 支柱，原版传承门槛永远不匹配）；
  - 每组 4 条互不重复，且不违反 can_pick 互斥（castle/city、婚姻三选一、战士/哲人）；
  - 数据表本身用 ast 扫重复 key（字典重复 key 会静默覆盖）；
  - 保留原文件 BOM 与换行风格。

用法：
  python gen_debug/_native_traditions_apply.py            # 干跑，只打印
  python gen_debug/_native_traditions_apply.py --apply    # 落盘
"""
import io
import os
import re
import ast
import csv
import sys
import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _native_traditions_data import GROUP_SETS, CULT_SETS  # noqa: E402

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CK3 = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"

CULT_FILE = os.path.join(MOD, "common", "culture", "cultures", "00_generated_cultures.txt")
GROUP_FILE = os.path.join(MOD, "common", "culture", "cultures", "zz_eu5_culture_group.txt")
CLASSIFY = os.path.join(MOD, "gen_debug", "_culture_classification.csv")
DATA = os.path.join(MOD, "gen_debug", "_native_traditions_data.py")
LOC = os.path.join(CK3, "localization", "simp_chinese", "culture", "traditions",
                   "cultural_traditions_l_simp_chinese.yml")
REPORT = os.path.join(MOD, "gen_debug", "_native_traditions_report.csv")

CONTINENTS = ("北美", "南美", "大洋洲")

EXCLUSIVE = [
    {"castle_keepers", "city_keepers"},
    {"concubines", "monogamous", "polygamous"},
    {"warrior_culture", "philosopher_culture"},
    {"hunters", "vegetarianism"},
    {"sacred_hunts", "vegetarianism"},
    {"isolationist", "cultural_primacy"},
    {"staunch_traditionalists", "fp3_fierce_independence"},
]


def dup_keys(path):
    """用 ast 找模块里字典的重复 key（字面量重复会静默覆盖）。"""
    tree = ast.parse(io.open(path, encoding="utf-8").read())
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            seen = set()
            for k in node.keys:
                if isinstance(k, ast.Constant):
                    if k.value in seen:
                        bad.append(k.value)
                    seen.add(k.value)
    return bad


def load_allowed():
    """返回允许使用的传统 key：基础游戏 00_*.txt 里不带 has_cultural_pillar 门槛的，
    加上本 mod 自己在 common/culture/traditions/ 里定义的传统（如从 RICE 抄来的
    tradition_RICE_andean_hydraulic_engineering）。"""
    allowed = set()
    for f in glob.glob(os.path.join(CK3, "common", "culture", "traditions", "00_*.txt")):
        if "debug" in os.path.basename(f):
            continue
        txt = io.open(f, encoding="utf-8-sig", errors="replace").read()
        idx = [(m.start(), m.group(1)) for m in re.finditer(r'^(tradition_[a-z0-9_A-Z]+)\s*=\s*\{', txt, re.M)]
        for i, (s, k) in enumerate(idx):
            e = idx[i + 1][0] if i + 1 < len(idx) else len(txt)
            if "has_cultural_pillar" not in txt[s:e]:
                allowed.add(k[len("tradition_"):])
    for f in glob.glob(os.path.join(MOD, "common", "culture", "traditions", "*.txt")):
        txt = io.open(f, encoding="utf-8-sig", errors="replace").read()
        for k in re.findall(r'(?m)^(tradition_[a-zA-Z0-9_]+)\s*=\s*\{', txt):
            allowed.add(k[len("tradition_"):])
    return allowed


def load_loc():
    loc = {}
    if os.path.exists(LOC):
        for line in io.open(LOC, encoding="utf-8-sig", errors="replace"):
            m = re.match(r'\s*(tradition_[a-z0-9_]+)_name:\s*"(.*?)"\s*$', line)
            if m:
                loc[m.group(1)[len("tradition_"):]] = m.group(2)
    # 本 mod 自己补的传统本地化（RICE 抄来的那条）
    for f in glob.glob(os.path.join(MOD, "localization", "simp_chinese", "*.yml")):
        for line in io.open(f, encoding="utf-8-sig", errors="replace"):
            m = re.match(r'\s*(tradition_[a-zA-Z0-9_]+)_name:\d?\s*"(.*?)"\s*$', line)
            if m:
                loc.setdefault(m.group(1)[len("tradition_"):], m.group(2))
    return loc


def read_text(path):
    raw = open(path, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    nl = "\r\n" if "\r\n" in text else "\n"
    return text, bom, nl


def write_text(path, text, bom):
    data = text.encode("utf-8")
    if bom:
        data = b"\xef\xbb\xbf" + data
    open(path, "wb").write(data)


BLOCK_RE = re.compile(r'(?m)^([a-z0-9_]+)\s*=\s*\{')
TRAD_RE = re.compile(r'(\n\ttraditions = \{\r?\n)((?:\t\ttradition_[A-Za-z0-9_]+\r?\n)+)(\t\})')


def split_blocks(text):
    out = []
    for m in BLOCK_RE.finditer(text):
        key = m.group(1)
        depth = 0
        i = m.end() - 1
        while i < len(text):
            c = text[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    out.append((key, m.start(), i + 1))
                    break
            i += 1
    return out


def heritage_of(block_text):
    m = re.search(r'\n\theritage = ([a-z0-9_]+)', block_text)
    return m.group(1) if m else None


def primary_group(eu5_groups):
    g = (eu5_groups or "").split("#")[0]
    g = g.split(";")[0].strip()
    return g or None


def main():
    apply = "--apply" in sys.argv
    allowed = load_allowed()
    loc = load_loc()

    bad = dup_keys(DATA)
    if bad:
        print("!! 数据表有重复 key：%s" % ", ".join(sorted(set(bad))))
        return 1

    # 1) 目标文化清单
    target = {}
    for r in csv.DictReader(io.open(CLASSIFY, encoding="utf-8-sig")):
        if any(r["continent"].startswith(c) for c in CONTINENTS):
            target[r["culture"]] = (r["continent"], r["heritage"], primary_group(r["eu5_groups"]))

    # 2) 校验策划表
    problems = []
    for key, trad in list(GROUP_SETS.items()) + list(CULT_SETS.items()):
        if len(trad) != 4:
            problems.append("%s: %d 条（应为 4）" % (key, len(trad)))
        if len(set(trad)) != len(trad):
            problems.append("%s: 有重复" % key)
        for t in trad:
            if t not in allowed:
                problems.append("%s: 传统 %s 不在允许池" % (key, t))
        for group in EXCLUSIVE:
            if len(group & set(trad)) > 1:
                problems.append("%s: 互斥 %s" % (key, sorted(group & set(trad))))

    # 3) 单文化文件
    text, bom, nl = read_text(CULT_FILE)
    edits = []
    uncovered = []
    for key, s, e in split_blocks(text):
        if key not in target:
            continue
        cont, heritage, pgroup = target[key]
        block = text[s:e]
        trad = CULT_SETS.get(key)
        if not trad:
            trad = GROUP_SETS.get(pgroup or "") or GROUP_SETS.get(heritage_of(block) or heritage or "")
        if not trad:
            uncovered.append((key, cont, pgroup, heritage))
            continue
        m = TRAD_RE.search(block)
        if not m:
            problems.append("%s: 找不到 traditions 块" % key)
            continue
        body = "".join("\t\ttradition_%s%s" % (t, nl) for t in trad)
        edits.append((s, e, block[:m.start(2)] + body + block[m.end(2):], key, trad, cont))

    # 4) 组文化文件
    gtext, gbom, gnl = read_text(GROUP_FILE)
    gedits = []
    for key, s, e in split_blocks(gtext):
        block = gtext[s:e]
        h = heritage_of(block)
        if h not in GROUP_SETS:
            continue
        trad = GROUP_SETS[h][:3]
        m = TRAD_RE.search(block)
        if not m:
            problems.append("组文化 %s: 找不到 traditions 块" % key)
            continue
        body = "".join("\t\ttradition_%s%s" % (t, gnl) for t in trad)
        gedits.append((s, e, block[:m.start(2)] + body + block[m.end(2):], key, trad, h))

    by_cont = {}
    for row in edits:
        by_cont[row[5]] = by_cont.get(row[5], 0) + 1
    print("单文化：目标 %d 个，将改写 %d 个 %s" % (
        len(target), len(edits), dict(sorted(by_cont.items()))))
    print("组文化：将改写 %d 个" % len(gedits))
    for k, cont, pg, h in uncovered:
        print("   未覆盖: %s (%s / %s / %s)" % (k, cont, pg, h))
    if problems:
        print("!! 落地问题：")
        for p in problems:
            print("   " + p)
        return 1

    if apply:
        rows = []
        for s, e, nb, key, trad, cont in edits:
            rows.append([key, cont, "文化", " / ".join(trad), " / ".join(loc.get(t, t) for t in trad)])
        for s, e, nb, key, trad, h in gedits:
            rows.append([key, "组文化", h, " / ".join(trad), " / ".join(loc.get(t, t) for t in trad)])
        # 报告被预览面板占用时依次退到 _2/_3/_4，不影响主产物写入
        fh = None
        for suffix in ["", "_2", "_3", "_4"]:
            out = REPORT.replace(".csv", "%s.csv" % suffix)
            try:
                fh = io.open(out, "w", encoding="utf-8-sig", newline="")
                break
            except PermissionError:
                continue
        if fh is None:
            print("!! 报告全部被占用，跳过报告")
            out = "(skipped)"
        else:
            with fh:
                w = csv.writer(fh)
                w.writerow(["key", "continent", "heritage_or_type", "traditions", "traditions_cn"])
                w.writerows(rows)
        for s, e, nb, key, trad, cont in sorted(edits, key=lambda x: -x[0]):
            text = text[:s] + nb + text[e:]
        write_text(CULT_FILE, text, bom)
        for s, e, nb, key, trad, h in sorted(gedits, key=lambda x: -x[0]):
            gtext = gtext[:s] + nb + gtext[e:]
        write_text(GROUP_FILE, gtext, gbom)
        print("已写入。报告：%s" % out)
    else:
        print("干跑：未写入。样例 ——")
        for s, e, nb, key, trad, cont in edits[:5]:
            print("  %s (%s) -> %s" % (key, cont, ", ".join(loc.get(t, t) for t in trad)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
