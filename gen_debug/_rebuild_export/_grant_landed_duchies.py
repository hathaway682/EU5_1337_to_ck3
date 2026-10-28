# -*- coding: utf-8 -*-
"""给够格的国家发地图上的有地公国头衔。

两条，满足其一即可：
  一、EU5 等级高于公国（k/e），控制该公国过半（不含刚好一半）的伯爵领，
      且这个公国内没有别的 EU5 公国把首都放在这里 —— 有，就留给那个公国。
  二、国家与公国同名（勃兰登堡就是勃兰登堡，哪怕 EU5 只把它写成伯国）。

同名优先于控制：纳瓦拉归纳瓦拉，不归占了它四分之三的卡斯蒂利亚。

用法：python _grant_landed_duchies.py --mod <mod> --export <eu5_export> [--dry-run]
"""
import argparse
import io
import json
import os
import re
import time
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
HIST = os.path.join("history", "titles", "zz_eu5_titles.txt")


def read(path):
    return io.open(path, encoding="utf-8-sig", errors="ignore", newline="").read().lstrip("\ufeff")


def blocks(text):
    """(key, parents, body) 逐块，按花括号计数配对。"""
    lines = text.split("\n")
    stack, res, depth = [], [], 0
    for i, raw in enumerate(lines):
        line = raw.rstrip("\r")
        s = line.strip()
        if not s:
            continue
        n_o, n_c = line.count("{"), line.count("}")
        m = re.match(r"^([A-Za-z0-9_:\.\-]+)\s*=\s*\{", s) if n_o else None
        if n_o:
            if m:
                stack.append((m.group(1), i, depth))
            depth += n_o
        if n_c:
            depth -= n_c
            while stack and depth <= stack[-1][2]:
                key, start, _ = stack.pop()
                res.append((key, tuple(k for k, _, _ in stack), "\n".join(lines[start + 1:i])))
    return res


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def duchy_map(mod):
    """有地公国 -> 它的伯爵领（含子公国下的）。"""
    tree = blocks(re.sub(r"(?m)^\s*#.*$", "", read(os.path.join(
        mod, "common", "landed_titles", "00_landed_titles.txt"))))
    own = {}
    kids = {}
    for key, parents, body in tree:
        if not key.startswith("d_"):
            continue
        own.setdefault(key, [])
        for m in re.finditer(r"(?m)^[ \t]*(c_[A-Za-z0-9_-]+)[ \t]*=[ \t]*\{", body):
            own[key].append(m.group(1))
        if parents:
            for m in re.finditer(r"(?m)^[ \t]*(d_[A-Za-z0-9_-]+)[ \t]*=[ \t]*\{", body):
                kids.setdefault(key, []).append(m.group(1))

    def all_of(key, seen=()):
        out = list(own.get(key) or [])
        for ch in kids.get(key) or []:
            if ch in seen:
                continue
            out += all_of(ch, seen + (key,))
        return out

    return {k: sorted(set(all_of(k))) for k in own}


def start_date(mod):
    p = os.path.join(mod, "common", "bookmarks", "groups", "00_bookmark_groups.txt")
    if os.path.exists(p):
        m = re.search(r"default_start_date\s*=\s*([0-9]+\.[0-9]+\.[0-9]+)", read(p))
        if m:
            return m.group(1)
    return "1337.4.1"


