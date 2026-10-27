# -*- coding: utf-8 -*-
import csv, collections, os
BASE = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape\gen_debug"
rows = list(csv.DictReader(open(os.path.join(BASE, '_mod_eu5_high_titles_coverage_1337.csv'), encoding='utf-8-sig')))
g = collections.defaultdict(list)
for r in rows:
    g[r['status']].append(r)

T = [
    ('same', 'A. 原版有同名头衔（h_ / e_ / k_）'),
    ('renamed', 'B. 同一实体，但 mod 与原版名字不同'),
    ('only_duchy', 'C. 原版只有公国级同名'),
    ('only_lower', 'D. 原版只有伯爵领 / 男爵领同名'),
    ('none', 'E. 原版完全没有对应头衔'),
    ('no_holder', 'X. 开局无 holder（开局不存在 / 未使用），不计入'),
]
L = []
L.append('# mod 的 EU5 王国级以上头衔 × CK3 原版对应（只看 1337 开局有 holder 的）')
L.append('')
L.append('## 口径')
L.append('')
L.append('- **mod 侧**：`zz_eu5_titular.txt` 的 `e_eu5_*` / `k_eu5_*` 共 114 个；**只有 `history/titles/zz_eu5_titles.txt` 里在 1337.4.1 前有 holder 的 81 个算「开局存在」**，其余 33 个列为 X 类不计入。')
L.append('- **原版侧**：CK3 `common/landed_titles/*.txt` 的 `h_` / `e_` / `k_`（含 h_china「中华」等霸权）。')
L.append('- 判定先按中文名完全相等；B 类为人工判断的同一实体异名。')
L.append('')
L.append('## 汇总')
L.append('')
L.append('| 分类 | 数量 |')
L.append('| --- | --- |')
for k, label in T:
    L.append('| %s | %d |' % (label, len(g[k])))
L.append('')
for k, label in T:
    L.append('## %s（%d）' % (label, len(g[k])))
    L.append('')
    if not g[k]:
        L.append('（无）')
        L.append('')
        continue
    L.append('| 名字 | mod 头衔 | 原版对应 |')
    L.append('| --- | --- | --- |')
    for r in sorted(g[k], key=lambda x: x['name']):
        L.append('| %s | %s | %s |' % (r['name'], r['mod_title'], r['vanilla'] or '—'))
    L.append('')

out = os.path.join(BASE, '_mod_eu5_high_titles_coverage_1337.md')
open(out, 'w', encoding='utf-8', newline='\n').write('\n'.join(L))
print('写出:', out)
for k, label in T:
    print(label, len(g[k]))
