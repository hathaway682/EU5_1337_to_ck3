"""Resolve EU5 nested name references using the backed-up EU5 localizations."""
from pathlib import Path
import json
import re

root = Path(__file__).resolve().parent.parent
source = Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261104_214624_eu5_dynasties/eu5/localization')
files = sorted((root / 'localization').glob('*/zzzz_eu5_family_l_*.yml'))
ref = re.compile(r'\$([\w.\-]+)\$')
entry = re.compile(r'^\s*([\w.\-]+):\d*\s*"(.*)"\s*(?:#.*)?$')
values = {}
for path in files:
    lang = path.parent.name
    texts = (source / lang).rglob('*.yml')
    choices = [p for p in texts if p.name.startswith(('dynasty_names_', 'character_names_', 'character_names_dynamic_', 'location_names_'))]
    choices.sort(key=lambda p: (0 if p.name.startswith('dynasty_names_') else
                                1 if p.name.startswith('location_names_') else 2, str(p)))
    d = {}
    for p in choices:
        for line in p.read_text(encoding='utf-8-sig').splitlines():
            m = entry.match(line)
            if m:
                d.setdefault(m.group(1).casefold(), m.group(2))
    values[lang] = d

prepared = {}
remaining = {}
replaced = {}
for path in files:
    lang = path.parent.name
    text = path.read_text(encoding='utf-8-sig')
    count = [0]
    def replace(m):
        value = values[lang].get(m.group(1).casefold())
        if value is None:
            return m.group(0)
        count[0] += 1
        return value
    for _ in range(5):
        updated = ref.sub(replace, text)
        if updated == text:
            break
        text = updated
    remaining[lang] = sorted(set(ref.findall(text)))
    replaced[lang] = count[0]
    prepared[path] = text
if any(remaining.values()):
    raise ValueError('Unresolved EU5 name references: ' + repr(remaining))
for path, text in prepared.items():
    path.write_text(text, encoding='utf-8-sig', newline='\n')
report_path = root / 'gen_debug/eu5_family_import_report_20261104.json'
report = json.loads(report_path.read_text(encoding='utf-8'))
report['nested_localization_references_resolved'] = replaced
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(replaced, ensure_ascii=False))
