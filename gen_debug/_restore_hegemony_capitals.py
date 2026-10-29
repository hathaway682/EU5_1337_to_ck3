#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""恢复王国以上(h/e/k)被回落成子块首府的首府，改回 CU 真实首府。

方法（与之前 _rebuild_dejure_cu.py 的 kcap 一致，不投影）：
  1) CU 头衔的首府县 C 的 capital 男爵领 B；
  2) B 在 _cu_vs_ours.csv 的 barony(我们的男爵领)列 -> our_county；
  3) 否则取 B 所在 CU province P -> csv 的 cu_province 主导 our_county；
  4) 仍找不到则保持现状(回落值)。
只改 h/e/k 的 capital 行；其余一字不动。
"""
import re, io, csv, glob, os, sys

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CU  = r"E:/SteamLibrary/steamapps/workshop/content/1158310/3811443965"
LTD = os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt")

PAT = re.compile(r"([A-Za-z0-9_.-]+)\s*=\s*\{")

def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()

def walk(text, parents=()):
    out = []; i = 0; n = len(text)
    while True:
        m = PAT.search(text, i)
        if not m:
            break
        key = m.group(1); j = m.end(); d = 1
        while j < n and d:
            if text[j] == "{": d += 1
            elif text[j] == "}": d -= 1
            j += 1
        body = text[m.end():j - 1]
        out.append((key, parents, body))
        out.extend(walk(body, parents + (key,)))
        i = j
    return out

# ---- CU 数据 ----
def cu_data():
    cucap = {}      # title -> capital county
    capb = {}       # county -> capital barony (no b_ prefix)
    bprov = {}      # barony (no b_ prefix) -> province number (in CU)
    for p in glob.glob(CU + "/common/landed_titles/*.txt"):
        t = read(p)
        for key, par, body in walk(t):
            if key[:2] in ("h_", "e_", "k_"):
                m = re.search(r"capital\s*=\s*(c_[A-Za-z0-9_-]+)", body)
                if m: cucap.setdefault(key, m.group(1))
            if key.startswith("c_"):
                m = re.search(r"capital\s*=\s*(b_[A-Za-z0-9_-]+)", body)
                if m: capb.setdefault(key, m.group(1)[2:])
                else:
                    m2 = re.search(r"(?m)^\s*(b_[A-Za-z0-9_-]+)\s*=\s*\{", body)
                    if m2: capb.setdefault(key, m2.group(1)[2:])
                # 该 county 下每个 b_ 的 province
                for bm in re.finditer(r"(?m)^\s*(b_[A-Za-z0-9_-]+)\s*=\s*\{(.*?)(\n\S|\Z)", body, re.S):
                    bk = bm.group(1)[2:]
                    pm = re.search(r"province\s*=\s*(\d+)", bm.group(2))
                    if pm: bprov[bk] = int(pm.group(1))
    return cucap, capb, bprov

# ---- csv 映射 ----
def csv_maps():
    rows = list(csv.DictReader(io.open(os.path.join(MOD, "gen_debug", "_cu_vs_ours.csv"), encoding="utf-8-sig")))
    barony2our = {}                 # 我们的男爵领 -> our_county
    cuprov2our = {}                 # cu_province -> Counter(our_county)
    for r in rows:
        b = r["barony"].strip()
        if b:
            barony2our.setdefault(b, r["our_county"])
        cp = r["cu_province"].strip()
        if cp:
            cuprov2our.setdefault(cp, {}).setdefault(r["our_county"], 0)
            cuprov2our[cp][r["our_county"]] += 1
    # 主导 our_county
    cuprov2ourbest = {k: max(v, key=v.get) for k, v in cuprov2our.items()}
    return barony2our, cuprov2ourbest

# ---- 当前文件 h/e/k 首府 ----
def current_caps():
    t = read(LTD).replace("\r\n", "\n")
    lines = t.split("\n")
    stack = []; cur = {}
    for ln in lines:
        m = re.match(r"^(\t*)([hek]_[a-z0-9_-]+)\s*=\s*\{", ln)
        if m:
            stack.append([m.group(2), len(m.group(1)), None]); continue
        if not stack: continue
        top = stack[-1]; ind = len(ln) - len(ln.lstrip("\t"))
        if ind == top[1] + 1 and ln.strip().startswith("capital"):
            mm = re.search(r"capital\s*=\s*(c_[a-z0-9_-]+)", ln)
            if mm: top[2] = mm.group(1)
        if ind <= top[1] and ln.strip() == "}" and stack:
            b = stack.pop()
            if b[0][0] in "hek" and b[2]:
                cur[b[0]] = b[2]
    return cur

def our_counties():
    t = read(LTD).replace("\r\n", "\n")
    return set(re.findall(r"(?m)^\t*(c_[a-z0-9_-]+)\s*=\s*\{", t))

def recover():
    cucap, capb, bprov = cu_data()
    barony2our, cuprov2ourbest = csv_maps()
    cur = current_caps()
    occ = our_counties()
    proposals = {}   # title -> (new_capital, method, note)
    for k, v in cur.items():
        c = cucap.get(k)
        if not c:
            continue
        b = capb.get(c)            # CU 首府男爵领名(无前缀)
        new = None; method = None
        if b and b in barony2our:
            cand = barony2our[b]
            if cand in occ:
                new, method = cand, "barony"
        if not new and b and b in bprov:
            cp = str(bprov[b])
            if cp in cuprov2ourbest:
                cand = cuprov2ourbest[cp]
                if cand in occ:
                    new, method = cand, "province"
        # 验证：新值确实存在且 != 当前值才改
        if new and new != v and new in occ:
            proposals[k] = (new, method, "cu=%s barony=%s" % (c, b))
    return proposals, cur


# 首府修正表（CAPITAL_FIX）
# 用法：键=本树 h/e/k 头衔，值=它应取的首府县（必须在 our_counties 内）。
# 两类来源：
#   A. 同 EU5 地点、但两 mod 拼写不同，导致同名匹配漏掉（roma/rome、kiev/kyiv、
#      praha/prague、xiliang 同名、igbo-ukwu 同名）——取该地点在我们树里所属县；
#   B. CU 首府城市在我们树里根本没有对应男爵领（odessa、atholl），取它真实所在
#      次区域的构成公国首府县作兜底（Yedisan / 苏格兰高地）。
# 仅当 cur[k] != 值 且 值存在时才改；不影响其它任何行。
CAPITAL_FIX = {
    "k_romagna": "c_romagna",        # A：本树同名郡（cur 本就 ==，无变化）
    "e_italy": "c_marittima",        # A：CU c_roma 首府男爵领 b_roma = 我们 b_rome -> c_marittima
    "e_russia": "c_kyiv",            # A：CU c_kiev 首府男爵领 b_kiev = 我们 b_kyiv -> c_kyiv
    "k_ruthenia": "c_kyiv",          # A：同上，CU c_kiev -> c_kyiv
    "k_hexi": "c_yongchang_gansu",   # A：CU c_liangzhou 首府男爵领 b_xiliang -> c_yongchang_gansu
    "k_igbo-benue": "c_west_igbo",   # A：CU c_igbo 首府男爵领 b_igbo-ukwu -> c_west_igbo
    "k_pontic_steppe": "c_qalancak", # B：Odessa 不在本树，取 Yedisan 次区域首府 c_qalancak
    "k_scotland": "c_moray",         # B：Atholl 不在本树，取苏格兰高地首府 c_moray
}


def full_changes():
    proposals, cur = recover()
    occ = our_counties()
    cucap, capb, bprov = cu_data()
    changes = {}
    for k, (new, method, note) in proposals.items():
        changes[k] = (new, "barony/province", note)
    for k, v in CAPITAL_FIX.items():
        if k in cur and v in occ and cur[k] != v:
            if k not in changes:
                changes[k] = (v, "capital-fix", "cu=%s" % cucap.get(k))
    return changes, cur

def apply_changes(changes):
    # 备份
    bak = LTD + ".bak_20261029_capfix"
    if not os.path.exists(bak):
        import shutil
        shutil.copy2(LTD, bak)
    lines = io.open(LTD, encoding="utf-8-sig").read().split("\n")
    # 计算每个标题块的范围
    stack = []          # (key, indent)
    # 先找每个 key 的起始行与层级
    start = {}
    for i, ln in enumerate(lines):
        m = re.match(r"^(\t*)([hek]_[a-z0-9_-]+)\s*=\s*\{", ln)
        if m:
            start[m.group(2)] = (i, len(m.group(1)))
    done = set()
    # 从后往前改，避免行号漂移
    for k in sorted(changes, key=lambda x: -start[x][0]):
        new, how, note = changes[k]
        i0, ind = start[k]
        # 找块结束：从 i0 开始统计花括号
        depth = 0; end = None
        for j in range(i0, len(lines)):
            depth += lines[j].count("{") - lines[j].count("}")
            if depth <= 0 and j > i0:
                end = j; break
        if end is None:
            end = len(lines)
        cap_ind = "\t" * (ind + 1)
        for j in range(i0 + 1, end):
            s = lines[j]
            if s.startswith(cap_ind) and s.strip().startswith("capital"):
                m2 = re.search(r"capital\s*=\s*(c_[a-z0-9_-]+)", s)
                if m2:
                    lines[j] = cap_ind + "capital = " + new
                    done.add(k)
                    break
    io.open(LTD, "w", encoding="utf-8", newline="").write("\n".join(lines))
    # 恢复 BOM
    raw = io.open(LTD, "rb").read()
    if not raw.startswith(b"\xef\xbb\xbf"):
        io.open(LTD, "wb").write(b"\xef\xbb\xbf" + raw)
    print("已写入 %d 个首府改动（备份 %s）" % (len(done), bak))
    return done


if __name__ == "__main__":
    import sys
    changes, cur = full_changes()
    print("拟改动 %d 个；当前值 -> 新值：" % len(changes))
    for k in sorted(changes):
        new, how, note = changes[k]
        print("  %-26s %-22s -> %-26s [%s] %s" % (k, cur[k], new, how, note))
    # 仍无法恢复（保持现状）的
    cucap, capb, bprov = cu_data()
    barony2our, cuprov2ourbest = csv_maps()
    occ = our_counties()
    stuck = []
    for k, v in cur.items():
        c = cucap.get(k)
        if not c or k in changes:
            continue
        b = capb.get(c)
        got = False
        if b and b in barony2our and barony2our[b] in occ: got = True
        if not got and b and b in bprov and str(bprov[b]) in cuprov2ourbest and cuprov2ourbest[str(bprov[b])] in occ: got = True
        if not got:
            stuck.append((k, v, c, b))
    print("\n其余保持现状 %d 个（其中 %d 个 cur==cu 本就正确，余下为 CU 首府县不在覆盖内）：" % (len(stuck), sum(1 for x in stuck if x[1] == x[2])))
    bad = [x for x in stuck if x[1] != x[2]]
    for k, v, c, b in sorted(bad):
        print("  %-26s cur=%-22s cu=%-16s barony=%s  (覆盖外)" % (k, v, c, b))
    if len(sys.argv) > 1 and sys.argv[1] == "--apply":
        apply_changes(changes)
