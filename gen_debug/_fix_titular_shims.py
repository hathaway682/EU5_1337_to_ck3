# -*- coding: utf-8 -*-
"""把 zz_vanilla_titulars.txt 里三个「屏蔽用 shim」换成原版真实定义。

背景：`zz_vanilla_titulars.txt` 是生成器（Ck3MapGen）用来**屏蔽原版 titular 头衔**的，
里面的 `capital = c_gen_buamu_4`、`can_create = { always = no }`、
`no_automatic_claims = yes`、`ai_primary_priority = { add = -1000 }` 都是占位/禁用值，
不是这些头衔的真实数据。

现在这三国改挂到了这三个键上（LAT→e_latin_empire、KOJ→k_jerusalem、
GLC→k_spanish_galicia），所以要用**原版 `00_landed_titles.txt` 的真实定义**，
只把 `capital` 换成我们地图里存在的 location：

| 键 | 原版 capital | 我们的 capital | 依据 |
|---|---|---|---|
| e_latin_empire | c_byzantion | c_constantinople | 我们地图无 c_byzantion，君堡在 c_constantinople（e_byzantium > k_thessalonika > d_thrace） |
| k_jerusalem | c_jerusalem | c_filastin | 我们地图无 c_jerusalem，耶路撒冷男爵领 b_jerusalem 属 c_filastin（d_levant > k_syria） |
| k_spanish_galicia | c_coruna | c_coruna | 原样存在 |

不搬原版的 de jure 子块（k_jerusalem 的 d_oultrejourdain 等）——本 mod 的法理树是 CU 1337，
混进原版子块会造出地图上不存在的领地。因此保留 `landless = yes`。

不搬引用本 mod 不存在的键的字段：`@always_primary_score`（CU 树没定义）、
`cultural_names` 里的 `cn_yilliqiyya`（本地化没有）。

用法：python gen_debug/_fix_titular_shims.py [--write]
"""
import argparse
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

BLOCKS = {
    "e_latin_empire": """e_latin_empire = {
\tlandless = yes
\tcapital = c_constantinople
\tcolor = { 150 105 56 }
\tdefinite_form = yes
\tcan_create = {
\t\trule_title_creation_imperial_power_projection_title_creation_trigger = yes
\t}
}
""",
    "k_jerusalem": """k_jerusalem = {
\tlandless = yes
\tcapital = c_filastin
\tcolor = { 180 180 180 }
\tcan_create = {
\t\tfaith = { religion_tag = christianity_religion }
\t}
\tcan_create_on_partition = {
\t\tfaith = { religion_tag = christianity_religion }
\t}
}
""",
    "k_spanish_galicia": """k_spanish_galicia = {
\tlandless = yes
\tcapital = c_coruna
\tcolor = { 255 224 94 }
\tcan_be_named_after_dynasty = no
\tcan_create = {
\t\ttrigger_if = {
\t\t\tlimit = { is_ai = yes }
\t\t\tfaith = { religion_tag = christianity_religion }
\t\t}
\t}
}
""",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mod", default=os.path.abspath(os.path.join(HERE, "..")))
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    path = os.path.join(args.mod, "common", "landed_titles", "zz_vanilla_titulars.txt")
    text = io.open(path, encoding="utf-8-sig", errors="ignore", newline="").read()

    for key, new in BLOCKS.items():
        pat = r'(?ms)^' + key + r' = \{\r?\n.*?^\}\r?\n'
        m = re.search(pat, text)
        if not m:
            print("!! 未找到 %s" % key)
            continue
        old = m.group(0)
        if old.replace("\r\n", "\n") == new:
            print("  %-20s 已是目标状态，跳过" % key)
            continue
        text = text[:m.start()] + new.replace("\n", "\r\n") + text[m.end():]
        print("  %-20s 已替换（%d -> %d 字节）" % (key, len(old), len(new)))

    if not args.write:
        print("\n(dry-run，未写盘。加 --write 落盘)")
        return

    with io.open(path, "wb") as fh:
        fh.write(b"\xef\xbb\xbf")
        fh.write(text.encode("utf-8"))
    print("\nwritten: %s" % path)


if __name__ == "__main__":
    main()
