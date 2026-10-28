# -*- coding: utf-8 -*-
"""暂时去掉 EU5 type=pop（人群国家）转换来的 herder 牧民国家。

- 603 个 herder 伯爵领：外东北 17 县（原本元的满洲）还给元 e_eu5_chi 的君主，
  其余 586 县变荒野。
- 448 个 eu5_regent_<tag> 占位统治者角色（定义 + government effect）删除。
- 首府地产：17 县 → castle_holding，586 县 → wilderness_holding。

用法：python _remove_herders.py            # 干跑，只打印统计
      python _remove_herders.py --apply    # 落盘（先自动备份）
"""
import json, os, re, shutil, sys, time

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
EXPORT = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export"
GAME = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"

APPLY = "--apply" in sys.argv

d = json.load(open(os.path.join(EXPORT, "eu5_politics.json"), encoding="utf-8"))
cs, cts = d["countries"], d["counties"]
HERD = {t for t, v in cs.items() if v.get("government") == "herder"}
HERD_CTS = {c for c, v in cts.items() if v.get("owner") in HERD}
REGENTS = {"eu5_regent_" + t.lower() for t in HERD}

# ---- 外东北（元的大满洲，去掉辽东）
BLOCK = re.compile(r"([A-Za-z0-9_]+)\s*=\s*\{")


def walk_blocks(text, path=()):
    i, n = 0, len(text)
    while i < n:
        m = BLOCK.search(text, i)
        if not m:
            return
        j, depth = m.end(), 1
        while j < n and depth:
            ch = text[j]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
            j += 1
        body = text[m.end():j - 1]
        yield path, m.group(1), body
        yield from walk_blocks(body, path + (m.group(1),))
        i = j


defs = re.sub(r"#[^\n]*", "", open(os.path.join(GAME, "in_game", "map_data", "definitions.txt"),
                                   encoding="utf-8", errors="ignore").read())
MANCHU = set()
for path, key, body in walk_blocks(defs):
    if key.endswith("_province") and "manchuria_region" in path and "liaodong_area" not in path:
        MANCHU.add("c_" + key[: -len("_province")])

YUAN_CTS = sorted(c for c in HERD_CTS if c in MANCHU)
WILD_CTS = sorted(c for c in HERD_CTS if c not in MANCHU)

# ---- 顶层块解析（保留注释与空行）
TOP = re.compile(r"^([A-Za-z0-9_]+)\s*=\s*\{", re.M)


def split_top(text):
    """[(key, start, end)] 顶层块的行区间；end 指向 `}` 之后。"""
    out = []
    for m in TOP.finditer(text):
        if m.start() > 0 and text[m.start() - 1] not in "\n\r":
            continue
        key = m.group(1)
        i, depth = m.end(), 1
        while i < len(text) and depth:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        out.append((key, m.start(), i))
    return out


def rewrite_titles(path, tag):
    text = open(path, encoding="utf-8-sig").read()
    blocks = split_top(text)
    out, last = [], 0
    n_yuan = n_wild = 0
    for key, s, e in blocks:
        if key not in HERD_CTS:
            continue
        body = text[s:e]
        if key in MANCHU:
            new = re.sub(r"holder\s*=\s*eu5_regent_\w+", "holder = yua_togon_temur", body)
            new = re.sub(r"government\s*=\s*herder_government", "government = celestial_government", new)
            n_yuan += 1
        else:
            new = re.sub(r"holder\s*=\s*eu5_regent_\w+", "holder = gen_wilderness_holder", body)
            new = re.sub(r"\n\s*government\s*=\s*herder_government", "", new)
            if "liege = e_eu5_chi" in new:
                new = new.replace("liege = e_eu5_chi", "liege = k_gen_wilderness")
            elif "liege =" not in new:
                # 在同一条日期块里补 liege
                new = re.sub(r"(holder = gen_wilderness_holder)", r"\1\n\t\tliege = k_gen_wilderness", new)
            n_wild += 1
        out.append(text[last:s])
        out.append(new)
        last = e
    out.append(text[last:])
    new_text = "".join(out)
    print(f"{tag}: 元 {n_yuan} 县 / 荒野 {n_wild} 县 | 变化 {new_text != text}")
    if APPLY and new_text != text:
        open(path, "w", encoding="utf-8-sig", newline="").write(new_text)


