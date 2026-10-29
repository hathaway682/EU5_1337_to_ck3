# -*- coding: utf-8 -*-
"""
Parse CK3 landed titles (mod + game) and apply the mod's on_action
de jure overrides (common/on_action/1337_de_jure_set.txt) to produce the
effective de jure structure of the mod at game start.

Outputs:
  _de_jure_structure.json  - machine readable full structure
  _de_jure_structure.md    - human readable report
"""

import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
GAME_LANDED = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game\common\landed_titles"

TIER_RE = re.compile(r"^([hkedcb])_([a-z0-9_-]+)$")
TIER_LABEL = {"h": "霸权", "e": "帝国", "k": "王国", "d": "公国", "c": "伯爵领", "b": "男爵领"}
TIER_RANK = {"h": 5, "e": 4, "k": 3, "d": 2, "c": 1, "b": 0}
TIER_GAME_NAME = {"tier_hegemony": "h", "tier_empire": "e", "tier_kingdom": "k",
                  "tier_duchy": "d", "tier_county": "c", "tier_barony": "b"}


def tokenize(path):
    """Minimal CK3 tokenizer: strips comments, keeps quoted strings intact."""
    tokens = []
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        for line in f:
            i, n = 0, len(line)
            while i < n:
                c = line[i]
                if c == "#":
                    break
                if c in "{}":
                    tokens.append(c)
                    i += 1
                elif c == '"':
                    j = i + 1
                    buf = []
                    while j < n:
                        if line[j] == '"':
                            break
                        buf.append(line[j])
                        j += 1
                    tokens.append("".join(buf))
                    i = j + 1
                elif c.isspace():
                    i += 1
                else:
                    j = i
                    while j < n and not line[j].isspace() and line[j] not in "{}#":
                        j += 1
                    tokens.append(line[i:j])
                    i = j
    return tokens


def parse_blocks(tokens, i=0):
    """Returns (blocks, next_index). A block is (key, value) where value is a
    list of blocks, a string, or None."""
    blocks = []
    while i < len(tokens):
        t = tokens[i]
        if t == "}":
            return blocks, i + 1
        if t == "{":
            inner, i = parse_blocks(tokens, i + 1)
            blocks.append((None, inner))
            continue
        key = t
        i += 1
        if i < len(tokens) and tokens[i] == "=":
            i += 1
            if i < len(tokens) and tokens[i] == "{":
                inner, i = parse_blocks(tokens, i + 1)
                blocks.append((key, inner))
            else:
                val = tokens[i] if i < len(tokens) else None
                i += 1
                blocks.append((key, val))
        else:
            blocks.append((key, None))
    return blocks, i


def find_block(blocks, key):
    for k, v in blocks:
        if k == key and isinstance(v, list):
            return v
    return None


def block_scalar(blocks, key):
    for k, v in blocks:
        if k == key and isinstance(v, str):
            return v
    return None


class LandedTitles:
    def __init__(self):
        self.titles = {}  # id -> dict
        self.order = []   # first-seen order

    def add_file(self, path, source):
        blocks, _ = parse_blocks(tokenize(path))
        self._walk(blocks, None, source)

    def _walk(self, blocks, parent, source):
        for key, inner in blocks:
            if not key:
                if isinstance(inner, list):
                    self._walk(inner, parent, source)
                continue
            m = TIER_RE.match(key)
            if not m or not isinstance(inner, list):
                continue
            tier = m.group(1)
            if key not in self.titles:
                self.titles[key] = {
                    "id": key,
                    "tier": tier,
                    "parent": parent,
                    "capital": None,
                    "children": [],
                    "sources": [],
                    "noble_family": False,
                    "landless": False,
                }
                self.order.append(key)
            t = self.titles[key]
            if source not in t["sources"]:
                t["sources"].append(source)
            if parent is not None:
                t["parent"] = parent
            if "noble_family" in t and t["noble_family"]:
                pass
            cap = block_scalar(inner, "capital")
            if cap and cap.startswith("c_"):
                t["capital"] = cap
            if "noble_family" in t:
                t["noble_family"] = t["noble_family"] or (block_scalar(inner, "noble_family") == "yes")
            if "landless" in t:
                # 只要任一文件声明 landless = yes 就视为 landless
                # （zz_vanilla_titulars.txt 封存原版头衔，ToSC_titles.txt 只补 capital）
                t["landless"] = t["landless"] or (block_scalar(inner, "landless") == "yes")
            # children
            for k2, v2 in inner:
                if k2 and TIER_RE.match(k2) and isinstance(v2, list):
                    if k2 not in t["children"]:
                        t["children"].append(k2)
            # recurse
            for k2, v2 in inner:
                if k2 and TIER_RE.match(k2) and isinstance(v2, list):
                    self._walk([(k2, v2)], key, source)

    def finalize(self):
        """Fill implicit capitals (first county child) and child lists from parent map."""
        for t in self.titles.values():
            if t["capital"] is None:
                for ch in t["children"]:
                    if self.titles[ch]["tier"] == "c" and not self.titles[ch]["noble_family"]:
                        t["capital"] = ch
                        break
        # rebuild children sorted by file order
        for t in self.titles.values():
            t["children"] = [c for c in self.order if self.titles[c]["parent"] == t["id"]]


