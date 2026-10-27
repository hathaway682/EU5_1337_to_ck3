# -*- coding: utf-8 -*-
"""
只读比对（限定版）：
  A. EU5 侧 —— 只取 1337 开局有领地的国家（main_menu/setup/start/10_countries.txt）
  B. CK3 侧 —— 只取公国及以上头衔（e_ / k_ / d_）
输出中文本地化名完全相同的清单。
"""
import os, re, csv, collections

EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"
CK3 = r"E:\SteamLibrary\steamapps\common\Crusader Kings III\game"
MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"

# ---------- yml ----------
LOC_RE = re.compile(r'^\s*([A-Za-z0-9_.\-]+)\s*:\s*(?:\d+\s*)?"(.*)"\s*$')

def parse_yml(path, out):
    try:
        raw = open(path, 'rb').read()
    except Exception:
        return
    if raw.startswith(b'\xef\xbb\xbf'):
        raw = raw[3:]
    for line in raw.decode('utf-8', 'replace').splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        m = LOC_RE.match(line)
        if m:
            out[m.group(1)] = m.group(2)

def walk_yml(root):
    res = {}
    for dp, _, fns in os.walk(root):
        for fn in fns:
            if fn.lower().endswith('.yml'):
                parse_yml(os.path.join(dp, fn), res)
    return res

VAR_RE = re.compile(r'\$([A-Za-z0-9_]+)\$')
FMT_RE = re.compile(r'#[A-Za-z0-9_!]*')

def clean(name, table, depth=0):
    if not name:
        return None
    if depth < 4:
        name = VAR_RE.sub(lambda m: table.get(m.group(1), m.group(0)), name)
    name = FMT_RE.sub('', name)
    return name.replace('\\"', '"').strip()

# ---------- EU5 1337 有地国家 ----------
TAG_LINE = re.compile(r'^\t([A-Z0-9]{2,5})\s*=\s*\{\s*$')
OWN_LINE = re.compile(r'^\t\t(own_\w+|control_\w+)\s*=\s*\{\s*$')

def collect_1337_tags():
    """返回 {tag: 地点数}"""
    path = os.path.join(EU5, 'main_menu', 'setup', 'start', '10_countries.txt')
    raw = open(path, 'rb').read()
    if raw.startswith(b'\xef\xbb\xbf'):
        raw = raw[3:]
    tags = {}
    cur = None
    in_own = 0
    for line in raw.decode('utf-8', 'replace').splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        m = TAG_LINE.match(line)
        if m:
            cur = m.group(1)
            tags.setdefault(cur, 0)
            in_own = 0
            continue
        if cur is None:
            continue
        if OWN_LINE.match(line):
            in_own += 1
            continue
        if in_own:
            if line.strip() == '}':
                in_own -= 1
                continue
            # 地点行：可能是多个空格分隔的词
            if line.startswith('\t\t\t'):
                tags[cur] += len(line.split())
    return tags

# ---------- CK3 公国以上头衔 ----------
TITLE_DEF = re.compile(r'^\s*([ekd]_[A-Za-z0-9_]+)\s*=\s*\{')

def collect_ck3_high_titles():
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

def main():
    ck3_loc = walk_yml(os.path.join(CK3, 'localization', 'simp_chinese'))
    eu5_loc = walk_yml(os.path.join(EU5, 'main_menu', 'localization', 'simp_chinese'))

    tags_all = collect_1337_tags()
    tags = {t: n for t, n in tags_all.items() if n > 0}
    print('10_countries.txt 中 tag 数:', len(tags_all), ' 其中有领地:', len(tags))
    print('无领地被排除:', len(tags_all) - len(tags))

    ck3_titles = collect_ck3_high_titles()
    print('CK3 公国以上头衔 key:', len(ck3_titles))

    title_name = {}
    for k in ck3_titles:
        if k in ck3_loc:
            v = clean(ck3_loc[k], ck3_loc)
            if v:
                title_name[k] = v
    print('其中有中文名:', len(title_name))

    by_name = collections.defaultdict(list)
    for k, v in title_name.items():
        by_name[v].append(k)

    hits = []
    miss_loc = []
    for t, n in sorted(tags.items()):
        if t not in eu5_loc:
            miss_loc.append(t)
            continue
        v = clean(eu5_loc[t], eu5_loc)
        if v and v in by_name:
            for tk in sorted(by_name[v]):
                hits.append((v, t, n, tk))

    print('EU5 侧缺中文名:', len(miss_loc), miss_loc[:20])
    print('\n===== 命中 %d 条 =====' % len(hits))
    for v, t, n, tk in sorted(hits):
        print('%s\t%s(%d地)\t%s' % (v, t, n, tk))

    out = os.path.join(MOD, 'gen_debug', '_eu5_1337_vs_ck3_high_title_samename.csv')
    with open(out, 'w', encoding='utf-8-sig', newline='\r\n') as f:
        f.write('name,eu5_tag,eu5_locations,ck3_title\n')
        for v, t, n, tk in sorted(hits):
            f.write('%s,%s,%d,%s\n' % (v, t, n, tk))
    print('\n写出:', out)

if __name__ == '__main__':
    main()
