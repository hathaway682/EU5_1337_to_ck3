# -*- coding: utf-8 -*-
"""把 19 个「单伯爵领公国」的公国头衔补回来（暂时性）。

只做加法，不动任何已有块：
  1) common/landed_titles/zz_eu5_titular.txt  补 17 个 d_eu5_* 块（kol/lie 已存在）
  2) history/titles/zz_eu5_titles.txt         补 19 个 d_eu5_* 历史块
  3) localization/.../zz_eu5_politics_l_simp_chinese.yml  修 d_eu5_lie 的 "$liege$"
  4) gen_debug/eu5_ck3_title_map.csv          19 行改成 d 级

默认 dry run，加 --apply 才写。写前自动备份。
"""
import csv
import io
import json
import os
import re
import shutil
import sys
import time

MOD = r'D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape'
EXPORT = r'D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export'
LT = os.path.join(MOD, 'common', 'landed_titles', 'zz_eu5_titular.txt')
HT = os.path.join(MOD, 'history', 'titles', 'zz_eu5_titles.txt')
LOC = os.path.join(MOD, 'localization', 'simp_chinese', 'zz_eu5_politics_l_simp_chinese.yml')
CSV = os.path.join(MOD, 'gen_debug', 'eu5_ck3_title_map.csv')

APPLY = '--apply' in sys.argv
STAMP = time.strftime('%Y%m%d_%H%M%S')

B1 = ['AAI', 'AOS', 'AQU', 'ATH', 'CDL', 'GLO', 'KOL', 'LCZ', 'LGC', 'LIE',
      'OEL', 'OPL', 'OPV', 'PLK', 'SDZ', 'SWD', 'TES', 'ZAG']

# SWB（萨克森-维滕贝格）不在名单里：它的伯爵领 c_flaming 答于 d_eu5_mag（马格德堡公国），
# 是 19 个里唯一真正同级附庸的，公国头衔该丢，不要给它补回来。

# 首府（seat）写死：CSV 被本脚本改过之后 ck3_key 已经是 d_ 级，不能再从 CSV 取。
SEAT = {'AAI': 'c_tashir', 'AOS': 'c_aosta', 'AQU': 'c_friuli', 'ATH': 'c_attica',
        'CDL': 'c_dali', 'GLO': 'c_glogow', 'KOL': 'c_koln_bucht', 'LCZ': 'c_leczyca',
        'LGC': 'c_legnica', 'LIE': 'c_liege', 'OEL': 'c_olesnica', 'OPL': 'c_opole',
        'OPV': 'c_opavsko', 'PLK': 'c_plock', 'SDZ': 'c_sieradz',
        'SWD': 'c_swidnica', 'TES': 'c_tesin', 'ZAG': 'c_zagan'}

p = json.load(io.open(os.path.join(EXPORT, 'eu5_politics.json'), encoding='utf-8-sig'))
countries, relations = p['countries'], p['relations']

io_titles = {'hre': 'e_hre', 'ilkhanate': 'e_ilkhanate',
             'tatar_yoke': 'e_golden_horde', 'middle_kingdom': 'h_china'}


def ctk(rank, tag):
    return 'k_papal_state' if tag == 'PAP' else '%s_eu5_%s' % (rank, tag.lower())


title_key = {t: ctk(c['rank'], t) for t, c in countries.items() if c.get('rank') in ('d', 'k', 'e')}
liege_title = {}
for rel in relations:
    if rel.get('ck3') != 'vassal':
        continue
    liege = rel.get('liege_title') or io_titles.get(rel.get('type') or '') or title_key.get(rel['first'])
    if liege and rel['second'] not in liege_title:
        liege_title[rel['second']] = liege
for rel in relations:
    if rel.get('ck3') != 'union' or rel['second'] in liege_title:
        continue
    above = liege_title.get(rel['first'])
    if above:
        liege_title[rel['second']] = above


