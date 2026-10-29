# -*- coding: utf-8 -*-
"""持有多个公国的角色，主头衔切到他首都所在的那个有地公国。

口径（用户 2026-10-29 当面定）：
  1. 持有多个公国的，主头衔切到首都所在公国 —— 和多伯爵一个处理法
     （生成器 _fix_politics_output.py 里那段：持 >=2 个县的角色穿他首都所在的那个县）。
  2. 主头衔本身没地的（阿图瓦 d_eu5_ars 这种 titular），也一样切到有地的那个。

做法：
  - 扫 history/titles 全部文件，取每个头衔在开局（最后一个日期块）的 holder。
  - 持 >=2 个 d_ 的 holder 才算。
  - 目标公国：按他统治的国家 rank 从高到低，取该国 capital 所在县**直接**归属的公国；
    该公国必须是他自己持有的、且 00_landed_titles.txt 里真有地（不是 titular）。
    bur_jeanne_iii_capet 就是这条：ARS 首都 arras 落在 d_picardy（不是他的），
    退到 FCB 首都 dole 落在 d_franche_comte（他的、有地）—— 阿图瓦切到弗朗什孔泰。
  - 一个都找不到的（首都所在的公国都被别人拿着），退到首都所在的县；再不行就不动。
  - 已经指向同一头衔的条目原样保留；指向别的才改。

用法：
  python gen_debug/_fix_duchy_primary.py            # dry run
  python gen_debug/_fix_duchy_primary.py --apply
"""
import argparse
import glob
import io
import json
import os
import re
import shutil
import time
from collections import defaultdict

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
EXP = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
PATH = os.path.join(MOD, "common", "on_action", "zz_eu5_primary_titles.txt")
LTD = os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt")

RANK = {"e": 3, "k": 2, "d": 1, "c": 0, None: -1}


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


def blocks(text):
    """[(key, body)]，只取顶层块。"""
    out, cur, depth = [], None, 0
    for ln in text.split("\n"):
        s = ln.rstrip("\r")
        m = re.match(r"^([hedkcb]_[A-Za-z0-9_-]+)\s*=\s*\{", s)
        if m and depth == 0:
            cur = [m.group(1), []]
            out.append(cur)
            depth = 1
            continue
        if cur is not None:
            depth += s.count("{") - s.count("}")
            cur[1].append(s)
            if depth <= 0:
                cur, depth = None, 0
    return [(k, "\n".join(b)) for k, b in out]


