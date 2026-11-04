"""Fill missing EU5-family cultures from each family's EU5 home location.

EU5 1337 population sizes are summed per culture; the largest group is mapped
using the mod's culture classification. The backup is the immutable input.
Use --apply to write, otherwise only report the proposed changes.
"""
from pathlib import Path
from collections import Counter, defaultdict
import csv
import importlib.util
import json
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
BACKUP = Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261104_221132_family_culture')
spec = importlib.util.spec_from_file_location('eu5_parser', BACKUP / '_gen_eu5_coa.py')
parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parser)
read = lambda p: p.read_text(encoding='utf-8-sig')
block = lambda s: parser.parse_top_blocks(s)
dyn_file = ROOT / 'common/dynasties/zz_eu5_dynasties.txt'
original_dyn = BACKUP / 'mod/common/dynasties/zz_eu5_dynasties.txt'
original_bytes = original_dyn.read_bytes()
if dyn_file.read_bytes() != original_bytes:
    raise RuntimeError('Dynasty file differs from the backed-up input; create a fresh backup first')

dynasties = dict(block(original_bytes.decode('utf-8-sig')))
setup = dict(block(dict(block(read(BACKUP / 'eu5/04_dynasties.txt')))['dynasty_manager']))
pops_text = dict(block(read(BACKUP / 'eu5/06_pops.txt')))['locations']
pops = defaultdict(Counter)
for location, body in block(pops_text):
    for pop in re.finditer(r'define_pop\s*=\s*\{([^{}]*)\}', body):
        size = re.search(r'\bsize\s*=\s*([0-9.]+)', pop.group(1))
        culture = re.search(r'\bculture\s*=\s*([\w.-]+)', pop.group(1))
        if size and culture:
            pops[location][culture.group(1)] += float(size.group(1))

mod_cultures = BACKUP / 'mod/common/culture/cultures'
ck_cultures = BACKUP / 'ck3_cultures'
mod_names = {p.name for p in mod_cultures.glob('*.txt')}
culture_files = list(mod_cultures.glob('*.txt')) + [p for p in ck_cultures.glob('*.txt') if p.name not in mod_names]
valid = set()
for p in culture_files:
    valid.update(re.findall(r'(?m)^([\w.\-]+)\s*=\s*\{', parser.strip_comments(read(p))))
classification = {}
with (BACKUP / 'mod/gen_debug/_culture_classification.csv').open(encoding='utf-8-sig', newline='') as f:
    for row in csv.DictReader(f):
        target = row['target'].removeprefix('NEW:').strip()
        classification[row['culture']] = target

report = []
for key, body in dynasties.items():
    if key == 'default_dynasty' or re.search(r'(?m)^\s*culture\s*=', body):
        continue
    row = {'dynasty': key, 'home': None, 'source_culture': None, 'share': None,
           'target_culture': None, 'status': None}
    if key not in setup:
        row['status'] = 'no_eu5_family_definition'
    else:
        home = re.search(r'(?m)^\s*home\s*=\s*"?([\w.\-]+)', setup[key])
        if not home:
            row['status'] = 'no_home'
        else:
            row['home'] = home.group(1)
            population = pops.get(row['home'])
            if not population:
                row['status'] = 'no_home_population'
            else:
                ranked = sorted(population.items(), key=lambda kv: (-kv[1], kv[0]))
                if len(ranked) > 1 and abs(ranked[0][1] - ranked[1][1]) < 1e-9:
                    row['status'] = 'population_tie'
                else:
                    culture, size = ranked[0]
                    row['source_culture'] = culture
                    row['share'] = round(size / sum(population.values()), 6)
                    target = classification.get(culture) or culture
                    if target not in valid:
                        row['status'] = 'target_culture_not_defined'
                        row['target_culture'] = target
                    else:
                        row['target_culture'] = target
                        row['status'] = 'ready'
    report.append(row)

ready = {row['dynasty']: row['target_culture'] for row in report if row['status'] == 'ready'}
lines = original_bytes.decode('utf-8-sig').splitlines(keepends=True)
newline = '\r\n' if b'\r\n' in original_bytes else '\n'
out = []
inserted = set()
key = None
for line in lines:
    m = re.match(r'^([\w.\-]+)\s*=\s*\{\s*$', line.rstrip('\r\n'))
    if m:
        key = m.group(1)
    out.append(line)
    if key in ready and re.match(r'^\s*name\s*=', line):
        if key in inserted:
            raise RuntimeError('Duplicate name for ' + key)
        out.append('\tculture = ' + ready[key] + newline)
        inserted.add(key)
if inserted != set(ready):
    raise RuntimeError('Could not insert all planned cultures: ' + repr(sorted(set(ready)-inserted)))

print('missing:', len(report), 'status:', dict(Counter(x['status'] for x in report)))
print('sample:', json.dumps(report[:8], ensure_ascii=True))
if '--apply' in sys.argv:
    output = ''.join(out).encode('utf-8')
    if original_bytes.startswith(b'\xef\xbb\xbf'):
        output = b'\xef\xbb\xbf' + output
    dyn_file.write_bytes(output)
    out_report = ROOT / 'gen_debug/eu5_family_home_culture_20261104.json'
    if out_report.exists():
        raise FileExistsError('Back up existing report before replacing: ' + str(out_report))
    out_report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
