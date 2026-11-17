# -*- coding: utf-8 -*-
"""只读勘察：我们的 name_list 块 vs 原版 CK3 文化/name_list。

输出三类：
  A. 我们的块 key 与原版 name_list key 重名 -> 顶掉原版
  B. 我们的文化 key 在原版不存在 -> 新文化（需要本地化）
  C. 孤儿块（没有文化引用）
"""
import io, os, re, collections

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
VAN = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"

def top_keys(path, key_re=r'^([A-Za-z0-9_]+)\s*=\s*\{'):
    out = set()
    for line in io.open(path, encoding="utf-8-sig", errors="replace"):
        m = re.match(key_re, line)
        if m:
            out.add(m.group(1))
    return out

# 原版文化（多个文件，顶层 key）
van_cult = set()
vdir = os.path.join(VAN, "common", "culture", "cultures")
for fn in os.listdir(vdir):
    if fn.endswith(".txt"):
        van_cult |= top_keys(os.path.join(vdir, fn))

# 原版 name_list
van_nl = set()
ndir = os.path.join(VAN, "common", "culture", "name_lists")
for fn in os.listdir(ndir):
    if fn.endswith(".txt"):
        van_nl |= top_keys(os.path.join(ndir, fn))

# 我们的文化
our_cult_file = os.path.join(MOD, "common", "culture", "cultures", "00_generated_cultures.txt")
our_cult = top_keys(our_cult_file)

# 我们的 name_list 块 + 被引用
nl_file = os.path.join(MOD, "common", "culture", "name_lists", "00_generated_name_lists.txt")
our_nl = top_keys(nl_file)
txt = io.open(our_cult_file, encoding="utf-8-sig", errors="replace").read()
used = set(re.findall(r'name_list\s*=\s*([A-Za-z0-9_-]+)', txt))

print("原版文化 %d / 原版 name_list %d" % (len(van_cult), len(van_nl)))
print("我们文化 %d / 我们 name_list 块 %d / 被引用 %d" % (len(our_cult), len(our_nl), len(used)))

overlap = our_nl & van_nl
print("\n[A] 我们的块 key 与原版 name_list 重名（顶掉原版）: %d" % len(overlap))
for k in sorted(overlap):
    print("   ", k)

orphan = our_nl - used
print("\n[C] 孤儿块（无文化引用）: %d" % len(orphan))
print("     其中与原版重名: %d / 不重名: %d" % (len(orphan & van_nl), len(orphan - van_nl)))

new_cult = our_cult - van_cult
print("\n[B] 我们的文化在原版不存在（新文化）: %d" % len(new_cult))
old_cult = our_cult & van_cult
print("    我们的文化与原版同名: %d" % len(old_cult))
print("    同名样例:", sorted(old_cult)[:20])

# 新文化的 name_list 引用
used_by_new = set()
for m in re.finditer(r'^([A-Za-z0-9_]+)\s*=\s*\{', txt, re.M):
    pass
print("\n新文化样例:", sorted(new_cult)[:15])
