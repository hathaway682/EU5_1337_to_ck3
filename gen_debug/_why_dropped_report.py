# -*- coding: utf-8 -*-
"""重写 _tier_mismatch.md 的 B 段。

判定照抄 _fix_politics_output.py 里产生 dropped 的四个分支，不按"领主是谁"倒推原因：
  B1 demoted  L528-546  rank=d 且只持 1 个伯爵领 且自己名下无附庸 且 liege 是某位领主
  B2 baron    L571-579  baronies 里带 drop_title
  B3 no_ruler L608-612  rank=d/k/e 但没有 ruler
  B4 旧清单残留          10-20 的 dropped 与 10-22 的 politics 对不上，现行数据已不满足上述任何一条
"""
import csv
import io
import json
import os
import re
from collections import Counter, OrderedDict

MOD = r'D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape'
EXPORT = r'D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export'
CSV = os.path.join(MOD, 'gen_debug', 'eu5_ck3_title_map.csv')
MD = os.path.join(MOD, 'gen_debug', '_tier_mismatch.md')

p = json.load(io.open(os.path.join(EXPORT, 'eu5_politics.json'), encoding='utf-8-sig'))
countries, relations = p['countries'], p['relations']
lowered = p.get('lowered') or {}
baronies = p.get('baronies') or {}
county = p.get('counties') or {}


def ctk(rank, tag):
    return 'k_papal_state' if tag == 'PAP' else '%s_eu5_%s' % (rank, tag.lower())


io_titles = {'hre': 'e_hre', 'ilkhanate': 'e_ilkhanate',
             'tatar_yoke': 'e_golden_horde', 'middle_kingdom': 'h_china'}
title_key = {t: ctk(c['rank'], t) for t, c in countries.items() if c.get('rank') in ('d', 'k', 'e')}

liege_title, liege_rel = {}, {}
for rel in relations:
    if rel.get('ck3') != 'vassal':
        continue
    liege = rel.get('liege_title') or io_titles.get(rel.get('type') or '') or title_key.get(rel['first'])
    if liege and rel['second'] not in liege_title:
        liege_title[rel['second']] = liege
        liege_rel[rel['second']] = rel
for rel in relations:
    if rel.get('ck3') != 'union' or rel['second'] in liege_title:
        continue
    above = liege_title.get(rel['first'])
    if above:
        liege_title[rel['second']] = above
        liege_rel[rel['second']] = rel

cc = Counter()
for info in county.values():
    if info.get('owner'):
        cc[info['owner']] += 1
lords = {rel['first'] for rel in relations if rel.get('ck3') == 'vassal'}

src, det = {}, {}
demoted = {}
for tag, rel in liege_rel.items():
    sub = countries.get(tag) or {}
    if sub.get('rank') != 'd' or cc.get(tag) != 1:
        continue
    if tag in lords:
        continue
    if rel.get('type') in io_titles:
        demoted[tag] = liege_title[tag]
    else:
        lord = countries.get(rel['first']) or {}
        if lord.get('rank') not in ('d', 'k', 'e'):
            continue
        if lord.get('ruler') and lord.get('ruler') == sub.get('ruler'):
            demoted[tag] = liege_title.get(rel['first'])
        else:
            demoted[tag] = title_key.get(rel['first'])
    src[title_key[tag]] = 'B1'
    det[title_key[tag]] = {'lord': rel['first'], 'type': rel.get('type'),
                           'liege_written': demoted.get(tag)}

for tag, was in lowered.items():
    if was.get('from') in ('d', 'k', 'e'):
        k = ctk(was['from'], tag)
        src.setdefault(k, 'lowered')
        det.setdefault(k, {'from': was['from'], 'to': was.get('to')})

baron_key = {}
for bk, baron in baronies.items():
    tag = baron.get('tag') or ''
    if not baron.get('drop_title') or not title_key.get(tag):
        continue
    k = title_key[tag]
    src.setdefault(k, 'B2')
    baron_key.setdefault(k, []).append(bk)

