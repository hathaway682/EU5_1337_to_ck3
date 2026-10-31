"""Merge shared-seat dioceses and make every 1337 clerical county exclusive.

User approved mergers while preserving the existing county map.
Dry run by default; --apply deploys only the two staged game files.
"""
from pathlib import Path
from collections import Counter, defaultdict
import csv
import json
import sys

import rebuild_geographical_regions_20261031 as g
import rebuild_ecclesiastical_titles_20261101 as helper

MOD = Path(__file__).resolve().parents[1]
BACKUP = Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261101_052534_clerical_overlap')
BASE = BACKUP / 'mod'
OUT = MOD / 'gen_debug/clerical_overlap_20261101'


def main():
    OUT.mkdir(exist_ok=True)
    old = json.loads((BASE / 'gen_debug/ecclesiastical_1178_20261101/region_provinces.json').read_text(encoding='utf-8'))
    rows = list(csv.DictReader((BASE / 'gen_debug/ecclesiastical_1178_20261101/ecclesiastical_titles.csv').open(encoding='utf-8-sig')))
    ts, bs, ancestry = g.titles(BASE / 'common/landed_titles')
    county_of = {bs[b]: next(c for c in chain if c.startswith('c_')) for b, chain in ancestry.items()}
    county_capitals = {}
    for barony, chain in ancestry.items():
        county_capitals.setdefault(county_of[bs[barony]], barony)
    active = {r['title']: r for r in rows if r['active'] == 'True'}
    seats = defaultdict(list)
    for title, row in active.items():
        seats[row['capital_county']].append(title)
    mergers, region_redirect = [], {r: r for r in old}
    retired = {}
    for county, titles in seats.items():
        if len(titles) < 2:
            continue
        leader = max(titles, key=lambda t: (active[t]['seat_barony'] == county_capitals[county], len(old[active[t]['region']]), t))
        for title in titles:
            if title != leader:
                region_redirect[active[title]['region']] = active[leader]['region']
                retired[title] = leader
        mergers.append({'county': county, 'retained': leader, 'retired': [t for t in titles if t != leader]})
    assert len(retired) == 5
    votes = defaultdict(Counter)
    capital_region = {}
    for region, pids in old.items():
        for pid in pids:
            votes[county_of[pid]][region_redirect[region]] += 1
            if bs[county_capitals[county_of[pid]]] == pid:
                capital_region[county_of[pid]] = region_redirect[region]
    reserved = {r['capital_county']: r['region'] for t, r in active.items() if t not in retired}
    assert len(reserved) == len(active) - len(retired)
    allocation = {}
    for county, counts in votes.items():
        allocation[county] = reserved.get(county) or max(counts, key=lambda r: (counts[r], r == capital_region.get(county), r))
    regions = {r: set() for r in old}
    for county, region in allocation.items():
        regions[region].update(ts[county])
    assert sum(bool(p) for p in regions.values()) == 70
    changes = {}
    for region, pids in regions.items():
        rest = set(pids)
        props = []
        for prefix, prop in [('d_', 'duchies'), ('c_', 'counties')]:
            selected = []
            for title, land in sorted(ts.items()):
                if title.startswith(prefix) and land and land <= rest:
                    selected.append(title)
                    rest -= land
            if selected:
                props.append((prop, ([], selected)))
        assert not rest, ('Incomplete counties in clerical region', region)
        changes[region] = '\n'.join(helper.render(([(region, (props, []))], [])))
    geo_rel = Path('map_data/geographical_regions/geographical_region.txt')
    history_rel = Path('history/titles/ce3/00_ecclesiastical_titles.txt')
    products = {geo_rel: helper.replace_blocks(helper.read(BASE / geo_rel), changes)}
    history = helper.read(BASE / history_rel)
    nodes = dict(g.parse(history)[0])
    history_changes = {}
    for title in retired:
        fields = [('government', 'ecclesiastical_government'), ('holder', '0'), ('clerical_region', 'none')]
        history_changes[title] = '\n'.join(helper.render(([(title, ([('1337.4.1', (fields, []))], []))], [])))
    products[history_rel] = helper.replace_blocks(history, history_changes)

    # Verify the staged game data, not just the allocation table.
    final = dict(g.parse(products[geo_rel])[0])
    previous = dict(g.parse(helper.read(BASE / geo_rel))[0])
    assert set(final) == set(previous)
    assert all(final[k] == previous[k] for k in previous if k not in regions)
    final_history = dict(g.parse(products[history_rel])[0])
    assert all(final_history[k] == nodes[k] for k in nodes if k not in retired)
    seen_counties, seen_pids = {}, set()
    for region, pids in regions.items():
        expanded = helper.expand(region, final, ts, {})
        assert expanded == pids
        assert not (seen_pids & expanded)
        seen_pids.update(expanded)
        for county in {county_of[p] for p in expanded}:
            assert ts[county] <= expanded
            assert county not in seen_counties, ('Overlapping clerical county', county)
            seen_counties[county] = region
    assert set(seen_counties) == set(allocation)
    for title, row in active.items():
        if title not in retired:
            assert seen_counties[row['capital_county']] == row['region']
    report = {'backup': str(BACKUP), 'active_regions': 70, 'assigned_counties': len(allocation),
              'assigned_baronies': len(seen_pids), 'overlapping_counties': 0, 'overlapping_baronies': 0,
              'mergers': mergers, 'unrelated_regions_unchanged': True, 'county_map_unchanged': True,
              'in_game_test_performed': False, 'validation': 'passed'}
    for rel, text in products.items():
        target = OUT / 'staged' / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8-sig')
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    (OUT / 'county_assignment.json').write_text(json.dumps(allocation, ensure_ascii=False, indent=2), encoding='utf-8')
    (OUT / 'region_provinces.json').write_text(json.dumps({r: sorted(p) for r, p in regions.items()}, indent=2), encoding='utf-8')
    with (OUT / 'ecclesiastical_titles.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        fields = list(rows[0]) + ['merged_into']
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            row['merged_into'] = retired.get(row['title'], '')
            if row['merged_into']:
                row.update(active=False, region='none', baronies=0)
            elif row['region'] in regions:
                row['baronies'] = len(regions[row['region']])
            writer.writerow(row)
    if '--apply' in sys.argv:
        for rel in products:
            assert (MOD / rel).read_bytes() in ((BASE / rel).read_bytes(), (OUT / 'staged' / rel).read_bytes())
        for rel in products:
            (MOD / rel).write_bytes((OUT / 'staged' / rel).read_bytes())
            assert (MOD / rel).read_bytes() == (OUT / 'staged' / rel).read_bytes()
        # No secondary changes to capitals, secular history or previous scripts.
        for folder in ('common/landed_titles', 'history/titles/ce3', 'map_data/geographical_regions'):
            for before in (BASE / folder).rglob('*.txt'):
                rel = before.relative_to(BASE)
                if rel not in products:
                    assert before.read_bytes() == (MOD / rel).read_bytes()
        print('Applied and verified 2 game files.')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
