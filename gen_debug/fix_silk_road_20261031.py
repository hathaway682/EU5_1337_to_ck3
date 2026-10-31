"""Adapt Silk Road arrows, region centers, and six markets to the EU5 map.

Dry run stages output and a mapping report; --apply deploys after validation.
"""
from pathlib import Path
from collections import Counter
import importlib.util
import json
import re
import sys
import numpy as np
from PIL import Image

MOD = Path(__file__).resolve().parents[1]
BACKUP = Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261031_180521_silk_road')
INPUT = BACKUP / 'inputs'
OUT = MOD / 'gen_debug/silk_road_fix_20261031'
OUT.mkdir(exist_ok=True)


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


g = module('region_parser', INPUT / 'rebuild_geographical_regions_20261031.py')
georef = module('georef', INPUT / '_georef.py')
title_sets, baronies, ancestry = g.titles(BACKUP / 'mod/common/landed_titles')
land = set(baronies.values())
hubs = {
    10148: ('china', 'b_jingzhao', 'changan_market_01'),
    9238: ('tibet', 'b_gyama', 'lhasa_market_01'),
    1362: ('india', 'b_lahore', 'lahur_bazaar_01'),
    9476: ('central_asia', 'b_shazhou', 'dunhuang_market_01'),
    4452: ('transcaspia', 'b_khiva', 'khiva_bazaar_01'),
    672: ('occident', 'b_yerevan', 'dvin_shuka_01'),
}
source_arrows = g.read(INPUT / 'vanilla/common/connection_arrows/silk_road_arrows.txt')
arrow_tree = g.parse(source_arrows)
routes = {key: list(map(int, dict(body[0])['provinces'][1])) for key, body in arrow_tree[0]}
needed = sorted(set(p for route in routes.values() for p in route))
Image.MAX_IMAGE_PIXELS = None
miller = Image.open(INPUT / 'georeference/miller_provinces.png')
assert miller.size == georef.MILLER_SIZE
lut = g.definitions(INPUT / 'vanilla/map_data/definition.csv')
size = int(lut.max()) + 1
count, sx, sy = np.zeros(size), np.zeros(size), np.zeros(size)
for y in range(0, miller.height, 128):
    ids = g.pixels(miller, lut, y)
    yy, xx = np.indices(ids.shape)
    count += np.bincount(ids.ravel(), minlength=size)
    sx += np.bincount(ids.ravel(), weights=xx.ravel(), minlength=size)
    sy += np.bincount(ids.ravel(), weights=(yy + y).ravel(), minlength=size)
assert all(count[p] for p in needed), ('Missing source geometry', [p for p in needed if not count[p]])
target_im = Image.open(BACKUP / 'mod/map_data/provinces.png').convert('RGB')
assert target_im.size == georef.GALL_SIZE
target_lut = g.definitions(BACKUP / 'mod/map_data/definition.csv')
is_land = np.zeros(int(target_lut.max()) + 1, dtype=bool)
is_land[list(land)] = True


def find_land(x, y, exclude=()):
    px, py = round(x), round(y)
    for radius in (0, 4, 12, 32, 64, 128):
        left, top = max(0, px - radius), max(0, py - radius)
        right, bottom = min(target_im.width, px + radius + 1), min(target_im.height, py + radius + 1)
        a = np.asarray(target_im.crop((left, top, right, bottom)), dtype=np.uint32)
        ids = target_lut[(a[:, :, 0] << 16) | (a[:, :, 1] << 8) | a[:, :, 2]]
        valid = is_land[ids] & ~np.isin(ids, list(exclude))
        yy, xx = np.where(valid)
        if len(xx):
            dist = (xx + left - x) ** 2 + (yy + top - y) ** 2
            j = int(np.argmin(dist))
            return int(ids[yy[j], xx[j]]), float(np.sqrt(dist[j]))
    raise AssertionError(('No playable land near source waypoint', x, y))


mapping, points = {}, {}
reverse = {p: b for b, p in baronies.items()}
for old in needed:
    mx, my = sx[old] / count[old], sy[old] / count[old]
    x, y = georef.lonlat_to_eu5_px(*georef.miller_px_to_lonlat(mx, my))
    target, distance = find_land(x, y)
    if old in hubs:
        target = baronies[hubs[old][1]]
    mapping[old] = target
    points[old] = {'source_centroid': [mx, my], 'eu5_pixel': [x, y],
                   'target': target, 'barony': reverse[target], 'nearest_land_distance': distance,
                   'hub_override': old in hubs}

