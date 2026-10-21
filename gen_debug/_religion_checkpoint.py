# -*- coding: utf-8 -*-
"""宗教地图保存点 / 一键还原（含 faith + rite）。

管 `history/provinces/00_generated_provinces.txt` 里每个省份的 `faith` 和 `rite`。
CK3 的宗教地图模式按 faith 上色，`rite` 决定显示哪个教会/学派，两者都是宗教状态。

用法：
    python _religion_checkpoint.py save [标签]
        在当前状态下打一个保存点，存到 gen_debug/religion_checkpoints/
        文件名 faith_<时间戳>[_标签].json
        结构 {"format": 2, "created": ..., "faith": {ID: faith}, "rite": {ID: rite}}

    python _religion_checkpoint.py list
        列出所有保存点

    python _religion_checkpoint.py restore latest            # 干跑
    python _religion_checkpoint.py restore latest --apply    # 真写
    python _religion_checkpoint.py restore faith_20261022_0130.json --apply
    python _religion_checkpoint.py restore latest --apply --faith-only   # 只还原 faith

还原原则（外科手术式）：
  - `faith =` 行：只改与快照不一致的省份，其它行原样保留；
  - `rite =` 行：快照有值就改成快照值（块里没有就补一行，位置紧跟 faith 行）；
    快照里没有 rite 的省份，文件里若多出 `rite =` 行就删掉；
  - culture / holding / 注释等其它行一个字节都不动；
  - 文件里新增、快照里没有的省份完全不动，只报数量；
  - 内容无变化就不写盘（连 mtime 都不动）；
  - 写盘前备份，保留原文件的 BOM 与 CRLF 行尾（按字节读写，不做换行翻译）。

兼容：format 1（老快照，扁平 {ID: faith}）只还原 faith，不动 rite——
因为老快照里「没有 rite 字段」不等于「当时没有 rite 行」。
"""
import io, json, os, re, sys, time
from collections import Counter

GEN = os.path.dirname(os.path.abspath(__file__))
MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
SRC = os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt")
SNAPDIR = os.path.join(GEN, "religion_checkpoints")

BOM = "\ufeff"
BLOCK = re.compile(r"^(\d+) = \{\s*$")
FAITH = re.compile(r"^(\s*)faith = (\S+)\s*$")
RITE = re.compile(r"^(\s*)rite = (\S+)\s*$")


def read_text(path):
    """读成 (正文, 行尾符)。正文不含 BOM，行尾符按实际内容判断。"""
    raw = io.open(path, "rb").read()
    text = raw.decode("utf-8-sig")
    sep = "\r\n" if b"\r\n" in raw else "\n"
    return text, sep


def write_text(path, text):
    """text 已经是用目标行尾符拼好的，直接按字节写，不做任何换行翻译。"""
    io.open(path, "wb").write((BOM + text).encode("utf-8"))


def iter_blocks(lines):
    """yield (pid, body_lines, close_line)。块 = `123 = {` ... `}`，body 不含两端。"""
    i, n = 0, len(lines)
    while i < n:
        m = BLOCK.match(lines[i])
        if not m:
            yield None, [lines[i]], None
            i += 1
            continue
        pid = int(m.group(1))
        j = i + 1
        body = []
        while j < n and lines[j].strip() != "}":
            body.append(lines[j])
            j += 1
        close = lines[j] if j < n else "}"
        yield pid, body, close
        i = j + 1


def parse_state(text, sep):
    """-> (faith{}, rite{})，只取每个省份块内第一条 faith / rite。"""
    faith, rite = {}, {}
    for pid, body, _close in iter_blocks(text.split(sep)):
        if pid is None:
            continue
        for line in body:
            m = FAITH.match(line)
            if m and pid not in faith:
                faith[pid] = m.group(2)
                continue
            m = RITE.match(line)
            if m and pid not in rite:
                rite[pid] = m.group(2)
    return faith, rite


