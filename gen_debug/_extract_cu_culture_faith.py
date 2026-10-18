# -*- coding: utf-8 -*-
"""只读：从 CrusaderUniversalis（工坊 3811443965）抽取每个 province 的 CK3 原版 culture / rite，
按「barony 名 == EU5 location 名」匹配回本 mod，并统计覆盖率与差异。

口径：
  - 该 mod 只给伯爵领首府写文化/信仰，其余通过 history/province_mapping 继承（target = rep）。
  - 取 867.1.1 开局值：顶层字段 + 所有日期 <= 867.1.1 的日期块按时间顺序覆盖。
输出：gen_debug/_cu_vs_ours.csv + 控制台统计。不写任何游戏文件。
"""
import io, os, re, csv, glob
from collections import Counter, defaultdict

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
CU = r"E:\SteamLibrary\steamapps\workshop\content\1158310\3811443965"
OURS = os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt")
OUTDIR = os.path.join(MOD, "gen_debug")
START = (1337, 1, 1)   # 本 mod 开局 1337.1.1（common/bookmarks/bookmarks/00_bookmarks.txt）

BLOCK = re.compile(r"([A-Za-z0-9_]+)\s*=\s*\{")


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


def walk_blocks(text, path=()):
    i, n = 0, len(text)
    while i < n:
        m = BLOCK.search(text, i)
        if not m:
            return
        j, depth = m.end(), 1
        while j < n and depth:
            c = text[j]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            j += 1
        body = text[m.end():j - 1]
        yield path, m.group(1), body
        yield from walk_blocks(body, path + (m.group(1),))
        i = j


def cu_landed_titles():
    """b_name -> (province_id, county_name)"""
    out = {}
    for p in glob.glob(os.path.join(CU, "common", "landed_titles", "*.txt")):
        t = read(p)
        for path, key, body in walk_blocks(t):
            if not key.startswith("b_"):
                continue
            m = re.search(r"\bprovince\s*=\s*(\d+)", body)
            if not m:
                continue
            county = next((x for x in reversed(path) if x.startswith("c_")), "")
            out[key[2:]] = (int(m.group(1)), county)
    return out


def cu_province_history():
    """pid -> (culture, rite) 在 867.1.1 的值（含日期块覆盖）"""
    out = {}
    for p in glob.glob(os.path.join(CU, "history", "provinces", "*.txt")):
        t = read(p)
        for m in re.finditer(r"(?m)^(\d+)\s*=\s*\{", t):
            pid = int(m.group(1))
            body = t[m.end() - 1:]
            d = 0
            for j, ch in enumerate(body):
                if ch == "{":
                    d += 1
                elif ch == "}":
                    d -= 1
                    if d == 0:
                        body = body[1:j]
                        break
            base_c = base_f = None
            dated = []
            depth = 0
            curdate = None
            for line in body.split("\n"):
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                md = re.match(r"(\d{1,4})\.(\d{1,2})\.(\d{1,2})\s*=\s*\{", s)
                if md:
                    curdate = (int(md.group(1)), int(md.group(2)), int(md.group(3)))
                mc = re.match(r"culture\s*=\s*(\S+)", s)
                mf = re.match(r"(?:rite|faith)\s*=\s*(\S+)", s)
                if depth == 1:
                    if mc and curdate:
                        dated.append((curdate, "c", mc.group(1)))
                    if mf and curdate:
                        dated.append((curdate, "f", mf.group(1)))
                elif depth == 0:
                    if mc:
                        base_c = mc.group(1)
                    if mf:
                        base_f = mf.group(1)
                depth += line.count("{") - line.count("}")
            c, f = base_c, base_f
            for dt, kind, val in sorted(dated, key=lambda x: x[0]):
                if dt <= START:
                    if kind == "c":
                        c = val
                    else:
                        f = val
            if c or f:
                out[pid] = (c, f)
    return out


def cu_mapping():
    """target_pid -> rep_pid"""
    out = {}
    for p in glob.glob(os.path.join(CU, "history", "province_mapping", "*.txt")):
        for line in read(p).split("\n"):
            m = re.match(r"\s*(\d+)\s*=\s*(\d+)\s*(?:#.*)?$", line)
            if m:
                out[int(m.group(1))] = int(m.group(2))
    return out


