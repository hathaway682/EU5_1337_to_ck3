# -*- coding: utf-8 -*-
"""生成「mod 当前不是王国级、但 CK3 原版存在同名王国级头衔」的清单（CSV + MD）。"""
import csv
import os
import re

MOD = r'D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape'
CK3 = r'E:\SteamLibrary\steamapps\common\Crusader Kings III\game'
CSV = os.path.join(MOD, 'gen_debug', 'eu5_ck3_title_map.csv')
OUT_CSV = os.path.join(MOD, 'gen_debug', '_non_kingdom_with_vanilla_k.csv')
OUT_MD = os.path.join(MOD, 'gen_debug', '_non_kingdom_with_vanilla_k.md')

LOC_RE = re.compile(r'^\s*([A-Za-z0-9_.\-]+)\s*:\s*(?:\d+\s*)?"(.*?)"\s*(?:#.*)?$')

# 中文/英文名对不上但确认是同一实体的人工别名
ALIAS = {
    'CND': 'k_candar',   # EU5 詹达尔 = 原版 钱达尔
    'TUR': 'k_ottoman',  # EU5 奥斯曼 = 原版 奥斯曼突厥
}


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

    kv = set()
    root = os.path.join(CK3, 'common', 'landed_titles')
    for fn in sorted(os.listdir(root)):
        if not fn.endswith('.txt'):
            continue
        for line in open(os.path.join(root, fn), 'rb').read().decode('utf-8', 'replace').splitlines():
            m = re.match(r'^\s*(k_[A-Za-z0-9_]+)\s*=\s*\{', line)
            if m:
                kv.add(m.group(1))

    by_zh, by_en = {}, {}
    for k in kv:
        if k in zh:
            by_zh.setdefault(zh[k], []).append(k)
        if k in en:
            by_en.setdefault(en[k], []).append(k)

    rows = list(csv.DictReader(open(CSV, encoding='utf-8-sig')))
    out = []
    for r in rows:
        if r['kind'] != 'country' or r['ck3_tier'] in ('e', 'k', 'h'):
            continue
        tag = r['eu5_tag']
        zh_name, en_name = r['eu5_country_zh'], r['eu5_country_en']
        cand = []
        if tag in ALIAS:
            cand = [ALIAS[tag]]
        elif zh_name and zh_name in by_zh:
            cand = by_zh[zh_name]
        elif en_name and en_name in by_en:
            cand = by_en[en_name]
        if not cand:
            continue
        vk = sorted(cand)[0]
        t = r['ck3_tier']
        if not r['ck3_key']:
            kind = '无头衔'
        elif t == 'd':
            kind = '已有公国级头衔'
        elif t == 'c':
            kind = '挂在伯爵领'
        elif t == 'b':
            kind = '挂在男爵领'
        else:
            kind = '其他'
        out.append({
            'tag': tag, 'eu5_tier': r['eu5_tier'], 'eu5_name_zh': zh_name, 'eu5_name_en': en_name,
            'mod_key': r['ck3_key'], 'mod_tier': t, 'vanilla_k': vk,
            'vanilla_k_zh': zh.get(vk, ''), 'kind': kind,
        })

    out.sort(key=lambda x: (x['kind'], x['tag']))
    with open(OUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()), lineterminator='\r\n')
        w.writeheader()
        w.writerows(out)

    groups = {}
    for x in out:
        groups.setdefault(x['kind'], []).append(x)
    lines = ['# mod 里不是王国级、但 CK3 原版有同名王国级头衔的 EU5 国家', '',
             '口径：`eu5_ck3_title_map.csv` 中 `kind=country` 且 `ck3_tier` 不是 e/k/h 的行；',
             '按 EU5 国家名（中/英）匹配原版 `k_` 头衔名，另有 2 条人工别名。', '',
             '合计 **%d** 个。' % len(out), '']
    for kind in ['已有公国级头衔', '挂在伯爵领', '挂在男爵领', '无头衔']:
        items = groups.get(kind, [])
        lines.append('## %s（%d）' % (kind, len(items)))
        lines.append('')
        lines.append('| EU5 | 中文名 | mod 头衔 | 原版王国级 |')
        lines.append('| --- | --- | --- | --- |')
        for x in items:
            lines.append('| %s | %s | %s | %s「%s」 |' % (
                x['tag'], x['eu5_name_zh'], x['mod_key'] or '—', x['vanilla_k'], x['vanilla_k_zh']))
        lines.append('')
    open(OUT_MD, 'w', encoding='utf-8').write('\n'.join(lines))

    print('共', len(out), '个')
    for kind in ['已有公国级头衔', '挂在伯爵领', '挂在男爵领', '无头衔']:
        print(' ', kind, len(groups.get(kind, [])))


if __name__ == '__main__':
    main()
