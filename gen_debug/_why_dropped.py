# -*- coding: utf-8 -*-
"""逐条查 B 类（rank-title-dropped）41 个国家被降级的真实原因。
依据生成器 _fix_politics_output.py 的 dropped 构造逻辑：
  demoted  = relations 里 lord.rank ∈ {d,k,e}（共主或附庸）+ baronies 里 drop_title=True
  declined = lowered 记录的旧等级 + 当前 rank 对不上的旧 key + drop_title 的 title_key
"""
import csv
import json
import os
import sys

MOD = r'D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape'
CSV = os.path.join(MOD, 'gen_debug', 'eu5_ck3_title_map.csv')
POL = sys.argv[1] if len(sys.argv) > 1 else \
    r'D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export\eu5_politics.json'

p = json.load(open(POL, encoding='utf-8-sig'))
countries = p['countries']
relations = p['relations']
unions = p.get('unions') or {}
lowered = p.get('lowered') or {}
baronies = p.get('baronies') or {}

# 谁和谁共主
union_of = {}
for man, tags in unions.items():
    own = (p['characters'].get(man) or {}).get('tag')
    for t in tags:
        if t != own:
            union_of.setdefault(t, []).append((man, own))

# 附庸关系：second 是附庸，first 是领主
lord_of = {}
for rel in relations:
    a, b = rel.get('first'), rel.get('second')
    if a and b:
        lord_of.setdefault(b, []).append((a, rel.get('type'), rel.get('ck3')))

# 只有一块男爵领且标了 drop_title 的
dropped_baron = {}
for bk, info in baronies.items():
    if info.get('drop_title'):
        dropped_baron.setdefault(info.get('tag') or '', []).append(bk)

rows = [r for r in csv.DictReader(open(CSV, encoding='utf-8-sig')) if r['kind'] == 'country']
b = [r for r in rows if 'rank-title-dropped' in r['note']]

print('politics:', os.path.basename(os.path.dirname(POL)), '| B 类', len(b))
print()
cats = {}
for r in sorted(b, key=lambda x: x['eu5_tag']):
    tag = r['eu5_tag']
    c = countries.get(tag) or {}
    rank, ruler = c.get('rank'), c.get('ruler')
    reasons = []
    if not ruler:
        reasons.append('EU5 无统治者（ruler 空），头衔无人可持')
    if tag in union_of:
        for man, own in union_of[tag]:
            reasons.append('共主邦联：与 %s 同一君主（%s）' % (own or '?', man))
    for lord, typ, ck3 in lord_of.get(tag, []):
        lr = (countries.get(lord) or {}).get('rank')
        same = (countries.get(lord) or {}).get('ruler') == ruler
        reasons.append('附庸于 %s（rank=%s%s，type=%s）' % (
            lord, lr, '，同一君主' if same else '', typ))
    if tag in lowered:
        reasons.append('EU5 等级下调 %s→%s' % (lowered[tag].get('from'), lowered[tag].get('to')))
    if tag in dropped_baron:
        reasons.append('只有男爵领 %s 且 drop_title' % ','.join(dropped_baron[tag]))
    if not reasons:
        reasons.append('!! 未命中任何条件，需人工查')
    key = reasons[0].split('（')[0].split('：')[0]
    cats.setdefault(key, []).append(tag)
    print('%-4s %-13s rank=%-2s %-18s' % (tag, r['eu5_country_zh'], rank or '-', r['ck3_key'] or '-'))
    for x in reasons:
        print('      -', x)
print()
print('=== 原因分布 ===')
for k, v in sorted(cats.items(), key=lambda x: -len(x[1])):
    print('%-30s %2d  %s' % (k, len(v), ' '.join(v)))
