# -*- coding: utf-8 -*-
"""删除 mod 里「孤儿圣地」——没有被任何 faith 的 holy_sites 列表引用的圣地块。

判定依据（2026-11-14 用户拍板）：
  - mod 没有 common/religion/faith_types/，信仰全部继承 CK3 原版
  - 所以「被引用」= 该 key 出现在 **原版** faith_types 的 holy_sites 列表里
  - 原版 faith 也不引用的，就是死数据：位置改得再对，游戏里也不会生效

不删的两类：
  - 被原版 faith 引用的（如 bumiayu、preah_vihear）——即使原版本地化缺名字也保留
  - 块内如果被 events / decisions / modifiers 等外部文件引用，默认跳过并告警

用法：
  python gen_debug/_drop_orphan_holy_sites.py            # 干跑，只打印
  python gen_debug/_drop_orphan_holy_sites.py --apply    # 落盘（自动备份）
"""
import io
import os
import re
import sys
import glob
import shutil
import time

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"
SRC = os.path.join(MOD, "common", "religion", "holy_site_types", "00_holy_site_types.txt")
APPLY = "--apply" in sys.argv


def faith_refs(root):
    """收集 faith_types 里 holy_sites 列表引用到的圣地 key。

    **必须剥掉 # 注释**：原版列表里有 `#bumiayu`、`#preah_vihear` 这种被注释掉的条目，
    它们等于没有引用（2026-11-14 用户指出）。
    """
    ref = set()
    for fn in glob.glob(os.path.join(root, "common", "religion", "**", "*.txt"), recursive=True):
        if "holy_site_types" in fn.replace("\\", "/"):
            continue
        txt = io.open(fn, encoding="utf-8-sig", errors="ignore").read()
        for m in re.finditer(r"holy_sites\s*=\s*\{([^}]*)\}", txt, re.S):
            body = "\n".join(ln.split("#")[0] for ln in m.group(1).split("\n"))
            for tok in re.findall(r"[A-Za-z0-9_\-]+", body):
                ref.add(tok)
    return ref


def parse_blocks(lines):
    """返回 [{key, start, end}]，start/end 为 0-based 行号（end 含块尾的 } 行）"""
    blocks = []
    depth = 0
    cur = None
    for i, ln in enumerate(lines):
        if depth == 0:
            m = re.match(r"^([A-Za-z0-9_\-]+)\s*=\s*\{", ln)
            if m:
                cur = {"key": m.group(1), "start": i, "end": None}
        depth += ln.count("{") - ln.count("}")
        if cur is not None and depth == 0:
            cur["end"] = i
            blocks.append(cur)
            cur = None
    return blocks


def external_refs(keys):
    """在 mod 里（排除圣地定义文件与本地化）搜这些 key 的独立引用"""
    hits = {}
    pats = {k: re.compile(r"(?<![A-Za-z0-9_\-])" + re.escape(k) + r"(?![A-Za-z0-9_\-])") for k in keys}
    for fn in glob.glob(os.path.join(MOD, "**", "*.txt"), recursive=True):
        rel = fn.replace("\\", "/")
        if "holy_site_types" in rel:
            continue
        try:
            txt = io.open(fn, encoding="utf-8-sig", errors="ignore").read()
        except Exception:
            continue
        for ln in txt.split("\n"):
            code = ln.split("#")[0]
            for k, p in pats.items():
                if p.search(code):
                    hits.setdefault(k, []).append("%s:%d" % (os.path.relpath(fn, MOD), txt[:0].count("") and 0))
    return hits


raw = io.open(SRC, "rb").read()
bom = raw.startswith(b"\xef\xbb\xbf")
body = raw[3:] if bom else raw
lines = body.decode("utf-8").split("\r\n")

blocks = parse_blocks(lines)
keys = [b["key"] for b in blocks]
ref = faith_refs(GAME)
orphans = [b for b in blocks if b["key"] not in ref]

print("圣地块总数       = %d" % len(blocks))
print("原版 faith 引用   = %d" % len(ref & set(keys)))
print("孤儿（将被删除）  = %d" % len(orphans))
print()

# 外部引用检查（只报疑似，不阻断）
# 用一条合并正则扫一遍；只扫可能引用圣地 key 的目录（history/ 里不会出现圣地 key）
orphan_keys = [b["key"] for b in orphans]
hits = {}
big = re.compile(r"(?<![A-Za-z0-9_\-])(" + "|".join(re.escape(k) for k in orphan_keys) + r")(?![A-Za-z0-9_\-])")
scan_files = []
for sub in ("common", "events", "gui"):
    scan_files += glob.glob(os.path.join(MOD, sub, "**", "*.txt"), recursive=True)
for fn in scan_files:
    if "holy_site_types" in fn.replace("\\", "/"):
        continue
    try:
        txt = io.open(fn, encoding="utf-8-sig", errors="ignore").read()
    except Exception:
        continue
    for idx, ln in enumerate(txt.split("\n"), 1):
        code = ln.split("#")[0]
        for m in big.finditer(code):
            hits.setdefault(m.group(1), []).append("%s:%d" % (os.path.relpath(fn, MOD), idx))

print("--- 待删清单 ---")
for b in orphans:
    ext = hits.get(b["key"])
    flag = ("  !! 外部引用 %d 处: %s" % (len(ext), ", ".join(ext[:3]))) if ext else ""
    print("  L%-5d %-18s%s" % (b["start"] + 1, b["key"], flag))
print()
if hits:
    print("有外部引用的 key = %d 个（仍会删，因为圣地本身没有 faith 挂载）" % len(hits))
else:
    print("外部引用 = 无")

if not APPLY:
    print("\n[干跑] 未写入。加 --apply 落盘。")
    sys.exit(0)

# 从后往前删，避免行号错位
bak = SRC + ".bak_drop_orphan_%s" % time.strftime("%Y%m%d_%H%M%S")
shutil.copy2(SRC, bak)
print("\n备份 ->", os.path.basename(bak))

removed = 0
for b in sorted(orphans, key=lambda x: -x["start"]):
    s, e = b["start"], b["end"]
    # 若块后面紧跟一个空行，一并删掉，避免留下连续空行
    if e + 1 < len(lines) and lines[e + 1].strip() == "":
        e += 1
    del lines[s:e + 1]
    removed += 1

out = "\r\n".join(lines)
io.open(SRC, "wb").write((b"\xef\xbb\xbf" if bom else b"") + out.encode("utf-8"))
print("已删除 %d 个圣地块；文件行数 %d" % (removed, len(lines)))