def usable(color, key):
    if color and len(color) == 3:
        lo, hi = min(color), max(color)
        if not (hi - lo <= 24 and hi >= 190):
            return color
    h = 0
    for ch in key:
        h = (h * 131 + ord(ch)) & 0xFFFFFF
    return [60 + (h >> 16) % 150, 60 + (h >> 8) % 150, 60 + (h & 0xFF) % 150]


# ---------------------------------------------------------------- 读 CSV 拿 seat / 名字
csv_rows = list(csv.DictReader(io.open(CSV, encoding='utf-8-sig')))
cby = {r['eu5_tag']: r for r in csv_rows if r['kind'] == 'country'}

# ---------------------------------------------------------------- 读两个 titel 文件的块结构
BLOCK_RE = re.compile(r'(?m)^([a-z]_[a-z0-9_]+)\s*=\s*\{')


def blocks(text):
    out = []
    for m in BLOCK_RE.finditer(text):
        j = m.end()
        d = 1
        while j < len(text) and d:
            if text[j] == '{':
                d += 1
            elif text[j] == '}':
                d -= 1
            j += 1
        out.append((m.start(), m.group(1), j))
    return out


def pick_run(text, key, prefix='d_eu5_'):
    """在所有 prefix 开头的连续块段里，挑 key 该落进去的那一段。"""
    bs = blocks(text)
    runs, cur = [], []
    for b in bs:
        if b[1].startswith(prefix):
            cur.append(b)
        else:
            if cur:
                runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    inside = [r for r in runs if r[0][1] <= key <= r[-1][1]]
    if inside:
        return inside[0]
    below = [r for r in runs if r[-1][1] < key]
    if below:
        return max(below, key=lambda r: r[-1][1])
    above = [r for r in runs if r[0][1] > key]
    if above:
        return min(above, key=lambda r: r[0][1])
    return runs[0] if runs else []


def insert_offset(text, run, key):
    """插到该段里第一个比 key 大的块之前；没有就插到该段最后一块之后（跳过空行）。"""
    if not run:
        return len(text)
    for start, k, end in run:
        if k > key:
            return start
    i = run[-1][2]
    if text[i:i + 2] == '\r\n':
        i += 2
    if text[i:i + 2] == '\r\n':
        i += 2
    return i


def county_hist(seat):
    """从 history/titles 里取该伯爵领 1337.4.1 的 holder / government / liege。

    liege 一律照抄伯爵领自己写的那一行，不用 politics.json 重算：
    公国的地和它的伯爵领必须答于同一个领主，否则 CK3 里两条 liege 打架。
    SWB 就是例子——politcs 按 type=hre 算成 e_hre，游戏里 c_flaming 写的是 d_eu5_mag。
    """
    t = io.open(HT, encoding='utf-8-sig', newline='').read()
    for start, k, end in blocks(t):
        if k != seat:
            continue
        body = t[start:end]
        segs = re.findall(r'1337\.4\.1\s*=\s*\{([^}]*)\}', body)
        if not segs:
            return None, None, None
        h = re.search(r'holder\s*=\s*(\S+)', segs[-1])
        g = re.search(r'government\s*=\s*(\S+)', segs[-1])
        l = re.search(r'liege\s*=\s*(\S+)', segs[-1])
        return ((h.group(1) if h else None), (g.group(1) if g else None),
                (l.group(1) if l else None))
    return None, None, None


