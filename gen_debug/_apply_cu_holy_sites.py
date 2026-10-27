# -*- coding: utf-8 -*-
"""把本 mod 的圣地定义换成 CrusaderUniversalis 的数据。

CU 的圣地文件是 CK3 原版圣地投影到 EU5 地图上的版本，但 **county / barony 用的是 CU 自己的命名**
（c_antiocheia / b_kiev / b_makka…），跟本 mod 的 EU5 派生命名（c_antakya / b_kyiv / b_mecca）对不上。

所以换算方式：
  1. CU 的 barony 在本 mod 存在  -> 用它，county 取本 mod 里包含该 barony 的县
  2. 否则若本 mod 已有同名圣地     -> 沿用本 mod 原来的 (county, barony)
  3. 否则若 CU 的 county 存在      -> 保留 county，删掉对不上的 barony 行
  4. 都不行                        -> 原样保留并报出来
默认 dry-run；--apply 才写（先备份）。
"""
import io, os, re, sys, shutil, time

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
CU = r"E:\SteamLibrary\steamapps\workshop\content\1158310\3811443965"
SRC = os.path.join(MOD, "common", "religion", "holy_site_types", "00_holy_site_types.txt")
CUS = os.path.join(CU, "common", "religion", "holy_site_types", "00_holy_site_types.txt")
DRY = "--apply" not in sys.argv

BLOCK = re.compile(r"([A-Za-z0-9_\-]+)\s*=\s*\{")


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


def split_blocks(text):
    """返回 [(key, start, end)]，end 为块结束 '}' 之后的位置"""
    out = []
    i, n = 0, len(text)
    while i < n:
        m = BLOCK.search(text, i)
        if not m:
            break
        j, d = m.end(), 1
        while j < n and d:
            c = text[j]
            if c == "{":
                d += 1
            elif c == "}":
                d -= 1
            j += 1
        out.append((m.group(1), m.start(), j))
        i = j
    return out


def walk(s, path=()):
    i, n = 0, len(s)
    while i < n:
        m = BLOCK.search(s, i)
        if not m:
            return
        j, d = m.end(), 1
        while j < n and d:
            c = s[j]
            if c == "{":
                d += 1
            elif c == "}":
                d -= 1
            j += 1
        body = s[m.end():j - 1]
        yield path, m.group(1), body
        yield from walk(body, path + (m.group(1),))
        i = j


def main():
    lt = read(os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt"))
    bar2county, counties, baronies = {}, set(), set()
    for path, key, body in walk(lt):
        if not key.startswith("b_"):
            continue
        baronies.add(key)
        c = next((x for x in reversed(path) if x.startswith("c_")), None)
        if c:
            bar2county[key] = c
            counties.add(c)

    ours = {}
    src_t = read(SRC)
    for key, s, e in split_blocks(src_t):
        blk = src_t[s:e]
        mc = re.search(r"(?m)^\s*county\s*=\s*(\S+)", blk)
        mb = re.search(r"(?m)^\s*barony\s*=\s*(\S+)", blk)
        ours[key] = (mc.group(1) if mc else None, mb.group(1) if mb else None)

    cu_t = read(CUS)
    cu_blocks = [(k, cu_t[s:e]) for k, s, e in split_blocks(cu_t)]
    print("本 mod 圣地 %d 个；CU 圣地 %d 个" % (len(ours), len(cu_blocks)))

    out_blocks, stat, unresolved = [], {"barony": 0, "ours": 0, "county": 0, "raw": 0}, []
    for key, blk in cu_blocks:
        mc = re.search(r"(?m)^(\s*)county\s*=\s*(\S+)", blk)
        mb = re.search(r"(?m)^(\s*)barony\s*=\s*(\S+)", blk)
        cu_c = mc.group(2) if mc else None
        cu_b = mb.group(2) if mb else None
        new_c = new_b = None
        if cu_b and cu_b in baronies:
            new_b = cu_b
            new_c = bar2county.get(cu_b)
            stat["barony"] += 1
        elif key in ours and ours[key][0]:
            new_c, new_b = ours[key]
            stat["ours"] += 1
        elif cu_c and cu_c in counties:
            new_c, new_b = cu_c, None
            stat["county"] += 1
        else:
            stat["raw"] += 1
            unresolved.append((key, cu_c, cu_b))
            continue

        nb = blk
        if mc and new_c:
            nb = nb[:mc.start(2)] + new_c + nb[mc.end(2):]
        # barony 行
        mb2 = re.search(r"(?m)^\s*barony\s*=\s*(\S+)[ \t]*\n?", nb)
        if mb2:
            if new_b:
                if mb2.group(1) != new_b:
                    nb = nb[:mb2.start(1)] + new_b + nb[mb2.end(1):]
            else:
                nb = nb[:mb2.start()] + nb[mb2.end():]
        out_blocks.append(nb)

    print("换算来源：", stat)
    if unresolved:
        print("无法换算、已丢弃：%d（均未被任何 faith 引用）" % len(unresolved))
        for k, c, b in unresolved[:20]:
            print("   %-28s county=%-24s barony=%s" % (k, c, b))

    new = "\r\n\r\n".join(b.rstrip() for b in out_blocks) + "\r\n"
    print("新文件大小：%d（旧 %d）" % (len(new), len(src_t)))
    if DRY:
        print("\n[dry-run] 未写文件。")
        return
    ts = time.strftime("%Y%m%d_%H%M%S")
    shutil.copy2(SRC, SRC + ".bak_cuholy_" + ts)
    io.open(SRC, "w", encoding="utf-8-sig", newline="").write(new)
    print("\nAPPLIED. backup:", SRC + ".bak_cuholy_" + ts)
    print("braces:", new.count("{"), new.count("}"))


if __name__ == "__main__":
    main()
