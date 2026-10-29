# -*- coding: utf-8 -*-
"""按 Crusader Universalis 的法理结构重建本 mod 的 h/e/k 层，d_ 按最大比例归属重挂。

规则（2026-10-29 用户确认）：
  - 公国在 CU 覆盖范围内有地的，按男爵领/province 数最大比例归到 CU 的王国；
  - 覆盖范围内没地的公国，保持现状（原王国 key，这些 key 都在 CU 里）；
  - h/e/k 三层整体换成 CU 的（color/capital 取 CU，capital 在 mod 里不存在时回退到子块首府）；
  - c_/b_/d_ 的地一律不动，d_ 块原文搬运。

只读 CU；只写 mod 的 common/landed_titles/00_landed_titles.txt（先写 .new）。
用法：python _rebuild_dejure_cu.py [--apply]
"""
import glob
import io
import os
import re
import csv
import sys
from collections import Counter, defaultdict

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
CU = r"E:\SteamLibrary\steamapps\workshop\content\1158310\3811443965"
LTD = os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt")
SRC = os.path.join(MOD, "gen_debug", "_dejure_src_20261029.txt")
PROBE = os.path.join(MOD, "gen_debug", "_probe_cu_dejure.out")
MAPOUT = os.path.join(MOD, "gen_debug", "_dejure_cu_map.csv")

PAT = re.compile(r"([A-Za-z0-9_.-]+)\s*=\s*\{")


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore", newline="").read()


def walk(text, parents=()):
    out = []
    i, n = 0, len(text)
    while True:
        m = PAT.search(text, i)
        if not m:
            break
        key = m.group(1)
        j = m.end()
        d = 1
        while j < n and d:
            c = text[j]
            if c == "{":
                d += 1
            elif c == "}":
                d -= 1
            j += 1
        body = text[m.end():j - 1]
        out.append((key, parents, body))
        out.extend(walk(body, parents + (key,)))
        i = j
    return out


def cu_tree():
    k2e, e2h = {}, {}
    info = {}
    order_h, order_e, order_k = [], [], []
    for p in sorted(glob.glob(os.path.join(CU, "common", "landed_titles", "*.txt"))):
        t = read(p)
        for key, par, body in walk(t):
            if not key[:2] in ("h_", "e_", "k_"):
                continue
            c = re.search(r"color\s*=\s*([^\r\n]+)", body)
            cap = re.search(r"capital\s*=\s*([A-Za-z0-9_]+)", body)
            df = re.search(r"definite_form\s*=\s*(\w+)", body)
            if key.startswith("k_"):
                if key not in info:
                    order_k.append(key)
                e = next((x for x in reversed(par) if x.startswith("e_")), None)
                if e:
                    k2e[key] = e
            elif key.startswith("e_"):
                if key not in info:
                    order_e.append(key)
                h = next((x for x in reversed(par) if x.startswith("h_")), None)
                if h:
                    e2h[key] = h
            else:
                if key not in info:
                    order_h.append(key)
            if key not in info:
                info[key] = {
                    "color": (c.group(1).strip() if c else ""),
                    "capital": (cap.group(1) if cap else ""),
                    "definite": (df.group(1) if df else ""),
                }
    return k2e, e2h, info, order_h, order_e, order_k




def cu_capital_maps():
    """CU 的县 -> 我们的县。
    一级：_cu_vs_ours.csv 的 cu_county 列直接对应；
    二级：CU 该县的首府男爵领名 -> csv 的 barony 列 -> our_county。"""
    rows = list(csv.DictReader(io.open(os.path.join(MOD, "gen_debug", "_cu_vs_ours.csv"), encoding="utf-8-sig")))
    cnt = defaultdict(Counter)
    bar = {}
    for r in rows:
        cnt[r["cu_county"]][r["our_county"]] += 1
        bar.setdefault(r["barony"], r["our_county"])
    c2o = {k: v.most_common(1)[0][0] for k, v in cnt.items()}
    # CU 每个县的首府男爵领
    capb = {}
    for p in glob.glob(os.path.join(CU, "common", "landed_titles", "*.txt")):
        t = read(p)
        for key, parents, body in walk(t):
            if not key.startswith("c_"):
                continue
            m = re.search(r"capital\s*=\s*(b_[A-Za-z0-9_-]+)", body)
            if m:
                capb.setdefault(key, m.group(1)[2:])
            else:
                m2 = re.search(r"(?m)^\s*(b_[A-Za-z0-9_-]+)\s*=\s*\{", body)
                if m2:
                    capb.setdefault(key, m2.group(1)[2:])
    return c2o, capb, bar


def date_of(s):
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)$", s)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


CUTOFF = (1337, 4, 1)


