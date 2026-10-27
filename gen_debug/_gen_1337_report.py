# -*- coding: utf-8 -*-
"""由 _eu5_1337_vs_ck3_high_title_samename.csv 生成 Markdown 报告"""
import csv, collections, os

BASE = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape\gen_debug"
rows = list(csv.DictReader(open(os.path.join(BASE, '_eu5_1337_vs_ck3_high_title_samename.csv'), encoding='utf-8-sig')))

by = collections.defaultdict(list)
for r in rows:
    by[r['name']].append(r)

def top(r):
    t = r['ck3_title']
    return t[0]

groups = collections.defaultdict(list)
for n, v in by.items():
    groups[min(top(r) for r in v)].append(n)  # e<k<d 字母序 e,d,k 不行

TIER = ['e', 'k', 'd']
def topt(v):
    for c in TIER:
        if any(top(r) == c for r in v):
            return c
    return 'd'
groups = collections.defaultdict(list)
for n, v in by.items():
    groups[topt(v)].append(n)

LABEL = {'e': '帝国级 e_', 'k': '王国级 k_', 'd': '公国级 d_'}

lines = []
lines.append('# EU5（1337 开局有地国家） × CK3 原版公国及以上头衔 同名对照')
lines.append('')
lines.append('## 口径')
lines.append('')
lines.append('- **EU5 侧**：`main_menu/setup/start/10_countries.txt` 中 1337.4.1 开局**至少持有一块领地**（`own_*` / `control_*` 列表非空）的国家 tag。')
lines.append('  - 文件里共 1206 个 tag，其中有地 **634 个**；另 572 个无地 tag 被排除（含只有 `our_cores_conquered_by_others` 的法理国家，如 GUY 吉耶纳、GLC 加利西亚、LON 莱昂、CRI 克里米亚）。')
lines.append('  - 中文名取 `main_menu/localization/simp_chinese/*.yml` 里的 `TAG:` 条目（634 个里 633 个有中文名，KEE 缺）。')
lines.append('- **CK3 侧**：`common/landed_titles/*.txt` 中的 `e_` / `k_` / `d_` 头衔，共 1662 个 key，其中 1620 个有简中名。')
lines.append('- **判定**：中文字符串完全相等（已解析 `$var$` 引用与 `#格式` 标记）。')
lines.append('')
lines.append('## 结果')
lines.append('')
lines.append('**%d 条命中**，去重后 **%d 个名字**。' % (len(rows), len(by)))
lines.append('')
for c in TIER:
    lines.append('- %s：%d 个名字' % (LABEL[c], len(groups[c])))
lines.append('')

for c in TIER:
    if not groups[c]:
        continue
    lines.append('## %s（%d）' % (LABEL[c], len(groups[c])))
    lines.append('')
    lines.append('| 名字 | EU5 tag | 领地数 | CK3 头衔 |')
    lines.append('| --- | --- | --- | --- |')
    for n in sorted(groups[c]):
        v = by[n]
        tags = '、'.join(sorted(set(r['eu5_tag'] for r in v)))
        loc = '、'.join(sorted(set(r['eu5_locations'] for r in v), key=int, reverse=True))
        titles = '、'.join(sorted(set(r['ck3_title'] for r in v)))
        lines.append('| %s | %s | %s | %s |' % (n, tags, loc, titles))
    lines.append('')

out = os.path.join(BASE, '_eu5_1337_vs_ck3_high_title_samename.md')
open(out, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
print('写出:', out)
print('条数', len(rows), '名字数', len(by))
for c in TIER:
    print(LABEL[c], len(groups[c]))
