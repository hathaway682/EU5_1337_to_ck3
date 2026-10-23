# -*- coding: utf-8 -*-
"""只读：把 mod 圣地全部 321 条与 CK3 原版圣地表逐 key 对照。
输出每个 key 的：mod 指向 / 原版指向 / 二者是否一致 / 原版 barony 在 mod 是否存在。
"""
import io, os, re, sys, json

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
MOD_HS = os.path.join(MOD, r"common\religion\holy_site_types\00_holy_site_types.txt")
MOD_LT = os.path.join(MOD, r"common\landed_titles\00_landed_titles.txt")
MOD_LOC_DIR = os.path.join(MOD, r"localization\simp_chinese")
VAN_HS = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game\common\religion\holy_site_types\00_holy_site_types.txt"
VAN_LOC_DIR = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game\localization\simp_chinese"


def read_txt(p):
    with io.open(p, "rb") as f:
        b = f.read()
    if b.startswith(b"\xef\xbb\xbf"):
        b = b[3:]
    return b.decode("utf-8", "replace")


def parse_hs(path):
    """行级 depth==1 解析，返回 {key: {"county":x,"barony":y}}"""
    txt = read_txt(path)
    lines = txt.split("\n")
    out = {}
    depth = 0
    cur = None
    for ln in lines:
        s = ln.strip()
        if s.startswith("#"):
            continue
        if depth == 0:
            m = re.match(r"^([a-zA-Z0-9_]+)\s*=\s*\{", s)
            if m:
                cur = m.group(1)
                out[cur] = {}
                depth = 1
                # 同一行可能还有内容，但圣地表不会
                continue
        elif depth == 1 and cur is not None:
            mc = re.match(r"^county\s*=\s*(\S+)", s)
            mb = re.match(r"^barony\s*=\s*(\S+)", s)
            if mc:
                out[cur]["county"] = mc.group(1)
            if mb:
                out[cur]["barony"] = mb.group(1)
        # 括号计数
        depth += s.count("{") - s.count("}")
        if depth <= 0:
            depth = 0
            cur = None
    return out


def load_loc(dirpath):
    """读目录下所有 yml，返回 {key: 中文}（同 key 后出现的覆盖先出现的）"""
    d = {}
    if not os.path.isdir(dirpath):
        return d
    for fn in os.listdir(dirpath):
        if not fn.lower().endswith(".yml"):
            continue
        p = os.path.join(dirpath, fn)
        try:
            txt = read_txt(p)
        except Exception:
            continue
        for ln in txt.split("\n"):
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            m = re.match(r'^([a-zA-Z0-9_.\-\'"]+)\s*:\s*\d*\s*"(.*)"\s*$', ln)
            if not m:
                continue
            k = m.group(1).strip('"')
            v = m.group(2)
            d[k] = v
    return d


def main():
    mod = parse_hs(MOD_HS)
    van = parse_hs(VAN_HS)
    print("mod 圣地 = %d   原版圣地 = %d" % (len(mod), len(van)))

    # mod 已有的 barony / county 集合
    lt = read_txt(MOD_LT)
    mod_bar = set(re.findall(r"^\s*(b_[a-zA-Z0-9_]+)\s*=\s*\{", lt, re.M))
    mod_cty = set(re.findall(r"^\s*(c_[a-zA-Z0-9_]+)\s*=\s*\{", lt, re.M))
    print("mod barony = %d   mod county = %d" % (len(mod_bar), len(mod_cty)))

    modloc = load_loc(MOD_LOC_DIR)
    vanloc = load_loc(VAN_LOC_DIR)

    both = sorted(set(mod) & set(van))
    print("两边都有的 key = %d" % len(both))

    diff = []
    for k in both:
        mv, vv = mod[k], van[k]
        mb, vb = mv.get("barony"), vv.get("barony")
        mc, vc = mv.get("county"), vv.get("county")
        if vb:
            exist = vb in mod_bar
            same = (mb == vb)
        else:
            exist = vc in mod_cty if vc else False
            same = (mc == vc)
        if same:
            continue
        diff.append({
            "key": k,
            "mod_b": mb, "mod_c": mc,
            "van_b": vb, "van_c": vc,
            "van_exist": exist,
            "mod_zh": modloc.get(mb or "") or modloc.get(mc or "") or "",
            "van_zh": vanloc.get(vb or "") or vanloc.get(vc or "") or "",
        })

    print("\n不一致 = %d 条；其中原版目标在 mod 存在的：" % len(diff))
    n = 0
    for r in diff:
        if r["van_exist"]:
            n += 1
            print("[%2d] %-22s mod=%-28s(%-8s) 原版=%-28s(%-8s)" % (
                n, r["key"], (r["mod_b"] or r["mod_c"]), r["mod_zh"],
                (r["van_b"] or r["van_c"]), r["van_zh"]))
    print("\n合计原版目标可用 = %d" % n)

    # ---- 按中文名比对：中文名一致 = 其实已经对了（只是 barony/county 粒度不同）----
    same_zh, diff_zh = [], []
    for r in diff:
        a = (r["mod_zh"] or "").strip()
        b = (r["van_zh"] or "").strip()
        if a and b and (a == b or a in b or b in a):
            same_zh.append(r)
        else:
            diff_zh.append(r)
    print("\n=== 中文名一致（实质已对，粒度不同）= %d 条 ===" % len(same_zh))
    print("\n=== 中文名不同（需人判）= %d 条 ===" % len(diff_zh))
    for r in diff_zh:
        print("  %-22s mod=%-26s(%-10s) 原版=%-26s(%-10s) 原版存在=%s" % (
            r["key"], (r["mod_b"] or r["mod_c"]), r["mod_zh"],
            (r["van_b"] or r["van_c"]), r["van_zh"], r["van_exist"]))

    # 不一致但原版目标在 mod 不存在（供参考）
    print("\n--- 原版目标在 mod 不存在（无法照抄）%d 条，仅列原版中文名 ---" % (len(diff) - n))
    for r in diff:
        if not r["van_exist"]:
            print("  %-22s 原版=%-26s(%-10s)  mod=%-24s(%s)" % (
                r["key"], (r["van_b"] or r["van_c"]), r["van_zh"],
                (r["mod_b"] or r["mod_c"]), r["mod_zh"]))


if __name__ == "__main__":
    main()