def drop_blocks(path, keys, tag):
    text = open(path, encoding="utf-8-sig").read()
    blocks = split_top(text)
    out, last, n = [], 0, 0
    for key, s, e in blocks:
        if key not in keys:
            continue
        # 连同块后紧跟的一个空行一起删
        end = e
        while end < len(text) and text[end] in "\r\n":
            end += 1
            if text[end - 1] == "\n" and end - 2 >= e and text[end - 2] == "\n":
                break
        out.append(text[last:s])
        last = end
        n += 1
    out.append(text[last:])
    new_text = "".join(out)
    print(f"{tag}: 删除 {n} 块（目标 {len(keys & {k for k, _, _ in blocks})}）| 变化 {new_text != text}")
    if APPLY and new_text != text:
        open(path, "w", encoding="utf-8-sig", newline="").write(new_text)


def rewrite_provinces(path):
    c2p = json.load(open(os.path.join(EXPORT, "_tmp_c2p.json"), encoding="utf-8"))
    yuan_pid = {c2p[c] for c in YUAN_CTS if c in c2p}
    wild_pid = {c2p[c] for c in WILD_CTS if c in c2p}
    text = open(path, encoding="utf-8-sig").read()
    lines = text.split("\n")
    cur, n_yuan, n_wild, other = None, 0, 0, 0
    for i, ln in enumerate(lines):
        m = re.match(r"^(\d+)\s*=\s*\{", ln)
        if m:
            cur = m.group(1)
        if re.search(r"holding = (herder_holding|tribal_holding)", ln):
            if cur in yuan_pid:
                lines[i] = re.sub(r"holding = (herder_holding|tribal_holding)", "holding = castle_holding", ln)
                n_yuan += 1
            elif cur in wild_pid:
                lines[i] = re.sub(r"holding = (herder_holding|tribal_holding)", "holding = wilderness_holding", ln)
                n_wild += 1
            else:
                if "herder_holding" in ln:
                    other += 1
    print(f"provinces: 元首府 {n_yuan} / 荒野首府 {n_wild} / 未归类 herder_holding {other}")
    new_text = "\n".join(lines)
    if APPLY and new_text != text:
        open(path, "w", encoding="utf-8-sig", newline="").write(new_text)


print("herder tag:", len(HERD), "| herder 县:", len(HERD_CTS))
print("外东北（还给元）:", len(YUAN_CTS), "| 变荒野:", len(WILD_CTS))
print("占位角色:", len(REGENTS))
print("---" if APPLY else "--- 干跑，不写盘 ---")

if APPLY:
    stamp = time.strftime("%Y%m%d_%H%M%S")
    bak = os.path.join(MOD, f"_backup_herder_remove_{stamp}")
    os.makedirs(bak, exist_ok=True)
    files = [
        os.path.join(MOD, "history", "titles", "zz_eu5_titles.txt"),
        os.path.join(MOD, "history", "characters", "zz_eu5_titles.txt"),
        os.path.join(MOD, "history", "characters", "zz_eu5_regents.txt"),
        os.path.join(MOD, "history", "characters", "zz_eu5_government.txt"),
        os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt"),
    ]
    for f in files:
        shutil.copy2(f, os.path.join(bak, os.path.basename(f)))
    print("备份:", bak)

rewrite_titles(os.path.join(MOD, "history", "titles", "zz_eu5_titles.txt"), "history/titles")
rewrite_titles(os.path.join(MOD, "history", "characters", "zz_eu5_titles.txt"), "history/characters/titles")
drop_blocks(os.path.join(MOD, "history", "characters", "zz_eu5_regents.txt"), REGENTS, "regents")
drop_blocks(os.path.join(MOD, "history", "characters", "zz_eu5_government.txt"), REGENTS, "government")
rewrite_provinces(os.path.join(MOD, "history", "provinces", "00_generated_provinces.txt"))
