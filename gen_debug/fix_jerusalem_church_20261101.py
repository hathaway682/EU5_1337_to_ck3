from pathlib import Path
from collections import defaultdict
import json, sys
import rebuild_geographical_regions_20261031 as g
import rebuild_ecclesiastical_titles_20261101 as h

M = Path(__file__).resolve().parents[1]
B = Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261101_094407_jerusalem_church')
O = M / 'gen_debug/jerusalem_church_20261101'
base = B / 'mod'
ts, bs, anc = g.titles(base / 'common/landed_titles')
pc = {p: anc[b][-2] for b, p in bs.items()}
old = json.loads((base / 'gen_debug/cilicia_church_20261101/county_assignment.json').read_text(encoding='utf-8'))
allocation = dict(old)
antioch, jerusalem = 'et_1178_antioch_region', 'et_1178_jerusalem_region'
counties = {'c_sharat', 'c_madian'}
for c in counties:
    assert allocation[c] == antioch
    allocation[c] = jerusalem
changed = {c for c in old.keys() | allocation.keys() if old.get(c) != allocation.get(c)}
assert changed == counties
affected = {antioch, jerusalem}
members = defaultdict(set)
for c, r in allocation.items():
    members[r].update(ts[c])
regions, files = h.load_regions(base / 'map_data/geographical_regions')
def compress(points):
    rest = set(points)
    props = []
    for prefix, prop in [('d_', 'duchies'), ('c_', 'counties')]:
        selected = []
        for title, land in sorted(ts.items()):
            if title.startswith(prefix) and land and land <= rest:
                selected.append(title)
                rest -= land
        if selected:
            props.append((prop, ([], selected)))
    assert not rest
    return props, []
replacements = defaultdict(dict)
for r in affected:
    replacements[files[r]][r] = '\n'.join(h.render(([(r, compress(members[r]))], [])))
products = {}
for filename, blocks in replacements.items():
    rel = Path('map_data/geographical_regions') / filename
    products[rel] = h.replace_blocks(h.read(base / rel), blocks)
final = dict(regions)
for text in products.values():
    final.update(dict(g.parse(text)[0]))
assert all(final[k] == v for k, v in regions.items() if k not in affected)
titles, histories = {}, {}
for p in (base / 'common/landed_titles').glob('*.txt'):
    titles.update(dict(g.parse(h.read(p))[0]))
for p in (base / 'history/titles/ce3').glob('*.txt'):
    for k, n in g.parse(h.read(p))[0]:
        assert k not in histories
        histories[k] = h.state(n, (1337, 4, 1))
seen, capitals = {}, {}
for title, state in histories.items():
    region = state.get('clerical_region', 'none')
    if region == 'none':
        continue
    points = h.expand(region, final, ts, {})
    for c in {pc[p] for p in points}:
        assert c not in seen, (c, title)
        assert ts[c] <= points
        seen[c] = title
        assert allocation.get(c) == region, (c, region, allocation.get(c))
    cap = dict(titles[title][0])['capital']
    assert cap not in capitals and seen.get(cap) == title
    capitals[cap] = title
assert len(capitals) == 79 and len(seen) == len(allocation) == 1038
assert 'c_avaria' not in seen
assert all(allocation[c] == jerusalem for c in counties)
assert allocation['c_moscow'] == 'et_1178_kyiv_region'
O.mkdir(parents=True, exist_ok=True)
for rel, text in products.items():
    p = O / 'staged' / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8-sig')
report = {'backup': str(B), 'county_changes': {c: {'from': old.get(c), 'to': allocation.get(c)} for c in sorted(changed)}, 'active_regions': len(capitals), 'assigned_counties': len(seen), 'overlaps': 0, 'in_game_test_performed': False}
(O / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
(O / 'county_assignment.json').write_text(json.dumps(allocation, ensure_ascii=False, indent=2), encoding='utf-8')
if '--apply' in sys.argv:
    for rel in products:
        assert (M / rel).read_bytes() == (base / rel).read_bytes()
    for rel in products:
        (M / rel).write_bytes((O / 'staged' / rel).read_bytes())
    for folder in ('history/titles/ce3', 'common/landed_titles'):
        for p in (base / folder).glob('*.txt'):
            assert p.read_bytes() == (M / p.relative_to(base)).read_bytes()
    for rel in products:
        assert (M / rel).read_bytes() == (O / 'staged' / rel).read_bytes()
sys.stdout.reconfigure(encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
