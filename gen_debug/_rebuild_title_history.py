# -*- coding: utf-8 -*-
"""按 mod 现行决定过滤 politics，再调 _patch_title_history.py 重建头衔历史。

要过滤的三类（都来自 politics.json 与 mod 现状不一致）：
  1. herder 国家（448 个，rank=None）——今天 13:18 的牧群移除已把它们删干净，
     它们的 603 个伯爵领现在由 gen_wilderness_holder 持有。不过滤就会写回 10-22
     新造的 eu5_regent_*，而那些占位角色在 history/characters 里并不存在。
  2. 已升王国的安纳托利亚贝伊 AYD/ERE/MEN/TUR —— politics 仍是 rank=d，
     不过滤会重新造出 d_eu5_ayd 等 4 个块，把贝伊升级覆盖回去。
  3. 任何指向不存在角色的 holder/ruler —— 一律不写，避免造出无主头衔。

用法：
  python gen_debug\\_rebuild_title_history.py            # dry run
  python gen_debug\\_rebuild_title_history.py --apply
"""
import glob
import io
import json
import os
import re
import shutil
import subprocess
import sys

MOD = r'D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape'
EXPORT = r'D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map\eu5_export'
PATCH = os.path.join(EXPORT, '_patch_title_history.py')
TMP = os.path.join(MOD, 'gen_debug', '_rebuild_export')

HERDER = 'herder'
BEYLIK_UPGRADED = {'AYD', 'ERE', 'MEN', 'TUR'}   # 已改为 k_aydin / k_eretnid / k_mentese / k_tekke

pol = json.load(io.open(os.path.join(EXPORT, 'eu5_politics.json'), encoding='utf-8-sig'))

# 现行角色 key
chars = set()
for f in glob.glob(os.path.join(MOD, 'history', 'characters', '**', '*.txt'), recursive=True):
    chars |= set(re.findall(r'(?m)^\s*([a-z0-9_]+)\s*=\s*\{',
                            io.open(f, encoding='utf-8-sig', errors='ignore').read()))
print('现行角色 key:', len(chars))

countries = pol['countries']
drop_herder = [t for t, c in countries.items() if (c.get('government') or '') == HERDER]
drop_beylik = [t for t in BEYLIK_UPGRADED if t in countries]
drop_tags = set(drop_herder) | set(drop_beylik)
print('剔除 herder 国家 %d、已升王国贝伊 %d' % (len(drop_herder), len(drop_beylik)))

for t in drop_tags:
    countries.pop(t, None)

n_county = n_baron = n_ruler = 0
for name, info in pol['counties'].items():
    if info.get('ruler') and info['ruler'] not in chars:
        info['ruler'] = None
        n_county += 1
    if info.get('owner') in drop_tags:
        info['owner'] = None
for name, b in (pol.get('baronies') or {}).items():
    if b.get('holder') and b['holder'] not in chars:
        b['holder'] = None
        n_baron += 1
for t, c in countries.items():
    if c.get('ruler') and c['ruler'] not in chars:
        c['ruler'] = None
        n_ruler += 1
print('清空不存在的持有者：县 %d、男爵领 %d、国家 %d' % (n_county, n_baron, n_ruler))

if '--apply' not in sys.argv:
    print('\n(dry run，只做了过滤统计，没有写文件、没有跑 patch)')
    print('加 --apply 才会写临时导出目录并重建头衔历史')
    sys.exit(0)

os.makedirs(TMP, exist_ok=True)
io.open(os.path.join(TMP, 'eu5_politics.json'), 'w', encoding='utf-8').write(
    json.dumps(pol, ensure_ascii=False))
for f in ('mapping.json', '_grant_landed_duchies.py'):
    shutil.copy2(os.path.join(EXPORT, f), os.path.join(TMP, f))
print('临时导出目录:', TMP)

r = subprocess.run([sys.executable, PATCH, '--mod', MOD, '--export', TMP],
                   capture_output=True, text=True, encoding='utf-8', errors='replace')
print(r.stdout)
if r.returncode:
    print('STDERR:', r.stderr[-3000:])
    sys.exit(r.returncode)
