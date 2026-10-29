# -*- coding: utf-8 -*-
"""Bake the runtime de jure changes from 1337_de_jure_set.txt directly into
the mod's landed titles files (00_landed_titles.txt + 2020_new_landed_titles.txt),
so the effective de jure structure is expressed statically in the files.

Applies the on_action operations in their original order:
  - set_de_jure_liege_title  -> physically moves the title block into the new parent
  - every_in_de_jure_hierarchy (tier_duchy) -> moves all duchy blocks under the kingdom
  - set_capital_county       -> sets/updates the `capital = c_xxx` line in the block

Comments attached above a moved block travel with it. Barony (b_) and county (c_)
moves are handled by the same block-move logic.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ON_ACTION = os.path.join(ROOT, "common", "on_action", "1337_de_jure_set.txt")
FILES = {
    "00": os.path.join(ROOT, "common", "landed_titles", "00_landed_titles.txt"),
    "2020": os.path.join(ROOT, "common", "ToSC_titles.txt"),
}

from _de_jure_parse import parse_on_action, LandedTitles


def read_text(path):
    raw = open(path, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig" if bom else "utf-8", errors="replace")
    nl = "\r\n" if "\r\n" in text else "\n"
    return text.replace("\r\n", "\n"), {"bom": bom, "nl": nl}


def write_text(path, text, meta):
    out = text.replace("\n", meta["nl"])
    enc = "utf-8-sig" if meta["bom"] else "utf-8"
    with open(path, "w", encoding=enc, newline="") as f:
        f.write(out)


def find_block(text, tid):
    """(start, end) of '<tid> = {' ... matching '}' inclusive, or None."""
    m = re.search(r"(?m)^[ \t]*%s\s*=\s*\{" % re.escape(tid), text)
    if not m:
        return None
    start = m.start()
    depth = 0
    i = start
    n = len(text)
    while i < n:
        c = text[i]
        if c == "#":
            j = text.find("\n", i)
            i = n if j == -1 else j
            continue
        if c == '"':
            j = text.find('"', i + 1)
            i = n if j == -1 else j + 1
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return start, i + 1
        i += 1
    return None


def preceding_comments(text, start):
    """Return (comment_start, comment_text) for contiguous '#' lines directly above start."""
    lines = text[:start].split("\n")
    chunks = []
    i = len(lines) - 1
    while i >= 0 and lines[i].lstrip().startswith("#"):
        chunks.insert(0, lines[i])
        i -= 1
    if not chunks:
        return start, ""
    comment_text = "\n".join(chunks)
    # comment_start = position right before the first comment line
    prefix = "\n".join(lines[:i + 1])
    comment_start = len(prefix) + (1 if prefix else 0)
    return comment_start, comment_text


def locate(texts, tid):
    """Find which file contains the block; return (key, start, end, comment_start)."""
    for key in ("00", "2020"):
        r = find_block(texts[key], tid)
        if r:
            start, end = r
            cs, _ = preceding_comments(texts[key], start)
            return key, cs, end
    return None


def move_block(texts, aid, bid):
    """Move title block A into block B (same or cross file). Returns True/False."""
    la = locate(texts, aid)
    lb = locate(texts, bid)
    if la is None:
        print("  [skip] %s not found" % aid)
        return False
    if lb is None:
        print("  [skip] target %s not found for %s" % (bid, aid))
        return False
    key_a, a_start, a_end = la
    key_b, b_start, b_end = lb
    if key_a == key_b and b_start < a_start < b_end:
        print("  [skip] %s already inside %s (no-op)" % (aid, bid))
        return False
    if key_a == key_b and a_start < b_start < a_end:
        print("  [skip] %s contains %s (would create cycle)" % (aid, bid))
        return False
    # extract block text (with comments)
    text_a = texts[key_a]
    _, block_text = preceding_comments(text_a, a_start)
    block_text = (block_text + "\n" if block_text else "") + text_a[a_start:a_end]
    # re-indent to the target parent's child level
    src_base = text_a[a_start:a_start + len(text_a[a_start:]) - len(text_a[a_start:].lstrip())]
    b_text = texts[key_b]
    b_own = b_text[b_start:b_start + len(b_text[b_start:]) - len(b_text[b_start:].lstrip())]
    inner = b_text[b_start:b_end].split("\n")[1:]
    tgt_base = None
    for line in inner:
        if line.strip() and not line.strip().startswith("}"):
            tgt_base = line[:len(line) - len(line.lstrip())]
            break
    if tgt_base is None:
        tgt_base = b_own + "\t"
    block_lines = block_text.split("\n")
    block_lines = [(tgt_base + ln[len(src_base):]) if ln.startswith(src_base) else ln
                   for ln in block_lines]
    block_text = "\n".join(block_lines)
    # cut from source
    texts[key_a] = text_a[:a_start] + text_a[a_end:]
    # re-locate target in the (possibly shifted) target text
    if key_a == key_b:
        lb2 = find_block(texts[key_b], bid)
        if lb2 is None:
            print("  [error] target %s lost after cut" % bid)
            return False
        b_end = lb2[1]
    # insert before B's closing brace
    text_b = texts[key_b]
    insert_at = b_end - 1  # position of '}' (0-based)
    prefix = text_b[:insert_at]
    suffix = text_b[insert_at:]
    if prefix and not prefix.endswith("\n"):
        prefix += "\n"
    texts[key_b] = prefix + block_text + "\n" + suffix
    print("  [move] %s -> %s" % (aid, bid))
    return True


def set_capital(text, tid, cap):
    r = find_block(text, tid)
    if r is None:
        return None
    start, end = r
    block = text[start:end]
    m = re.search(r"(?m)^(\t*)capital\s*=\s*c_[a-z0-9_-]+", block)
    if m:
        new_block = block[:m.start()] + m.group(1) + "capital = " + cap + block[m.end():]
    else:
        nl = block.find("\n")
        new_block = block[:nl + 1] + "\tcapital = %s\n" % cap + block[nl + 1:]
    return text[:start] + new_block + text[end:]


def main():
    texts = {k: read_text(v)[0] for k, v in FILES.items()}
    metas = {k: read_text(v)[1] for k, v in FILES.items()}

    ops = parse_on_action(ON_ACTION)
    print("ops:", len(ops))
    moved = 0
    skipped = 0
    for op in ops:
        kind = op["kind"]
        if kind == "invalid" or kind == "missing":
            print("  [warn] %s %s" % (kind, op.get("title")))
            skipped += 1
            continue
        tid = op["title"]
        if kind == "direct":
            if move_block(texts, tid, op["target"]):
                moved += 1
            else:
                skipped += 1
        elif kind == "hierarchy":
            target = op["target"]
            la = locate(texts, tid)
            if la is None:
                print("  [skip] %s not found for hierarchy" % tid)
                skipped += 1
                continue
            key, k_start, k_end = la
            # find all duchy blocks currently inside K's block
            span = texts[key][k_start:k_end]
            found = []
            for m in re.finditer(r"(?m)^(\s*)(d_[a-z0-9_-]+)\s*=\s*\{", span):
                found.append((m.start(), m.group(2)))
            found.sort()
            if not found:
                print("  [skip] %s hierarchy has no duchies" % tid)
                skipped += 1
                continue
            for _, d in found:
                if move_block(texts, d, target):
                    moved += 1
                else:
                    skipped += 1
        elif kind == "capital":
            new00 = set_capital(texts["00"], tid, op["target"])
            if new00 is not None:
                texts["00"] = new00
            else:
                new2020 = set_capital(texts["2020"], tid, op["target"])
                if new2020 is not None:
                    texts["2020"] = new2020
                else:
                    print("  [skip] %s not found for capital" % tid)
                    skipped += 1
                    continue
            print("  [capital] %s = %s" % (tid, op["target"]))
            moved += 1

    for k, v in FILES.items():
        write_text(v, texts[k], metas[k])
    print("done: moved=%d skipped=%d" % (moved, skipped))

    # ---- verification: parse baked files WITHOUT on_action ----
    lt = LandedTitles()
    lt.add_file(FILES["00"], "mod:00_landed_titles.txt")
    lt.add_file(FILES["2020"], "mod:ToSC_titles.txt")
    lt.finalize()
    baked = lt.titles
    current = json.load(open(os.path.join(ROOT, "_de_jure_structure.json"), encoding="utf-8"))["titles"]
    mism = 0
    for tid in sorted(baked):
        b = baked[tid]["parent"]
        c = current.get(tid, {}).get("parent")
        if b != c:
            mism += 1
            if mism <= 30:
                print("MISMATCH %-24s baked=%-16s expected=%s" % (tid, b, c))
    print("parent mismatches vs expected effective structure:", mism)


if __name__ == "__main__":
    main()
