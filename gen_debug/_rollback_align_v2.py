# -*- coding: utf-8 -*-
"""回滚 _apply_align_v2.py 落地的 A+B 层（170 个 dynasty name + 75 条 COA 别名）。

外科手术式回滚：
- 只回滚 CSV 中 tier in (A,B) 的 170 个 mod_key 的 name，恢复为 alignv2 备份中的原值
- 只删除别名文件中 key 属于这 170 个集合的行（藤原并入产生的 house_* 三行不在集合内，保留）
- 不整文件恢复，避免冲掉之后的藤原系并入改动
"""
import csv, os, re, sys, shutil
from datetime import datetime

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
CSV = os.path.join(MOD, "gen_debug", "dynasty_alignment_candidates.csv")
DYN = os.path.join(MOD, "common", "dynasties", "zz_eu5_dynasties.txt")
DYN_BAK = DYN + ".bak_alignv2_20261031_145736"
ALIAS = os.path.join(MOD, "common", "coat_of_arms", "coat_of_arms", "95_zz_eu5_dynasty_aliases.txt")

DRY = "--dry-run" in sys.argv


def read_text(path):
    raw = open(path, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    nl = "\r\n" if "\r\n" in text else "\n"
    return text, nl, bom


def write_text(path, text, nl, bom):
    data = (b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8")
    open(path, "wb").write(data)


def parse_name_map(text, nl):
    """返回 {key: (name_value, name_line_index)}，只处理顶格 key = { ... } 顶层块。"""
    lines = text.split(nl)
    out = {}
    i = 0
    while i < len(lines):
        m = re.match(r"^([A-Za-z0-9_\-]+)\s*=\s*\{\s*$", lines[i])
        if m:
            key = m.group(1)
            depth = 1
            j = i + 1
            name_val = None
            name_idx = None
            while j < len(lines) and depth > 0:
                if depth == 1 and name_val is None:
                    mm = re.match(r'^(\s*)name\s*=\s*"([^"]*)"', lines[j])
                    if mm:
                        name_val = mm.group(2)
                        name_idx = j
                depth += lines[j].count("{") - lines[j].count("}")
                j += 1
            out[key] = (name_val, name_idx)
            i = j
        else:
            i += 1
    return out, lines


def main():
    rows = [r for r in csv.DictReader(open(CSV, encoding="utf-8-sig")) if r["tier"] in ("A", "B")]
    keys = {r["mod_key"] for r in rows}
    print("A+B keys: %d" % len(keys))

    # ---------- 1. 回滚 dynasty name ----------
    cur_text, nl, bom = read_text(DYN)
    bak_text, _, _ = read_text(DYN_BAK)
    cur_map, cur_lines = parse_name_map(cur_text, nl)
    bak_map, _ = parse_name_map(bak_text, nl)

    changes = []
    missing = []
    for k in sorted(keys):
        if k not in cur_map:
            missing.append(k)
            continue
        cur_val, idx = cur_map[k]
        bak_val = bak_map.get(k, (None, None))[0]
        if cur_val != bak_val and idx is not None and bak_val is not None:
            changes.append((k, cur_val, bak_val, idx))

    print("name to revert: %d | missing in current file: %d" % (len(changes), len(missing)))
    if missing:
        print("  missing:", missing)
    for c in changes[:10]:
        print("   %-32s %s -> %s" % (c[0], c[1], c[2]))

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if not DRY:
        shutil.copy2(DYN, DYN + ".bak_rollback_" + ts)
        shutil.copy2(ALIAS, ALIAS + ".bak_rollback_" + ts)
        print("backup: *.bak_rollback_%s" % ts)
        for k, cur_val, bak_val, idx in changes:
            cur_lines[idx] = re.sub(r'(name\s*=\s*")[^"]*(")',
                                    lambda m: m.group(1) + bak_val + m.group(2),
                                    cur_lines[idx], count=1)
        write_text(DYN, nl.join(cur_lines), nl, bom)

    # ---------- 2. 删除 A+B 新增的别名 ----------
    a_text, a_nl, a_bom = read_text(ALIAS)
    a_lines = a_text.split(a_nl)
    kept, dropped = [], []
    for l in a_lines:
        m = re.match(r"^([A-Za-z0-9_\-]+)\s*=\s*\S+", l)
        if m and m.group(1) in keys:
            dropped.append(l)
        else:
            kept.append(l)
    print("alias lines dropped: %d | kept: %d" % (len(dropped), len(kept)))
    for l in dropped[:10]:
        print("   -", l)

    if not DRY:
        out = a_nl.join(kept)
        write_text(ALIAS, out, a_nl, a_bom)

    if DRY:
        print("\n[dry-run] nothing written")
        return

    # ---------- 3. 自检 ----------
    t2, nl2, bom2 = read_text(DYN)
    m2, _ = parse_name_map(t2, nl2)
    bad = [(k, m2.get(k, (None,))[0], bak_map.get(k, (None,))[0]) for k in keys
           if k in m2 and m2[k][0] != bak_map.get(k, (None,))[0]]
    print("\nverify name: mismatched = %d" % len(bad))
    for b in bad[:10]:
        print("   BAD", b)

    a2, _, _ = read_text(ALIAS)
    left = [l for l in a2.split(a_nl) if l.strip() and not l.strip().startswith("#")
            and re.match(r"^([A-Za-z0-9_\-]+)\s*=", l) and re.match(r"^([A-Za-z0-9_\-]+)", l).group(1) in keys]
    print("verify alias: residual A+B keys = %d" % len(left))
    for l in left[:10]:
        print("   LEFT", l)

    raw = open(DYN, "rb").read()
    print("DYN BOM=%s CRLF=%d bareLF=%d" % (raw[:3] == b"\xef\xbb\xbf", raw.count(b"\r\n"),
                                            raw.count(b"\n") - raw.count(b"\r\n")))
    raw = open(ALIAS, "rb").read()
    print("ALIAS BOM=%s CRLF=%d bareLF=%d" % (raw[:3] == b"\xef\xbb\xbf", raw.count(b"\r\n"),
                                              raw.count(b"\n") - raw.count(b"\r\n")))


if __name__ == "__main__":
    main()
