# -*- coding: utf-8 -*-
"""删掉我们生成的、与原版 CK3 同名的 name_list 块。

这些块没有任何我方文化引用（唯一例外 bobo，它的文化块也引用 name_list_bobo），
却因为 key 与原版同名而覆盖了原版名字池，导致原版文化（法国、丹麦、英格兰……）
用上我们程序化生成的 cul_ 键人名。

删块后原版同名 name_list 生效，文化引用不变。
幂等：块已不存在则跳过。保留 BOM + CRLF。
"""
import io, os, re, sys

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
# 基准用 Beta 版：它是正式版的超集（正式版独有的 name_list 为空），
# 且项目其余 beta_* 审计也以它为原版口径。
VAN = r"D:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III Beta\game"

NL = os.path.join(MOD, "common", "culture", "name_lists", "00_generated_name_lists.txt")

def top_keys(path):
    out = set()
    for line in io.open(path, encoding="utf-8-sig", errors="replace"):
        m = re.match(r'^([A-Za-z0-9_]+)\s*=\s*\{', line)
        if m:
            out.add(m.group(1))
    return out

van_nl = set()
ndir = os.path.join(VAN, "common", "culture", "name_lists")
for fn in os.listdir(ndir):
    if fn.endswith(".txt"):
        van_nl |= top_keys(os.path.join(ndir, fn))

raw = io.open(NL, encoding="utf-8-sig", newline="").read()
lines = raw.split("\r\n")

drop = set()
for line in lines:
    m = re.match(r'^(name_list_[A-Za-z0-9_-]+)\s*=\s*\{', line)
    if m and m.group(1) in van_nl:
        drop.add(m.group(1))

if not drop:
    print("没有可删的块，已是最新状态。")
    sys.exit(0)

print("待删块 %d 个:" % len(drop))
for k in sorted(drop):
    print("   ", k)

out = []
i = 0
removed = 0
while i < len(lines):
    line = lines[i]
    m = re.match(r'^(name_list_[A-Za-z0-9_-]+)\s*=\s*\{', line)
    if m and m.group(1) in drop:
        depth = line.count("{") - line.count("}")
        i += 1
        while i < len(lines) and depth > 0:
            depth += lines[i].count("{") - lines[i].count("}")
            i += 1
        # 吃掉块后紧跟的一个空行，避免留下双空行
        if i < len(lines) and lines[i].strip() == "":
            i += 1
        removed += 1
        continue
    out.append(line)
    i += 1

print("实际删除块: %d" % removed)
with io.open(NL, "w", encoding="utf-8", newline="") as fp:
    fp.write("\ufeff" + "\r\n".join(out))
print("已写回", NL)
