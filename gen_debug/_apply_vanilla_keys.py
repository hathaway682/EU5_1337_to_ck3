# -*- coding: utf-8 -*-
"""把 A/B 类（含术赤）的 mod 自造 titular key 替换成 CK3 原版 key。
只改 gen_debug/eu5_ck3_title_map.csv：
  - ck3_key  列：old -> new
  - ck3_tier 列：跟随新 key 前缀
  - ck3_name_en / ck3_name_zh：换成原版头衔的名字
  - ck3_liege 列：全表联动替换（引用同一批 key 的行）
"""
import csv
import os
import re
import sys

MOD = r'D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape'
CK3 = r'E:\SteamLibrary\steamapps\common\Crusader Kings III\game'
CSV = os.path.join(MOD, 'gen_debug', 'eu5_ck3_title_map.csv')

# old(mod key) -> new(vanilla key)
MAP = {
    # A 类：原版有同名
    'e_eu5_chi': 'h_china',
    'k_eu5_dan': 'k_denmark',
    'k_eu5_yem': 'k_yemen',
    'e_eu5_bul': 'k_bulgaria',
    'k_eu5_cro': 'k_croatia',
    'e_eu5_kbo': 'e_kanem_bornu',
    'k_eu5_hun': 'k_hungary',
    'k_eu5_cha': 'k_champa',
    'k_eu5_cas': 'k_castille',
    'k_eu5_tib': 'e_tibet',
    'k_eu5_mam': 'k_egypt',
    'k_eu5_ser': 'k_serbia',
    'k_eu5_cyp': 'k_cyprus',
    'k_eu5_dai': 'k_viet',
    'k_eu5_chg': 'e_chagatai',
    'k_eu5_vlr': 'k_opolye',
    'k_eu5_dlh': 'k_delhi',
    'k_eu5_nor': 'k_norway',
    'e_eu5_jap': 'e_japan',
    'k_eu5_geo': 'k_georgia',
    'k_eu5_fra': 'k_france',
    'k_eu5_pol': 'k_poland',
    'k_eu5_boh': 'k_bohemia',
    'k_eu5_maj': 'e_majapahit',
    'e_eu5_tre': 'k_trebizond',
    'k_eu5_swe': 'k_sweden',
    'k_eu5_nav': 'k_navarra',
    'k_eu5_sco': 'k_scotland',
    'k_eu5_eng': 'k_england',
    'k_eu5_por': 'k_portugal',
    'k_eu5_sic': 'k_sicily',
    'k_eu5_nap': 'k_naples',
    'k_eu5_ara': 'k_aragon',
    'k_eu5_aju': 'k_ajuraan',
    'e_eu5_mal': 'e_mali',
    # B 类：同一实体、名字不同
    'e_eu5_eth': 'e_abyssinia',
    'e_eu5_byz': 'e_byzantium',
    'k_eu5_mor': 'k_maghreb',
    'k_eu5_jmb': 'k_malayadvipa',
    'k_eu5_kor': 'e_goryeo',
    'k_eu5_qch': 'k_dzungaria',
    'e_eu5_khm': 'e_kambuja',
    # 用户指定：术赤
    'k_eu5_glh': 'e_golden_horde',
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

    missing = [k for k in MAP.values() if k not in zh]
    if missing:
        print('!! 缺中文名:', missing)

    rows = list(csv.DictReader(open(CSV, encoding='utf-8-sig')))
    fields = list(rows[0].keys())

    changed = {'key': 0, 'liege': 0}
    log = []
    for r in rows:
        old = r['ck3_key']
        if old in MAP:
            new = MAP[old]
            r['ck3_key'] = new
            r['ck3_tier'] = new.split('_')[0]
            r['ck3_name_en'] = en.get(new, r['ck3_name_en'])
            r['ck3_name_zh'] = zh.get(new, r['ck3_name_zh'])
            changed['key'] += 1
            log.append((r['kind'], r['eu5_tag'], old, new, r['ck3_name_zh']))
        if r['ck3_liege'] in MAP:
            r['ck3_liege'] = MAP[r['ck3_liege']]
            changed['liege'] += 1

    # 冲突检查：改完后 ck3_key 是否有重复
    from collections import Counter
    dup = [(k, c) for k, c in Counter(x['ck3_key'] for x in rows).items() if c > 1 and k]

    tmp = CSV + '.tmp'
    with open(tmp, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator='\r\n')
        w.writeheader()
        w.writerows(rows)

    print('ck3_key 改动行:', changed['key'], ' ck3_liege 改动行:', changed['liege'])
    print('ck3_key 重复:', dup if dup else '无')
    print('--- 明细 ---')
    for x in log:
        print('  %-8s %-4s %-12s -> %-16s %s' % x)


if __name__ == '__main__':
    main()