# ---------------------------------------------------------------- 组装
plan_lt, plan_ht = [], []
for tag in B1:
    r = cby[tag]
    c = countries.get(tag) or {}
    key = 'd_eu5_' + tag.lower()
    seat = SEAT[tag]
    color = usable(c.get('color'), key)
    holder, gov, liege = county_hist(seat)
    if not holder or not liege:
        print('!! %s 缺 holder(%s) 或 liege(%s)，跳过' % (tag, holder, liege))
        continue
    lt_block = 'd_eu5_%s = {\r\n\tcolor = { %d %d %d }\r\n\tcapital = %s\r\n}' % (
        tag.lower(), color[0], color[1], color[2], seat)
    ht_block = 'd_eu5_%s = {\r\n\t1337.4.1 = {\r\n\t\tholder = %s\r\n\t\tgovernment = %s\r\n\t\tliege = %s\r\n\t}\r\n}' % (
        tag.lower(), holder, gov or 'feudal_government', liege)
    plan_lt.append((key, lt_block, seat, color))
    plan_ht.append((key, ht_block, holder, gov, liege))

lt_text = io.open(LT, encoding='utf-8-sig', newline='').read()
ht_text = io.open(HT, encoding='utf-8-sig', newline='').read()
lt_have = {k for _, k, _ in blocks(lt_text)}
ht_have = {k for _, k, _ in blocks(ht_text)}

print('=== 计划（%s）===' % ('APPLY' if APPLY else 'dry run'))
print('%-12s %-14s %-22s %-9s %-14s %s' % ('key', 'seat', 'holder', 'gov', 'liege', '颜色'))
for (key, lb, seat, color), (_, hb, holder, gov, liege) in zip(plan_lt, plan_ht):
    print('%-12s %-14s %-22s %-9s %-14s %s %s' % (
        key, seat, holder, gov or '-', liege, color,
        '(landed_titles 已有)' if key in lt_have else ''))

# ---------------------------------------------------------------- 写
if APPLY:
    for path in (LT, HT, CSV, LOC):
        shutil.copy2(path, path + '.bak_b1duchy_' + STAMP)

    new_lt = lt_text
    added_lt = 0
    for key, lb, seat, color in plan_lt:
        if key in lt_have:
            continue
        run = pick_run(new_lt, key)
        pos = insert_offset(new_lt, run, key)
        new_lt = new_lt[:pos] + lb + '\r\n\r\n' + new_lt[pos:]
        added_lt += 1
    io.open(LT, 'w', encoding='utf-8-sig', newline='').write(new_lt)

    new_ht = ht_text
    added_ht = 0
    for key, hb, holder, gov, liege in plan_ht:
        if key in ht_have:
            continue
        run = pick_run(new_ht, key)
        pos = insert_offset(new_ht, run, key)
        new_ht = new_ht[:pos] + hb + '\r\n\r\n' + new_ht[pos:]
        added_ht += 1
    io.open(HT, 'w', encoding='utf-8-sig', newline='').write(new_ht)

    # 本地化：只修 $liege$
    loc = io.open(LOC, encoding='utf-8-sig', newline='').read()
    fixed = loc.replace('d_eu5_lie:0 "$liege$"', 'd_eu5_lie:0 "列日"')
    if fixed != loc:
        io.open(LOC, 'w', encoding='utf-8-sig', newline='').write(fixed)
        print('本地化：d_eu5_lie "$liege$" -> "列日"')

    # CSV
    out = []
    changed = 0
    for r in csv_rows:
        if r['kind'] == 'country' and r['eu5_tag'] in B1:
            key = 'd_eu5_' + r['eu5_tag'].lower()
            r = dict(r)
            r['ck3_key'] = key
            r['ck3_tier'] = 'd'
            r['ck3_name_en'] = r['eu5_country_en']
            r['ck3_name_zh'] = r['eu5_country_zh']
            r['note'] = ','.join(x for x in r['note'].split(',')
                                 if not x.startswith('rank-title-dropped'))
            changed += 1
        out.append(r)
    with io.open(CSV, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()), lineterminator='\r\n')
        w.writeheader()
        w.writerows(out)

    print('landed_titles 新增 %d 块；history/titles 新增 %d 块；CSV 改 %d 行' % (
        added_lt, added_ht, changed))
else:
    print('\n(dry run，未写入。加 --apply 执行)')
