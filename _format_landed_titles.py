# -*- coding: utf-8 -*-
"""Re-indent CK3 landed titles files by brace depth.

Every line gets indented with one tab per nesting level (closing-brace lines
one level less). Comments, blank lines, inline comments and the file preamble
are preserved. Encoding (BOM) and newline style are kept.
"""
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
FILES = [
    os.path.join(ROOT, "common", "landed_titles", "00_landed_titles.txt"),
    os.path.join(ROOT, "common", "landed_titles", "ToSC_titles.txt"),
]


def read_text(path):
    raw = open(path, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig" if bom else "utf-8", errors="replace")
    nl = "\r\n" if "\r\n" in text else "\n"
    return text.replace("\r\n", "\n"), {"bom": bom, "nl": nl}


def write_text(path, text, meta):
    with open(path, "w", encoding="utf-8-sig" if meta["bom"] else "utf-8", newline="") as f:
        f.write(text.replace("\n", meta["nl"]))


def brace_delta(content):
    """Net brace change of a content line (comments/strings skipped)."""
    delta = 0
    i = 0
    n = len(content)
    while i < n:
        c = content[i]
        if c == "#":
            break
        if c == '"':
            j = content.find('"', i + 1)
            i = n if j == -1 else j + 1
            continue
        if c == "{":
            delta += 1
        elif c == "}":
            delta -= 1
        i += 1
    return delta


def format_text(text):
    out = []
    depth = 0
    for raw in text.split("\n"):
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            out.append("")
            continue
        if stripped.startswith("}"):
            indent = max(0, depth - 1)
        else:
            indent = depth
        out.append("\t" * indent + stripped)
        depth += brace_delta(stripped)
        if depth < 0:
            depth = 0
    return "\n".join(out)


def main():
    for path in FILES:
        text, meta = read_text(path)
        write_text(path, format_text(text), meta)
        print("formatted:", os.path.basename(path))


if __name__ == "__main__":
    main()