def load_snap(path):
    """-> (faith{}, rite{}, has_rite_data)。老格式只给 faith。"""
    obj = json.load(io.open(path, encoding="utf-8"))
    if isinstance(obj, dict) and obj.get("format") == 2:
        return ({int(k): v for k, v in obj.get("faith", {}).items()},
                {int(k): v for k, v in obj.get("rite", {}).items()},
                True)
    return ({int(k): v for k, v in obj.items()}, {}, False)


def cmd_save(label):
    text, sep = read_text(SRC)
    faith, rite = parse_state(text, sep)
    os.makedirs(SNAPDIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    name = "faith_%s%s.json" % (stamp, ("_" + label) if label else "")
    path = os.path.join(SNAPDIR, name)
    obj = {
        "format": 2,
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "faith": {str(k): faith[k] for k in sorted(faith)},
        "rite": {str(k): rite[k] for k in sorted(rite)},
    }
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=0))
    print("保存点已写入: %s" % path)
    print("省份数: %d（有 faith %d / 有 rite %d）" % (len(set(faith) | set(rite)),
                                                  len(faith), len(rite)))
    print("faith 种类: %d" % len(set(faith.values())))
    for k, v in Counter(faith.values()).most_common(10):
        print("   %-28s %d" % (k, v))
    if len(set(faith.values())) > 10:
        print("   ...（共 %d 种）" % len(set(faith.values())))
    print("rite 种类: %d" % len(set(rite.values())))
    for k, v in Counter(rite.values()).most_common(10):
        print("   %-28s %d" % (k, v))
    if len(set(rite.values())) > 10:
        print("   ...（共 %d 种）" % len(set(rite.values())))


def cmd_list():
    if not os.path.isdir(SNAPDIR):
        print("还没有任何保存点。")
        return
    names = sorted(n for n in os.listdir(SNAPDIR) if n.endswith(".json"))
    if not names:
        print("还没有任何保存点。")
        return
    for n in names:
        p = os.path.join(SNAPDIR, n)
        try:
            f, r, ok = load_snap(p)
            info = "%d 省 / faith %d 种 / rite %d 种" % (
                len(set(f) | set(r)), len(set(f.values())), len(set(r.values())))
            if not ok:
                info += "（老格式，无 rite）"
        except Exception as e:
            info = "读取失败: %s" % e
        print("%-44s %-40s %s" % (n, info,
                                  time.strftime("%Y-%m-%d %H:%M:%S",
                                                time.localtime(os.path.getmtime(p)))))


def resolve(name):
    if name == "latest":
        if not os.path.isdir(SNAPDIR):
            sys.exit("还没有任何保存点。")
        names = sorted(n for n in os.listdir(SNAPDIR) if n.endswith(".json"))
        if not names:
            sys.exit("还没有任何保存点。")
        return os.path.join(SNAPDIR, names[-1])
    if os.path.isfile(name):
        return name
    p = os.path.join(SNAPDIR, name)
    if os.path.isfile(p):
        return p
    sys.exit("找不到保存点: %s" % name)


