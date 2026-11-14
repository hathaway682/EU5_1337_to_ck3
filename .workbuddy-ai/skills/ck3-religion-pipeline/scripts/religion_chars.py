# -*- coding: utf-8 -*-
"""角色层的 religion / rite：只读体检 + 外科手术式改写。

CK3 角色块里的 `religion =` 和 `rite =` 决定这个人信什么、属于哪个教派。
省份层（`religion_audit.py` / `religion_set.py`）管地图上色，这里管**人**。

用法：
    # 概览（只读）
    python religion_chars.py
    python religion_chars.py --top 40
    python religion_chars.py --religion shia
    python religion_chars.py --rite maliki
    python religion_chars.py --char bkz_sayf_al_din_abu_abdallah_muhammad

    # 跨宗教执政：角色的 religion 与他所属 EU5 tag 的 religion_definition 不一致
    python religion_chars.py --cross

    # 改写（默认 dry-run）
    python religion_chars.py --set --char a,b --religion sunni --rite maliki
    python religion_chars.py --set --char a,b --religion sunni --rite maliki --apply
    python religion_chars.py --set --tag BKZ --religion sunni --rite maliki --apply
    python religion_chars.py --set --all-religion shia --religion sunni --rite maliki --apply
    python religion_chars.py --set --char x --drop-rite --apply

校验（不加 --force 时生效）：
  * religion 必须在 faith_types 里有定义，rite 必须在 rite_types 里有定义；
  * rite 的父 faith 的 religion 必须等于角色 religion 的 religion（跨 religion 拒绝）。

块解析：角色块以第 0 列的 `key = {` 开头，内部有 `1234.1.1 = { ... }` 日期块，
所以按**大括号深度**切，不能按「下一个空行」切。
"""
import argparse
import io
import os
import re
import sys
import time
from collections import Counter, defaultdict

import _common as C

CHARDIR = os.path.join(C.MOD, "history", "characters")
CHAR_OPEN = re.compile(r"^([A-Za-z0-9_\.\-]+)\s*=\s*\{\s*$")
REL_LINE = re.compile(r"^(\s*)religion\s*=\s*(\S+)\s*$")
RITE_CH = re.compile(r"^(\s*)rite\s*=\s*(\S+)\s*$")

EU5_GAME = os.environ.get("EU5_GAME") or \
    r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"


# ---------------------------------------------------------------- 块解析

def read_chars():
    """-> [(file, lines, sep)]，按字节读，保 CRLF。"""
    out = []
    for fn in sorted(os.listdir(CHARDIR)):
        if not fn.endswith(".txt"):
            continue
        p = os.path.join(CHARDIR, fn)
        raw = io.open(p, "rb").read()
        text = raw.decode("utf-8-sig")
        sep = "\r\n" if b"\r\n" in raw else "\n"
        out.append((fn, text.split(sep), sep))
    return out


def iter_char_blocks(lines):
    """yield (key, body_lines, start_index, close_index)。

    非角色行 yield (None, [line], i, i)。块原文 = lines[start:close+1]，
    这样不改的块可以原样搬回去，一个字节都不动。
    """
    i, n = 0, len(lines)
    while i < n:
        m = CHAR_OPEN.match(lines[i])
        if not m:
            yield None, [lines[i]], i, i
            i += 1
            continue
        d, j = 0, i
        while j < n:
            d += lines[j].count("{") - lines[j].count("}")
            if d == 0:
                break
            j += 1
        yield m.group(1), lines[i + 1:j], i, j
        i = j + 1


def block_fields(body):
    """-> (religion, rite, religion 行号, rite 行号)，只看深度 0 的字段。"""
    rel = rite = None
    ri = wi = None
    d = 0
    for k, line in enumerate(body):
        if d == 0:
            m = REL_LINE.match(line)
            if m and rel is None:
                rel, ri = m.group(2), k
            else:
                m2 = RITE_CH.match(line)
                if m2 and rite is None:
                    rite, wi = m2.group(2), k
        d += line.count("{") - line.count("}")
    return rel, rite, ri, wi


def is_definition(body):
    """是不是「角色定义块」。

    `history/characters/` 里同一个 key 可能出现两次：一次是 `zz_eu5_characters.txt`
    里的完整定义（有 name / culture / dynasty），一次是 `zz_eu5_government.txt` 里
    只有 `1337.4.1 = { effect = { ... } }` 的补丁块。后者没有 religion 字段，
    往里塞 `religion =` 会写出畸形数据，必须排除。
    """
    for line in body:
        s = line.strip()
        if s.startswith(("name =", "culture =", "dynasty =", "dynasty_house =")):
            return True
    return False


