"""Copy the EU5 continent/subcontinent labels, preserving original translations."""
from pathlib import Path
import json
import re
import sys

MOD = Path(__file__).resolve().parents[1]
BACKUP = Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261031_134214_geographical_regions')
OUT = MOD / 'gen_debug/geographical_regions_localization_20261031'
report = json.loads((MOD / 'gen_debug/geographical_regions_rebuild_20261031/report.json').read_text(encoding='utf-8'))
keys = {}
for kind in ('continent', 'subcontinent'):
    for unit in report['eu5_' + kind + 's']:
        keys['eu5_' + kind + '_' + unit] = unit
OUT.mkdir(exist_ok=True)
for folder in sorted((BACKUP / 'inputs/eu5_localization').iterdir()):
    lang = folder.name
    src = folder / ('region_names_l_' + lang + '.yml')
    labels = dict(re.findall(r'^\s*([^\s:#]+):(?:\d+)?\s*("[^\n]*")', src.read_text(encoding='utf-8-sig'), re.M))
    assert set(keys.values()) <= labels.keys(), (lang, set(keys.values()) - labels.keys())
    content = 'l_' + lang + ':\n' + '\n'.join(' ' + k + ':0 ' + labels[v] for k, v in sorted(keys.items())) + '\n'
    name = 'eu5_geographical_regions_l_' + lang + '.yml'
    (OUT / name).write_text(content, encoding='utf-8-sig')
    if '--apply' in sys.argv:
        target = MOD / 'localization' / lang / name
        assert not target.exists(), 'Back up existing localization before overwriting it'
        target.write_bytes((OUT / name).read_bytes())
    print(lang, len(keys), 'labels')
