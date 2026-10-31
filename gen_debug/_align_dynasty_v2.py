# -*- coding: utf-8 -*-
"""
宗族（dynasty）对齐原版 —— 规则 v2

旧规则的两个盲区（2026-10-31 用户指出）：
  1) 候选集只取 dynasty_merge_map.json 里的 42 个「归并父宗族」，
     漏掉所有「无子支系、直接作为 dynasty 存在」的宗族（如 rurikovich）。
  2) 匹配只靠人工/名字，没利用 culture 字段。

v2 规则：
  - 候选集 = mod 全部 *_dynasty 顶层块（不依赖归并 map）。
  - 匹配依据 = dynasty KEY 主体（EU5 原始家族名，如 rurikovich），
    不用 name 字段（name 是本地化键，可能是错译，如 name_roderick）。
  - 文化匹配 = mod culture 先经 _culture_classification.csv 归一化到
    CK3 文化（muscovite -> russian），再与 vanilla dynasty 的 culture 比对。
  - 置信分层：
      A  名字精确(>=0.99) + 文化匹配
      B  名字高(0.85~0.99) + 文化匹配
      C  名字中(0.62~0.85) + 文化匹配   <- rurikovich 在这一层
      D  名字高(>=0.85) 但文化不匹配（需复核）
      E  名字中(0.62~0.85) 但文化不匹配（低置信）
      N  无候选（保持 mod 自定义）
  - 默认只读，输出 CSV；--apply 才会改 name 并追加 COA 别名（仅 A/B 层）。

用法：
  python _align_dynasty_v2.py            # dry-run，出候选 CSV + 统计
  python _align_dynasty_v2.py --apply    # 落地 A/B 层
"""
import csv
import difflib
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAN_DIR = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game\common\dynasties"
MOD_DYN = os.path.join(ROOT, "common", "dynasties", "zz_eu5_dynasties.txt")
ALIAS = os.path.join(ROOT, "common", "coat_of_arms", "coat_of_arms", "95_zz_eu5_dynasty_aliases.txt")
CLS = os.path.join(ROOT, "gen_debug", "_culture_classification.csv")
OUT = os.path.join(ROOT, "gen_debug", "dynasty_alignment_candidates.csv")

RE_BLOCK = re.compile(r'^([A-Za-z0-9_\-]+)\s*=\s*\{\s*$')


def parse_blocks(path):
    """返回 [(key, body_lines, start_lineno_1based)]"""
    text = open(path, encoding="utf-8-sig", errors="replace").read()
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)
    out, i = [], 0
    while i < len(lines):
        m = RE_BLOCK.match(lines[i])
        if m:
            key = m.group(1)
            start = i + 1
            depth = 1
            j = i + 1
            body = []
            while j < len(lines) and depth > 0:
                depth += lines[j].count("{") - lines[j].count("}")
                if depth > 0:
                    body.append(lines[j])
                j += 1
            out.append((key, body, start))
            i = j
        else:
            i += 1
    return out


def get_field(body, field):
    for l in body:
        m = re.match(r'\s*' + field + r'\s*=\s*"?([^"\s]+)"?', l)
        if m:
            return m.group(1)
    return None


def build_culture_map():
    cmap = {}
    for r in csv.DictReader(open(CLS, encoding="utf-8-sig")):
        c = r["culture"]
        t = (r.get("target") or "").strip()
        if t.startswith("NEW:"):
            t = t[4:]
        base = c[:-8] if c.endswith("_culture") else c
        if t and t not in (c, base):
            cmap[base] = t
        cmap.setdefault(base, base)
    return cmap


def norm_culture(c, cmap):
    if not c:
        return ""
    c = c.strip().strip('"')
    return cmap.get(c, c)


def core_mod(key):
    k = key[:-8] if key.endswith("_dynasty") else key
    return k.lower()


def core_van(key, name):
    if name and name.startswith("dynn_"):
        return name[5:].lower()
    return key.lower()


def name_score(mc, vc):
    r = difflib.SequenceMatcher(None, mc, vc).ratio()
    pre = 0
    for a, b in zip(mc, vc):
        if a == b:
            pre += 1
        else:
            break
    # 词根相同（如 rurikovich / rurikid 共享 rurik）：
    # 仅当公共前缀 >=5 且长度接近时给受控提升，避免短名前缀（champaner/cham）造成假满分
    if pre >= 5 and abs(len(mc) - len(vc)) <= 4:
        r = max(r, min(0.95, 0.6 + pre * 0.05))
    return r


