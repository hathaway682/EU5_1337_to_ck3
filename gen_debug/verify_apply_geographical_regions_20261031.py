"""Validate staged region expansion; optionally deploy the already-reviewed output."""
from pathlib import Path
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('region_builder', HERE / 'rebuild_geographical_regions_20261031.py')
geo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(geo)
stage = HERE / 'geographical_regions_rebuild_20261031'
expected = json.loads((stage / 'region_provinces.json').read_text(encoding='utf-8'))
title_provinces, baronies, _ = geo.titles(geo.MOD / 'common/landed_titles')
current_ids = set()
for line in (geo.MOD / 'map_data/definition.csv').read_text(encoding='utf-8-sig').splitlines():
    if line.split(';')[0].isdigit():
        current_ids.add(int(line.split(';')[0]))
seen = set()
ref_counts = {'duchies': 0, 'counties': 0, 'provinces': 0}
for file in sorted(stage.glob('*.txt')):
    assert file.read_bytes().startswith(b'\xef\xbb\xbf')
    for key, body in geo.parse(geo.read(file))[0]:
        assert key not in seen, ('Duplicate key', key)
        seen.add(key)
        result = set()
        for prop, value in body[0]:
            assert prop not in ('kingdoms', 'empires', 'hegemonies'), (key, prop)
            if prop in ('duchies', 'counties'):
                for title in value[1]:
                    assert title in title_provinces, (key, title)
                    assert title.startswith('d_' if prop == 'duchies' else 'c_')
                    assert not (result & title_provinces[title]), ('Redundant title', key, title)
                    result.update(title_provinces[title])
                ref_counts[prop] += len(value[1])
            elif prop == 'provinces':
                values = set(map(int, value[1]))
                assert values <= current_ids and 0 not in values
                assert not (values & result)
                result.update(values)
                ref_counts[prop] += len(value[1])
        assert result == set(expected[key]), ('Extent mismatch', key)
assert seen == expected.keys()
report = json.loads((stage / 'report.json').read_text(encoding='utf-8'))
assert not report['unresolved_cu_titles']
assert not [k for k in report['empty_regions'] if k.startswith('sea_')]
land = set(baronies.values())
for kind in ('continent', 'subcontinent'):
    partition = [set(v) for k, v in expected.items() if k.startswith('eu5_' + kind + '_')]
    assert set.union(*partition) == land
    assert sum(map(len, partition)) == len(land)
print('Validated regions:', len(seen), '| baronies:', len(land), '| references:', ref_counts)
print('Source-empty regions:', report['empty_regions'])
print('EU5 continents/subcontinents are complete, disjoint partitions of all baronies.')
if '--apply' in sys.argv:
    dest = geo.MOD / 'map_data/geographical_regions'
    # Protect other concurrent work: overwritten files must still equal the snapshot.
    for original in (geo.BACKUP / 'original_regions').glob('*.txt'):
        assert (dest / original.name).read_bytes() == original.read_bytes(), ('Changed since backup', original.name)
    for file in stage.glob('*.txt'):
        target = dest / file.name
        if not (geo.BACKUP / 'original_regions' / file.name).exists():
            assert not target.exists(), ('Unbacked existing file', target)
    for file in stage.glob('*.txt'):
        target = dest / file.name
        target.write_bytes(file.read_bytes())
        assert target.read_bytes() == file.read_bytes()
    print('Applied and verified all', len(list(stage.glob('*.txt'))), 'region files.')