def parse_on_action(path):
    """Extract de jure override operations in file order.
    Returns list of dicts: kind in direct/hierarchy/capital, title, target,
    plus optional tier limit info."""
    blocks, _ = parse_blocks(tokenize(path))
    ops = []
    # find the 1337_de_jure_set block
    target = None
    for k, v in blocks:
        if k == "1337_de_jure_set" and isinstance(v, list):
            target = v
            break
    if target is None:
        return ops
    effect = find_block(target, "effect")
    if effect is None:
        return ops

    def walk(entries):
        for key, val in entries:
            if not key or not isinstance(val, list):
                continue
            m = re.match(r"^title:(.+)$", key)
            if m:
                tid = m.group(1)
                if not re.match(r"^[hkedcb]_[a-z0-9_-]+$", tid):
                    ops.append({"kind": "invalid", "title": key, "target": None, "note": "malformed title key"})
                    continue
                # check what's inside
                for k2, v2 in val:
                    if k2 == "set_de_jure_liege_title" and isinstance(v2, str):
                        tm = re.match(r"^title:(.+)$", v2)
                        ops.append({"kind": "direct", "title": tid, "target": tm.group(1) if tm else v2})
                    elif k2 == "set_capital_county" and isinstance(v2, str):
                        tm = re.match(r"^title:(.+)$", v2)
                        ops.append({"kind": "capital", "title": tid, "target": tm.group(1) if tm else v2})
                    elif k2 == "every_in_de_jure_hierarchy" and isinstance(v2, list):
                        tier_lim = None
                        new_parent = None
                        for k3, v3 in v2:
                            if k3 == "limit" and isinstance(v3, list):
                                for k4, v4 in v3:
                                    if k4 == "tier" and isinstance(v4, str):
                                        tier_lim = v4
                            elif k3 == "set_de_jure_liege_title" and isinstance(v3, str):
                                tm = re.match(r"^title:(.+)$", v3)
                                new_parent = tm.group(1) if tm else v3
                        ops.append({"kind": "hierarchy", "title": tid, "target": new_parent, "tier": tier_lim})
            else:
                # anonymous / other nested blocks (should not happen in effect)
                walk(val)

    walk(effect)
    return ops


def collect_hierarchy(titles, root_id, tier_filter=None):
    """All titles in the de jure hierarchy of root_id (excluding root itself),
    computed from the current parent map."""
    out = []
    stack = [root_id]
    while stack:
        cur = stack.pop()
        for tid, t in titles.items():
            if t["parent"] == cur:
                if tier_filter is None or t["tier"] == tier_filter:
                    out.append(tid)
                stack.append(tid)
    return out


def apply_on_action(titles, ops):
    changes = []
    for op in ops:
        tid = op["title"]
        if op["kind"] == "invalid":
            changes.append({"kind": "invalid", "title": tid, "note": op.get("note")})
            continue
        if tid not in titles:
            changes.append({"kind": "missing", "title": tid, "target": op.get("target"), "note": "标题在有效法理中不存在"})
            continue
        if op["kind"] == "direct":
            tgt = op["target"]
            if tgt not in titles:
                changes.append({"kind": "missing", "title": tid, "target": tgt, "note": "目标标题不存在"})
                continue
            old = titles[tid]["parent"]
            if old == tgt:
                changes.append({"kind": "direct", "title": tid, "from": old, "to": tgt, "note": "本来就在该法理下，无实际变化"})
                continue
            titles[tid]["parent"] = tgt
            changes.append({"kind": "direct", "title": tid, "from": old, "to": tgt})
        elif op["kind"] == "capital":
            tgt = op["target"]
            if tgt not in titles:
                changes.append({"kind": "missing", "title": tid, "target": tgt, "note": "目标首都伯爵领不存在"})
                continue
            old = titles[tid]["capital"]
            titles[tid]["capital"] = tgt
            changes.append({"kind": "capital", "title": tid, "from": old, "to": tgt})
        elif op["kind"] == "hierarchy":
            tgt = op["target"]
            if tgt not in titles:
                changes.append({"kind": "missing", "title": tid, "target": tgt, "note": "目标标题不存在"})
                continue
            moved = []
            tier = TIER_GAME_NAME.get(op.get("tier"))
            for t in collect_hierarchy(titles, tid, tier_filter=tier):
                if t == tgt:
                    continue
                old = titles[t]["parent"]
                if old == tgt:
                    continue
                titles[t]["parent"] = tgt
                moved.append((t, old))
            changes.append({"kind": "hierarchy", "title": tid, "from": titles[tid]["parent"],
                            "to": tgt, "moved": moved, "tier": op.get("tier")})
    return changes


