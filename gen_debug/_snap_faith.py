# -*- coding: utf-8 -*-
"""faith 快照 / 还原。

用法：
    python _snap_faith.py snap    -> 写 _faith_snapshot.json
    python _snap_faith.py restore -> 按快照把 faith 行改回去（只改不一致的行）

用途：本次只重算 rite，faith 是前几轮（人口多数 + CU 男爵领回填）定稿的结果，
不能被 rite 生成链里附带写 faith 的分支（如 BOS -> bosnian_church）覆盖。
"""
import io, os, re, json, sys, time

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
SRC = os.path.join(MOD, "history/provinces/00_generated_provinces.txt")
SNAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_faith_snapshot.json")


def parse(txt):
    out = {}
    for m in re.finditer(r"(?m)^(\d+) = \{(.*?)\n\}", txt, re.S):
        f = re.search(r"(?m)^\s*faith = (\S+)", m.group(2))
        if f:
            out[int(m.group(1))] = f.group(1)
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "snap"
    txt = io.open(SRC, encoding="utf-8-sig", newline="").read()

    if mode == "snap":
        d = parse(txt)
        io.open(SNAP, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))
        print("snapshot: %d provinces -> %s" % (len(d), SNAP))
        return

    snap = json.load(io.open(SNAP, encoding="utf-8"))
    snap = {int(k): v for k, v in snap.items()}
    lines = txt.split("\n")
    out = []
    cur = None
    changed = 0
    missing = 0
    for line in lines:
        m = re.match(r"^(\d+) = \{$", line)
        if m:
            cur = int(m.group(1))
            out.append(line)
            continue
        fm = re.match(r"^(\s*)faith = (\S+)\s*$", line)
        if fm and cur is not None and cur in snap:
            want = snap[cur]
            if fm.group(2) != want:
                out.append("%sfaith = %s" % (fm.group(1), want))
                changed += 1
                continue
        elif fm and cur is not None and cur not in snap:
            missing += 1
        out.append(line)
    res = "\n".join(out)
    if res == txt:
        print("faith 无变化")
    else:
        stamp = time.strftime("%Y%m%d_%H%M%S")
        bak = SRC + ".bak_faithrestore_" + stamp
        io.open(bak, "w", encoding="utf-8-sig", newline="\n").write(txt)
        io.open(SRC, "w", encoding="utf-8-sig", newline="\n").write(res)
        print("faith 还原 %d 行；备份 -> %s" % (changed, os.path.basename(bak)))
    print("快照外的新 province: %d" % missing)
    print("braces:", res.count("{"), res.count("}"))


main()
