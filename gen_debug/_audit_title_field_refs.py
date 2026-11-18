# -*- coding: utf-8 -*-
"""只读：校验原版 rank>=k 头衔里待补字段所引用的 culture / heritage / faith / title / scripted_trigger
在本 mod（+ 游戏原版）里是否都存在。"""
import os
import re
import glob
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _audit_title_dynamic_fields import parse_blocks, GAME, TITLE_RE, KEY_RE, MOD

GAME_COMMON = os.path.join(GAME, '..')
MOD_COMMON = os.path.join(MOD, 'common')


def collect_keys(patterns, extra_dirs=()):
    keys = set()
    for pat in patterns:
        for d in list(extra_dirs) + [GAME_COMMON, MOD_COMMON]:
            for f in glob.glob(os.path.join(d, pat)):
                for line in open(f, encoding='utf-8-sig', errors='replace'):
                    m = KEY_RE.match(line.strip())
                    if m:
                        keys.add(m.group(1))
                    else:
                        m2 = re.match(r'^([A-Za-z_][A-Za-z0-9_.\-]*)\s*=\s*(yes|no|\{)', line.strip())
                        if m2:
                            keys.add(m2.group(1))
    return keys


def collect_titles():
    keys = set()
    for d in [os.path.join(GAME_COMMON, 'landed_titles'), os.path.join(MOD_COMMON, 'landed_titles')]:
        for f in glob.glob(os.path.join(d, '*.txt')):
            for line in open(f, encoding='utf-8-sig', errors='replace'):
                m = re.match(r'^\s*([hedcb]_[A-Za-z0-9_.\-]+)\s*=\s*\{', line)
                if m:
                    keys.add(m.group(1))
    return keys


def main():
    cultures = collect_keys(['culture/cultures/*.txt', 'culture/cultures/*/*.txt'])
    pillars = collect_keys(['culture/pillars/*.txt', 'culture/pillars/*/*.txt'])
    faiths = collect_keys(['religion/religions/*.txt', 'religion/religions/*/*.txt'])
    triggers = collect_keys(['scripted_triggers/*.txt'])
    titles = collect_titles()

    print('cultures %d / pillars %d / faiths %d / triggers %d / titles %d'
          % (len(cultures), len(pillars), len(faiths), len(triggers), len(titles)))

    game = parse_blocks(open(os.path.join(GAME, '00_landed_titles.txt'),
                             encoding='utf-8-sig', errors='replace').read().splitlines())
    lines = open(os.path.join(GAME, '00_landed_titles.txt'),
                 encoding='utf-8-sig', errors='replace').read().splitlines()

    def block_text(rec):
        start = rec['start']
        depth = 0
        out = []
        for i in range(start, len(lines)):
            l = lines[i]
            out.append(l)
            depth += l.count('{') - l.count('}')
            if depth <= 0:
                break
        return out

    bad = collections.defaultdict(list)
    for key, recs in game.items():
        if not key.startswith(('h_', 'e_', 'k_')):
            continue
        for rec in recs:
            txt = '\n'.join(block_text(rec))
            for m in re.finditer(r'culture:([A-Za-z0-9_]+)', txt):
                if m.group(1) not in cultures:
                    bad['culture'].append((key, m.group(1)))
            for m in re.finditer(r'has_cultural_pillar\s*=\s*([A-Za-z0-9_]+)', txt):
                if m.group(1) not in pillars:
                    bad['pillar'].append((key, m.group(1)))
            for m in re.finditer(r'faith:([A-Za-z0-9_]+)', txt):
                if m.group(1) not in faiths:
                    bad['faith'].append((key, m.group(1)))
            for m in re.finditer(r'title:([hedcb]_[A-Za-z0-9_.\-]+)', txt):
                if m.group(1) not in titles:
                    bad['title'].append((key, m.group(1)))
            for m in re.finditer(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*yes\s*$', txt, re.M):
                pass
    if not bad:
        print('所有引用均可解析')
    for k, v in bad.items():
        print('\n[%s] 无法解析 %d 处:' % (k, len(v)))
        for t, ref in v:
            print('  %-28s %s' % (t, ref))


if __name__ == '__main__':
    main()