def rebuild_children(titles):
    for t in titles.values():
        t["children"] = []
    for t in titles.values():
        if t["parent"] and t["parent"] in titles:
            titles[t["parent"]]["children"].append(t["id"])


def load_all():
    lt = LandedTitles()
    # game files that still load alongside the mod (mod's 00 replaces the game 00)
    game_files = [
        "01_japan.txt",
        "01_japan_noble_family.txt",
        "01_korea_noble_family.txt",
        "01_other_noble_family.txt",
        "02_china.txt",
        "03_seasia.txt",
        "04_china_noble_families.txt",
        "05_goryeo.txt",
        "06_philippines.txt",
    ]
    for fn in game_files:
        p = os.path.join(GAME_LANDED, fn)
        if os.path.exists(p):
            lt.add_file(p, f"game:{fn}")
    # mod files (later => override)
    lt.add_file(os.path.join(ROOT, "common", "landed_titles", "00_landed_titles.txt"), "mod:00_landed_titles.txt")
    lt.add_file(os.path.join(ROOT, "common", "landed_titles", "2020_new_landed_titles.txt"), "mod:2020_new_landed_titles.txt")
    lt.finalize()
    return lt


def tree_lines(titles, root, prefix="", out=None, max_tier="c"):
    if out is None:
        out = []
    t = titles[root]
    mark = ""
    out.append(prefix + root)
    for ch in t["children"]:
        ct = titles[ch]
        if TIER_RANK[ct["tier"]] < TIER_RANK[max_tier]:
            continue
        if ct["noble_family"] or (ct["landless"] and ct["tier"] == "c" and ct["id"].startswith("c_nf")):
            continue
        tree_lines(titles, ch, prefix + "    ", out, max_tier)
    return out


