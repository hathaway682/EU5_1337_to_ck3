"""Restore the 1178 ecclesiastical framework on the conversion's 1337 map.

Dry-run by default. Inputs and overwritten products were backed up on F:.
Uses the registered Miller/Gall transform, never regenerates secular politics.
1178 is the territorial baseline, not a source of living 1337 office holders.
"""
from pathlib import Path
from collections import Counter, defaultdict
import csv
import importlib.util
import json
import re
import sys

import numpy as np
from PIL import Image

MOD = Path(__file__).resolve().parents[1]
BACKUP = Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261101_050756_ecclesiastical_1178')
BASE = BACKUP / 'mod'
VANILLA = BACKUP / 'inputs/vanilla'
OUT = MOD / 'gen_debug/ecclesiastical_1178_20261101'
START = (1337, 4, 1)
REFERENCE = (1178, 10, 1)


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


g = module('ecclesiastical_parser', BASE / 'gen_debug/rebuild_geographical_regions_20261031.py')
geo = module('ecclesiastical_georef', BACKUP / 'inputs/_georef.py')


def read(path):
    return path.read_text(encoding='utf-8-sig', errors='replace')


def date_key(value):
    return tuple(map(int, value.split('.')))


def state(node, date):
    result = {k: v for k, v in node[0] if not re.fullmatch(r'\d+\.\d+\.\d+', k)}
    for key, value in sorted(((k, v) for k, v in node[0] if re.fullmatch(r'\d+\.\d+\.\d+', k)), key=lambda x: date_key(x[0])):
        if date_key(key) <= date:
            result.update(dict(value[0]))
    return result


def render(node, indent=0):
    lines = []
    for key, value in node[0]:
        if isinstance(value, tuple):
            lines.append('\t' * indent + key + ' = {')
            lines.extend(render(value, indent + 1))
            lines.append('\t' * indent + '}')
        else:
            lines.append('\t' * indent + key + ' = ' + value)
    if node[1]:
        lines.append('\t' * indent + ' '.join(node[1]))
    return lines


def top_spans(text):
    tokens = [m for m in g.TOKEN.finditer(text) if not m.group().startswith('#')]
    result, depth, begin = {}, 0, None
    for i, token in enumerate(tokens):
        if token.group() == '{':
            if depth == 0:
                assert tokens[i - 1].group() == '='
                begin = (tokens[i - 2].group(), tokens[i - 2].start())
            depth += 1
        elif token.group() == '}':
            depth -= 1
            if depth == 0:
                result[begin[0]] = (begin[1], token.end())
    assert depth == 0
    return result


def replace_blocks(text, changes):
    spans = top_spans(text)
    for begin, end, replacement in sorted([(spans[k][0], spans[k][1], v) for k, v in changes.items()], reverse=True):
        text = text[:begin] + replacement + text[end:]
    return text


def load_regions(folder):
    nodes, files = {}, {}
    for path in sorted(folder.glob('*.txt')):
        for key, node in g.parse(read(path))[0]:
            assert key not in nodes, ('Duplicate geographical region', key)
            nodes[key], files[key] = node, path.name
    return nodes, files


def expand(key, regions, titles, cache):
    if key in cache:
        return cache[key]
    members = set()
    for prop, value in regions[key][0]:
        if prop in ('duchies', 'counties', 'baronies', 'kingdoms', 'empires', 'hegemonies'):
            for title in value[1]:
                assert title in titles, ('Missing geographical title', key, title)
                members.update(titles[title])
        elif prop == 'provinces':
            members.update(map(int, value[1]))
        elif prop == 'regions':
            for child in value[1]:
                members.update(expand(child, regions, titles, cache))
    cache[key] = members
    return members