def load_all():
    """-> {(file, key): (religion, rite)}"""
    out = {}
    for fn, lines, _sep in read_chars():
        for key, body, _s, _c in iter_char_blocks(lines):
            if key is None or not is_definition(body):
                continue
            rel, rite, _ri, _wi = block_fields(body)
            out[(fn, key)] = (rel, rite)
    return out


# ---------------------------------------------------------------- EU5 侧

def load_eu5_char_tags():
    """EU5 角色 key -> tag。文件随版本挪过位置，这里把两种都试一遍。"""
    cands = [
        os.path.join(EU5_GAME, "main_menu", "setup", "1337", "05_characters.txt"),
        os.path.join(EU5_GAME, "main_menu", "setup", "start", "05_characters.txt"),
    ]
    path = next((p for p in cands if os.path.isfile(p)), None)
    if not path:
        return {}, None
    txt = io.open(path, encoding="utf-8-sig", errors="ignore").read()
    out = {}
    for m in re.finditer(r"(?m)^\s*([A-Za-z0-9_\.\-]+)\s*=\s*\{", txt):
        key, i, d = m.group(1), m.end() - 1, 0
        for j in range(i, len(txt)):
            if txt[j] == "{":
                d += 1
            elif txt[j] == "}":
                d -= 1
                if d == 0:
                    b = txt[i:j + 1]
                    t = re.search(r"(?m)^\s*tag\s*=\s*([A-Z]{3})", b)
                    if t:
                        out[key] = t.group(1)
                    break
    return out, path


def load_faith_map():
    """EU5 religion key -> CK3 faith。跨宗教判定必须先把国教翻译成 CK3 faith，
    否则 `theravada` 对 `theravada_faith`、`tengri` 对 `tengri_pagan` 全是假阳性。"""
    p = os.path.join(C.MOD, "..", "Global_modern_map", "eu5_export",
                     "eu5_ck3_faith_map.csv")
    p = os.path.normpath(p)
    if not os.path.isfile(p):
        return {}, None
    out = {}
    import csv
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            k = (r.get("eu5_religion") or "").strip()
            v = (r.get("ck3_faith") or "").strip()
            if k and v:
                out[k] = v
    return out, p


def load_country_religion():
    """tag -> EU5 religion_definition。"""
    d = os.path.join(EU5_GAME, "in_game", "setup", "countries")
    out = {}
    if not os.path.isdir(d):
        return out
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".txt"):
            continue
        txt = io.open(os.path.join(d, fn), encoding="utf-8-sig",
                      errors="ignore").read()
        for m in re.finditer(r"(?m)^([A-Z]{3})\s*=\s*\{", txt):
            key, i, dep = m.group(1), m.end() - 1, 0
            for j in range(i, len(txt)):
                if txt[j] == "{":
                    dep += 1
                elif txt[j] == "}":
                    dep -= 1
                    if dep == 0:
                        b = txt[i:j + 1]
                        r = re.search(r"(?m)^\s*religion_definition\s*=\s*(\w+)", b)
                        if r:
                            out[key] = r.group(1)
                        break
    return out


# ---------------------------------------------------------------- 命令