def compute(mod, export):
    pol = json.load(io.open(os.path.join(export, "eu5_politics.json"), encoding="utf-8"))
    countries, county = pol["countries"], pol["counties"]
    mapping = json.load(io.open(os.path.join(export, "mapping.json"), encoding="utf-8"))
    loc_county = {l["name"]: "c_" + l["county"] for l in mapping["locations"] if l.get("county")}

    duchies = duchy_map(mod)
    owner_of = {c: (county.get(c) or {}).get("owner") for c in county}
    seated = {}
    for tag, c in countries.items():
        if (c.get("rank") or "") == "d" and c.get("capital"):
            seated[tag] = loc_county.get(c["capital"])

    grants, blocked, why = {}, [], {}
    for d in sorted(duchies):
        cs = duchies[d]
        if not cs:
            continue
        n = len(cs)
        held = defaultdict(int)
        for c in cs:
            o = owner_of.get(c)
            if o:
                held[o] += 1
        dn = norm(d[2:])
        same = sorted(t for t in held if dn and norm((countries.get(t) or {}).get("name_en")) == dn)
        if same:
            grants[d] = same[0]
            why[d] = "same name"
            continue
        for tag, k in sorted(held.items(), key=lambda kv: -kv[1]):
            if (countries.get(tag) or {}).get("rank") not in ("k", "e"):
                continue
            if k * 2 <= n:
                continue
            others = sorted(x for x, cc in seated.items() if x != tag and cc in cs)
            if others:
                blocked.append((d, tag, "%d/%d" % (k, n), ",".join(others)))
                continue
            grants[d] = tag
            why[d] = "control %d/%d" % (k, n)
            break
    return grants, why, blocked, countries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mod", required=True)
    ap.add_argument("--export", default=HERE)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    grants, why, blocked, countries = compute(args.mod, args.export)
    date = start_date(args.mod)
    path = os.path.join(args.mod, HIST)
    text = read(path)
    nl = "\r\n" if "\r\n" in text else "\n"
    declared = {m.group(1) for m in re.finditer(r"(?m)^([A-Za-z0-9_]+) = \{", text)}

    todo, no_ruler, already = [], [], []
    for d, tag in sorted(grants.items()):
        if d in declared:
            already.append(d)
            continue
        c = countries.get(tag) or {}
        holder = c.get("ruler") or c.get("regent")
        if not holder:
            no_ruler.append((d, tag))
            continue
        todo.append((d, tag, holder, why[d]))

    print("duchies to grant: %d (already have a block: %d, no ruler: %d, blocked: %d)"
          % (len(todo), len(already), len(no_ruler), len(blocked)))
    if not todo or args.dry_run:
        return
    if not text.endswith(nl):
        text += nl
    out = [text]
    out.append("# The duchies of the map, worn from day one by the country that is them, or that\n"
               "# holds more than half of them and has no other duke seated inside.\n\n")
    for d, tag, holder, w in todo:
        out.append("%s = {%s\t%s = {%s\t\tholder = %s%s\t}%s}%s%s"
                   % (d, nl, date, nl, holder, nl, nl, nl, nl))
    body = "".join(out)
    bak = path + ".bak_" + time.strftime("%Y%m%d_%H%M%S")
    with io.open(bak, "w", encoding="utf-8-sig", newline="") as fh:
        fh.write(text)
    with io.open(path, "w", encoding="utf-8-sig", newline="") as fh:
        fh.write(body)
    print("granted %d duchies at %s -> %s" % (len(todo), date, path))

    rep = os.path.join(HERE, "_tmp_diag")
    if not os.path.isdir(rep):
        os.makedirs(rep, exist_ok=True)
    with io.open(os.path.join(rep, "grant_landed_duchies.txt"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write("date: %s\ngranted: %d\n" % (date, len(todo)))
        for d, tag, holder, w in todo:
            c = countries.get(tag) or {}
            fh.write("%-26s %-4s %-24s %-22s %s%s"
                     % (d, tag, (c.get("name_en") or "")[:24], holder, w, "\n"))
        fh.write("\nblocked by another duke's capital: %d\n" % len(blocked))
        for d, tag, k, others in blocked:
            fh.write("    %-26s %-4s held=%-8s others=%s\n" % (d, tag, k, others))
        if no_ruler:
            fh.write("\nno ruler: %d %s\n" % (len(no_ruler), no_ruler[:10]))


if __name__ == "__main__":
    main()