def cmd_restore(name, apply, faith_only):
    path = resolve(name)
    snap_f, snap_r, has_rite_data = load_snap(path)
    do_rite = has_rite_data and not faith_only
    text, sep = read_text(SRC)
    lines = text.split(sep)

    out = []
    seen_f, seen_r = set(), set()
    ch_f, ch_r, add_r, del_r = [], [], [], []

    for pid, body, close in iter_blocks(lines):
        if pid is None:
            out.extend(body)
            continue
        out.append("%d = {" % pid)
        if pid not in snap_f:
            # 快照里没有这个省：完全不动
            out.extend(body)
            if close is not None:
                out.append(close)
            continue

        want_f = snap_f.get(pid)
        want_r = snap_r.get(pid) if do_rite else None
        new_body = []
        faith_idx = None
        rite_done = False
        for line in body:
            mf = FAITH.match(line)
            if mf:
                seen_f.add(pid)
                if want_f is not None and mf.group(2) != want_f:
                    ch_f.append((pid, mf.group(2), want_f))
                    line = "%sfaith = %s" % (mf.group(1), want_f)
                faith_idx = len(new_body)
                new_body.append(line)
                continue
            mr = RITE.match(line)
            if mr:
                seen_r.add(pid)
                if do_rite:
                    if want_r is None:
                        del_r.append((pid, mr.group(2)))
                        continue
                    rite_done = True
                    if mr.group(2) != want_r:
                        ch_r.append((pid, mr.group(2), want_r))
                        line = "%srite = %s" % (mr.group(1), want_r)
                new_body.append(line)
                continue
            new_body.append(line)

        if do_rite and want_r is not None and not rite_done:
            indent = "    "
            if faith_idx is not None:
                indent = FAITH.match(new_body[faith_idx]).group(1)
            pos = (faith_idx + 1) if faith_idx is not None else len(new_body)
            new_body.insert(pos, "%srite = %s" % (indent, want_r))
            add_r.append((pid, want_r))

        out.extend(new_body)
        if close is not None:
            out.append(close)

    new_text = sep.join(out)
    only_snap = sorted(set(snap_f) - seen_f)
    only_file = sorted(seen_f - set(snap_f))

    print("保存点: %s%s" % (os.path.basename(path),
                          "" if do_rite else "（只还原 faith）"))
    print("快照省份: %d（带 rite %d）/ 文件内省份: %d"
          % (len(snap_f), len(snap_r), len(seen_f)))
    print("faith 需要改回: %d 行" % len(ch_f))
    for (o, n), v in Counter((o, n) for _, o, n in ch_f).most_common(10):
        print("   %-26s -> %-26s %d" % (o, n, v))
    if do_rite:
        print("rite 需要改值: %d 行 / 需要补行: %d / 需要删行: %d"
              % (len(ch_r), len(add_r), len(del_r)))
        for (o, n), v in Counter((o, n) for _, o, n in ch_r).most_common(10):
            print("   改  %-24s -> %-24s %d" % (o, n, v))
        for (n,), v in Counter((r,) for _, r in add_r).most_common(5):
            print("   补  + %-24s (原无 rite)        %d" % (n, v))
        for (n,), v in Counter((r,) for _, r in del_r).most_common(5):
            print("   删  - %-24s (快照无 rite)      %d" % (n, v))
    if only_file:
        print("文件里有、快照里没有（保持原样）: %d 个" % len(only_file))
    if only_snap:
        print("快照里有、文件里找不到（跳过）: %d 个 %s" % (len(only_snap), only_snap[:10]))
    print("braces: %d %d" % (new_text.count("{"), new_text.count("}")))

    total = len(ch_f) + (len(ch_r) + len(add_r) + len(del_r) if do_rite else 0)
    if total == 0:
        print("\n与保存点一致，未写盘。")
        return
    if not apply:
        print("\n[dry-run] 未写盘。加 --apply 执行。")
        return

    stamp = time.strftime("%Y%m%d_%H%M%S")
    bak = SRC + ".bak_relrestore_" + stamp
    io.open(bak, "wb").write(io.open(SRC, "rb").read())
    write_text(SRC, new_text)
    print("\n已还原：faith %d 行、rite %d 行（改 %d / 补 %d / 删 %d）。"
          % (len(ch_f), len(ch_r) + len(add_r) + len(del_r),
             len(ch_r), len(add_r), len(del_r)))
    print("备份 -> %s" % os.path.basename(bak))
    chk = io.open(SRC, "rb").read()
    print("校验: CRLF=%d LF=%d BOM=%s faith=%d rite=%d"
          % (chk.count(b"\r\n"), chk.count(b"\n"), chk[:3] == b"\xef\xbb\xbf",
             len(re.findall(rb"(?m)^\s*faith = ", chk)),
             len(re.findall(rb"(?m)^\s*rite = ", chk))))


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return
    mode = argv[0]
    if mode == "save":
        cmd_save(argv[1] if len(argv) > 1 else "")
    elif mode == "list":
        cmd_list()
    elif mode == "restore":
        rest = [a for a in argv[1:] if not a.startswith("--")]
        if not rest:
            sys.exit("用法: restore <latest|文件名> [--apply] [--faith-only]")
        cmd_restore(rest[0], "--apply" in argv, "--faith-only" in argv)
    else:
        sys.exit("未知命令: %s（可用: save / list / restore）" % mode)


if __name__ == "__main__":
    main()