def final_holder(body):
    """最后一个日期块里的 holder；没有日期块就取第一处 holder。"""
    ds = re.findall(r"(?m)^\t(\d+\.\d+\.\d+) = \{", body)
    if ds:
        m = re.search(r"(?m)^\t" + re.escape(ds[-1]) + r" = \{(.*?)\n\t\}", body, re.S)
        if m:
            h = re.search(r"holder\s*=\s*(\S+)", m.group(1))
            if h:
                return h.group(1)
    h = re.search(r"(?m)^\s*holder\s*=\s*(\S+)", body)
    return h.group(1) if h else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    landed_d = set(re.findall(r"(?m)^\t*(d_[a-z0-9_-]+)\s*=\s*\{", read(LTD)))
    landed_c = set(re.findall(r"(?m)^\t*(c_[a-z0-9_-]+)\s*=\s*\{", read(LTD)))

    # 县 -> 直接归属的公国
    stack, direct = [], {}
    for ln in read(LTD).split("\n"):
        s = ln.rstrip("\r")
        m = re.match(r"^(\t*)([hedkcb]_[a-z0-9_-]+)\s*=\s*\{", s)
        if m:
            key = m.group(2)
            d = next((x for x in reversed(stack) if x.startswith("d_")), None)
            if d and key.startswith("c_"):
                direct.setdefault(key, d)
            stack.append(key)
            continue
        if s.strip() == "}" and stack:
            stack.pop()

    # holder -> 持有的头衔
    held = defaultdict(list)
    for p in glob.glob(os.path.join(MOD, "history", "titles", "**", "*.txt"), recursive=True):
        t = re.sub(r"(?m)#[^\n]*$", "", read(p))
        for key, body in blocks(t):
            h = final_holder(body)
            if h:
                held[h].append(key)

    pol = json.load(io.open(os.path.join(EXP, "eu5_politics.json"), encoding="utf-8-sig"))
    mapping = json.load(io.open(os.path.join(EXP, "mapping.json"), encoding="utf-8-sig"))
    loc_county = {l["name"]: "c_" + l["county"] for l in mapping["locations"] if l.get("county")}

    role2tags = defaultdict(list)
    for tag, c in pol["countries"].items():
        for r in (c.get("ruler"), c.get("regent")):
            if r:
                role2tags[r].append(tag)

    def pick(role, ds):
        """目标头衔：首都所在的有地公国；退而求其次，首都所在的县。"""
        tags = sorted(role2tags.get(role, []),
                      key=lambda x: -RANK.get(pol["countries"][x].get("rank"), -1))
        for tag in tags:
            cty = loc_county.get(pol["countries"][tag].get("capital") or "")
            d = direct.get(cty) if cty else None
            if d and d in ds and d in landed_d:
                return d, tag
        for tag in tags:
            cty = loc_county.get(pol["countries"][tag].get("capital") or "")
            if cty and cty in held.get(role, []) and cty in landed_c:
                return cty, tag
        return None, None

    want = {}
    skipped_king = []
    for role, ts in held.items():
        ds = [x for x in ts if x.startswith("d_")]
        if len(ds) < 2:
            continue
        # 还持王国/帝国的，主头衔是王国，不在这条规则里（用户 2026-10-29 定：只切纯公国持有人）
        if any(x[0] in "ke" for x in ts):
            skipped_king.append(role)
            continue
        t, tag = pick(role, ds)
        if t:
            want[role] = (t, tag, len(ds))
    print("跳过持王国/帝国的：%d" % len(skipped_king))

    text = read(PATH)
    lines = text.split("\n")
    cur = {}
    for i, ln in enumerate(lines):
        m = re.match(r"^\t\tcharacter:([a-z0-9_]+) = \{", ln)
        if m:
            cur[m.group(1)] = i
    for role, i in cur.items():
        for j in range(i, min(i + 7, len(lines))):
            m = re.search(r"set_primary_title_to = title:([a-z0-9_]+)", lines[j])
            if m:
                cur[role] = (i, j, m.group(1))
                break

    changes, adds, same = [], [], []
    for role, (t, tag, n) in sorted(want.items()):
        old = cur.get(role)
        if isinstance(old, tuple):
            if old[2] == t:
                same.append(role)
            else:
                changes.append((role, old[2], t, n, tag))
        else:
            adds.append((role, t, n, tag))

    print("持有 >=2 个公国：%d，能定目标：%d" % (
        len([1 for ts in held.values() if len([x for x in ts if x.startswith('d_')]) > 1]),
        len(want)))
    print("  已是目标：%d  需要改：%d  新增：%d" % (len(same), len(changes), len(adds)))
    for role, a, b, n, tag in changes:
        print("  %-45s %-3d d  %s -> %s   (%s)" % (role, n, a, b, tag))
    for role, t, n, tag in adds:
        print("  %-45s %-3d d  + %s   (%s)" % (role, n, t, tag))

    if not args.apply:
        print("\n(dry run)")
        return

    for role, _a, b, _n, _t in changes:
        lines[cur[role][1]] = re.sub(r"title:[a-z0-9_]+", "title:" + b, lines[cur[role][1]])

    head_end = None
    for i, ln in enumerate(lines):
        if ln.strip() == "effect = {":
            head_end = i
            break
    tail = None
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == "}":
            tail = i
            break
    body = lines[head_end + 1:tail]
    # 新增条目按 ruler 名插到排序位置
    for role, t, _n, _tag in adds:
        new = ["\t\tcharacter:%s = {" % role,
               "\t\t\tif = {",
               "\t\t\t\tlimit = { is_alive = yes }",
               "\t\t\t\tset_primary_title_to = title:%s" % t,
               "\t\t\t}",
               "\t\t}"]
        at = None
        for i, ln in enumerate(body):
            m = re.match(r"^\t\tcharacter:([a-z0-9_]+) = \{", ln)
            if m and m.group(1) > role:
                at = i
                break
        if at is None:
            body.extend(new)
        else:
            body[at:at] = new

    out = lines[:head_end + 1] + body + lines[tail:]
    bak = PATH + ".bak_" + time.strftime("%Y%m%d_%H%M%S")
    shutil.copy2(PATH, bak)
    with io.open(PATH, "w", encoding="utf-8-sig", newline="\r\n") as fh:
        fh.write("\n".join(out))
    print("\napplied: %d changed, %d added -> %s" % (len(changes), len(adds), PATH))
    print("backup: %s" % bak)


if __name__ == "__main__":
    main()
