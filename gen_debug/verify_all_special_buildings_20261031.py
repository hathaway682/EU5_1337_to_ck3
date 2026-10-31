"""Independent checks for mapped building locations and preserved historical guards."""
from pathlib import Path
from collections import Counter, defaultdict
import importlib.util
import json
import re

MOD = Path(__file__).resolve().parents[1]
OUT = MOD / 'gen_debug/all_special_buildings_20261031'
report = json.loads((OUT / 'report.json').read_text(encoding='utf-8'))
BACKUP = Path(report['backup'])
V = BACKUP / 'inputs/vanilla'
spec = importlib.util.spec_from_file_location('g', BACKUP / 'inputs/rebuild_geographical_regions_20261031.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


def read(p):
    return p.read_text(encoding='utf-8-sig', errors='replace')


def walk(node, path=()):
    for key, value in node[0]:
        yield path, key, value
        if isinstance(value, tuple):
            yield from walk(value, path + (key,))


defs, prev = {}, {}
for folder in (V / 'common/buildings', BACKUP / 'mod/common/buildings'):
    for p in sorted(folder.glob('*.txt')):
        for key, body in g.parse(read(p))[0]:
            if isinstance(body, tuple):
                defs[key] = body
for key, body in defs.items():
    nxt = dict(body[0]).get('next_building')
    if nxt:
        prev[nxt] = key


def family(key):
    while key in prev:
        key = prev[key]
    return key


COMMANDS = {'special_building', 'special_building_slot', 'add_special_building', 'add_special_building_slot', 'duchy_capital_building', 'remove_building'}
source = defaultdict(list)
for p in (V / 'history/provinces').glob('*.txt'):
    for pid, node in g.parse(read(p))[0]:
        if pid.isdigit():
            source[int(pid)].extend(node[0])
old = dict(g.parse(read(BACKUP / 'mod/history/provinces/00_generated_provinces.txt'))[0])
new = dict(g.parse(read(OUT / 'history/provinces/00_generated_provinces.txt'))[0])
assert old.keys() == new.keys()
_, baronies, ancestry = g.titles(BACKUP / 'mod/common/landed_titles')
valid_pids = set(baronies.values())
placements = {(p['source_province'], p['building_family']): p for p in report['placements']}
for row in placements.values():
    assert row['target_province'] in valid_pids
    assert baronies[row['target_barony']] == row['target_province']
    assert row['building_family'] in defs
assert len(placements) == 312
assert len({p['target_province'] for p in placements.values()}) == 305
assert len(report['slot_conflicts_resolved']) == 5


def trace(node, wanted, context=()):
    out = Counter()
    for key, value in node[0]:
        if key in COMMANDS and isinstance(value, str) and value in defs and family(value) == wanted:
            out[(key, value, context)] += 1
        elif isinstance(value, tuple) and key != 'limit':
            limits = [v for k, v in value[0] if k == 'limit']
            marker = (key, json.dumps(limits, ensure_ascii=False))
            out.update(trace(value, wanted, context + (marker,)))
    return out


checked = 0
for group, row in placements.items():
    if 'history' not in row['sources'] or row['rule'] == 'preserved_silk_road':
        continue
    expected = trace((source[group[0]], []), group[1])
    actual = trace(new[str(row['target_province'])], group[1])
    # Explicit matching slots added before effect-based construction are additive.
    for record, count in expected.items():
        assert actual[record] >= count, ('Historical date/guard lost', row, record, count, actual[record])
    checked += sum(expected.values())


def strip_special(node):
    pairs = []
    for key, value in node[0]:
        if key in COMMANDS:
            continue
        if isinstance(value, tuple):
            value = strip_special(value)
            if not value[0] and not value[1]:
                continue
        pairs.append((key, value))
    if all(k == 'limit' for k, _ in pairs):
        pairs = []
    return pairs, node[1]


developed = {baronies[x['barony']]: x['to'] for x in report['developed_sites']}
for pid, node in old.items():
    before, after = strip_special(node), strip_special(new[pid])
    if int(pid) in developed:
        before = ([(key, developed[int(pid)] if key == 'holding' else value) for key, value in before[0]], before[1])
    assert before == after, ('Unrelated province history changed', pid)
for pid, node in new.items():
    for _, key, value in walk(node):
        if key in COMMANDS and isinstance(value, str):
            assert value in defs, ('Undefined special building', pid, key, value)

startup = g.parse(read(OUT / 'common/on_action/game_start.txt'))
bindings = Counter()
for path, key, value in walk(startup):
    if key not in ('add_special_building', 'add_special_building_slot'):
        continue
    assert value in defs
    scope = next((part for part in reversed(path) if re.fullmatch(r'title:b_[\w-]+\.title_province', part)), None)
    assert scope, ('Unresolved fixed startup building', path, key)
    barony = scope.removeprefix('title:').removesuffix('.title_province')
    assert barony in baronies, ('Missing startup barony', barony)
    assert any(row['target_barony'] == barony and row['building_family'] == family(value) for row in placements.values()), (barony, value)
    bindings[(barony, family(value), key)] += 1

# Compare every non-slot startup construction and its guards before/after remap.
def startup_trace(node, path=()):
    result = Counter()
    for key, value in node[0]:
        if key in ('add_special_building', 'remove_building') and isinstance(value, str):
            result[(key, value, path)] += 1
        elif isinstance(value, tuple) and key != 'limit':
            marker = 'building_province' if re.fullmatch(r'title:b_[\w-]+\.title_province', key) else key
            limits = json.dumps([v for k, v in value[0] if k == 'limit'], ensure_ascii=False)
            result.update(startup_trace(value, path + ((marker, limits),)))
    return result
assert startup_trace(startup) == startup_trace(g.parse(read(BACKUP / 'mod/common/on_action/game_start.txt')))

assert placements[(1365, 'qutb_minar_01')]['target_barony'] == 'b_delhi'
assert next(p for p in placements.values() if p['building_family'] == 'sankore_university')['target_barony'] == 'b_timbuktu'
silk = json.loads(read(BACKUP / 'inputs/report.json'))
for hub in silk['hubs']:
    assert trace(new[str(hub['province'])], hub['building']) == trace(old[str(hub['province'])], hub['building'])
for rel in ('events/decisions_events/major_decisions_events.txt', 'common/decisions/80_major_decisions.txt'):
    g.parse(read(OUT / rel))
wall_override = read(OUT / 'common/buildings/zz_eu5_special_building_locations.txt')
assert 'title:b_rome' in wall_override and 'title:b_roma' not in wall_override
assert dict(new[str(baronies['b_rome'])][0])['duchy_capital_building'] == 'aurelian_walls_01'
assert any(key == 'duchy_capital_building' and value == 'theodosian_walls_01' for _, key, value in walk(new[str(baronies['b_constantinople'])]))
title_before = read(BACKUP / 'mod/common/landed_titles/00_landed_titles.txt')
title_after = read(OUT / 'common/landed_titles/00_landed_titles.txt')
assert title_after == title_before.replace('capital = c_patrimonio', 'capital = c_marittima', 1)
assert g.titles(OUT / 'common/landed_titles')[1] == g.titles(BACKUP / 'mod/common/landed_titles')[1]
summary = {'status': 'PASS', 'building_arrangements': len(placements), 'physical_sites': 305,
           'historical_commands_with_preserved_dates_and_guards': checked,
           'startup_building_bindings': sum(bindings.values()), 'developed_historical_holdings': len(developed),
           'six_silk_road_sites_preserved': True,
           'unrelated_province_history_preserved': True, 'tested_in_game': False}
(OUT / 'validation.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
