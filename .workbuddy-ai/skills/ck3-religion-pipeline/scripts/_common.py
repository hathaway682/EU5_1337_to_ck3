# -*- coding: utf-8 -*-
"""省份史文件的字节级读写（BOM + CRLF 安全）。

`history/provinces/00_generated_provinces.txt` 是**纯 CRLF + UTF-8 BOM**。
用 `newline=""` 或默认文本模式读会踩两个坑：
  * 默认文本模式会把 CRLF 翻译成 LF，写回去就变成混行尾；
  * `newline=""` 读进来的每行尾带 `\r`，`^(\\d+) = \\{$` 匹配不上，统计全空。

这里的做法是：按字节读 → 判断行尾符 → 用该行尾符 split → 处理完按该行尾符 join
→ 按字节写（BOM 单独拼）。全程不做换行翻译。
"""
import io
import os
import re

_HERE = os.path.abspath(__file__)
# scripts -> ck3-religion-pipeline -> skills -> .workbuddy-ai -> mod 根
MOD = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(_HERE)))))
PROV = os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt")
FAITH_TYPES = os.path.join(MOD, "common", "religion", "faith_types", "00_faith_types.txt")
RITE_DIR = os.path.join(MOD, "common", "religion", "rite_types")
LANDED = os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt")
LOC_ZH = os.path.join(MOD, "localization", "simp_chinese")
VANILLA = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"
VANILLA_LOC_ZH = os.path.join(VANILLA, "localization", "simp_chinese")

BOM = "\ufeff"
BLOCK_OPEN = re.compile(r"^(\d+) = \{\s*$")
FAITH_LINE = re.compile(r"^(\s*)faith = (\S+)\s*$")
RITE_LINE = re.compile(r"^(\s*)rite = (\S+)\s*$")
COUNTY_LINE = re.compile(r"^(\s*)culture = (\S+)\s*$")


# ---------------------------------------------------------------- 读写

def read_prov(path=None):
    """-> (lines, sep)。lines 不含行尾符，sep 是实际行尾符（'\\r\\n' 或 '\\n'）。"""
    path = path or PROV
    raw = io.open(path, "rb").read()
    text = raw.decode("utf-8-sig")
    sep = "\r\n" if b"\r\n" in raw else "\n"
    return text.split(sep), sep


def write_prov(lines, sep, path=None):
    """按字节写回，BOM 保留。写前不备份（调用方负责）。"""
    path = path or PROV
    io.open(path, "wb").write((BOM + sep.join(lines)).encode("utf-8"))


def byte_stats(path=None):
    """体检用：BOM / 行尾符 / 括号。"""
    path = path or PROV
    raw = io.open(path, "rb").read()
    text = raw.decode("utf-8-sig")
    return {
        "bytes": len(raw),
        "bom": raw.startswith(b"\xef\xbb\xbf"),
        "crlf": raw.count(b"\r\n"),
        "lf": raw.count(b"\n"),
        "lone_lf": raw.count(b"\n") - raw.count(b"\r\n"),
        "open": text.count("{"),
        "close": text.count("}"),
    }


# ---------------------------------------------------------------- 块解析

def iter_blocks(lines):
    """yield (pid, body_lines, close_index)。非省块行 yield (None, [line], i)。"""
    i, n = 0, len(lines)
    while i < n:
        m = BLOCK_OPEN.match(lines[i])
        if not m:
            yield None, [lines[i]], i
            i += 1
            continue
        pid = int(m.group(1))
        j = i + 1
        body = []
        while j < n and lines[j].strip() != "}":
            body.append(lines[j])
            j += 1
        yield pid, body, j
        i = j + 1


def parse_state(lines):
    """-> (faith{pid: val}, rite{pid: val})，每块只取第一条。"""
    faith, rite = {}, {}
    for pid, body, _ in iter_blocks(lines):
        if pid is None:
            continue
        for line in body:
            m = FAITH_LINE.match(line)
            if m and pid not in faith:
                faith[pid] = m.group(2)
                continue
            m = RITE_LINE.match(line)
            if m and pid not in rite:
                rite[pid] = m.group(2)
    return faith, rite


# ---------------------------------------------------------------- 定义表

