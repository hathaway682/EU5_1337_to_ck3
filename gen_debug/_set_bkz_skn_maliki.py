# -*- coding: utf-8 -*-
"""把 BKZ / SKN 两家的角色从 shia 改成 sunni + maliki（马立克派）。

用户 2026-10-22 01:52 定：「他们暂时改成马立克派，省的马穆鲁克天天拔他们头衔」。
理由：马穆鲁克（MAM）是 sunni/shafii，什叶附庸会被反复拔头衔；改成马立克派同属逊尼，
不再触发异教拔头衔。**只改角色，不改省份**（省份仍按人口多数保持 shia）。

默认 dry-run，加 --apply 才写盘（先备份，保 BOM 与 CRLF）。
"""
import io, os, re, shutil, sys, time

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
SRC = os.path.join(MOD, "history", "characters", "zz_eu5_characters.txt")
APPLY = "--apply" in sys.argv

TARGETS = {
    "bkz_alam_al_din_ali",
    "bkz_daughter_nasr",
    "bkz_rukn_al_din_al_husayn",
    "bkz_sayf_al_din_abu_abdallah_muhammad",
    "bkz_shujah_al_din_nasr",
    "bkz_umm_al_hayr",
    "skn_zayd_ibn_abi_numayy_ibn_ajlan",
}

BOM = "\ufeff"
BLOCK = re.compile(r"^([A-Za-z0-9_]+) = \{\s*$")
REL = re.compile(r"^(\s*)religion = (\S+)\s*$")
RITE = re.compile(r"^(\s*)rite = (\S+)\s*$")

raw = io.open(SRC, "rb").read()
text = raw.decode("utf-8-sig")
sep = "\r\n" if b"\r\n" in raw else "\n"
lines = text.split(sep)

out = []
cur = None
depth = 0
touched = {}
for line in lines:
    m = BLOCK.match(line)
    if m and depth == 0:
        cur = m.group(1)
        depth = 1
        out.append(line)
        continue
    if cur is not None:
        depth += line.count("{") - line.count("}")
        if depth <= 0:
            cur = None
            depth = 0
            out.append(line)
            continue
        if cur in TARGETS:
            mr = REL.match(line)
            if mr:
                old = mr.group(2)
                new = "sunni"
                touched.setdefault(cur, {"old": old, "rite": None})
                out.append("%sreligion = %s" % (mr.group(1), new))
                out.append("%srite = maliki" % mr.group(1))
                touched[cur]["rite"] = "maliki"
                continue
            mt = RITE.match(line)
            if mt:
                # 已有 rite 行就不重复插
                touched.setdefault(cur, {"old": "?", "rite": None})
                out.append("%srite = maliki" % mt.group(1))
                touched[cur]["rite"] = "maliki"
                continue
    out.append(line)

print("目标角色 %d 个，实际命中 %d 个：" % (len(TARGETS), len(touched)))
for k in sorted(touched):
    print("   %-46s %s -> sunni / rite = maliki" % (k, touched[k]["old"]))

missing = TARGETS - set(touched)
if missing:
    print("未命中（不存在或没有 religion 行）：", sorted(missing))

new_text = sep.join(out)
if new_text == text:
    print("\n无变化。")
    sys.exit(0)
if not APPLY:
    print("\n[dry-run] 未写盘。加 --apply 执行。")
    sys.exit(0)

stamp = time.strftime("%Y%m%d_%H%M%S")
bak = SRC + ".bak_bkzskn_" + stamp
shutil.copy2(SRC, bak)
io.open(SRC, "wb").write((BOM + new_text).encode("utf-8"))
chk = io.open(SRC, "rb").read()
print("\n已写入。备份 -> %s" % os.path.basename(bak))
print("校验: CRLF=%d LF=%d BOM=%s braces %d/%d"
      % (chk.count(b"\r\n"), chk.count(b"\n"), chk[:3] == b"\xef\xbb\xbf",
         chk.count(b"{"), chk.count(b"}")))
