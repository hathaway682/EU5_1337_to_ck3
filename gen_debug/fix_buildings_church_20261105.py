from pathlib import Path
from collections import defaultdict
import json, sys
import rebuild_geographical_regions_20261031 as g
import rebuild_ecclesiastical_titles_20261101 as h

M = Path(__file__).resolve().parents[1]
B = Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261105_053001_buildings_church')
O = M / 'gen_debug/buildings_church_20261105'
base = B / 'mod'
ts, bs, anc = g.titles(base / 'common/landed_titles')
pc = {p: anc[b][-2] for b, p in bs.items()}
old = json.loads((base / 'gen_debug/jerusalem_church_20261101/county_assignment.json').read_text(encoding='utf-8'))
allocation = dict(old)
kyiv, gniezno = 'et_1178_kyiv_region', 'et_1178_gniezno_region'
aquileia, milano = 'et_867_aquileia_region', 'et_1178_milano_region'
pagan = {'c_ashmyany', 'c_breslauja', 'c_svir', 'c_grodno'}
for c in pagan:
    assert allocation.pop(c) == kyiv
assert allocation['c_podlasie'] == kyiv
allocation['c_podlasie'] = gniezno
assert allocation['c_valtellina'] == aquileia
allocation['c_valtellina'] = milano
changed = {c for c in old.keys() | allocation.keys() if old.get(c) != allocation.get(c)}
assert changed == pagan | {'c_podlasie', 'c_valtellina'}
affected = {kyiv, gniezno, aquileia, milano}
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
assert len(capitals) == 79 and len(seen) == len(allocation) == 1034
assert 'c_avaria' not in seen
assert all(c not in seen for c in pagan)
assert allocation['c_podlasie'] == gniezno and allocation['c_valtellina'] == milano
assert allocation['c_moscow'] == 'et_1178_kyiv_region'
# Preserve each province's unrelated history while moving only its building directives.
rel = Path('history/provinces/00_generated_provinces.txt')
province_text = h.read(base / rel)
spans = h.top_spans(province_text)
blocks = {p: province_text[slice(*spans[p])] for p in ('1','4','3745','3746','3748')}
def transfer(src, dst, fragment):
    assert blocks[src].count(fragment) == 1 and fragment not in blocks[dst]
    blocks[src] = blocks[src].replace(fragment, '')
    assert blocks[dst].endswith('}')
    blocks[dst] = blocks[dst][:-1] + fragment + '}'
transfer('4','1','\tspecial_building = temple_of_uppsala_01\n')
a = blocks['3745'].index('\teffect = {')
market = blocks['3745'][a:blocks['3745'].rfind('}')]
assert 'add_special_building_slot = dvin_shuka_01' in market and 'add_special_building = dvin_shuka_01' in market
transfer('3745','3748',market)
transfer('3746','3745','\t304.1.1 = {\n\t\tspecial_building_slot = etchmiadzin_cathedral\n\t}\n')
products[rel] = h.replace_blocks(province_text, blocks)
rel = Path('common/on_action/game_start.txt')
txt = h.read(base / rel)
old_uni = 'title:b_enkoping.title_province = { add_special_building_slot = generic_university }'
new_uni = 'title:b_uppsala.title_province = { add_special_building_slot = generic_university }'
assert txt.count(old_uni) == 1 and new_uni not in txt
products[rel] = txt.replace(old_uni,new_uni)
rel = Path('common/connection_arrows/silk_road_arrows.txt')
txt = h.read(base / rel)
assert txt.count('3745 # b_yerevan') == 3
products[rel] = txt.replace('3745 # b_yerevan','3748 # b_khor_virap')
rel = Path('common/situation/situations/tgp_silk_road.txt')
txt = h.read(base / rel)
assert txt.count('capital_province = 3745 # Dvin') == 1
products[rel] = txt.replace('capital_province = 3745 # Dvin','capital_province = 3748 # Khor Virap (Dvin market)')
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