def blocks(txt):
    """`key = { ... }` 顶层块 -> [(key, body)]，用括号计数切，不依赖缩进。"""
    out = []
    for m in re.finditer(r"(?m)^([A-Za-z0-9_\.\-]+)\s*=\s*\{", txt):
        key, i, d = m.group(1), m.end() - 1, 0
        for j in range(i, len(txt)):
            if txt[j] == "{":
                d += 1
            elif txt[j] == "}":
                d -= 1
                if d == 0:
                    out.append((key, txt[i:j + 1]))
                    break
    return out


def load_faiths(path=None):
    """-> {faith: {'main_rite': ..., 'religion': ...}}

    religion 取自 `faith_details = { religion = xxx }`。判断一个 rite 能不能挂到某个省，
    要看**两者 religion 是否相同**，而不是 faith 是否相同 —— vanilla 的基督教就是
    9 个 rite 全绑在伞形 faith `christian_faith` 上，而省份写的是 orthodox / catholic。
    """
    path = path or FAITH_TYPES
    txt = io.open(path, encoding="utf-8-sig", errors="ignore").read()
    out = {}
    for k, b in blocks(txt):
        mr = re.search(r"(?m)^\s*main_rite\s*=\s*([A-Za-z0-9_\.\-]+)", b)
        rg = re.search(r"(?m)^\s*religion\s*=\s*([A-Za-z0-9_\.\-]+)", b)
        out[k] = {"main_rite": mr.group(1) if mr else None,
                  "religion": rg.group(1) if rg else None}
    return out


def load_rites():
    """-> {rite: {'faith': 父faith, 'file': 定义所在文件名}}"""
    out = {}
    for fn in sorted(os.listdir(RITE_DIR)):
        if not fn.endswith(".txt"):
            continue
        txt = io.open(os.path.join(RITE_DIR, fn), encoding="utf-8-sig",
                      errors="ignore").read()
        for k, b in blocks(txt):
            m = re.search(r"(?m)^\s*faith\s*=\s*([A-Za-z0-9_\.\-]+)", b)
            out.setdefault(k, {"faith": m.group(1) if m else None, "file": fn})
    return out


def load_prov_county(path=None):
    """-> {province_id: county_key}，栈解析 landed_titles。"""
    path = path or LANDED
    out = {}
    for fn in sorted(os.listdir(os.path.dirname(path))):
        if not fn.endswith(".txt"):
            continue
        stack = []
        p = os.path.join(os.path.dirname(path), fn)
        for line in io.open(p, encoding="utf-8-sig", errors="ignore"):
            m = re.match(r"^(\t*)([cedkb]_[A-Za-z_0-9]+)\s*=\s*\{", line)
            if m:
                ind = len(m.group(1))
                stack = [s for s in stack if s[1] < ind]
                stack.append((m.group(2), ind))
                continue
            pm = re.match(r"^\s*province\s*=\s*(\d+)", line)
            if pm and stack and stack[-1][0].startswith("b_"):
                cs = [k for k, _ in stack if k.startswith("c_")]
                if cs:
                    out.setdefault(int(pm.group(1)), cs[-1])
    return out


def county_provinces(path=None):
    """-> {county_key: [province_id, ...]}"""
    out = {}
    for p, c in load_prov_county(path).items():
        out.setdefault(c, []).append(p)
    for c in out:
        out[c].sort()
    return out


# ---------------------------------------------------------------- 本地化

def load_loc_zh():
    """mod + 原版的中文本地化 -> {key: 中文}。原版优先度低，不覆盖 mod。"""
    out = {}
    for root_dir in (VANILLA_LOC_ZH, LOC_ZH):
        if not os.path.isdir(root_dir):
            continue
        for root, _, fs in os.walk(root_dir):
            for fn in fs:
                if not fn.endswith(".yml"):
                    continue
                try:
                    lines = io.open(os.path.join(root, fn), encoding="utf-8-sig",
                                    errors="ignore")
                except OSError:
                    continue
                for line in lines:
                    m = re.match(r'\s*([a-zA-Z0-9_\.\-]+):\d*\s*"([^"]*)"', line)
                    if m:
                        out[m.group(1)] = m.group(2)
    return out