output_routes = {}
arrow_blocks = []
for key, body in arrow_tree[0]:
    props = dict(body[0])
    route = []
    for old in routes[key]:
        new = mapping[old]
        # Several vanilla baronies can lie in one EU5 location. Keep each once.
        if new not in route:
            route.append(new)
    if len(route) == 2:
        start = points[routes[key][0]]['eu5_pixel']
        end = points[routes[key][-1]]['eu5_pixel']
        middle, _ = find_land((start[0] + end[0]) / 2, (start[1] + end[1]) / 2, exclude=route)
        route.insert(1, middle)
    assert len(route) > 2, ('Arrow too short', key, route)
    assert set(route) <= land
    if props.get('is_primary') == 'yes':
        assert route[0] in [baronies[b] for _, b, _ in hubs.values()]
    output_routes[key] = route
    lines = [key + ' = {']
    if 'is_primary' in props:
        lines.append('\tis_primary = ' + props['is_primary'])
    lines += ['\tarrow_type = "silkRoadArrow"', '\tprovinces = {']
    lines += ['\t\t' + str(p) + ' # ' + reverse[p] for p in route]
    lines += ['\t}', '}\n']
    arrow_blocks.append('\n'.join(lines))
arrows = '# Vanilla Silk Road paths projected onto the EU5 map; six centers adapted to existing settlements.\n\n' + '\n'.join(arrow_blocks)

situation = g.read(INPUT / 'vanilla/common/situation/situations/tgp_silk_road.txt')
region_members = json.loads((MOD / 'gen_debug/geographical_regions_rebuild_20261031/region_provinces.json').read_text(encoding='utf-8'))
for old, (region, barony, market) in hubs.items():
    pid = baronies[barony]
    assert pid in region_members['tgp_silk_road_' + region + '_region'], ('Hub outside region', region, barony)
    situation, replacements = re.subn(r'(capital_province\s*=\s*)' + str(old) + r'\b', lambda m: m[1] + str(pid), situation)
    assert replacements == 1

history_path = Path('history/provinces/00_generated_provinces.txt')
history = g.read(BACKUP / 'mod' / history_path)
market_ids = {m for _, _, m in hubs.values()}
removed = Counter()
pattern = re.compile(r'(?m)^[ \t]*(special_building_slot|special_building)\s*=\s*(' + '|'.join(market_ids) + r')\s*\r?\n')


def remove_old(match):
    removed[(match[1], match[2])] += 1
    return ''


history = pattern.sub(remove_old, history)
assert len(removed) == 12 and all(v == 1 for v in removed.values()), removed
hub_report = []
for old, (region, barony, market) in hubs.items():
    pid = baronies[barony]
    block_pattern = re.compile(r'(?m)^' + str(pid) + r'\s*=\s*\{(.*?)^\}', re.S)
    match = block_pattern.search(history)
    assert match
    body = match[1]
    assert not re.search(r'\bspecial_building(?:_slot)?\s*=', body), ('Special slot occupied', barony)
    holding = re.search(r'\bholding\s*=\s*(\w+)', body)[1]
    if barony == 'b_gyama':
        assert holding == 'none'
        # EU5 merges Potala and Jokhang into Lhasa. Keep Jokhang at b_lhasa;
        # provide the separate market settlement in Gyama, in the same county.
        body, n = re.subn(r'(\bholding\s*=\s*)none\b', r'\g<1>city_holding', body)
        assert n == 1
        history = history[:match.start(1)] + body + history[match.end(1):]
        match = block_pattern.search(history)
        holding = 'city_holding'
    assert holding not in ('none', 'wilderness_holding'), ('Uninhabited market hub', barony)
    effect = ('    effect = {\n        if = {\n            limit = { has_tgp_dlc_trigger = yes }\n'
              '            add_special_building_slot = ' + market + '\n'
              '            add_special_building = ' + market + '\n        }\n    }\n')
    history = history[:match.end() - 1] + effect + history[match.end() - 1:]
    hub_report.append({'region': region, 'barony': barony, 'province': pid, 'building': market, 'holding': holding})
g.parse(history)
g.parse(situation)
g.parse(arrows)
outputs = {
    Path('common/connection_arrows/silk_road_arrows.txt'): arrows,
    Path('common/situation/situations/tgp_silk_road.txt'): situation,
    history_path: history,
    Path('localization/replace/english/zz_gen_silk_road_l_english.yml'): '# Generated random Silk Road names disabled; inherit the game localization.\n',
}
for rel, content in outputs.items():
    target = OUT / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding='utf-8-sig')
report = {'backup': str(BACKUP), 'arrows': len(output_routes), 'source_waypoints': len(needed),
          'hubs': hub_report, 'mapping': points, 'routes': output_routes,
          'removed_random_markets': {str(k): v for k, v in removed.items()},
          'max_nearest_land_distance': max(p['nearest_land_distance'] for p in points.values())}
(OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in report.items() if k not in ('mapping', 'routes')}, ensure_ascii=False, indent=2))
if '--apply' in sys.argv:
    for rel in outputs:
        dest = MOD / rel
        original = BACKUP / 'mod' / rel
        assert (dest.read_bytes() == original.read_bytes()) if original.exists() else not dest.exists(), ('Unbacked change', rel)
    for rel in outputs:
        dest = MOD / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((OUT / rel).read_bytes())
        assert dest.read_bytes() == (OUT / rel).read_bytes()
    print('Applied four Silk Road files.')