daimyo = set()
for org in p['organizations']:
    if org['type'] == 'japanese_shogunate':
        daimyo = set(org['members'])
for tag, c in countries.items():
    if tag not in daimyo or c.get('rank') in ('d', 'k', 'e'):
        continue
    for rank in ('d', 'k', 'e'):
        src.setdefault(ctk(rank, tag), 'daimyo')

for tag, c in countries.items():
    if c.get('rank') not in ('d', 'k', 'e') or c.get('ruler'):
        continue
    if title_key.get(tag) and liege_title.get(tag):
        src.setdefault(title_key[tag], 'B3')

CN = {r['eu5_tag']: r['eu5_country_zh'] for r in
      csv.DictReader(io.open(CSV, encoding='utf-8-sig')) if r['kind'] == 'country'}
rows = [r for r in csv.DictReader(io.open(CSV, encoding='utf-8-sig')) if r['kind'] == 'country']
b = sorted([r for r in rows if 'rank-title-dropped' in r['note']], key=lambda x: x['eu5_tag'])
NOTE = re.compile(r'rank-title-dropped\s*\(([^)]+)\)')

groups = OrderedDict((k, []) for k in ('B1', 'B2', 'B3', 'B4'))
for r in b:
    m = NOTE.search(r['note'])
    k = m.group(1) if m else ''
    s = src.get(k, 'B4')
    if s in ('lowered', 'daimyo'):
        s = 'B4'
    groups[s].append((r, k))

L = []
L.append('## B. 头衔被丢掉（rank-title-dropped）（%d）' % len(b))
L.append('')
L.append('这 %d 行的 note 都来自 `gen_debug/eu5_titles_dropped.txt`：`_fix_politics_output.py` 判定'
         '「这个 key 不声明、不写 history 块」的清单。按代码里真正产生这个 key 的分支分四类，'
         '不按「领主是谁」倒推：' % len(b))
L.append('')
L.append('| 分支 | 行数 | 代码位置 | 判定 |')
L.append('| --- | --- | --- | --- |')
L.append('| B1 单伯爵领公国 | %d | L528-546 | EU5 rank=d、只持 1 个伯爵领、自己名下没有任何附庸、且 liege 是某位领主 |'
         % len(groups['B1']))
L.append('| B2 只剩男爵领 | %d | L571-579 | `baronies` 里这一项带 `drop_title`，整块地只剩一个男爵领 |'
         % len(groups['B2']))
L.append('| B3 无君主 | %d | L608-612 | rank=d/k/e 但 EU5 没给 ruler，头衔没人能持有 |' % len(groups['B3']))
L.append('| B4 旧清单残留 | %d | — | 清单是 10-20 写的、politics 是 10-22 的，现行数据已不满足上面任何一条 |'
         % len(groups['B4']))
L.append('')
L.append('> 神罗成员不是降级原因。B1 里 `type=hre` 的那几行，代码只多做一件事：'
         '`liege =` 那一行写 `e_hre` 而不是写领主本人的 `d_eu5_ubv`（L535-539）。'
         '降不降级由 L531-534 三条决定，跟领主是帝国、王国还是公国无关——神罗是帝国，'
         '它底下最高只有波希米亚这个王国，它不会把任何人降级。')
L.append('')

L.append('### B1. 单伯爵领公国（%d）' % len(groups['B1']))
L.append('')
L.append('EU5 把它写成公国（rank=d），但它只持有一个伯爵领、自己名下没有任何附庸，'
         '同时 liege 又是某位领主。这种公国在 CK3 里没有可写的东西：头衔不声明、history 块不写，'
         '地直接按伯爵领落地。下表「领主」一列是它的 liege，「liege 写」一列是最终落进 '
         '`liege =` 的 key。')