def ours_parse():
    t = read(OURS)
    d = {}
    for m in re.finditer(r"(?m)^(\d+)\s*=\s*\{", t):
        pid = int(m.group(1))
        body = t[m.end() - 1:]
        k = 0
        for j, ch in enumerate(body):
            if ch == "{":
                k += 1
            elif ch == "}":
                k -= 1
                if k == 0:
                    body = body[:j + 1]
                    break
        c = re.search(r"(?m)^\s*culture\s*=\s*(\S+)", body)
        f = re.search(r"(?m)^\s*faith\s*=\s*(\S+)", body)
        d[pid] = (c.group(1) if c else None, f.group(1) if f else None)
    return d


def main():
    print("== 读取 CrusaderUniversalis ==")
    cu_lt = cu_landed_titles()
    print("  baronies:", len(cu_lt))
    cu_hist = cu_province_history()
    print("  province 历史块（含文化或信仰）:", len(cu_hist))
    cu_map = cu_mapping()
    print("  province_mapping 条数:", len(cu_map))

    # 解析映射链
    def resolve(pid, seen=None):
        seen = seen or set()
        if pid in cu_hist:
            return cu_hist[pid]
        if pid in cu_map and pid not in seen:
            seen.add(pid)
            return resolve(cu_map[pid], seen)
        return (None, None)

    name_cf = {}
    for bname, (pid, county) in cu_lt.items():
        c, f = resolve(pid)
        if c or f:
            name_cf[bname] = (c, f, county, pid)
    print("  barony 名 -> (culture, rite) 可解析:", len(name_cf))

    # 本 mod 的 barony 名 -> province
    ours_lt = read(os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt"))
    ours_by_name = {}
    for path, key, body in walk_blocks(ours_lt):
        if not key.startswith("b_"):
            continue
        m = re.search(r"\bprovince\s*=\s*(\d+)", body)
        if m:
            county = next((x for x in reversed(path) if x.startswith("c_")), "")
            ours_by_name[key[2:]] = (int(m.group(1)), county)
    print("== 本 mod ==")
    print("  baronies:", len(ours_by_name))

    cur = ours_parse()
    common = sorted(set(ours_by_name) & set(name_cf))
    print("  按 barony 名匹配上:", len(common))
    only_ours = len(ours_by_name) - len(common)
    only_cu = len(name_cf) - len(common)
    print("  仅本 mod 有:", only_ours, " 仅 CU 有:", only_cu)

    rows = []
    chg_c = chg_f = 0
    for bname in common:
        pid, county = ours_by_name[bname]
        oc, of = cur.get(pid, (None, None))
        nc, nf, cucounty, cupid = name_cf[bname]
        if nc and nc != oc:
            chg_c += 1
        if nf and nf != of:
            chg_f += 1
        rows.append([bname, pid, county, oc, of, nc or "", nf or "", cucounty, cupid])

    print()
    print("== 差异 ==")
    print("  culture 会变:", chg_c, " faith/rite 会变:", chg_f)
    print("  样例:")
    for r in rows[:15]:
        print("    %-22s %s/%s -> %s/%s" % (r[0], r[3], r[4], r[5], r[6]))

    with io.open(os.path.join(OUTDIR, "_cu_vs_ours.csv"), "w",
                 encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["barony", "our_province", "our_county", "our_culture", "our_faith",
                    "cu_culture", "cu_rite", "cu_county", "cu_province"])
        w.writerows(rows)
    print()
    print("csv:", os.path.join(OUTDIR, "_cu_vs_ours.csv"))

    # 键空间合法性：CU 的 culture/rite 在本 mod 定义里存在吗
    def keys(sub):
        s = set()
        for root, d, fs in os.walk(os.path.join(MOD, "common", sub)):
            for fn in fs:
                if fn.endswith(".txt"):
                    s |= set(re.findall(r"(?m)^\s*([a-z0-9_]+)\s*=\s*\{",
                                        read(os.path.join(root, fn))))
        return s
    cults, faiths = keys("culture"), keys("religion")
    badc = sorted({r[5] for r in rows if r[5]} - cults)
    badf = sorted({r[6] for r in rows if r[6]} - faiths)
    print()
    print("CU 的 culture 不在本 mod 定义里:", len(badc), badc[:15])
    print("CU 的 rite    不在本 mod 定义里:", len(badf), badf[:15])


if __name__ == "__main__":
    main()
