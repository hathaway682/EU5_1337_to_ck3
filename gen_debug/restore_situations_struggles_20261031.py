"""Restore the six unmodified vanilla histories after checking their dependencies."""
from pathlib import Path
import hashlib
import importlib.util
import json
import re

MOD = Path(__file__).resolve().parents[1]
BACKUP = Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261031_175349_situations_struggles')
spec = importlib.util.spec_from_file_location('geo', MOD / 'gen_debug/rebuild_geographical_regions_20261031.py')
geo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(geo)
VANILLA = BACKUP / 'inputs/vanilla'
WORKSHOP = BACKUP / 'inputs/workshop'


def tokens(text):
    return [m.group() for m in geo.TOKEN.finditer(text) if not m.group().startswith('#')]


def clean(text):
    return re.sub(r'#[^\n]*', '', text)


definitions = {
    'mpo_the_great_steppe_history.txt': 'common/situation/situations/the_great_steppe.txt',
    'pam_the_christian_church_history.txt': 'common/situation/situations/pam_christian_situation.txt',
    'tgp_dynastic_cycle_history.txt': 'common/situation/situations/tgp_dynastic_cycle.txt',
    'tgp_silk_road_history.txt': 'common/situation/situations/tgp_silk_road.txt',
    'iberian_struggle_history.txt': 'common/struggle/struggles/iberian_struggle_script.txt',
    'persian_struggle_history.txt': 'common/struggle/struggles/persian_struggle_script.txt',
}
regions = {}
for file in (MOD / 'map_data/geographical_regions').glob('*.txt'):
    for key, body in geo.parse(geo.read(file))[0]:
        assert key not in regions
        regions[key] = body
rows = []
pending = []
for kind in ('situations', 'struggles'):
    for src in sorted((VANILLA / 'history' / kind).glob('*.txt')):
        text = geo.read(src)
        assert tokens(text) == tokens(geo.read(WORKSHOP / 'history' / kind / src.name)), ('Workshop differs', src.name)
        parsed = geo.parse(text)
        assert parsed[0] and not parsed[1]
        assert all(re.fullmatch(r'-?\d+\.\d+\.\d+', key) for key, _ in parsed[0])
        definition = clean(geo.read(VANILLA / definitions[src.name]))
        def_keys = set(re.findall(r'\b([\w-]+)\s*=\s*\{', definition))
        phases = set(re.findall(r'\b(?:start_phase|phase)\s*=\s*(\w+)', clean(text)))
        assert phases <= def_keys, ('Unknown phases', src.name, phases - def_keys)
        types = set(re.findall(r'\b(?:type|struggle_type)\s*=\s*(\w+)', clean(text)))
        assert types <= def_keys, ('Unknown type', src.name, types - def_keys)
        required = set()
        for body in re.findall(r'\b(?:geographical_regions|regions)\s*=\s*\{([^{}]*)\}', definition):
            required.update(body.split())
        required.update(re.findall(r'\bgeographical_region\s*=\s*(\w+)', definition))
        assert required <= regions.keys(), ('Missing regions', src.name, required - regions.keys())
        for key in required:
            assert any(prop in ('duchies', 'counties', 'provinces', 'regions') and value[1] for prop, value in regions[key][0]), ('Empty region', key)
        dest = MOD / 'history' / kind / src.name
        original = BACKUP / 'original_history' / kind / src.name
        assert dest.read_bytes() == original.read_bytes(), ('Changed after backup', dest)
        data = text.encode('utf-8-sig')
        pending.append((dest, data))
        rows.append({'file': str(dest.relative_to(MOD)), 'source': str(src),
                     'workshop_script_tokens_identical': True,
                     'dates': [key for key, _ in parsed[0]],
                     'types': sorted(types), 'phases': sorted(phases),
                     'regions': sorted(required), 'sha256': hashlib.sha256(data).hexdigest()})
assert len(pending) == 6
for dest, data in pending:
    dest.write_bytes(data)
    assert dest.read_bytes() == data
    print('Restored:', dest.relative_to(MOD))
report = MOD / 'gen_debug/restored_situations_struggles_20261031.json'
assert not report.exists(), 'Back up previous report before overwriting'
report.write_text(json.dumps({'backup': str(BACKUP), 'files': rows,
                              'persian_struggle_ends': '970.1.1', 'current_bookmark': '1337.4.1',
                              'validation': 'Static syntax, types, phases, geographic references and deployed file bytes verified. Not tested in game.'},
                             ensure_ascii=False, indent=2), encoding='utf-8')
print('PASS: six histories restored; types, phases, and all required geographical regions resolve.')