# Named seats; aliases also disambiguate overseas namesakes. Where the EU5 map
# has no separate city, a nearby named tile supplies the correct county pointer.
SEAT_ALIASES = {
    'santiago': 'santiago_compostela', 'tingitana': 'tangier',
    'tarentaise': 'moutiers', 'eauze': 'lectoure', 'aix': 'aix_en_provence',
    'embrun': 'gap', 'torres': 'sassari', 'reggio_calabria': 'reggiocal',
    'santa_severina': 'cotrone', 'roma': 'rome', 'capua': 'caserta',
    'napoli': 'naples', 'trani': 'barletta', 'ragusa': 'dubrovnik',
    'hamburg': 'bremen', 'cyprus': 'nicosia_cyp', 'georgia': 'tbilisi',
    'kartli': 'mtskheta', 'armenia': 'van', 'seleucia_ctesiphon': 'baghdad',
    'tyre': 'sidon', 'africa': 'tunis',
}
PROXY_SEATS = {'eauze', 'embrun', 'torres', 'santa_severina', 'capua', 'trani', 'tyre'}
KNOWN_OFFICES = {
    'roma': 'k_papal_state', 'constantinople': 'k_orthodox',
    'alexandria': 'd_coptic_papacy', 'armenia': 'd_apostolic_church',
    'aquileia': 'd_eu5_aqu', 'salzburg': 'd_salzburg', 'trier': 'd_eu5_tri',
    'mainz': 'd_eu5_mai', 'magdeburg': 'd_eu5_mag', 'cologne': 'd_eu5_kol',
    'hamburg': 'd_eu5_bre',
}


