"""Read-only verification of the deployed 1178 ecclesiastical baseline."""
from pathlib import Path
import csv
import json
import re
import sys

import rebuild_geographical_regions_20261031 as g

sys.stdout.reconfigure(encoding='utf-8')
mod = Path(__file__).resolve().parents[1]
backup = Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261101_050756_ecclesiastical_1178')
out = mod / 'gen_debug/ecclesiastical_1178_20261101'
report = json.loads((out / 'report.json').read_text(encoding='utf-8'))
allowed = set(report['files'])
changed = []
for old in (backup / 'mod').rglob('*'):
    # Imports create interpreter caches beside the snapshotted parser. They
    # are derived files, not part of the source snapshot or game products.
    if not old.is_file() or '__pycache__' in old.parts:
        continue
    rel = old.relative_to(backup / 'mod')
    live = mod / rel
    assert live.exists(), ('Unexpected deletion', str(rel))
    if old.read_bytes() != live.read_bytes():
        assert str(rel) in allowed, ('Unexpected change', str(rel))
        changed.append(str(rel))

regions = {}
for path in (mod / 'map_data/geographical_regions').glob('*.txt'):
    for key, node in g.parse(g.read(path))[0]:
        assert key not in regions
        regions[key] = node
history = {}
for path in (mod / 'history/titles/ce3').glob('*.txt'):
    for key, node in g.parse(g.read(path))[0]:
        assert key not in history
        history[key] = dict(dict(node[0])['1337.4.1'][0])
assert sum(k.startswith('d_et_') for k in history) == 77
assert sum(n.get('clerical_region', 'none') != 'none' for k, n in history.items() if k.startswith('d_et_')) == 75
for key, node in history.items():
    region = node.get('clerical_region', 'none')
    assert region == 'none' or region in regions
titles = {}
for path in (mod / 'common/landed_titles').glob('*.txt'):
    for key, node in g.parse(g.read(path))[0]:
        if key.startswith(('d_et_', 'd_cd_')):
            assert key not in titles, ('Duplicate declaration', key)
            titles[key] = node
assert len(titles) == 132
assert not any(dict(n[0]).get('capital') == 'c_gen_buamu_4' for n in titles.values())
for rel in report['files']:
    path = mod / rel
    assert path.read_bytes().startswith(b'\xef\xbb\xbf')
    assert path.read_bytes() == (out / 'staged' / rel).read_bytes()
for key in ('d_cd_velletri', 'd_cd_santa_rufina'):
    assert ('set_variable', 'suppressed_cardinalate') in history[key]['effect'][0]

validation = {
    'result': 'passed', 'changed_existing_files': changed,
    'new_game_file': 'history/titles/ce3/01_cardinalate_status.txt',
    'unrelated_backed_up_source_files_unchanged': True,
    'ecclesiastical_title_histories': 77,
    'unique_ecclesiastical_and_cardinal_declarations': 132,
    'active_regions': 75, 'region_overlap_baronies': report['region_overlap_baronies'],
    'in_game_test_performed': False,
}
(out / 'validation.json').write_text(json.dumps(validation, ensure_ascii=False, indent=2), encoding='utf-8')
locpath = Path('E:/SteamLibrary/steamapps/common/Crusader Kings III/game/localization/simp_chinese/dlc/pam/pam_ecclesiastical_titles_l_simp_chinese.yml')
loc = dict(re.findall(r'^\s*([^\s:#]+):(?:\d+)?\s*"(.*)"\s*$', g.read(locpath), re.M))
rows = list(csv.DictReader((out / 'ecclesiastical_titles.csv').open(encoding='utf-8-sig')))
lines = [
    '# 1178 教省基线\n\n',
    '基准为 CK3 原版 1178.10.1 的有效教省，初始化日期为本 mod 的 1337.4.1。教省边界通过已有 Miller/Gall 地理配准转换，最大引用公国。\n\n',
    '77 个教区历史块中，75 个教省有效，梅里达和欧兹维持撤销；另保留原版仅有声明的格鲁吉亚兼容头衔。恢复 54 个独立枢机头衔声明，并保留奥斯蒂亚—韦莱特里、波尔图—圣鲁菲娜的合并状态。\n\n',
    '沿用 11 位已有 1337 教士；64 个有效教区尚未指定 1337 持有人，没有导入已经去世的 1178 主教。原版开局逻辑负责枢机人选。\n\n',
    '所有教座地块都位于自己的教省范围内，教省地块不重叠。对于未单独建模的城市，使用附近地块提供教座伯爵领引用；没有新增或拆分伯爵领。\n\n',
    '已通过静态语法、引用、重复声明、边界与未改文件校验；未进行游戏内测试。\n\n',
    f'备份：`{backup}`\n\n',
    '| 教省 | 头衔 | 教座地块 | 教座伯爵领 | 地块数 | 1337 持有人 |\n',
    '|---|---|---|---|---:|---|\n',
]
for row in rows:
    title = row['title']
    name = loc.get(history[title].get('name', title), loc.get(title, title))
    status = '已撤销' if row['active'] == 'False' else row['baronies']
    seat = '`' + row['seat_barony'] + '`' + ('（代理）' if row['seat_is_proxy'] == 'True' else '')
    holder = row['holder_1337'] if row['holder_1337'] != '0' else '待补'
    lines.append(f"| {name} | `{title}` | {seat} | `{row['capital_county']}` | {status} | {holder} |\n")
lines.extend(['\n## 同属一个伯爵领的教座\n\n', '保留各自教座地块与教省范围，未改动世俗伯爵领划分。\n\n'])
for county, keys in report['shared_seat_counties'].items():
    lines.append(f"- `{county}`：" + '、'.join(loc.get(k, k) for k in keys) + '\n')
(out / '教省基线_1178.md').write_text(''.join(lines), encoding='utf-8')
print(json.dumps(validation, ensure_ascii=False, indent=2))
