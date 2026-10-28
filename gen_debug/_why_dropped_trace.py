# -*- coding: utf-8 -*-
"""只读：复现 _fix_politics_output.py 的 dropped 构造，标出每个 key 由哪一段产生。

不再按"领主是谁"猜原因，而是直接跑生成器的五个分支：
  demoted    (L528-546) rank=d 且 只有 1 个伯爵领 且 自己不是任何人的领主
  lowered    (L567-570) EU5 把等级下调过
  baron      (L571-579) 只剩一块男爵领且 drop_title
  daimyo     (L593-602) 幕府成员但 rank 不是 d/k/e
  no_ruler   (L604-612) rank=d/k/e 但没有 ruler
"""
import csv
import io
import json
import os
import re
from collections import Counter

MOD = r'D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape'
EXPORT = r'D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export'
CSV = os.path.join(MOD, 'gen_debug', 'eu5_ck3_title_map.csv')

p = json.load(io.open(os.path.join(EXPORT, 'eu5_politics.json'), encoding='utf-8-sig'))
countries = p['countries']
relations = p['relations']
lowered = p.get('lowered') or {}
baronies = p.get('baronies') or {}
county = p.get('counties') or {}
characters = p.get('characters') or {}


def ctk(rank, tag):
    if tag == 'PAP':
        return 'k_papal_state'
    return '%s_eu5_%s' % (rank, tag.lower())


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

county_count = Counter()
for info in county.values():
    if info.get('owner'):
        county_count[info['owner']] += 1
lords = {rel['first'] for rel in relations if rel.get('ck3') == 'vassal'}

src = {}
detail = {}

# --- demoted ---
demoted = {}
for tag, rel in liege_rel.items():
    sub = countries.get(tag) or {}
    if sub.get('rank') != 'd' or county_count.get(tag) != 1:
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
    src[title_key[tag]] = 'demoted'
    detail[title_key[tag]] = {
        'rank': sub.get('rank'), 'counties': county_count.get(tag, 0),
        'lord': rel['first'], 'type': rel.get('type'),
        'lord_rank': (countries.get(rel['first']) or {}).get('rank'),
        'same_ruler': (countries.get(rel['first']) or {}).get('ruler') == sub.get('ruler'),
    }

# --- lowered ---
for tag, was in lowered.items():
    old = was.get('from')
    if old in ('d', 'k', 'e'):
        k = ctk(old, tag)
        src.setdefault(k, 'lowered')
        detail.setdefault(k, {'from': old, 'to': was.get('to')})

# --- baronies drop_title ---
for bk, baron in baronies.items():
    tag = baron.get('tag') or ''
    if not baron.get('drop_title') or not title_key.get(tag):
        continue
    k = title_key[tag]
    src.setdefault(k, 'baron')
    detail.setdefault(k, {'barony': bk})

# --- daimyo ---
daimyo = set()
for org in p['organizations']:
    if org['type'] == 'japanese_shogunate':
        daimyo = set(org['members'])
for tag, c in countries.items():
    if tag not in daimyo or c.get('rank') in ('d', 'k', 'e'):
        continue
    for rank in ('d', 'k', 'e'):
        k = ctk(rank, tag)
        src.setdefault(k, 'daimyo')
        detail.setdefault(k, {'rank': c.get('rank')})

# --- no ruler ---
for tag, c in countries.items():
    if c.get('rank') not in ('d', 'k', 'e') or c.get('ruler'):
        continue
    if title_key.get(tag) and liege_title.get(tag):
        k = title_key[tag]
        src.setdefault(k, 'no_ruler')
        detail.setdefault(k, {'rank': c.get('rank'), 'liege': liege_title.get(tag)})

rows = [r for r in csv.DictReader(io.open(CSV, encoding='utf-8-sig')) if r['kind'] == 'country']
b = sorted([r for r in rows if 'rank-title-dropped' in r['note']], key=lambda x: x['eu5_tag'])

NOTE = re.compile(r'rank-title-dropped\s*\(([^)]+)\)')

print('B 类行数:', len(b))
print()
cnt = Counter()
miss = []
for r in b:
    m = NOTE.search(r['note'])
    k = m.group(1) if m else '?'
    s = src.get(k, '未命中')
    cnt[s] += 1
    d = detail.get(k) or {}
    tag = r['eu5_tag']
    c = countries.get(tag) or {}
    print('%-5s %-10s %s→%-3s key=%-14s src=%-9s rank=%s counties=%s lord=%s type=%s lord_rank=%s %s'
          % (tag, r['eu5_country_zh'], r['eu5_tier'], r['ck3_tier'] or '空', k, s,
             c.get('rank'), county_count.get(tag, 0),
             d.get('lord', '-'), d.get('type', '-'), d.get('lord_rank', '-'),
             ('same_ruler' if d.get('same_ruler') else '')))
    if s == '未命中':
        miss.append((tag, k, r['note']))
print()
print('来源分布:', dict(cnt))
if miss:
    print('未命中:')
    for x in miss:
        print('  ', x)
