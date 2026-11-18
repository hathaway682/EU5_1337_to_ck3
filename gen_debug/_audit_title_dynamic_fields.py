# -*- coding: utf-8 -*-
"""
只读审计：原版 landed_titles 里 rank>=k 的头衔块内的「非子头衔字段」
（cultural_names / ai_primary_priority / definite_form / ruler_uses_title_name ...），
本 mod 同名头衔块是否缺失。

用法: python gen_debug/_audit_title_dynamic_fields.py
输出: gen_debug/_title_dynamic_fields_report.txt
"""
import os
import re
import glob
import collections

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = r"D:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III Beta\game\common\landed_titles"

KEY_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_.\-]*)\s*=\s*\{')
TITLE_RE = re.compile(r'^([hedcbk])_')
RANK = ('h_', 'e_', 'k_')


def parse_blocks(lines):
    """返回 {key: [ {start, fields:set, child_blocks:set} ]}，只保留头衔 key"""
    out = collections.defaultdict(list)
    stack = []  # {'key','depth','start','fields','blocks','is_title'}
    depth = 0
    for i, raw in enumerate(lines):
        line = raw
        if '#' in line:
            line = line.split('#')[0]
        line = line.strip()
        if not line:
            continue
        opens = line.count('{')
        closes = line.count('}')
        m = KEY_RE.match(line)
        if m and opens > closes:
            key = m.group(1)
            is_title = bool(TITLE_RE.match(key))
            node = {'key': key, 'depth': depth, 'start': i,
                    'fields': set(), 'blocks': set(), 'is_title': is_title}
            if stack:
                stack[-1]['blocks'].add(key)
            stack.append(node)
            depth += 1
            if opens - closes > 1:
                depth += opens - closes - 1
            continue
        # 字段行
        fm = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*[=<]', line)
        if fm and stack:
            stack[-1]['fields'].add(fm.group(1))
        depth += opens - closes
        while stack and depth <= stack[-1]['depth']:
            node = stack.pop()
            if node['is_title']:
                out[node['key']].append(node)
    while stack:
        node = stack.pop()
        if node['is_title']:
            out[node['key']].append(node)
    return out


def load_dir(path):
    out = collections.defaultdict(list)
    for f in sorted(glob.glob(os.path.join(path, '*.txt'))):
        lines = open(f, encoding='utf-8-sig', errors='replace').read().splitlines()
        for key, recs in parse_blocks(lines).items():
            for rec in recs:
                rec['file'] = os.path.basename(f)
                out[key].append(rec)
    return out


def main():
    game = load_dir(GAME)
    mod = load_dir(os.path.join(MOD, 'common', 'landed_titles'))

    ranks = sorted(k for k in game if k.startswith(RANK))
    print('原版 rank>=k 头衔数:', len(ranks))
    freq = collections.Counter()
    for k in ranks:
        for rec in game[k]:
            for f in rec['fields']:
                freq[f] += 1
            for f in rec['blocks']:
                if not TITLE_RE.match(f):
                    freq[f] += 1
    print('原版 rank>=k 块内字段频次:')
    for f, c in freq.most_common():
        print('  %-30s %d' % (f, c))

    interesting = {f for f in freq if f not in ('color', 'color2', 'capital')}
    rows = []
    for k in ranks:
        if k not in mod:
            continue
        gf = set()
        for rec in game[k]:
            gf |= rec['fields']
            gf |= {b for b in rec['blocks'] if not TITLE_RE.match(b)}
        mf = set()
        for rec in mod[k]:
            mf |= rec['fields']
            mf |= {b for b in rec['blocks'] if not TITLE_RE.match(b)}
        missing = sorted(f for f in gf if f in interesting and f not in mf)
        if missing:
            rows.append((k, missing, game[k][0]['file'], game[k][0]['start'] + 1))

    out = os.path.join(MOD, 'gen_debug', '_title_dynamic_fields_report.txt')
    with open(out, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('原版 rank>=k 头衔数: %d\n' % len(ranks))
        fh.write('原版 rank>=k 块内字段频次:\n')
        for f, c in freq.most_common():
            fh.write('  %-30s %d\n' % (f, c))
        fh.write('\n两边都有、但 mod 缺失字段的头衔: %d\n' % len(rows))
        fh.write('缺失字段统计: %s\n\n' % dict(collections.Counter(m for r in rows for m in r[1])))
        for k, miss, gf, gl in rows:
            fh.write('%s\t%s\t%s:%d\n' % (k, ','.join(miss), gf, gl))
    print('\n报告:', out)
    print('两边都有且缺字段的头衔:', len(rows))
    print('缺失字段统计:', dict(collections.Counter(m for r in rows for m in r[1])))


if __name__ == '__main__':
    main()