def main():
    OUT.mkdir(exist_ok=True)
    our_titles, our_b, our_anc = g.titles(BASE / 'common/landed_titles')
    source_titles, source_b, _ = g.titles(VANILLA / 'common/landed_titles')
    our_land = set(our_b.values())
    our_regions, region_files = load_regions(BASE / 'map_data/geographical_regions')
    source_regions, _ = load_regions(VANILLA / 'map_data/geographical_regions')
    source_history = dict(g.parse(read(VANILLA / 'history/titles/ce3/00_ecclesiastical_titles.txt'))[0])
    source_defs_text = read(VANILLA / 'common/landed_titles/07_pam_ecclesiastical_titles.txt')
    source_defs = dict(g.parse(source_defs_text)[0])
    ecclesiastical = {k: state(n, REFERENCE) for k, n in source_history.items() if k.startswith('d_et_')}
    active = {k: n['clerical_region'] for k, n in ecclesiastical.items() if n.get('clerical_region', 'none') != 'none'}
    assert len(ecclesiastical) == 77 and len(active) == 75
    assert len(set(active.values())) == 75
    source_cache, current_cache = {}, {}
    region_keys = sorted(active.values())
    region_index = {key: i + 1 for i, key in enumerate(region_keys)}
    source_assignment = np.zeros(65536, dtype=np.int16)
    for key in region_keys:
        members = expand(key, source_regions, source_titles, source_cache)
        assert members and max(members) < len(source_assignment)
        for pid in members:
            assert source_assignment[pid] == 0, ('Overlapping vanilla 1178 clerical regions', key, pid)
            source_assignment[pid] = region_index[key]

    # Majority of registered raster overlap, excluding source water/impassables.
    # Category zero is valid source land outside all 1178 ecclesiastical regions.
    cache_path = OUT / 'raster_votes.npz'
    if cache_path.exists():
        votes = np.load(cache_path)['votes']
    else:
        Image.MAX_IMAGE_PIXELS = None
        our_map = Image.open(BASE / 'map_data/provinces.png')
        source_map = np.asarray(Image.open(BACKUP / 'inputs/miller_provinces.png').convert('RGB'), dtype=np.uint32)
        source_lut = g.definitions(VANILLA / 'map_data/definition.csv')
        source_pixels = source_lut[(source_map[:, :, 0] << 16) | (source_map[:, :, 1] << 8) | source_map[:, :, 2]]
        del source_map, source_lut
        our_lut = g.definitions(BASE / 'map_data/definition.csv')
        allowed = np.zeros(int(our_lut.max()) + 1, dtype=bool)
        allowed[list(our_land)] = True
        source_playable = np.zeros(65536, dtype=bool)
        source_playable[list(source_b.values())] = True
        stride = len(region_keys) + 1
        votes = np.zeros((len(allowed), stride), dtype=np.int64)
        ga, _, gc, gf = geo.GALL_WF
        ma, _, mc, mf = geo.MILLER_WF
        gx = np.arange(our_map.width, dtype=np.float64)
        mx = np.rint(((gc + gx * ga) * geo.SQ2 - mc) / ma).astype(np.int32)
        xvalid = (mx >= 0) & (mx < source_pixels.shape[1])
        mx = mx.clip(0, source_pixels.shape[1] - 1)
        for y in range(0, our_map.height, 128):
            gy = np.arange(y, min(y + 128, our_map.height), dtype=np.float64)
            phi = 2 * np.arctan((gf - gy * -geo.GALL_WF[1]) / (geo.R * (1 + geo.SQ2 / 2)))
            ym = geo.R * 1.25 * np.log(np.tan(np.pi / 4 + .4 * phi))
            my = np.rint((mf - ym) / -geo.MILLER_WF[1]).astype(np.int32)
            yvalid = (my >= 0) & (my < source_pixels.shape[0])
            q = source_pixels[my.clip(0, source_pixels.shape[0] - 1)[:, None], mx[None, :]]
            p = g.pixels(our_map, our_lut, y)
            valid = allowed[p] & source_playable[q] & yvalid[:, None] & xvalid[None, :]
            code = p[valid].astype(np.int64) * stride + source_assignment[q[valid]]
            votes += np.bincount(code, minlength=votes.size).reshape(votes.shape)
            if y % 2048 == 0:
                print('Registered raster rows', y, '/', our_map.height, flush=True)
        np.savez_compressed(cache_path, votes=votes)
    assigned = votes.argmax(axis=1)
    members = {key: {pid for pid in our_land if assigned[pid] == region_index[key]} for key in region_keys}

    # Actual named seats take precedence over coarse source borders and coastal
    # raster displacement. Never give the same barony to two clerical regions.
    seat_pins = []
    for title, region in active.items():
        name = title[5:]
        barony = 'b_' + SEAT_ALIASES.get(name, name)
        pid = our_b[barony]
        if pid not in members[region]:
            previous = [k for k, ps in members.items() if pid in ps]
            for key in previous:
                members[key].remove(pid)
            members[region].add(pid)
            seat_pins.append({'title': title, 'barony': barony, 'previous_regions': previous, 'region': region})
    assert all(members.values())
    owners = {}
    for key, ps in members.items():
        for pid in ps:
            assert pid not in owners
            owners[pid] = key

    products = {}
    replacement_blocks = defaultdict(dict)
    for key, ps in members.items():
        rest = set(ps)
        props = []
        for tier, prop in [('d_', 'duchies'), ('c_', 'counties')]:
            selected = []
            for title, land in sorted(our_titles.items()):
                if title.startswith(tier) and land and land <= rest:
                    selected.append(title)
                    rest -= land
            if selected:
                props.append((prop, ([], selected)))
        if rest:
            props.append(('provinces', ([], list(map(str, sorted(rest))))))
        node = (props, [])
        replacement_blocks[region_files[key]][key] = '\n'.join(render(([(key, node)], [])))
    for filename, changes in replacement_blocks.items():
        rel = Path('map_data/geographical_regions') / filename
        products[rel] = replace_blocks(read(BASE / rel), changes)

    # Restore every vanilla ecclesiastical/cardinal declaration in its dedicated
    # file, and remove its old Africa-capital shim to avoid duplicate keys.
    declared = {k for k in source_defs if k.startswith(('d_et_', 'd_cd_'))}
    # Vanilla repeats the identical d_cd_san_stefano block; declare it once.
    assert len(declared) == 132
    capitals, seats = {}, {}
    declaration_nodes = []
    for key, node in source_defs.items():
        if key not in declared:
            declaration_nodes.append((key, node))
            continue
        if key.startswith('d_et_'):
            name = key[5:]
            barony = 'b_' + SEAT_ALIASES.get(name, name)
        else:
            cap = dict(node[0])['capital']
            barony = {'c_roma': 'b_rome', 'c_ravenna': 'b_ravenna', 'c_ancona': 'b_ancona'}[cap]
        assert barony in our_b, ('Unmapped seat', key, barony)
        county = next(k for k in our_anc[barony] if k.startswith('c_'))
        capitals[key], seats[key] = county, barony
        props = [(k, county if k == 'capital' else v) for k, v in node[0]]
        declaration_nodes.append((key, (props, node[1])))
    products[Path('common/landed_titles/07_pam_ecclesiastical_titles.txt')] = (
        '# Vanilla ecclesiastical/cardinal properties; seats adapted to the EU5 map.\n'
        '# Territorial reference: 1178.10.1. Do not restore the titular shims.\n\n'
        + '\n'.join(render((declaration_nodes, []))) + '\n')
    shim_rel = Path('common/landed_titles/zz_vanilla_titulars.txt')
    shim_before = read(BASE / shim_rel)
    assert declared <= top_spans(shim_before).keys()
    products[shim_rel] = replace_blocks(shim_before, {key: '' for key in declared})

    politics = {}
    for path in sorted((BASE / 'history/titles').glob('*.txt')):
        for key, node in g.parse(read(path))[0]:
            assert key not in politics, ('Existing duplicate title history', key, path.name)
            politics[key] = state(node, START)
    characters = {}
    for path in sorted((BASE / 'history/characters').glob('*.txt')):
        for key, node in g.parse(read(path))[0]:
            previous = characters.get(key, ([], []))
            characters[key] = (previous[0] + node[0], previous[1] + node[1])
    rows, history_lines = [], [
        '# 1337 setup using the vanilla 1178.10.1 ecclesiastical geography.\n',
        '# Regions suppressed by 1178 stay suppressed. No 1178 holder is imported.\n',
        '# Existing 1337 clergy are reused; other offices have no authored holder yet.\n',
        '# Cardinalates are declared in landed_titles and filled by vanilla setup.\n',
    ]
    for title, props in ecclesiastical.items():
        name = title[5:]
        region = props.get('clerical_region', 'none')
        holder, liege = '0', None
        if name in KNOWN_OFFICES:
            current = politics[KNOWN_OFFICES[name]]
            holder = current['holder']
            assert holder != '0' and holder in characters
            char = state(characters[holder], START)
            assert char.get('religion') in ('catholic', 'orthodox', 'miaphysitism', 'armenian_apostolic'), (title, char.get('religion'))
            assert not any(date_key(k) <= START and any(a == 'death' for a, b in n[0]) for k, n in characters[holder][0] if re.fullmatch(r'\d+\.\d+\.\d+', k))
            liege = current.get('liege')
            if liege and liege != '0':
                assert politics[liege].get('holder', '0') != '0'
        fields = [('government', 'ecclesiastical_government'), ('holder', holder), ('clerical_region', region)]
        if liege:
            fields.append(('liege', liege))
        if 'name' in props:
            fields.append(('name', props['name']))
        history_lines.append('\n' + '\n'.join(render(([(title, ([('1337.4.1', (fields, []))], []))], []))) + '\n')
        old = expand(region, our_regions, our_titles, current_cache) if region != 'none' else set()
        new = members.get(region, set())
        rows.append({'title': title, 'reference_date': '1178.10.1', 'region': region,
                     'active': region != 'none', 'capital_county': capitals[title], 'seat_barony': seats[title],
                     'seat_is_proxy': name in PROXY_SEATS, 'holder_1337': holder,
                     'holder_source_title': KNOWN_OFFICES.get(name, ''), 'liege_1337': liege or '',
                     'reference_holder_1178_not_imported': props.get('holder', '0'),
                     'baronies': len(new), 'baronies_added': len(new - old), 'baronies_removed': len(old - new)})
    products[Path('history/titles/ce3/00_ecclesiastical_titles.txt')] = ''.join(history_lines)

    # Preserve the 1178 institutional mergers without importing old cardinals.
    # Vanilla's vacancy selection reads suppressed_cardinalate directly.
    cardinal_lines = ['# Cardinalate mergers already in force at the 1178 reference date.\n']
    for title in ('d_cd_ostia', 'd_cd_porto', 'd_cd_velletri', 'd_cd_santa_rufina'):
        effects = []
        for date, node in sorted(source_history[title][0], key=lambda x: date_key(x[0])):
            if date_key(date) <= REFERENCE:
                for prop, value in node[0]:
                    if prop == 'effect':
                        effects.extend((k, v) for k, v in value[0]
                                       if k == 'set_title_name' or (k == 'set_variable' and v == 'suppressed_cardinalate'))
        assert effects
        fields = [('government', 'ecclesiastical_government'), ('holder', '0'), ('effect', (effects, []))]
        cardinal_lines.append('\n' + '\n'.join(render(([(title, ([('1337.4.1', (fields, []))], []))], []))) + '\n')
    products[Path('history/titles/ce3/01_cardinalate_status.txt')] = ''.join(cardinal_lines)

    # Character history effects otherwise overwrite these same bishops' title
    # history government. Change only the existing generic-theocracy command.
    government_rel = Path('history/characters/zz_eu5_government.txt')
    government_before = read(BASE / government_rel)
    government_nodes = dict(g.parse(government_before)[0])
    government_spans = top_spans(government_before)
    government_changes = {}
    for holder in {r['holder_1337'] for r in rows} - {'0'}:
        if holder in government_nodes:
            begin, end = government_spans[holder]
            old = government_before[begin:end]
            updated, count = re.subn(r'(\bchange_government\s*=\s*)theocracy_government\b',
                                     r'\1ecclesiastical_government', old)
            assert count == 1, ('Unexpected clergy government patch', holder, count)
            government_changes[holder] = updated
    assert len(government_changes) == 8
    products[government_rel] = replace_blocks(government_before, government_changes)
    government_after = dict(g.parse(products[government_rel])[0])
    assert set(government_after) == set(government_nodes)
    assert all(government_after[k] == government_nodes[k] for k in government_nodes if k not in government_changes)

    # Semantic verification, including untouched geographical definitions and
    # every unrelated titular declaration, before any live product is written.
    final_regions = dict(our_regions)
    for rel, text in products.items():
        parsed = g.parse(text)
        if str(rel).replace('\\', '/').startswith('map_data/geographical_regions/'):
            final_regions.update(dict(parsed[0]))
    for key in our_regions:
        if key not in members:
            assert final_regions[key] == our_regions[key], ('Unrelated region changed', key)
    for key, ps in members.items():
        assert expand(key, final_regions, our_titles, {}) == ps
        assert all(prop not in ('kingdoms', 'empires', 'hegemonies') for prop, _ in final_regions[key][0])
    shim_after = dict(g.parse(products[shim_rel])[0])
    shim_before_nodes = dict(g.parse(shim_before)[0])
    assert set(shim_after) == set(shim_before_nodes) - declared
    assert all(shim_after[key] == shim_before_nodes[key] for key in shim_after)
    all_declarations = Counter()
    for path in sorted((BASE / 'common/landed_titles').glob('*.txt')):
        rel = path.relative_to(BASE)
        text = products.get(rel, read(path))
        for key, _ in g.parse(text)[0]:
            if re.fullmatch(r'[hkedcb]_[\w-]+', key):
                all_declarations[key] += 1
    assert all(all_declarations[key] == 1 for key in declared)
    for row in rows:
        assert row['capital_county'] in our_titles
        if row['active']:
            assert our_b[row['seat_barony']] in members[row['region']]
    for rel, text in products.items():
        target = OUT / 'staged' / rel
        target.parent.mkdir(exist_ok=True, parents=True)
        target.write_text(text, encoding='utf-8-sig', newline='\n')
    with (OUT / 'ecclesiastical_titles.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = {'backup': str(BACKUP), 'reference_date': '1178.10.1', 'scenario_date': '1337.4.1',
              'ecclesiastical_histories': len(rows), 'active_regions': len(active),
              'inactive_titles': [r['title'] for r in rows if not r['active']],
              'ecclesiastical_declarations': sum(k.startswith('d_et_') for k in declared),
              'cardinal_declarations': sum(k.startswith('d_cd_') for k in declared),
              'suppressed_cardinalates': ['d_cd_velletri', 'd_cd_santa_rufina'],
              'existing_1337_clergy_reused': sum(r['holder_1337'] != '0' for r in rows),
              'government_overrides_corrected': len(government_changes),
              'unassigned_active_holders': sum(r['holder_1337'] == '0' and r['active'] for r in rows),
              'region_baronies': len(owners), 'region_overlap_baronies': 0, 'seat_pins': seat_pins,
              'shared_seat_counties': {c: [r['title'] for r in rows if r['active'] and r['capital_county'] == c]
                                       for c, n in Counter(r['capital_county'] for r in rows if r['active']).items() if n > 1},
              'files': [str(rel) for rel in products], 'validation': 'passed'}
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    (OUT / 'region_provinces.json').write_text(json.dumps({k: sorted(v) for k, v in members.items()}, indent=2), encoding='utf-8')
    if '--apply' in sys.argv:
        for rel in products:
            live = (MOD / rel).read_bytes() if (MOD / rel).exists() else None
            original = (BASE / rel).read_bytes() if (BASE / rel).exists() else None
            staged = (OUT / 'staged' / rel).read_bytes()
            assert live in (original, staged), ('Live file changed since backup', rel)
        for rel in products:
            (MOD / rel).write_bytes((OUT / 'staged' / rel).read_bytes())
        print('Applied', len(products), 'files.', flush=True)
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
