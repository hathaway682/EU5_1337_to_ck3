"""Fill missing EU5-tag title names using the corresponding EU5 translations.

Inputs are the backed-up title definitions, mod localization, and EU5 country
names. Only absent keys are added, in new per-language files. --apply writes.
"""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
BACKUP = Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261104_234023_title_localization')
languages = ['english', 'simp_chinese', 'french', 'german', 'spanish', 'russian',
             'polish', 'braz_por', 'japanese', 'korean', 'turkish']
title_re = re.compile(r'(?m)^\s*([edkch]_eu5_[A-Za-z0-9_]+)\s*=\s*\{')
loc_re = re.compile(r'(?m)^\s*([\w.\-]+):\d*\s*"(.*)"\s*(?:#.*)?$')
read = lambda p: p.read_text(encoding='utf-8-sig')
titles = set()
for path in (BACKUP / 'mod/common/landed_titles').glob('*.txt'):
    text = re.sub(r'(?m)#.*$', '', read(path))
    titles.update(title_re.findall(text))

outputs = {}
report = {}
for lang in languages:
    existing = set()
    for base in (BACKUP / 'mod/localization' / lang, BACKUP / 'mod/localization/replace' / lang):
        if base.exists():
            for path in base.rglob('*.yml'):
                existing.update(m.group(1) for m in loc_re.finditer(read(path)))
    source = BACKUP / 'eu5' / lang / ('country_names_l_' + lang + '.yml')
    country = {m.group(1): m.group(2) for m in loc_re.finditer(read(source))}
    lines = ['l_' + lang + ':']
    translated, unresolved, adjectives = [], [], []
    for key in sorted(titles - existing):
        tag = key.split('_eu5_', 1)[1].upper()
        value = country.get(tag)
        if value is None or '$' in value or '[' in value:
            unresolved.append(key)
            continue
        lines.append(' ' + key + ':0 "' + value + '"')
        translated.append(key)
        adj_key, adj = key + '_adj', country.get(tag + '_ADJ')
        if adj_key not in existing and adj and '$' not in adj and '[' not in adj:
            lines.append(' ' + adj_key + ':0 "' + adj + '"')
            adjectives.append(adj_key)
    dest = ROOT / 'localization' / lang / ('zzzz_eu5_title_missing_l_' + lang + '.yml')
    if dest.exists(): raise FileExistsError('Back up the existing generated output: ' + str(dest))
    outputs[dest] = '\n'.join(lines) + '\n'
    report[lang] = {'titles': translated, 'adjectives': adjectives, 'unresolved': unresolved}
print('Total EU5-tag titles:', len(titles))
for lang, item in report.items():
    print(lang, 'titles:', len(item['titles']), 'adjectives:', len(item['adjectives']),
          'unresolved:', len(item['unresolved']), item['unresolved'][:10])
if any(v['unresolved'] for v in report.values()):
    raise ValueError('Some title names could not be resolved from EU5')
if 'd_eu5_bij' not in report['simp_chinese']['titles']:
    raise ValueError('Expected screenshot title was not selected')
if '--apply' in sys.argv:
    for dest, body in outputs.items():
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(body, encoding='utf-8-sig', newline='\n')
    (ROOT / 'gen_debug/eu5_missing_title_localization_20261104.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