L.append('')
L.append('| EU5 | 中文名 | 层级 | 领主 | 关系 type | liege 写 | 现头衔 |')
L.append('| --- | --- | --- | --- | --- | --- | --- |')
for r, k in groups['B1']:
    d = det.get(k) or {}
    lord = d.get('lord') or '—'
    L.append('| %s | %s | %s→%s | %s %s | %s | %s | %s |' % (
        r['eu5_tag'], r['eu5_country_zh'], r['eu5_tier'], r['ck3_tier'] or '空',
        CN.get(lord, lord), lord, d.get('type') or '—',
        d.get('liege_written') or '—', r['ck3_key'] or '—'))
L.append('')
lc = Counter((det.get(k) or {}).get('lord') for r, k in groups['B1'])
L.append('领主分布：' + '、'.join('%s %s（%d）' % (CN.get(t, t), t, n) for t, n in lc.most_common()))
L.append('')

L.append('### B2. 只剩一块男爵领（%d）' % len(groups['B2']))
L.append('')
L.append('EU5 仍给 d 或 k 级，但 `baronies` 里这一项标了 `drop_title`——整块地只剩一个男爵领，'
         '实际地位就是男爵，公国/王国头衔没有落脚点。')
L.append('')
L.append('| EU5 | 中文名 | 层级 | 剩下的男爵领 | 现头衔 |')
L.append('| --- | --- | --- | --- | --- |')
for r, k in groups['B2']:
    L.append('| %s | %s | %s→%s | %s | %s |' % (
        r['eu5_tag'], r['eu5_country_zh'], r['eu5_tier'], r['ck3_tier'] or '空',
        '、'.join(baron_key.get(k) or ['—']), r['ck3_key'] or '—'))
L.append('')

L.append('### B3. 无君主（%d）' % len(groups['B3']))
L.append('')
L.append('| EU5 | 中文名 | 层级 | 情况 | 现头衔 |')
L.append('| --- | --- | --- | --- | --- |')
for r, k in groups['B3']:
    c = countries.get(r['eu5_tag']) or {}
    L.append('| %s | %s | %s→%s | rank=%s、伯爵领 %d 个、EU5 没有给 ruler（汉萨同盟这种有成员没君主的国家） | %s |' % (
        r['eu5_tag'], r['eu5_country_zh'], r['eu5_tier'], r['ck3_tier'] or '空',
        c.get('rank'), cc.get(r['eu5_tag'], 0), r['ck3_key'] or '—'))
L.append('')

L.append('### B4. 旧清单残留（%d）' % len(groups['B4']))
L.append('')
L.append('`eu5_titles_dropped.txt` 是 10-20 10:26 写的，`eu5_politics.json` 是 10-22 22:24 的，'
         '中间重新导出过 politics 但没重跑 `_fix_politics_output.py`。这 %d 行在旧数据里满足 '
         'B1 的条件，现在的伯爵领数已经变了，按现行数据不会再丢。它们的 note 是旧清单带来的。'
         % len(groups['B4']))
L.append('')
L.append('| EU5 | 中文名 | 层级 | 现行 rank | 现行伯爵领数 | 现行领主 | 现头衔 |')
L.append('| --- | --- | --- | --- | --- | --- | --- |')
for r, k in groups['B4']:
    c = countries.get(r['eu5_tag']) or {}
    rels = [(x['first'], x.get('type')) for x in relations if x.get('second') == r['eu5_tag']]
    lord = '、'.join('%s %s(%s)' % (CN.get(a, a), a, t) for a, t in rels) or '—'
    L.append('| %s | %s | %s→%s | %s | %d | %s | %s |' % (
        r['eu5_tag'], r['eu5_country_zh'], r['eu5_tier'], r['ck3_tier'] or '空',
        c.get('rank'), cc.get(r['eu5_tag'], 0), lord, r['ck3_key'] or '—'))
L.append('')

text = io.open(MD, encoding='utf-8').read()
new_b = '\n'.join(L)
text = re.sub(r'## B\..*?(?=## C\.)', new_b + '\n', text, flags=re.S)
io.open(MD, 'w', encoding='utf-8', newline='').write(text)

print('B 段已重写：B1=%d B2=%d B3=%d B4=%d' % (
    len(groups['B1']), len(groups['B2']), len(groups['B3']), len(groups['B4'])))
