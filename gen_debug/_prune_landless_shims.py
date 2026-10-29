# -*- coding: utf-8 -*-
"""从 landless shim / 无地头衔文件里剔除新法理树已占用的 h/e/k key。

新法理树（00_landed_titles.txt）把一批 key 变成了有地头衔，同名的无地声明会
后加载覆盖整块，必须删掉。只删顶层块，不碰其它内容。
"""
import io
import os
import re
import sys

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
NEW = os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt")
TARGETS = [
    os.path.join(MOD, "common", "landed_titles", "zz_eu5_titular.txt"),
    os.path.join(MOD, "common", "landed_titles", "zz_vanilla_titulars.txt"),
]

PAT = re.compile(r"(?m)^([a-z]_[A-Za-z0-9_-]+)\s*=\s*\{")


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore", newline="").read()


def main():
    apply = "--apply" in sys.argv
    new_keys = set(re.findall(r"(?m)^\t*([hek]_[a-z0-9_-]+)\s*=\s*\{", read(NEW)))
    print("new h/e/k keys:", len(new_keys))

    for path in TARGETS:
        t = read(path)
        out = []
        removed = []
        i, n = 0, len(t)
        while True:
            m = PAT.search(t, i)
            if not m:
                out.append(t[i:])
                break
            key = m.group(1)
            j = m.end()
            d = 1
            while j < n and d:
                c = t[j]
                if c == "{":
                    d += 1
                elif c == "}":
                    d -= 1
                j += 1
            # 吃掉块尾的换行
            k = j
            while k < n and t[k] in "\r\n":
                k += 1
            if key in new_keys:
                out.append(t[i:m.start()])
                removed.append(key)
            else:
                out.append(t[i:k])
            i = k
        body = "".join(out)
        print("%s: removed %d -> %s" % (os.path.basename(path), len(removed), ",".join(sorted(removed)[:8]) + ("..." if len(removed) > 8 else "")))
        if apply:
            with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
                f.write(body)
            print("  applied")
        else:
            with io.open(path + ".pruned", "w", encoding="utf-8-sig", newline="") as f:
                f.write(body)


if __name__ == "__main__":
    main()