def cmd_audit(a):
    state = load_all()
    faiths = C.load_faiths()
    rites = C.load_rites()
    loc = {} if a.no_loc else C.load_loc_zh()

    def zh(k):
        return loc.get(k, "")

    rel_c = Counter(v[0] for v in state.values() if v[0])
    rite_c = Counter(v[1] for v in state.values() if v[1])
    no_rel = [k for k, v in state.items() if not v[0]]

    print("=" * 74)
    print("角色块 %d 个 | 有 religion %d | 有 rite %d | 无 religion %d"
          % (len(state), sum(rel_c.values()), sum(rite_c.values()), len(no_rel)))
    print("-" * 74)
    print("religion 分布（共 %d 种）" % len(rel_c))
    for k, v in rel_c.most_common(a.top):
        print("  %-30s %5d  %s" % (k, v, zh(k)))
    print("-" * 74)
    print("rite 分布（共 %d 种）" % len(rite_c))
    for k, v in rite_c.most_common(a.top):
        print("  %-30s %5d  %s" % (k, v, zh(k)))

    # 跨 religion 的 rite（真错）
    bad = []
    for (fn, key), (rel, rite) in state.items():
        if not rel or not rite:
            continue
        parent = rites.get(rite, {}).get("faith")
        r1 = faiths.get(rel, {}).get("religion")
        r2 = faiths.get(parent, {}).get("religion")
        if r1 and r2 and r1 != r2:
            bad.append((fn, key, rel, rite, parent, r1, r2))
    print("-" * 74)
    if bad:
        print("★ rite 与 religion 跨宗教：%d 个角色" % len(bad))
        for fn, key, rel, rite, parent, r1, r2 in bad[:15]:
            print("   %-46s %s(%s) + %s(%s)" % (key, rel, r1, rite, r2))
    else:
        print("rite 与 religion 归属校验：没有跨宗教的错配 ✓")

    und = sorted({v[0] for v in state.values() if v[0] and v[0] not in faiths})
    unr = sorted({v[1] for v in state.values() if v[1] and v[1] not in rites})
    print("未定义的 religion：%d %s" % (len(und), und[:8]))
    print("未定义的 rite：%d %s" % (len(unr), unr[:8]))

    if a.cross:
        tags, path = load_eu5_char_tags()
        crel = load_country_religion()
        fmap, mpath = load_faith_map()
        print("=" * 74)
        if not path:
            print("★ 找不到 EU5 05_characters.txt，跳过跨宗教统计")
            return
        if not mpath:
            print("★ 找不到 eu5_ck3_faith_map.csv，无法把 EU5 宗教翻成 CK3 faith，跳过")
            return
        rows, sib = [], []
        unknown = Counter()
        for (fn, key), (rel, _r) in state.items():
            tag = tags.get(key)
            if not tag or not rel:
                continue
            cr = crel.get(tag)
            if not cr:
                continue
            want = fmap.get(cr)
            if not want:
                unknown[cr] += 1
                continue
            if want == rel:
                continue
            # 同宗教内的兄弟 faith（如 miaphysite -> miaphysitism vs armenian_apostolic）不算错
            r1 = faiths.get(want, {}).get("religion")
            r2 = faiths.get(rel, {}).get("religion")
            if r1 and r2 and r1 == r2:
                sib.append((key, tag, cr, want, rel))
            else:
                rows.append((key, tag, cr, want, rel))
        print("跨宗教执政：%d 人（角色 religion 与 tag 国教的 religion 不同）" % len(rows))
        for tag, n in Counter(t for _k, t, _c, _w, _r in rows).most_common(a.top):
            print("  %-6s %d 人" % (tag, n))
        for key, tag, cr, want, rel in rows[:15]:
            print("   %-44s %s: 国教 %-14s(%s) 角色 %s" % (key, tag, cr, want, rel))
        if sib:
            print("同宗教内的兄弟 faith（正常）：%d 人，例：%s"
                  % (len(sib), ", ".join("%s %s->%s" % (k, w, r)
                                         for k, _t, _c, w, r in sib[:3])))
        if unknown:
            print("（%d 个角色的国教宗教 key 不在映射表里，未计入）" % sum(unknown.values()))

    if a.religion:
        sel = [(k, v) for k, v in state.items() if v[0] == a.religion]
        print("=" * 74)
        print("religion = %s：%d 人" % (a.religion, len(sel)))
        for r, n in Counter(v[1] or "<无 rite>" for _k, v in sel).most_common():
            print("  rite %-22s %4d  %s" % (r, n, zh(r)))
    if a.rite:
        sel = [(k, v) for k, v in state.items() if v[1] == a.rite]
        print("=" * 74)
        print("rite = %s：%d 人" % (a.rite, len(sel)))
        for r, n in Counter(v[0] or "<无 religion>" for _k, v in sel).most_common():
            print("  religion %-24s %4d" % (r, n))
    if a.char:
        want = set(re.split(r"[\s,]+", a.char.strip()))
        print("=" * 74)
        for (fn, key), (rel, rite) in sorted(state.items()):
            if key in want:
                print("  %-46s religion=%-18s rite=%-16s [%s]"
                      % (key, rel or "-", rite or "-", fn))


