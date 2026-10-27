# -*- coding: utf-8 -*-
"""由 _eu5_country_vs_ck3_title_samename.csv 生成分层 Markdown 报告"""
import csv, collections, os

BASE = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape\gen_debug"
rows = list(csv.DictReader(open(os.path.join(BASE, '_eu5_country_vs_ck3_title_samename.csv'), encoding='utf-8-sig')))

by = collections.defaultdict(list)
for r in rows:
    by[r['name']].append((r['eu5_tag'], r['ck3_title']))

TIER = [('e', '帝国级 e_'), ('k', '王国级 k_'), ('d', '公国级 d_'), ('c', '伯爵领 c_'), ('b', '男爵领 b_')]

def top_tier(titles):
    for c, _ in TIER:
        if any(t[1][0] == c for t in titles):
            return c
    return 'b'

groups = collections.defaultdict(list)
for n, v in by.items():
    groups[top_tier(v)].append(n)

lines = []
lines.append('# EU5 国家名 与 CK3 原版头衔名 同名词表')
lines.append('')
lines.append('数据源：')
lines.append('')
lines.append('- EU5：`Europa Universalis V/game/in_game/setup/countries/*.txt` 中定义的 2310 个国家 tag，中文名取 `main_menu/localization/simp_chinese/country_names_l_simp_chinese.yml`（及其它 simp_chinese 文件）中的 `TAG:` 条目。')
lines.append('- CK3：`Crusader Kings III/game/common/landed_titles/*.txt` 中定义的 17297 个头衔（e_/k_/d_/c_/b_），中文名取 `game/localization/simp_chinese/` 中的同名 key。')
lines.append('- 比对规则：中文字符串完全相等（已解析 `$var$` 引用与 `#格式` 标记）。')
lines.append('')
lines.append('合计：**%d 个不同的名字**，对应 **%d 条 (名字, EU5 tag, CK3 头衔) 组合**。' % (len(by), len(rows)))
lines.append('')
lines.append('按该名字在 CK3 中出现的最高头衔层级分组：')
lines.append('')
for c, label in TIER:
    lines.append('- %s：%d 个名字' % (label, len(groups[c])))
lines.append('')
lines.append('> 说明：一个名字可能同时命中多个层级的头衔（例如「威尼斯」同时是 k_venice / d_venice / c_venezia / b_venezia），本表按最高层级归档，括号内列出全部命中的 CK3 头衔。')
lines.append('')

for c, label in TIER:
    if not groups[c]:
        continue
    lines.append('## %s（%d）' % (label, len(groups[c])))
    lines.append('')
    lines.append('| 名字 | EU5 tag | CK3 头衔 |')
    lines.append('| --- | --- | --- |')
    for n in sorted(groups[c]):
        v = by[n]
        tags = '、'.join(sorted(set(t for t, _ in v)))
        titles = '、'.join(sorted(set(tk for _, tk in v)))
        lines.append('| %s | %s | %s |' % (n, tags, titles))
    lines.append('')

out = os.path.join(BASE, '_eu5_country_vs_ck3_title_samename.md')
open(out, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
print('写出:', out)
print('名字数:', len(by), ' 组合数:', len(rows))
for c, label in TIER:
    print(label, len(groups[c]))
