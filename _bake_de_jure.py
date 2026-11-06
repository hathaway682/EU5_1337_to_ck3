# -*- coding: utf-8 -*-
"""Bake the runtime de jure changes from 1337_de_jure_set.txt directly into
the mod's single landed titles file (00_landed_titles.txt),
so the effective de jure structure is expressed statically in the files.

Applies the on_action operations in their original order:
  - set_de_jure_liege_title  -> physically moves the title block into the new parent
  - every_in_de_jure_hierarchy -> moves descendants matching the requested tier
  - set_capital_county       -> sets/updates the `capital = c_xxx` line in the block

Comments attached above a moved block travel with it. Barony (b_) and county (c_)
moves are handled by the same block-move logic.
"""
import copy
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
ON_ACTION = os.path.join(ROOT, "common", "on_action", "1337_de_jure_set.txt")
FILES = {
    "00": os.path.join(ROOT, "common", "landed_titles", "00_landed_titles.txt"),
}

from _de_jure_parse import parse_on_action, apply_on_action, LandedTitles, TIER_GAME_NAME


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
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                elif text[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
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
    # start points at the beginning of the title line, after its preceding '\n'.
    if lines and lines[-1] == "":
        lines.pop()
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
    """Find which file contains the block; return (key, start, end)."""
    for key in texts:
        r = find_block(texts[key], tid)
        if r:
            start, end = r
            return key, start, end
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
    comment_start, _ = preceding_comments(text_a, a_start)
    block_text = text_a[comment_start:a_end]
    # re-indent to the target parent's child level
    src_base = re.match(r"[ \t]*", text_a[a_start:]).group()
    b_text = texts[key_b]
    b_own = re.match(r"[ \t]*", b_text[b_start:]).group()
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
    cut_end = a_end
    tail = re.match(r"[ \t]*\n", text_a[a_end:])
    if tail:
        cut_end += tail.end()
    texts[key_a] = text_a[:comment_start] + text_a[cut_end:]
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
    close_line = text_b.rfind("\n", 0, insert_at) + 1
    if not text_b[close_line:insert_at].strip():
        insert_at = close_line
    else:
        # Expand an inline target while preserving its own closing indentation.
        text_b = text_b[:insert_at] + b_own + text_b[insert_at:]
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
    expected_lt = LandedTitles()
    for k, path in FILES.items():
        expected_lt.add_file(path, k)
    expected = copy.deepcopy(expected_lt.titles)
    apply_on_action(expected, ops)
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
            # Select the requested tier from the current subtree, before moving.
            span = texts[key][k_start:k_end]
            tier_name = op.get("tier")
            if tier_name is not None and tier_name not in TIER_GAME_NAME:
                raise ValueError("Unknown hierarchy tier: %s" % tier_name)
            tier = TIER_GAME_NAME.get(tier_name)
            prefix = re.escape(tier) if tier else "[hkedcb]"
            found = []
            for m in re.finditer(r"(?m)^[ \t]*(" + prefix + r"_[a-z0-9_-]+)[ \t]*=[ \t]*\{", span):
                child = m.group(1)
                if child != tid and child != target:
                    found.append((m.start(), child))
            found.sort()
            if not found:
                print("  [skip] %s hierarchy has no matching titles (%s)" % (tid, tier_name or "all"))
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
    from _de_jure_parse import parse_blocks
    for key, text in texts.items():
        tokens = [m.group() for m in re.finditer(
            r'#[^\n]*|"(?:\\.|[^"\\])*"|[{}=]|[^\s{}="#]+', text)
            if not m.group().startswith("#")]
        blocks, _ = parse_blocks(tokens)
        lt._walk(blocks, None, key)
    baked = lt.titles
    current = expected
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