def cmd_set(a):
    faiths = C.load_faiths()
    rites = C.load_rites()

    if a.religion and a.religion not in faiths:
        sys.exit("★ religion %s 在 faith_types 里没有定义" % a.religion)
    if a.rite and a.rite not in rites:
        sys.exit("★ rite %s 在 rite_types 里没有定义" % a.rite)
    if a.rite and a.religion and not a.force:
        parent = rites[a.rite]["faith"]
        r1 = faiths.get(a.religion, {}).get("religion")
        r2 = faiths.get(parent, {}).get("religion")
        if r1 and r2 and r1 != r2:
            sys.exit("★ rite %s 的父 faith %s 属于 %s，与 religion %s（%s）跨宗教。\n"
                     "  如确实要写，加 --force。" % (a.rite, parent, r2, a.religion, r1))

    # ---- 选目标 ----
    state = load_all()
    targets = set()
    if a.char:
        want = {x for x in re.split(r"[\s,]+", a.char.strip()) if x}
        for (fn, key) in state:
            if key in want:
                targets.add((fn, key))
        missing = want - {k for _f, k in targets}
        if missing:
            print("★ 找不到这些角色 key：%s" % sorted(missing)[:10])
    if a.char_file:
        want = {x.strip() for x in io.open(a.char_file, encoding="utf-8")
                if x.strip()}
        for (fn, key) in state:
            if key in want:
                targets.add((fn, key))
    if a.tag:
        tags, _p = load_eu5_char_tags()
        for (fn, key) in state:
            if tags.get(key) == a.tag.upper():
                targets.add((fn, key))
    if a.all_religion:
        for (fn, key), (rel, _r) in state.items():
            if rel == a.all_religion:
                targets.add((fn, key))
    if a.all_rite:
        for (fn, key), (_rel, rite) in state.items():
            if rite == a.all_rite:
                targets.add((fn, key))

    if not targets:
        sys.exit("★ 没有目标角色。用 --char / --char-file / --tag / --all-religion / --all-rite")
    if not (a.religion or a.rite or a.drop_rite):
        sys.exit("★ 要给 --religion 或 --rite（或 --drop-rite）")

    # ---- 改 ----
    by_file = defaultdict(set)
    for fn, key in targets:
        by_file[fn].add(key)

    stat = Counter()
    examples = []
    pending = {}          # fn -> (new_lines, sep, 该文件改动数)

    for fn, lines, sep in read_chars():
        if fn not in by_file:
            continue
        out = []
        changed = 0
        for key, body, start, close in iter_char_blocks(lines):
            if key is None or key not in by_file[fn] or not is_definition(body):
                # 非目标：整块原样搬回
                out.extend(lines[start:close + 1])
                continue

            nb = list(body)
            rel, rite, ri, wi = block_fields(nb)
            old = (rel, rite)
            before = changed

            if a.drop_rite and wi is not None:
                nb.pop(wi)
                stat["rite 删除"] += 1
                changed += 1
                if ri is not None and ri > wi:
                    ri -= 1

            if a.religion:
                rel, rite, ri, wi = block_fields(nb)
                if ri is not None:
                    if rel != a.religion:
                        nb[ri] = "%sreligion = %s" % (
                            REL_LINE.match(nb[ri]).group(1), a.religion)
                        stat["religion 改写"] += 1
                        changed += 1
                else:
                    indent = "\t"
                    nb.insert(0, "%sreligion = %s" % (indent, a.religion))
                    stat["religion 新增"] += 1
                    changed += 1

            if a.rite:
                rel, rite, ri, wi = block_fields(nb)
                if wi is not None:
                    if rite != a.rite:
                        nb[wi] = "%srite = %s" % (
                            RITE_CH.match(nb[wi]).group(1), a.rite)
                        stat["rite 改写"] += 1
                        changed += 1
                else:
                    indent = REL_LINE.match(nb[ri]).group(1) if ri is not None else "\t"
                    pos = (ri + 1) if ri is not None else 0
                    nb.insert(pos, "%srite = %s" % (indent, a.rite))
                    stat["rite 新增"] += 1
                    changed += 1

            if changed > before and len(examples) < 10:
                examples.append((key, old[0], old[1], a.religion or old[0],
                                 a.rite or old[1]))
            out.append(lines[start])          # 原样的 `key = {`
            out.extend(nb)
            out.append(lines[close])
        pending[fn] = (out, sep, changed)

    print("目标角色 %d 个" % len(targets))
    for k, v in stat.items():
        if v:
            print("  %-14s %d" % (k, v))
    for key, of, orr, nf, nr in examples:
        print("  %-44s religion %-16s -> %-16s | rite %-14s -> %s"
              % (key, of or "-", nf or "-", orr or "-", nr or "-"))

    if not sum(stat.values()):
        print("无变化，不写盘。")
        return 0
    if not a.apply:
        print("（dry run，加 --apply 才写盘）")
        return 0

    stamp = time.strftime("%Y%m%d_%H%M%S")
    for fn, (out, sep, changed) in pending.items():
        if not changed:
            continue
        p = os.path.join(CHARDIR, fn)
        io.open(p + ".bak_charrel_" + stamp, "wb").write(io.open(p, "rb").read())
        io.open(p, "wb").write((C.BOM + sep.join(out)).encode("utf-8"))
    print("已写入 %d 个文件。备份后缀 .bak_charrel_%s"
          % (sum(1 for _o, _s, c in pending.values() if c), stamp))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--religion")
    ap.add_argument("--rite")
    ap.add_argument("--char", help="角色 key，逗号/空格分隔")
    ap.add_argument("--char-file")
    ap.add_argument("--tag", help="按 EU5 tag 选（读 setup/1337/05_characters.txt）")
    ap.add_argument("--all-religion", help="当前 religion = X 的全部角色")
    ap.add_argument("--all-rite")
    ap.add_argument("--cross", action="store_true", help="跨宗教执政统计")
    ap.add_argument("--no-loc", action="store_true")
    ap.add_argument("--set", action="store_true", help="改写模式")
    ap.add_argument("--drop-rite", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    if a.set:
        return cmd_set(a)
    cmd_audit(a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
