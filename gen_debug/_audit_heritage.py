# -*- coding: utf-8 -*-
"""只读：把 1895 个新文化按 heritage 分组，并统计各自 name_list 里的 cul_ 键数。"""
import io, os, re, collections

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
VAN = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"

cult_file = os.path.join(MOD, "common", "culture", "cultures", "00_generated_cultures.txt")
nl_file = os.path.join(MOD, "common", "culture", "name_lists", "00_generated_name_lists.txt")

def blocks(path):
    """返回 [(key, [行])]，按大括号深度切顶层块。"""
    out, cur, depth, key = [], None, 0, None
    for line in io.open(path, encoding="utf-8-sig", errors="replace"):
        if cur is None:
            m = re.match(r'^([A-Za-z0-9_]+)\s*=\s*\{', line)
            if m:
                cur, key, depth = [line], m.group(1), line.count("{") - line.count("}")
                if depth == 0:
                    out.append((key, cur)); cur = None
            continue
        cur.append(line)
        depth += line.count("{") - line.count("}")
        if depth <= 0:
            out.append((key, cur)); cur = None
    return out

van_cult = set()
vdir = os.path.join(VAN, "common", "culture", "cultures")
for fn in os.listdir(vdir):
    if fn.endswith(".txt"):
        for k, _ in blocks(os.path.join(vdir, fn)):
            van_cult.add(k)

cult_blocks = blocks(cult_file)
new_cult = [(k, b) for k, b in cult_blocks if k not in van_cult]
print("我们的文化块 %d / 新文化 %d" % (len(cult_blocks), len(new_cult)))

her = {}
for k, b in new_cult:
    h = ""
    for ln in b:
        m = re.match(r'^\s*heritage\s*=\s*([A-Za-z0-9_]+)', ln)
        if m:
            h = m.group(1); break
    her[k] = h

# 每文化的 name_list 引用
nl_ref = {}
for k, b in new_cult:
    for ln in b:
        m = re.match(r'^\s*name_list\s*=\s*([A-Za-z0-9_-]+)', ln)
        if m:
            nl_ref[k] = m.group(1); break

nl_blocks = {k: b for k, b in blocks(nl_file)}
def cul_keys(nlkey):
    s = set()
    for ln in nl_blocks.get(nlkey, []):
        s |= set(re.findall(r'\bcul_[A-Za-z0-9_-]+', ln))
    return s

cnt = collections.Counter(her.values())
print("\nheritage 分布（新文化）:")
for h, n in cnt.most_common():
    print("  %-32s %4d" % (h or "(无)", n))

total_keys = set()
for k, _ in new_cult:
    total_keys |= cul_keys(nl_ref.get(k, ""))
print("\n新文化引用到的 cul_ 键总数: %d" % len(total_keys))