def history_overrides():
    """{title: target}，取 <= 1337.4.1 的最后一个法理变更。"""
    res = {}
    for p in glob.glob(os.path.join(CU, "history", "titles", "*.txt")):
        t = read(p)
        t = re.sub(r"(?m)#[^\n]*$", "", t)
        for key, parents, body in walk(t):
            if parents:
                continue
            if key[:2] not in ("d_", "k_", "e_", "h_"):
                continue
            for m in re.finditer(r'(?m)^\tde_jure_liege\s*=\s*"?([A-Za-z0-9_-]+|0)"?', body):
                res.setdefault(key, []).append(((0, 0, 0), m.group(1)))
            for dk, dpar, dbody in walk(body):
                if dpar:
                    continue
                dt = date_of(dk)
                if not dt or dt > CUTOFF:
                    continue
                for m in re.finditer(r'(?m)^\s*de_jure_liege\s*=\s*"?([A-Za-z0-9_-]+|0)"?', dbody):
                    res.setdefault(key, []).append((dt, m.group(1)))
                for m in re.finditer(r"set_de_jure_liege_title\s*=\s*title:([A-Za-z0-9_-]+)", dbody):
                    res.setdefault(key, []).append((dt, m.group(1)))
    return {k: sorted(v)[-1][1] for k, v in res.items()}


def mod_blocks():
    """返回 [(d_key, 原文块)]，按出现顺序。"""
    t = read(SRC)
    t = t.replace("\r\n", "\n")
    res = []
    pat = re.compile(r"(?m)^\t{3}(d_[A-Za-z0-9_-]+)\s*=\s*\{")
    i, n = 0, len(t)
    while True:
        m = pat.search(t, i)
        if not m:
            break
        j = m.end()
        d = 1
        while j < n and d:
            c = t[j]
            if c == "{":
                d += 1
            elif c == "}":
                d -= 1
            j += 1
        end = t.index("\n", j) if "\n" in t[j:] else n
        res.append((m.group(1), t[m.start():end]))
        i = j
    return res


def orig_d2k():
    t = read(SRC).replace("\r\n", "\n")
    lines = t.split("\n")
    stack, d2k, depth = [], {}, 0
    for ln in lines:
        s = ln.strip()
        m = re.match(r"^([hedkcb]_[A-Za-z0-9_-]+)\s*=\s*\{", s)
        if m:
            key = m.group(1)
            if key.startswith("d_"):
                k = next((x for x in reversed(stack) if x.startswith("k_")), None)
                d2k[key] = k
            stack.append(key)
        depth += ln.count("{") - ln.count("}")
        while stack and depth <= len(stack) - 1:
            stack.pop()
    return d2k


