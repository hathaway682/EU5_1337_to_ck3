# -*- coding: utf-8 -*-
"""找出 mod 当前不是王国级（ck3_tier 不是 e/k/h）、但 CK3 原版存在同名王国级头衔的 EU5 国家。"""
import csv
import os
import re

MOD = r'D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape'
CK3 = r'E:\SteamLibrary\steamapps\common\Crusader Kings III\game'
CSV = os.path.join(MOD, 'gen_debug', 'eu5_ck3_title_map.csv')

LOC_RE = re.compile(r'^\s*([A-Za-z0-9_.\-]+)\s*:\s*(?:\d+\s*)?"(.*?)"\s*(?:#.*)?$')


def walk_yml(root):
    d = {}
    for dp, _, fns in os.walk(root):
        for fn in sorted(fns):
            if not fn.endswith('.yml'):
                continue
            raw = open(os.path.join(dp, fn), 'rb').read()
            if raw.startswith(b'\xef\xbb\xbf'):
                raw = raw[3:]
            for line in raw.decode('utf-8', 'replace').splitlines():
                m = LOC_RE.match(line)
                if m:
                    d[m.group(1)] = m.group(2)
    return d


def main():
    en = walk_yml(os.path.join(CK3, 'localization', 'english'))
    zh = walk_yml(os.path.join(CK3, 'localization', 'simp_chinese'))

    # 原版 k_ 头衔定义
    kv = set()
    root = os.path.join(CK3, 'common', 'landed_titles')
    for fn in sorted(os.listdir(root)):
        if not fn.endswith('.txt'):
            continue
        for line in open(os.path.join(root, fn), 'rb').read().decode('utf-8', 'replace').splitlines():
            m = re.match(r'^\s*(k_[A-Za-z0-9_]+)\s*=\s*\{', line)
            if m:
                kv.add(m.group(1))

    by_zh = {}
    by_en = {}
    for k in kv:
        if k in zh:
            by_zh.setdefault(zh[k], []).append(k)
        if k in en:
            by_en.setdefault(en[k], []).append(k)

    rows = list(csv.DictReader(open(CSV, encoding='utf-8-sig')))
    hits = []
    for r in rows:
        if r['kind'] != 'country':
            continue
        if r['ck3_tier'] in ('e', 'k', 'h'):
            continue
        zh_name = r['eu5_country_zh']
        en_name = r['eu5_country_en']
        cand = []
        if zh_name and zh_name in by_zh:
            cand = by_zh[zh_name]
        elif en_name and en_name in by_en:
            cand = by_en[en_name]
        if cand:
            hits.append((r['eu5_tag'], r['eu5_tier'], r['ck3_key'], r['ck3_tier'],
                         zh_name, en_name, '、'.join(sorted(cand))))

    print('命中:', len(hits))
    print('%-5s %-4s %-16s %-3s %-14s %-22s %s' % ('tag', 'eu5', 'ck3_key', 't', '中文名', '英文名', '原版王国级'))
    for h in sorted(hits):
        print('%-5s %-4s %-16s %-3s %-14s %-22s %s' % h)


if __name__ == '__main__':
    main()
