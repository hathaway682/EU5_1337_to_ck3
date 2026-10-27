# -*- coding: utf-8 -*-
"""
只读比对：EU5 国家（tag）的中文本地化名 与 CK3 原版头衔（e_/k_/d_/c_/b_）的中文本地化名
输出完全同名的清单。
"""
import os, re, sys, json, collections

EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"
CK3 = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"

# ---------- 通用 yml 解析 ----------
LOC_RE = re.compile(r'^\s*([A-Za-z0-9_.\-]+)\s*:\s*(?:\d+\s*)?"(.*)"\s*$')

def parse_yml(path, out):
    try:
        raw = open(path, 'rb').read()
    except Exception:
        return
    if raw.startswith(b'\xef\xbb\xbf'):
        raw = raw[3:]
    txt = raw.decode('utf-8', 'replace')
    for line in txt.splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        m = LOC_RE.match(line)
        if m:
            k, v = m.group(1), m.group(2)
            out[k] = v  # 后出现的覆盖前面（DLC 覆盖原版）

def walk_yml(root):
    res = {}
    for dp, _, fns in os.walk(root):
        for fn in fns:
            if fn.lower().endswith('.yml'):
                parse_yml(os.path.join(dp, fn), res)
    return res

# ---------- CK3 头衔 key ----------
TITLE_DEF = re.compile(r'^\s*([ekdcb]_[A-Za-z0-9_]+)\s*=\s*\{')

def collect_ck3_titles():
    keys = set()
    root = os.path.join(CK3, 'common', 'landed_titles')
    for fn in os.listdir(root):
        if not fn.endswith('.txt'):
            continue
        raw = open(os.path.join(root, fn), 'rb').read().decode('utf-8', 'replace')
        for line in raw.splitlines():
            m = TITLE_DEF.match(line)
            if m:
                keys.add(m.group(1))
    return keys

# ---------- EU5 国家 tag ----------
TAG_DEF = re.compile(r'^([A-Z0-9]{2,5})\s*=\s*\{')

def collect_eu5_tags():
    tags = set()
    root = os.path.join(EU5, 'in_game', 'setup', 'countries')
    for fn in os.listdir(root):
        if not fn.endswith('.txt'):
            continue
        raw = open(os.path.join(root, fn), 'rb').read().decode('utf-8', 'replace')
        for line in raw.splitlines():
            m = TAG_DEF.match(line)
            if m:
                tags.add(m.group(1))
    return tags

# ---------- 名字清洗 ----------
VAR_RE = re.compile(r'\$([A-Za-z0-9_]+)\$')
FMT_RE = re.compile(r'#[A-Za-z0-9_!]*')
def clean(name, table, depth=0):
    if name is None:
        return None
    if depth < 4:
        name = VAR_RE.sub(lambda m: table.get(m.group(1), m.group(0)), name)
    name = FMT_RE.sub('', name)
    name = name.replace('\\"', '"').strip()
    return name

def main():
    print('解析 CK3 本地化...')
    ck3_loc = walk_yml(os.path.join(CK3, 'localization', 'simp_chinese'))
    print('  CK3 本地化条目:', len(ck3_loc))
    print('解析 EU5 本地化...')
    eu5_loc = walk_yml(os.path.join(EU5, 'main_menu', 'localization', 'simp_chinese'))
    print('  EU5 本地化条目:', len(eu5_loc))

    ck3_titles = collect_ck3_titles()
    eu5_tags = collect_eu5_tags()
    print('  CK3 头衔 key:', len(ck3_titles), ' EU5 国家 tag:', len(eu5_tags))

    # CK3 头衔 -> 中文名
    title_name = {}
    missing_loc = 0
    for k in ck3_titles:
        if k in ck3_loc:
            title_name[k] = clean(ck3_loc[k], ck3_loc)
        else:
            missing_loc += 1
    print('  CK3 头衔缺本地化:', missing_loc)

    # EU5 tag -> 中文名
    tag_name = {}
    for t in eu5_tags:
        if t in eu5_loc:
            tag_name[t] = clean(eu5_loc[t], eu5_loc)

    # 建立 名字 -> 头衔列表
    by_name = collections.defaultdict(list)
    for k, v in title_name.items():
        if v:
            by_name[v].append(k)

    hits = []
    for t, v in sorted(tag_name.items()):
        if v and v in by_name:
            for tk in sorted(by_name[v]):
                hits.append((v, t, tk))

    print('\n===== 完全同名命中 %d 条 =====' % len(hits))
    # 按名字分组打印
    grouped = collections.defaultdict(list)
    for v, t, tk in hits:
        grouped[v].append((t, tk))
    for v in sorted(grouped):
        items = grouped[v]
        print('%s\t%s' % (v, ' | '.join('%s=%s' % (t, tk) for t, tk in items)))

    out = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape\gen_debug\_eu5_country_vs_ck3_title_samename.csv"
    with open(out, 'w', encoding='utf-8-sig', newline='\r\n') as f:
        f.write('name,eu5_tag,ck3_title\n')
        for v, t, tk in sorted(hits):
            f.write('%s,%s,%s\n' % (v, t, tk))
    print('\n写出:', out)

if __name__ == '__main__':
    main()
