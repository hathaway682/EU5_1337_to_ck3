# -*- coding: utf-8 -*-
"""只读：按「实际写进 liege= 的那个 key 是哪一级」判定每个国家是否真的必须降级。

公国（d）做王国（k）/帝国（e）的附庸合法，不需要降级；
只有当它实际的 liege 也是公国或更低（d/c/b），才真的必须降一级。
"""
import io
import json
from collections import Counter

EXPORT = r'D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export'
p = json.load(io.open(EXPORT + r'\eu5_politics.json', encoding='utf-8-sig'))
countries, relations = p['countries'], p['relations']
county = p.get('counties') or {}

io_titles = {'hre': 'e_hre', 'ilkhanate': 'e_ilkhanate',
             'tatar_yoke': 'e_golden_horde', 'middle_kingdom': 'h_china'}


def ctk(rank, tag):
    return 'k_papal_state' if tag == 'PAP' else '%s_eu5_%s' % (rank, tag.lower())


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

# 这 19 个（B1 单伯爵领公国）
B1 = ['AAI', 'AOS', 'AQU', 'ATH', 'CDL', 'GLO', 'KOL', 'LCZ', 'LGC', 'LIE',
      'OEL', 'OPL', 'OPV', 'PLK', 'SDZ', 'SWB', 'SWD', 'TES', 'ZAG']

print('=== B1 的 19 个：实际 liege 的层级 ===')
need, free = [], []
for t in sorted(B1):
    c = countries.get(t) or {}
    key = liege_title.get(t) or ''
    tier = key.split('_')[0] if key else ''
    rel = liege_rel.get(t) or {}
    ok = tier in ('k', 'e', 'h')
    (free if ok else need).append(t)
    print('%-4s rank=%s counties=%d 领主=%-4s(%s,type=%s) liege=%-12s(%s级) %s'
          % (t, c.get('rank'), cc.get(t, 0), rel.get('first'), ctk((countries.get(rel.get('first')) or {}).get('rank') or '-', rel.get('first') or 'x'),
             rel.get('type'), key, tier or '空', '合法，不必降' if ok else '必须降'))

print()
print('不必降 %d：%s' % (len(free), ' '.join(free)))
print('必须降 %d：%s' % (len(need), ' '.join(need) or '—'))

# 全量：rank=d 的国家里，实际 liege 是 d/c 的有哪些（真正必须降的）
print()
print('=== 全量：rank=d 且实际 liege 也是 d/c 级的 ===')
allneed = []
for t, c in countries.items():
    if c.get('rank') != 'd' or t not in liege_title:
        continue
    key = liege_title[t]
    tier = key.split('_')[0]
    if tier in ('d', 'c', 'b'):
        rel = liege_rel.get(t) or {}
        allneed.append((t, cc.get(t, 0), t in lords, rel.get('first'), rel.get('type'), key))
for x in sorted(allneed):
    print('%-4s counties=%d is_lord=%s 领主=%s(%s) liege=%s' % x)
print('共', len(allneed))