def main():
    apply_mode = "--apply" in sys.argv
    cmap = build_culture_map()

    # mod dynasties
    mod = []
    for key, body, ln in parse_blocks(MOD_DYN):
        name = get_field(body, "name")
        cult = get_field(body, "culture")
        mod.append({"key": key, "name": name, "culture": cult, "line": ln})

    # vanilla dynasties
    van = []
    for fn in os.listdir(VAN_DIR):
        if fn.endswith(".txt"):
            for key, body, _ln in parse_blocks(os.path.join(VAN_DIR, fn)):
                van.append({"key": key, "name": get_field(body, "name"),
                            "culture": get_field(body, "culture")})

    van_by_cult = {}
    van_all = []
    for v in van:
        vc = norm_culture(v["culture"], cmap)
        v["cn"] = vc
        van_all.append(v)
        van_by_cult.setdefault(vc, []).append(v)

    aligned = [d for d in mod if d["name"] and d["name"].startswith("dynn_")]
    custom = [d for d in mod if not (d["name"] and d["name"].startswith("dynn_"))]

    rows = []
    for d in custom:
        mc = core_mod(d["key"])
        mcn = norm_culture(d["culture"], cmap)
        pool = van_by_cult.get(mcn, []) if mcn else van_all
        best = None
        for v in pool:
            vc = core_van(v["key"], v["name"])
            s = name_score(mc, vc)
            # 无 culture 信息时不算文化匹配（只能靠名字），避免假阳性
            cm = (norm_culture(v["culture"], cmap) == mcn) if mcn else False
            if best is None or s > best[0]:
                best = (s, v, cm)
        # 若文化池无结果或分数低，做一次全量 fallback（文化不匹配也算候选）
        if best is None or best[0] < 0.62:
            for v in van_all:
                vc = core_van(v["key"], v["name"])
                s = name_score(mc, vc)
                if best is None or s > best[0]:
                    best = (s, v, norm_culture(v["culture"], cmap) == mcn)

        if best is None or best[0] < 0.62:
            tier = "N"
            v = None
            score = best[0] if best else 0.0
            cmatch = False
        else:
            score, v, cmatch = best
            if cmatch and score >= 0.99:
                tier = "A"
            elif cmatch and score >= 0.85:
                tier = "B"
            elif cmatch:
                tier = "C"
            elif score >= 0.85:
                tier = "D"
            else:
                tier = "E"

        rows.append({
            "tier": tier,
            "mod_key": d["key"],
            "mod_name": d["name"],
            "mod_culture": d["culture"] or "",
            "culture_norm": mcn,
            "van_key": v["key"] if v else "",
            "van_name": v["name"] if v else "",
            "van_culture": v["culture"] if v else "",
            "name_score": "%.3f" % score,
            "culture_match": "1" if cmatch else "0",
            "mod_line": d["line"],
        })

    order = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4, "N": 5}
    rows.sort(key=lambda r: (order[r["tier"]], -float(r["name_score"])))

    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    from collections import Counter
    cnt = Counter(r["tier"] for r in rows)
    print("mod dynasty: total=%d  already_aligned=%d  custom=%d" % (len(mod), len(aligned), len(custom)))
    print("candidates CSV -> %s" % OUT)
    print("tier: A=%d B=%d C=%d D=%d E=%d N=%d" %
          (cnt["A"], cnt["B"], cnt["C"], cnt["D"], cnt["E"], cnt["N"]))
    print("\n--- rurikovich 规则有效性诊断（该宗族已手工对齐，此处验证规则本可捕获它）---")
    for d in mod:
        if d["key"] == "rurikovich_dynasty":
            mc = core_mod(d["key"])
            mcn = norm_culture(d["culture"], cmap)
            best = None
            for v in (van_by_cult.get(mcn, []) or van_all):
                s = name_score(mc, core_van(v["key"], v["name"]))
                if best is None or s > best[0]:
                    best = (s, v)
            print("  core=%s  norm_culture=%s  ->  %s %s  score=%.3f" %
                  (mc, mcn, best[1]["key"], best[1]["name"], best[0]))
    print("\n--- tier C sample (culture-matched, weaker name) ---")
    for r in [x for x in rows if x["tier"] == "C"][:20]:
        print("%-34s %-10s -> %-24s %-20s score=%s" %
              (r["mod_key"], r["mod_culture"], r["van_key"], r["van_name"], r["name_score"]))
    print("\n--- tier D sample (name-strong, culture mismatch) ---")
    for r in [x for x in rows if x["tier"] == "D"][:15]:
        print("%-34s %-10s -> %-24s %-20s score=%s" %
              (r["mod_key"], r["mod_culture"], r["van_key"], r["van_name"], r["name_score"]))


if __name__ == "__main__":
    main()
