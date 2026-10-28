# -*- coding: utf-8 -*-
"""把 9 个安纳托利亚贝伊国在 title_map 里的 country 行改成王国级原版 key。"""
import csv
import os
import re

MOD = r'D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape'
CK3 = r'E:\SteamLibrary\steamapps\common\Crusader Kings III\game'
CSV = os.path.join(MOD, 'gen_debug', 'eu5_ck3_title_map.csv')

# eu5_tag -> (old_key, new_key)
BEY = {
    'AYD': ('d_eu5_ayd', 'k_aydin'),
    'SRU': ('c_saruhan', 'k_saruhan'),
    'MEN': ('d_eu5_men', 'k_mentese'),
    'KAR': ('c_konya', 'k_karaman'),
    'GRM': ('c_kutahya', 'k_germiyan'),
    'TEK': ('c_antalya', 'k_tekke'),
    'ERE': ('d_eu5_ere', 'k_eretnid'),
    'CND': ('c_kastamonu', 'k_candar'),
    'TUR': ('d_eu5_tur', 'k_ottoman'),
}

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

    rows = list(csv.DictReader(open(CSV, encoding='utf-8-sig')))
    fields = list(rows[0].keys())
    n_key = n_liege = 0
    for r in rows:
        if r['kind'] == 'country' and r['eu5_tag'] in BEY:
            old, new = BEY[r['eu5_tag']]
            if r['ck3_key'] != old:
                print('!! %s 当前 key 不是 %s（是 %s），跳过' % (r['eu5_tag'], old, r['ck3_key']))
                continue
            r['ck3_key'] = new
            r['ck3_tier'] = 'k'
            r['ck3_name_en'] = en.get(new, r['ck3_name_en'])
            r['ck3_name_zh'] = zh.get(new, r['ck3_name_zh'])
            n_key += 1
            print('  %-4s %-14s -> %-12s %s / %s' % (
                r['eu5_tag'], old, new, r['ck3_name_en'], r['ck3_name_zh']))
        if r['ck3_liege'] == 'd_eu5_men':
            r['ck3_liege'] = 'k_mentese'
            n_liege += 1

    with open(CSV, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator='\r\n')
        w.writeheader()
        w.writerows(rows)
    print('country 行改 %d 条，liege 改 %d 条' % (n_key, n_liege))


if __name__ == '__main__':
    main()
