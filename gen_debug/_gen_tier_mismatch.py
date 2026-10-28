# -*- coding: utf-8 -*-
"""回溯：EU5 等级与 CK3 头衔等级不一致的国家，分类给原因。只读，输出 CSV + MD。"""
import csv
import os
from collections import Counter, defaultdict

MOD = r'D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape'
CSV = os.path.join(MOD, 'gen_debug', 'eu5_ck3_title_map.csv')
OUT_CSV = os.path.join(MOD, 'gen_debug', '_tier_mismatch.csv')
OUT_MD = os.path.join(MOD, 'gen_debug', '_tier_mismatch.md')

# A 类：主动按原版 key 调整层级
A_UP = {
    'TIB': ('k→e', '原版只有 e_tibet，无 k_ 级'),
    'CHG': ('k→e', '原版只有 e_chagatai，无 k_ 级'),
    'MAJ': ('k→e', '原版只有 e_majapahit，无 k_ 级'),
    'KOR': ('k→e', '原版只有 e_goryeo，无 k_ 级'),
    'GLH': ('k→e', '原版只有 e_golden_horde，无 k_ 级'),
    'BUL': ('e→k', '原版只有 k_bulgaria，无 e_ 级'),
    'TRE': ('e→k', '原版只有 k_trebizond，无 e_ 级'),
    'CHI': ('e→h', '原版最高是霸权 h_china，无 e_china'),
    'AYD': ('d→k', 'EU5 贝伊国为公国级，原版有 k_aydin'),
    'MEN': ('d→k', 'EU5 贝伊国为公国级，原版有 k_mentese'),
    'ERE': ('d→k', 'EU5 贝伊国为公国级，原版有 k_eretnid'),
    'TUR': ('d→k', 'EU5 贝伊国为公国级，原版有 k_ottoman'),
    'SRU': ('-→k', 'EU5 无 rank，原版有 k_saruhan'),
    'KAR': ('-→k', 'EU5 无 rank，原版有 k_karaman'),
    'GRM': ('-→k', 'EU5 无 rank，原版有 k_germiyan'),
    'TEK': ('-→k', 'EU5 无 rank，原版有 k_tekke'),
    'CND': ('-→k', 'EU5 无 rank，原版有 k_candar'),
}


def classify(r):
    tag = r['eu5_tag']
    if r['eu5_tier'] == r['ck3_tier']:
        return 'same', ''
    if tag in A_UP:
        return 'A', A_UP[tag][1]
    if 'rank-title-dropped' in r['note']:
        return 'B', '作为附庸/共主次级成员，CK3 不允许同级附庸，降级后挂到实际领地'
    if r['eu5_tier'] == '-':
        return 'C', 'EU5 未给 rank（城邦/部落/共联次级），按实际领地挂'
    return 'D', 'EU5 与 CK3 地图粒度不同'


def main():
    rows = [r for r in csv.DictReader(open(CSV, encoding='utf-8-sig')) if r['kind'] == 'country']
    out = []
    for r in rows:
        kind, reason = classify(r)
        if kind == 'same':
            continue
        out.append({
            'category': kind, 'eu5_tier': r['eu5_tier'], 'ck3_tier': r['ck3_tier'],
            'eu5_tag': r['eu5_tag'], 'eu5_name_zh': r['eu5_country_zh'],
            'ck3_key': r['ck3_key'], 'reason': reason, 'note': r['note'],
        })
    out.sort(key=lambda x: (x['category'], x['eu5_tier'], x['ck3_tier'], x['eu5_tag']))
    with open(OUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()), lineterminator='\r\n')
        w.writeheader()
        w.writerows(out)

    cnt = Counter((x['category'], x['eu5_tier'], x['ck3_tier']) for x in out)
    same = sum(1 for r in rows if r['eu5_tier'] == r['ck3_tier'])

    L = ['# EU5 与 CK3 头衔等级不一致的国家（回溯）', '',
         '来源：`eu5_ck3_title_map.csv` 的 `kind=country` 行，比较 `eu5_tier` 与 `ck3_tier`。', '',
         '- 总数 %d，其中等级一致 %d、不一致 **%d**。' % (len(rows), same, len(out)), '',
         '## 分类计数', '', '| 类别 | EU5→CK3 | 数量 |', '| --- | --- | --- |']
    for (cat, a, b), n in sorted(cnt.items()):
        L.append('| %s | %s→%s | %d |' % (cat, a, b or '空', n))
    L.append('')

    titles = {
        'A': '## A. 主动按原版 key 调整层级',
        'B': '## B. 为了成为别人的附庸而降级（rank-title-dropped）',
        'C': '## C. EU5 未给 rank，按实际领地挂',
        'D': '## D. 粒度差异',
    }
    for cat in ['A', 'B', 'C', 'D']:
        items = [x for x in out if x['category'] == cat]
        L.append(titles[cat] + '（%d）' % len(items))
        L.append('')
        if cat == 'A':
            L.append('| EU5 | 中文名 | 变化 | 原版 key | 原因 |')
            L.append('| --- | --- | --- | --- | --- |')
            for x in items:
                L.append('| %s | %s | %s | %s | %s |' % (
                    x['eu5_tag'], x['eu5_name_zh'], A_UP[x['eu5_tag']][0], x['ck3_key'], x['reason']))
        else:
            L.append('| EU5 | 中文名 | EU5→CK3 | 现头衔 | note |')
            L.append('| --- | --- | --- | --- | --- |')
            for x in items:
                L.append('| %s | %s | %s→%s | %s | %s |' % (
                    x['eu5_tag'], x['eu5_name_zh'], x['eu5_tier'], x['ck3_tier'] or '空',
                    x['ck3_key'] or '—', x['note'][:70]))
        L.append('')
    open(OUT_MD, 'w', encoding='utf-8').write('\n'.join(L))
    print('总数', len(rows), '一致', same, '不一致', len(out))
    for k, v in sorted(cnt.items()):
        print(' ', k, v)


if __name__ == '__main__':
    main()