def main():
    apply = "--apply" in sys.argv

    k2e, e2h, info, order_h, order_e, order_k = cu_tree()
    ov = history_overrides()
    k2e.update({k: v for k, v in ov.items() if k.startswith("k_") and v.startswith("e_")})
    e2h.update({k: v for k, v in ov.items() if k.startswith("e_") and v.startswith("h_")})
    print("CU h=%d e=%d k=%d | de jure overrides=%d" % (len(order_h), len(order_e), len(order_k), len(ov)))

    blocks = mod_blocks()
    print("mod d_ blocks=%d" % len(blocks))
    orig = orig_d2k()
    print("orig d2k=%d" % len(orig))

    rows = list(csv.DictReader(io.open(PROBE, encoding="utf-8-sig")))
    target = {}
    for r in rows:
        d = r["duchy"]
        if r["top_kingdom"]:
            target[d] = r["top_kingdom"]

    modc = set(re.findall(r"(?m)^\s*(c_[A-Za-z0-9_-]+)\s*=\s*\{", read(SRC)))
    cu_county2our, cu_cty_cap, barony2our = cu_capital_maps()
    print("capital maps: cu_county=%d barony=%d" % (len(cu_county2our), len(barony2our)))

    # 每个 d_ 的目标王国
    plan = {}
    for d, blk in blocks:
        k = target.get(d) or orig.get(d)
        if not k:
            print("!! no target for", d)
            continue
        plan[d] = k

    # 分组
    k_duchies = defaultdict(list)
    d_cap = {}
    for d, blk in blocks:
        k = plan.get(d)
        if not k:
            continue
        k_duchies[k].append(blk)
        m = re.search(r"(?m)^\s*capital\s*=\s*(c_[A-Za-z0-9_-]+)", blk)
        if m:
            d_cap[d] = m.group(1)

    # k -> e
    e_ks = defaultdict(list)
    for k in k_duchies:
        e = k2e.get(k)
        e_ks[e].append(k)
    h_es = defaultdict(list)
    for e in e_ks:
        h = e2h.get(e) if e else None
        h_es[h].append(e)

    # capital 回退
    def kcap(k):
        c = info.get(k, {}).get("capital", "")
        if c and c in modc:
            return c
        if c:
            if c in cu_county2our:
                return cu_county2our[c]
            b = cu_cty_cap.get(c)
            if b and b in barony2our:
                return barony2our[b]
        for blk in k_duchies.get(k, []):
            m = re.search(r"(?m)^\s*capital\s*=\s*(c_[A-Za-z0-9_-]+)", blk)
            if m:
                return m.group(1)
        return ""

    def ecap(e):
        c = info.get(e, {}).get("capital", "")
        if c and c in modc:
            return c
        for k in e_ks.get(e, []):
            v = kcap(k)
            if v:
                return v
        return ""

    def hcap(h):
        c = info.get(h, {}).get("capital", "")
        if c and c in modc:
            return c
        for e in h_es.get(h, []):
            if e:
                v = ecap(e)
                if v:
                    return v
        return ""

    out = []
    out.append("# De jure tree rebuilt on Crusader Universalis (2026-10-29).")
    out.append("# h/e/k come from CU; every duchy is placed under the CU kingdom holding the")
    out.append("# largest share of its baronies in CU; duchies outside CU coverage keep their old")
    out.append("# kingdom. c_/b_ blocks and all province ids are untouched.")
    out.append("")

    def emit_h(h):
        body = []
        c = info.get(h, {}).get("color", "")
        cap = hcap(h)
        body.append("%s = {" % h)
        if c:
            body.append("\tcolor = %s" % c)
        if cap:
            body.append("\tcapital = %s" % cap)
        for e in sorted(h_es.get(h, []), key=lambda x: (x is None, x or "")):
            if not e:
                continue
            body.extend(emit_e(e, 1))
        body.append("}")
        return body

    def emit_e(e, lv):
        t = "\t" * lv
        body = []
        c = info.get(e, {}).get("color", "")
        cap = ecap(e)
        body.append("%s%s = {" % (t, e))
        if c:
            body.append("%scolor = %s" % (t + "\t", c))
        if cap:
            body.append("%scapital = %s" % (t + "\t", cap))
        for k in sorted(e_ks.get(e, [])):
            body.extend(emit_k(k, lv + 1))
        body.append("%s}" % t)
        return body

    def reindent(blk, delta):
        out = []
        for line in blk.split("\n"):
            if not line.strip():
                out.append("")
                continue
            n = len(line) - len(line.lstrip("\t"))
            out.append("\t" * max(0, n + delta) + line.lstrip("\t"))
        return "\n".join(out)

    def emit_k(k, lv):
        t = "\t" * lv
        body = []
        c = info.get(k, {}).get("color", "")
        cap = kcap(k)
        body.append("%s%s = {" % (t, k))
        if c:
            body.append("%scolor = %s" % (t + "\t", c))
        if cap:
            body.append("%scapital = %s" % (t + "\t", cap))
        delta = lv + 1 - 3
        for blk in k_duchies.get(k, []):
            body.append(reindent(blk, delta))
        body.append("%s}" % t)
        return body

    # 有霸权的
    for h in order_h:
        if h in h_es:
            out.extend(emit_h(h))
            out.append("")
    # 顶层帝国
    for e in sorted([x for x in h_es.get(None, []) if x]):
        if not e:
            continue
        out.extend(emit_e(e, 0))
        out.append("")
    # 顶层王国
    for k in sorted(e_ks.get(None, [])):
        out.extend(emit_k(k, 0))
        out.append("")

    text = "\n".join(out).replace("\n", "\r\n") + "\r\n"
    dst = LTD + ".new"
    with io.open(dst, "w", encoding="utf-8-sig", newline="") as f:
        f.write(text)
    print("wrote", dst, len(text), "bytes")

    # 映射表
    with io.open(MAPOUT, "w", encoding="utf-8", newline="") as f:
        f.write("duchy,old_kingdom,new_kingdom,changed\n")
        for d, k in sorted(plan.items()):
            o = orig.get(d) or ""
            f.write("%s,%s,%s,%d\n" % (d, o, k, int(o != k)))
    print("wrote", MAPOUT)

    # 统计
    ch = sum(1 for d, k in plan.items() if (orig.get(d) or "") != k)
    print("duchies=%d moved=%d kingdoms=%d empires=%d hegemonies=%d" % (
        len(plan), ch, len(k_duchies), len([e for e in e_ks if e]), len([h for h in h_es if h])))

    if apply:
        os.replace(dst, LTD)
        print("applied ->", LTD)


if __name__ == "__main__":
    main()
