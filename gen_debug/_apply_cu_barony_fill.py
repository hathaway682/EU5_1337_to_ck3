# -*- coding: utf-8 -*-
"""按【男爵领 × CU 县】的直接重合，给非洲 / 东南亚仍是 pagan 的省份填 faith。

原则（这次不再做任何区域统计外推）：
  - 只有该男爵领所在的县在 CU 里有 rite 数据，才动它；没有就保持原样
  - 不做"多数 rite"投票、不做兜底、不跨县推广
  - 只处理当前 faith == pagan 的省份（其余一律不动）
默认 dry-run；--apply 才写。
"""
import io, os, re, csv, glob, sys, shutil, time
from collections import Counter, defaultdict

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
CU = r"E:\SteamLibrary\steamapps\workshop\content\1158310\3811443965"
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"
SRC = os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt")
OUTDIR = os.path.join(MOD, "gen_debug")
START = (1173, 1, 1)
DRY = "--apply" not in sys.argv

AFRICA = {"maghreb", "egypt", "nubia", "somalia", "ethiopia", "sahel", "guinea",
          "central_africa", "kongo", "southern_africa", "zimbabwe", "swahili_coast",
          "madagascar", "macronesia"}
SEA = {"indochina", "indonesia"}

BLOCK = re.compile(r"([A-Za-z0-9_]+)\s*=\s*\{")


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


def walk(text, path=()):
    i, n = 0, len(text)
    while i < n:
        m = BLOCK.search(text, i)
        if not m:
            return
        j, d = m.end(), 1
        while j < n and d:
            c = text[j]
            if c == "{":
                d += 1
            elif c == "}":
                d -= 1
            j += 1
        body = text[m.end():j - 1]
        yield path, m.group(1), body
        yield from walk(body, path + (m.group(1),))
        i = j


def faith_tables():
    """返回 rite -> [faith...]（可能多对一，需要人工确认）"""
    faith_main = {}
    d = os.path.join(MOD, "common", "religion", "faith_types")
    for fn in os.listdir(d):
        if not fn.endswith(".txt"):
            continue
        for path, key, body in walk(read(os.path.join(d, fn))):
            if path:
                continue
            m = re.search(r"(?m)^\s*main_rite\s*=\s*(\S+)", body)
            if m:
                faith_main[key] = m.group(1)
    r2f = defaultdict(list)
    for f, r in faith_main.items():
        r2f[r].append(f)
    return faith_main, r2f


def cu_barony_rite():
    """CU 块 -> (男爵领名, rite)。CU 只写伯爵领首府，所以这里拿到的是首府男爵领的 rite。"""
    hist, comment_barony, comment_county = {}, {}, {}
    for p in glob.glob(os.path.join(CU, "history", "provinces", "*.txt")):
        t = read(p)
        for m in re.finditer(r"(?m)^(\d+)\s*=\s*\{([^\n]*)", t):
            pid = int(m.group(1))
            mc = re.search(r"#\s*(b_[a-z0-9_]+),\s*(c_[a-z0-9_\-]+)", m.group(2))
            if mc:
                comment_barony[pid] = mc.group(1)[2:]
                comment_county[pid] = mc.group(2)
            else:
                mb = re.search(r"#\s*(b_[a-z0-9_]+)", m.group(2))
                if mb:
                    comment_barony[pid] = mb.group(1)[2:]
            bp = t.index("{", m.end(1))
            body = t[bp:]
            d = 0
            for j, ch in enumerate(body):
                if ch == "{":
                    d += 1
                elif ch == "}":
                    d -= 1
                    if d == 0:
                        body = body[1:j]
                        break
            base, dated, depth, cur = None, [], 0, None
            for line in body.split("\n"):
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                md = re.match(r"(\d{1,4})\.(\d{1,2})\.(\d{1,2})\s*=\s*\{", s)
                if md:
                    cur = (int(md.group(1)), int(md.group(2)), int(md.group(3)))
                mf = re.match(r"(?:rite|faith)\s*=\s*(\S+)", s)
                if mf:
                    if depth == 1 and cur:
                        dated.append((cur, mf.group(1)))
                    elif depth == 0:
                        base = mf.group(1)
                depth += line.count("{") - line.count("}")
            v = base
            for dt, val in sorted(dated):
                if dt <= START:
                    v = val
            if v:
                hist[pid] = v
    mapping = {}
    for p in glob.glob(os.path.join(CU, "history", "province_mapping", "*.txt")):
        for line in read(p).split("\n"):
            m = re.match(r"\s*(\d+)\s*=\s*(\d+)\s*(?:#.*)?$", line)
            if m:
                mapping[int(m.group(1))] = int(m.group(2))

    def resolve(pid, seen=None):
        seen = seen or set()
        if pid in hist:
            return hist[pid]
        if pid in mapping and pid not in seen:
            seen.add(pid)
            return resolve(mapping[pid], seen)
        return None

    # CU 只写伯爵领首府：拿到「首府男爵领名 -> rite」
    out = {}
    for pid, bname in comment_barony.items():
        r = resolve(pid)
        if r:
            out[bname] = r
    return out