def main():
    lt = load_all()
    titles = lt.titles

    # structural diff: mod 00 file alone vs game 00 file (before on_action)
    mod00 = LandedTitles()
    mod00.add_file(os.path.join(ROOT, "common", "landed_titles", "00_landed_titles.txt"), "mod:00_landed_titles.txt")
    mod00.finalize()
    vanilla = LandedTitles()
    vanilla.add_file(os.path.join(GAME_LANDED, "00_landed_titles.txt"), "game:00_landed_titles.txt")
    vanilla.finalize()
    file_diffs = []
    for tid in sorted(set(mod00.titles) | set(vanilla.titles)):
        a = mod00.titles.get(tid)
        b = vanilla.titles.get(tid)
        if a is None:
            file_diffs.append({"kind": "removed", "title": tid, "from": b["parent"], "to": "（已删除）"})
        elif b is None:
            file_diffs.append({"kind": "added", "title": tid, "from": "（新增）", "to": a["parent"]})
        elif a["parent"] != b["parent"]:
            file_diffs.append({"kind": "parent", "title": tid, "tier": a["tier"],
                               "from": b["parent"], "to": a["parent"]})
        elif a["capital"] != b["capital"]:
            file_diffs.append({"kind": "capital", "title": tid, "tier": a["tier"],
                               "from": b["capital"], "to": a["capital"]})

    ops = parse_on_action(os.path.join(ROOT, "common", "on_action", "1337_de_jure_set.txt"))
    changes = apply_on_action(titles, ops)
    rebuild_children(titles)

    # commented-out intended changes inside the on_action file
    commented = []
    with open(os.path.join(ROOT, "common", "on_action", "1337_de_jure_set.txt"), encoding="utf-8-sig") as f:
        for line in f:
            s = line.strip()
            if s.startswith("#") and ("title:" in s or "set_de_jure" in s):
                commented.append(s.lstrip("#").strip())

    # ---- JSON output ----
    out = {
        "titles": titles,
        "on_action_changes": changes,
        "file_level_parent_changes": file_diffs,
    }
    with open(os.path.join(ROOT, "_de_jure_structure.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    # ---- Markdown report ----
    L = []
    L.append("# All Under Dreams 生效法理结构（游戏开局）\n")
    L.append("> 依据：模组 `common/landed_titles/00_landed_titles.txt`（替换原版同名文件）、`2020_new_landed_titles.txt`，"
             "叠加 `common/on_action/1337_de_jure_set.txt` 的运行时改动；游戏本体其余法理文件（01~06）按原样并入。\n")

    L.append("## 一、顶级头衔总览\n")
    L.append("| 顶级头衔 | 层级 | 法理上级 | 直接下属王国/帝国数 | 法理首都 |")
    L.append("| --- | --- | --- | --- | --- |")
    tops = [t for t in titles.values() if t["parent"] is None and not t["noble_family"] and TIER_RANK[t["tier"]] >= 4]
    tops.sort(key=lambda t: (-TIER_RANK[t["tier"]], t["id"]))
    for t in tops:
        kids = [c for c in t["children"] if TIER_RANK[titles[c]["tier"]] >= 3]
        L.append(f"| {t['id']} | {TIER_LABEL[t['tier']]} | {t['parent'] or '—'} | {len(kids)} | {t['capital'] or '—'} |")

    L.append("\n## 二、on_action 对法理的改动（`1337_de_jure_set.txt`）\n")
    L.append("按脚本内书写顺序列出。`层级移动` 一栏列出该操作实际搬动的公国。\n")
    L.append("| 操作 | 标题 | 原法理上级 | 改为 | 说明 |")
    L.append("| --- | --- | --- | --- | --- |")
    for ch in changes:
        if ch["kind"] == "direct":
            L.append(f"| 直接改属 | {ch['title']} | {ch['from'] or '—'} | {ch['to']} | {ch.get('note', '')} |")
        elif ch["kind"] == "hierarchy":
            names = "、".join(m[0] for m in ch.get("moved", [])) or "（无）"
            L.append(f"| 整王国搬移 | {ch['title']}（下属公国） | {ch['from'] or '—'} | {ch['to']} | {names} |")
        elif ch["kind"] == "capital":
            note = "无实际变化" if ch["from"] == ch["to"] else ""
            L.append(f"| 改法理首都 | {ch['title']} | {ch['from']} | {ch['to']} | {note} |")
        elif ch["kind"] == "missing":
            L.append(f"| ⚠ 缺失 | {ch['title']} | — | {ch.get('target','—')} | {ch.get('note','')} |")
        elif ch["kind"] == "invalid":
            L.append(f"| ⚠ 无效键 | {ch['title']} | — | — | {ch.get('note','')}（此写法游戏不会生效） |")

    # new titles from mod 2020
    L.append("\n## 三、模组新增头衔（`2020_new_landed_titles.txt`）\n")
    L.append("| 头衔 | 层级 | 法理上级（生效后） | 法理首都 |")
    L.append("| --- | --- | --- | --- |")
    new_ids = [
        "d_french_lowlands", "d_french_lorraine", "k_corsica", "k_belgium", "k_luxembourg",
        "k_netherlands", "e_netherlands", "k_slovenia", "k_west_germany", "k_east_germany",
        "e_alpine", "h_europa",
    ]
    for tid in new_ids:
        t = titles.get(tid)
        if t:
            L.append(f"| {tid} | {TIER_LABEL[t['tier']]} | {t['parent'] or '—'} | {t['capital'] or '—'} |")
    L.append("\n> 注：`d_french_lorraine` 与 `e_alpine` 已定义但未被 on_action 引用，目前是无法理上级的空头衔（on_action 中 `d_french_lorraine` 的相关行被注释）。")

    # file-level parent changes (mod 00 vs game 00)
    if file_diffs:
        L.append("\n## 四、模组文件内直接改动的法理归属（对比原版 00 文件）\n")
        L.append("> 这些改动写死在 `00_landed_titles.txt` 里，不依赖 on_action。\n")
        L.append("| 头衔 | 层级 | 类型 | 原版 | 模组文件 |")
        L.append("| --- | --- | --- | --- | --- |")
        for d in file_diffs:
            kind_label = {"parent": "法理上级", "capital": "法理首都", "added": "新增", "removed": "删除"}.get(d["kind"], d["kind"])
            L.append(f"| {d['title']} | {TIER_LABEL.get(d.get('tier'), '—')} | {kind_label} | {d['from'] or '—'} | {d['to'] or '—'} |")

    if commented:
        L.append("\n## 五、on_action 中被注释掉、不会生效的改动\n")
        L.append("> 这些行被 `#` 注释，游戏运行时不会执行，仅作作者意图参考。\n")
        L.append("```")
        L.extend(commented)
        L.append("```")

    # full tree
    L.append("\n## 六、完整生效法理树（h → e → k → d → c）\n")
    L.append("> 省略男爵领与 `c_nf_*` 无地家族头衔；顶层王国/公国等特殊头衔不展开。\n")
    for root in [t["id"] for t in tops]:
        L.append(f"\n### {root}\n")
        L.append("```")
        L.extend(tree_lines(titles, root, "", max_tier="c"))
        L.append("```")

    with open(os.path.join(ROOT, "_de_jure_structure.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")

    print(f"titles: {len(titles)}")
    print(f"on_action ops: {len(ops)}, changes: {len(changes)}")
    print(f"file-level parent diffs: {len(file_diffs)}")
    tops_list = ", ".join(t["id"] for t in tops)
    print("top-level:", tops_list)


if __name__ == "__main__":
    main()