def main():
    lt = read(os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt"))
    prov_county, prov_king, prov_loc = {}, {}, {}
    for path, key, body in walk(lt):
        if not key.startswith("b_"):
            continue
        m = re.search(r"\bprovince\s*=\s*(\d+)", body)
        if not m:
            continue
        pid = int(m.group(1))
        prov_loc[pid] = key[2:]
        c = next((x for x in reversed(path) if x.startswith("c_")), None)
        k = next((x for x in reversed(path) if x.startswith("k_")), None)
        if c:
            prov_county[pid] = c
        if k:
            prov_king[pid] = k

    def region(pid):
        k = (prov_king.get(pid) or "")[2:]
        if k in AFRICA:
            return "africa"
        if k in SEA:
            return "sea"
        return None

    raw = read(SRC)
    cur, has_rite = {}, set()
    for m in re.finditer(r"(?m)^(\d+)\s*=\s*\{(.*?)^\}", raw, re.S):
        b = m.group(2)
        f = re.search(r"(?m)^\s*faith\s*=\s*(\S+)", b)
        cur[int(m.group(1))] = f.group(1) if f else None
        if re.search(r"(?m)^\s*rite\s*=", b):
            has_rite.add(int(m.group(1)))

    pop_rel = defaultdict(Counter)
    pt = read(os.path.join(EU5, "main_menu", "setup", "start", "06_pops.txt"))
    for m in re.finditer(r"(?ms)^[ \t]*([a-z0-9_']+)[ \t]*=[ \t]*\{\n(.*?)^[ \t]*\}", pt):
        loc = m.group(1)
        for pm in re.finditer(r"define_pop\s*=\s*\{([^}]*)\}", m.group(2)):
            pb = pm.group(1)
            sz = re.search(r"\bsize\s*=\s*([0-9.]+)", pb)
            rl = re.search(r"\breligion\s*=\s*([a-z0-9_]+)", pb)
            if sz and rl:
                pop_rel[loc][rl.group(1)] += float(sz.group(1))

    faith_main, r2f = faith_tables()
    cu_bar = cu_barony_rite()

    # CU 的首府男爵领 -> 落在我们的哪个县 -> 整县染色（同县多个 CU 首府时取多数并记冲突）
    cand = defaultdict(Counter)
    hit = []
    for p, loc in prov_loc.items():
        if loc in cu_bar and p in prov_county:
            cand[prov_county[p]][cu_bar[loc]] += 1
            hit.append(p)
    cu_b, conflicts = {}, []
    for c, cc in cand.items():
        rite, n = cc.most_common(1)[0]
        cu_b[c] = rite
        if len(cc) > 1:
            conflicts.append((c, dict(cc)))
    print("CU 首府男爵领：匹配到我们 %d 个男爵领 -> 染色 %d 个伯爵领（冲突 %d）"
          % (len(hit), len(cu_b), len(conflicts)))
    if conflicts:
        for c, d in conflicts[:8]:
            print("   冲突 %-28s %s" % (c, d))

    plan, no_cu = {}, []
    for pid, county in prov_county.items():
        rg = region(pid)
        if not rg:
            continue
        if cur.get(pid) != "pagan":
            continue
        r = cu_b.get(county)
        if not r:
            no_cu.append(pid)
            continue
        cand = r2f.get(r) or []
        if len(cand) != 1:
            no_cu.append(pid)
            continue
        plan[pid] = (cand[0], r)

    amb = sorted({cu_b[c] for c in cu_b if len(r2f.get(cu_b[c]) or []) != 1})
    print("CU 里 faith 不唯一的 rite（本次跳过）：", amb)
    print()
    print("非洲/东南亚 pagan 省：%d" % (len(plan) + len(no_cu)))
    print("  有 CU 县数据、可填：%d" % len(plan))
    print("  无 CU 数据 / rite 歧义：%d" % len(no_cu))
    print()
    byreg = Counter(region(p) for p in plan)
    print("  可填按区域：", dict(byreg))
    print()
    tr = Counter((cur[p], f) for p, (f, r) in plan.items())
    print("faith 迁移：")
    for k, v in tr.most_common():
        print("  %-22s -> %-26s %d" % (k[0], k[1], v))

    # 按 EU5 宗教看还剩多少没填
    left = Counter()
    for p in no_cu:
        loc = prov_loc.get(p)
        e = min(pop_rel[loc].items(), key=lambda kv: (-kv[1], kv[0]))[0] if loc in pop_rel and pop_rel[loc] else "(no pops)"
        left[(region(p), e)] += 1
    print()
    print("填不上的（按 EU5 宗教）：")
    for (rg, e), v in left.most_common(20):
        print("  %-8s %-30s %d" % (rg, e, v))

    with io.open(os.path.join(OUTDIR, "_cu_barony_fill_plan.csv"), "w",
                 encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["province", "barony", "county", "region", "eu5_religion",
                    "old_faith", "new_faith", "new_rite", "has_rite_line"])
        for pid in sorted(plan):
            f, r = plan[pid]
            loc = prov_loc.get(pid)
            e = min(pop_rel[loc].items(), key=lambda kv: (-kv[1], kv[0]))[0] if loc in pop_rel and pop_rel[loc] else ""
            w.writerow([pid, loc, prov_county.get(pid), region(pid), e,
                        cur.get(pid), f, r, "Y" if pid in has_rite else ""])

    if DRY:
        print("\n[dry-run] 未写文件。")
        return

    ts = time.strftime("%Y%m%d_%H%M%S")
    out, cur_pid, lines = [], None, 0
    for line in raw.split("\n"):
        m = re.match(r"^(\d+) = \{$", line)
        if m:
            cur_pid = int(m.group(1))
            out.append(line)
            continue
        if line.strip() == "}":
            out.append(line)
            continue
        if cur_pid in plan:
            f, r = plan[cur_pid]
            mf = re.match(r"^(\s*)faith\s*=\s*(\S+)", line)
            mr = re.match(r"^(\s*)rite\s*=\s*(\S+)", line)
            if mf:
                out.append("%sfaith = %s" % (mf.group(1), f))
                if mf.group(2) != f:
                    lines += 1
                continue
            if mr:
                out.append("%srite = %s" % (mr.group(1), r))
                if mr.group(2) != r:
                    lines += 1
                continue
        out.append(line)
    new = "\n".join(out)
    if new != raw:
        shutil.copy2(SRC, SRC + ".bak_cufill_" + ts)
        io.open(SRC, "w", encoding="utf-8-sig", newline="\n").write(new)
        print("\nAPPLIED. changed_lines=%d" % lines)
        print("backup:", SRC + ".bak_cufill_" + ts)
        print("braces:", new.count("{"), new.count("}"))
    else:
        print("\nno change")


if __name__ == "__main__":
    main()
