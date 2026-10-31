"""Map all fixed vanilla special-building sites onto the EU5 mod map.

Stages historical buildings and remaps fixed on-start building scopes. Sources
and all files to be modified are backed up on F:. Use --apply to deploy.
"""
from pathlib import Path
from collections import defaultdict, Counter
import importlib.util
import csv
import json
import re
import sys
import numpy as np
from PIL import Image

MOD = Path(__file__).resolve().parents[1]
BACKUP = Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261031_181602_all_special_buildings')
INPUT = BACKUP / 'inputs'
VANILLA = INPUT / 'vanilla'
OUT = MOD / 'gen_debug/all_special_buildings_20261031'
OUT.mkdir(exist_ok=True)


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


g = module('geo', INPUT / 'rebuild_geographical_regions_20261031.py')
geo = module('georef', INPUT / '_georef.py')


def read(path):
    # A few installed history files have legacy accented comments.
    return path.read_text(encoding='utf-8-sig', errors='replace')


def walk(node, path=()):
    for key, value in node[0]:
        yield path, key, value
        if isinstance(value, tuple):
            yield from walk(value, path + (key,))


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


def blocks(text):
    """Balanced block spans, ignoring braces in comments and quoted strings."""
    toks = [m for m in g.TOKEN.finditer(text) if not m.group().startswith('#')]
    stack = []
    result = []
    for i, token in enumerate(toks):
        if token.group() == '{':
            key = toks[i - 2] if i >= 2 and toks[i - 1].group() == '=' else None
            stack.append((key, token))
        elif token.group() == '}':
            key, opening = stack.pop()
            if key:
                result.append((key.group(), key.start(), key.end(), opening.end(), token.start(), token.end()))
    assert not stack
    return result


def edit(text, replacements):
    for start, end, value in sorted(replacements, reverse=True):
        text = text[:start] + value + text[end:]
    return text


building_defs, definition_file = {}, {}
for folder in (VANILLA / 'common/buildings', BACKUP / 'mod/common/buildings'):
    for file in sorted(folder.glob('*.txt')):
        for key, value in g.parse(read(file))[0]:
            if isinstance(value, tuple):
                building_defs[key] = value
                definition_file[key] = file.name
ducal_landmarks = {'theodosian_walls_01', 'aurelian_walls_01'}
special = {key for key, value in building_defs.items() if ('type', 'special') in value[0]} | ducal_landmarks
previous = {}
for key in special:
    nxt = dict(building_defs[key][0]).get('next_building')
    if nxt in special:
        assert nxt not in previous, ('Ambiguous building upgrade', nxt)
        previous[nxt] = key


def root(key):
    seen = set()
    while key in previous:
        assert key not in seen
        seen.add(key)
        key = previous[key]
    return key


COMMANDS = {'special_building', 'special_building_slot', 'add_special_building', 'add_special_building_slot', 'duchy_capital_building'}
BUILD_COMMANDS = COMMANDS | {'remove_building'}
our_sets, our_b, our_anc = g.titles(BACKUP / 'mod/common/landed_titles')
_, vanilla_b, vanilla_anc = g.titles(VANILLA / 'common/landed_titles')
reverse_vanilla = {p: b for b, p in vanilla_b.items()}
reverse_our = {p: b for b, p in our_b.items()}
history_file = Path('history/provinces/00_generated_provinces.txt')
current_history = read(BACKUP / 'mod' / history_file)
current_nodes = dict(g.parse(current_history)[0])
holding = {int(pid): dict(node[0]).get('holding', 'none') for pid, node in current_nodes.items()}
loc_text = read(INPUT / 'building_locators.txt')
centers = {int(pid): (float(x), 8191 - float(z)) for pid, x, _, z in re.findall(
    r'\bid\s*=\s*(\d+)\s+position\s*=\s*\{\s*([\d.-]+)\s+([\d.-]+)\s+([\d.-]+)', loc_text)}
assert set(our_b.values()) <= centers.keys()
source_nodes, source_files, groups = {}, {}, defaultdict(set)
all_source_nodes = {}
for file in sorted((VANILLA / 'history/provinces').glob('*.txt')):
    for pid, body in g.parse(read(file))[0]:
        if not pid.isdigit():
            continue
        numeric_pid = int(pid)
        if numeric_pid in all_source_nodes:
            all_source_nodes[numeric_pid] = (all_source_nodes[numeric_pid][0] + body[0], [])
        else:
            all_source_nodes[numeric_pid] = body
        found = {root(value) for _, key, value in walk(body) if key in COMMANDS and isinstance(value, str) and value in special}
        if found:
            pid = int(pid)
            if pid in source_nodes:
                body = (source_nodes[pid][0] + body[0], source_nodes[pid][1] + body[1])
            source_nodes[pid] = body
            source_files[pid] = file.name
            for building in found:
                groups[(pid, building)].add('history')

game_start_rel = Path('common/on_action/game_start.txt')
game_start = read(BACKUP / 'mod' / game_start_rel)
on_start_scopes = []
for key, start, end, body_start, body_end, closing in blocks(game_start):
    match = re.fullmatch(r'title:(b_[\w-]+)\.title_province', key)
    if not match:
        continue
    source_barony = match[1]
    body = game_start[body_start:body_end]
    buildings = re.findall(r'\badd_special_building(?:_slot)?\s*=\s*([\w-]+)', re.sub(r'#[^\n]*', '', body))
    if not buildings:
        continue
    assert all(b in special for b in buildings), ('Undefined startup building', key, buildings)
    assert source_barony in vanilla_b, ('Unknown startup source barony', source_barony)
    roots = {root(b) for b in buildings}
    assert len(roots) == 1, ('Mixed building families in one startup scope', key, roots)
    family = roots.pop()
    pid = vanilla_b[source_barony]
    groups[(pid, family)].add('on_start')
    on_start_scopes.append((start, end, pid, family))

# Keep the six audited Silk Road sites exactly as already placed.
silk = json.loads(read(INPUT / 'report.json'))
locked = {}
source_market = {'changan_market_01': 10148, 'lhasa_market_01': 9238, 'lahur_bazaar_01': 1362,
                 'dunhuang_market_01': 9476, 'khiva_bazaar_01': 4452, 'dvin_shuka_01': 672}
for item in silk['hubs']:
    locked[(source_market[item['building']], item['building'])] = item['province']
assert set(locked) <= groups.keys()

needed = sorted({pid for pid, _ in groups})
Image.MAX_IMAGE_PIXELS = None
image = Image.open(INPUT / 'georeference/miller_provinces.png')
assert image.size == geo.MILLER_SIZE
lut = g.definitions(VANILLA / 'map_data/definition.csv')
size = int(lut.max()) + 1
count, sx, sy = np.zeros(size), np.zeros(size), np.zeros(size)
for y in range(0, image.height, 128):
    ids = g.pixels(image, lut, y)
    yy, xx = np.indices(ids.shape)
    count += np.bincount(ids.ravel(), minlength=size)
    sx += np.bincount(ids.ravel(), weights=xx.ravel(), minlength=size)
    sy += np.bincount(ids.ravel(), weights=(yy + y).ravel(), minlength=size)
assert all(count[p] for p in needed), ('Missing reference geography', [p for p in needed if not count[p]])
points = {p: geo.lonlat_to_eu5_px(*geo.miller_px_to_lonlat(sx[p] / count[p], sy[p] / count[p])) for p in needed}
target_image = Image.open(BACKUP / 'mod/map_data/provinces.png').convert('RGB')
target_lut = g.definitions(BACKUP / 'mod/map_data/definition.csv')
all_land = sorted(our_b.values())
xy = np.array([centers[p] for p in all_land])
land = set(all_land)


def projected_province(point):
    x, y = point
    rgb = target_image.getpixel((max(0, min(16383, round(x))), max(0, min(8191, round(y)))))
    pid = int(target_lut[(rgb[0] << 16) | (rgb[1] << 8) | rgb[2]])
    if pid in land:
        return pid
    return all_land[int(np.argmin(np.sum((xy - point) ** 2, axis=1)))]


desired, rules = {}, {}
our_case = {key.casefold(): pid for key, pid in our_b.items()}
for group in groups:
    pid, family = group
    point = points[pid]
    candidate = projected_province(point)
    rule = 'projection'
    source_barony = reverse_vanilla[pid]
    named = our_case.get(source_barony.casefold())
    if named and np.linalg.norm(np.array(centers[named]) - point) < 100:
        candidate, rule = named, 'name_and_position'
    aliases = {'b_indraprastha': 'b_delhi', 'b_lahur': 'b_lahore',
               'b_potala': 'b_lhasa', 'b_dunhuang_2': 'b_shazhou',
               'b_nanhai': 'b_guangzhou'}
    if source_barony in aliases and aliases[source_barony] in our_b:
        named = our_b[aliases[source_barony]]
        if np.linalg.norm(np.array(centers[named]) - point) < 100:
            candidate, rule = named, 'historical_city_alias_and_position'
    if group in locked:
        candidate, rule = locked[group], 'preserved_silk_road'
    landmark_cities = {'sankore_university': 'b_timbuktu', 'qutb_minar_01': 'b_delhi'}
    if family in landmark_cities:
        candidate, rule = our_b[landmark_cities[family]], 'verified_landmark_city'
    desired[group], rules[group] = candidate, rule

placements, occupied = {}, {}
for group, pid in locked.items():
    assert pid not in occupied
    placements[group], occupied[pid] = pid, group
# Named exact matches have priority over fallback samples in adjacent locations.
# These are alternative slots selected by DLC guards, or an explicit replacement.
# They must share their historical site instead of becoming two monuments.
shared_with = {
    (848, 'generic_university'): (848, 'somapura_university_01'),
    (1862, 'generic_university'): (1862, 'drassanes_01'),
    (4694, 'generic_university'): (4694, 'al_qarawiyyin_university_01'),
    (12989, 'generic_university'): (12989, 'yuelu_academy_01'),
    (10816, 'temples_angkor_01'): (10816, 'angkor_wat_01'),
}
assert set(shared_with) <= groups.keys() and set(shared_with.values()) <= groups.keys()
order = sorted((group for group in groups if group not in locked and group not in shared_with and group[1] not in ducal_landmarks), key=lambda group: (rules[group] != 'verified_landmark_city', 'name' not in rules[group] and 'alias' not in rules[group], group))
relocations = []
for group in order:
    candidate = desired[group]
    if candidate in occupied:
        county = next(x for x in our_anc[reverse_our[candidate]] if x.startswith('c_'))
        point = points[group[0]]
        distance = np.sum((xy - point) ** 2, axis=1)
        nearby = [all_land[i] for i in np.argsort(distance) if all_land[i] not in occupied]
        same_county = [p for p in nearby if p in our_sets[county] and np.linalg.norm(np.array(centers[p]) - point) < 60]
        chosen = (same_county or nearby)[0]
        relocations.append({'source': group[0], 'building': group[1], 'from': reverse_our[candidate], 'to': reverse_our[chosen]})
        candidate = chosen
        rules[group] += '_separate_slot'
    placements[group] = candidate
    occupied[candidate] = group
for group, primary in shared_with.items():
    placements[group] = placements[primary]
    rules[group] = 'shared_original_site_with_' + primary[1]
for group in groups:
    if group[1] in ducal_landmarks:
        barony = 'b_constantinople' if group[1] == 'theodosian_walls_01' else 'b_rome'
        placements[group] = our_b[barony]
        rules[group] = 'separate_duchy_building_slot'
assert len(placements) == len(groups)
assert len(set(placements.values())) == len(groups) - len(shared_with) - len(ducal_landmarks)


def filter_buildings(node, family):
    """Retain building history, its dates, DLC guards, and branch structure."""
    result = []
    for key, value in node[0]:
        if key in BUILD_COMMANDS and isinstance(value, str) and value in special and root(value) == family:
            result.append((key, value))
        elif isinstance(value, tuple) and key != 'limit':
            child = filter_buildings(value, family)
            if child[0]:
                result.append((key, child))
    if result:
        limits = [(key, value) for key, value in node[0] if key == 'limit']
        result = limits + result
    # Preserve empty earlier conditional branches if a later branch has work.
    result_keys = [k for k, _ in result]
    if any(k in ('else', 'else_if') for k in result_keys):
        out = []
        kept = iter(result)
        # Recompute in original order so an else never gets detached from its if.
        result_by_id = {id(v): (k, v) for k, v in result if isinstance(v, tuple)}
        for k, v in node[0]:
            if k in ('if', 'else_if', 'else') and isinstance(v, tuple):
                child = filter_buildings(v, family)
                if not child[0]:
                    child = ([(x, z) for x, z in v[0] if x == 'limit'], [])
                out.append((k, child))
            elif k == 'limit':
                out.append((k, v))
            elif k in BUILD_COMMANDS and isinstance(v, str) and v in special and root(v) == family:
                out.append((k, v))
            elif isinstance(v, tuple):
                child = filter_buildings(v, family)
                if child[0]:
                    out.append((k, child))
        result = out
    return result, []


def ensure_effect_slots(node, family):
    pairs = []
    for key, value in node[0]:
        if isinstance(value, tuple):
            value = ensure_effect_slots(value, family)
        if key == 'add_special_building':
            pairs.append(('add_special_building_slot', family))
        pairs.append((key, value))
    return pairs, node[1]


def source_holding(pid):
    """Use the vanilla holding at the actual 1337 bookmark, including dated changes."""
    node = all_source_nodes.get(pid, ([], []))
    result = dict(node[0]).get('holding', 'none')
    dated = []
    for date, body in node[0]:
        if re.fullmatch(r'\d+\.\d+\.\d+', date) and isinstance(body, tuple):
            dt = tuple(map(int, date.split('.')))
            if dt <= (1337, 4, 1):
                dated.append((dt, body))
    for _, body in sorted(dated, key=lambda pair: pair[0]):
        if 'holding' in dict(body[0]):
            result = dict(body[0])['holding']
    return result


fragments = defaultdict(list)
for group, target in placements.items():
    source_pid, family = group
    if 'history' in groups[group] and group not in locked:
        filtered = filter_buildings(source_nodes[source_pid], family)
        assert filtered[0]
        fragments[target].append(ensure_effect_slots(filtered, family))

# Remove only undefined random generator wonders. The valid Silk Road effects stay.
undefined = {value for _, key, value in walk(g.parse(current_history)) if key in COMMANDS and isinstance(value, str) and value not in building_defs}
assert all(key.startswith('wonder_c_gen_') for key in undefined), ('Unexpected undefined special building', undefined)
removed_random = []
history = current_history
if undefined:
    rx = re.compile(r'(?m)^[ \t]*(special_building_slot|special_building)\s*=\s*(' + '|'.join(map(re.escape, undefined)) + r')[ \t]*\r?\n')
    def remove(match):
        removed_random.append(match[2])
        return ''
    history = rx.sub(remove, history)

developed = []
new_holdings = {}
for group, target in placements.items():
    if group in locked:
        continue
    if holding[target] in ('none', 'wilderness_holding'):
        src_holding = source_holding(group[0])
        if src_holding in ('none', 'wilderness_holding'):
            continue
        new_holding = src_holding
        new_holdings[target] = new_holding
        if not any(row['barony'] == reverse_our[target] for row in developed):
            developed.append({'barony': reverse_our[target], 'from': holding[target], 'to': new_holding, 'building': group[1]})
history_edits = []
for key, start, end, body_start, body_end, closing in blocks(history):
    if not key.isdigit() or int(key) not in (fragments.keys() | new_holdings.keys()):
        continue
    pid = int(key)
    body = history[body_start:body_end]
    if pid in new_holdings:
        body, n = re.subn(r'(\bholding\s*=\s*)\w+', lambda m: m[1] + new_holdings[pid], body, count=1)
        assert n == 1
    for fragment in fragments.get(pid, []):
        body += '\n\t# Historical special building, mapped from the installed CK3 map.\n' + '\n'.join(render(fragment, 1)) + '\n'
    history_edits.append((body_start, body_end, body))
history = edit(history, history_edits)
assert len(history_edits) == len(fragments.keys() | new_holdings.keys())

scope_edits = [(start, end, 'title:' + reverse_our[placements[(pid, family)]] + '.title_province') for start, end, pid, family in on_start_scopes]
startup = edit(game_start, scope_edits)
# Add a matching base slot before startup building construction when absent.
startup = re.sub(r'\badd_special_building\s*=\s*([\w-]+)', lambda m: 'add_special_building_slot = ' + root(m[1]) + '\n\t\t\t\tadd_special_building = ' + m[1], startup)

outputs = {history_file: history, game_start_rel: startup}
# Aurelian Walls use the duchy slot; fix their sole fixed-location restriction.
wall_source = read(VANILLA / 'common/buildings/00_special_buildings.txt')
wall_span = next(x for x in blocks(wall_source) if x[0] == 'aurelian_walls_01')
wall_definition = wall_source[wall_span[1]:wall_span[5]].replace('title:b_roma', 'title:b_rome')
outputs[Path('common/buildings/zz_eu5_special_building_locations.txt')] = '# Aurelian Walls: adapt the fixed barony requirement to the EU5 Rome province.\n' + wall_definition + '\n'
title_rel = Path('common/landed_titles/00_landed_titles.txt')
title_text = read(BACKUP / 'mod' / title_rel)
lazio_span = next(x for x in blocks(title_text) if x[0] == 'd_lazio')
lazio_body = title_text[lazio_span[3]:lazio_span[4]]
rome_county = next(k for k in our_anc['b_rome'] if k.startswith('c_'))
lazio_body, n = re.subn(r'(\bcapital\s*=\s*)c_patrimonio\b', lambda m: m[1] + rome_county, lazio_body, count=1)
assert n == 1
outputs[title_rel] = edit(title_text, [(lazio_span[3], lazio_span[4], lazio_body)])
# The legacy university decision is hidden in the current game, but keep its
# event options, requirements and tooltips pointed at the same adapted sites.
event_rel = Path('events/decisions_events/major_decisions_events.txt')
decision_rel = Path('common/decisions/80_major_decisions.txt')
event_original = read(VANILLA / event_rel)
university_sites = {}
for source_barony, family in re.findall(r'title:(b_[\w-]+)\.title_province\s*=\s*\{\s*add_special_building_slot\s*=\s*(\w+)', event_original):
    group = (vanilla_b[source_barony], root(family))
    assert group in placements
    university_sites[source_barony] = reverse_our[placements[group]]
decision_original = read(VANILLA / decision_rel)
decision_block = next(x for x in blocks(decision_original) if x[0] == 'found_university_decision')
decision_body = decision_original[decision_block[3]:decision_block[4]]
for source_barony in set(re.findall(r'title:(b_[\w-]+)', decision_body)):
    if source_barony in university_sites:
        continue
    candidates = [(pid, family) for pid, family in groups if pid == vanilla_b.get(source_barony)]
    preferred = next((group for group in candidates if group[1] == 'generic_university'), None)
    if preferred is None and len(candidates) == 1:
        preferred = candidates[0]
    if preferred:
        university_sites[source_barony] = reverse_our[placements[preferred]]


def remap_university_body(text):
    return re.sub(r'title:(b_[\w-]+)\b', lambda m: 'title:' + university_sites.get(m[1], m[1]), text)


event_block = next(x for x in blocks(event_original) if x[0] == 'major_decisions.2001')
outputs[event_rel] = edit(event_original, [(event_block[3], event_block[4], remap_university_body(event_original[event_block[3]:event_block[4]]))])
outputs[decision_rel] = edit(decision_original, [(decision_block[3], decision_block[4], remap_university_body(decision_body))])
for rel, text in outputs.items():
    g.parse(text)
    target = OUT / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding='utf-8-sig')
rows = []
for group, target in sorted(placements.items()):
    source_pid, family = group
    x, y = points[source_pid]
    cx, cy = centers[target]
    rows.append({'building_family': family, 'source_province': source_pid, 'source_barony': reverse_vanilla[source_pid],
                 'target_province': target, 'target_barony': reverse_our[target], 'county': next(k for k in our_anc[reverse_our[target]] if k.startswith('c_')),
                 'sources': '+'.join(sorted(groups[group])), 'rule': rules[group], 'distance_pixels': round(float(np.hypot(cx - x, cy - y)), 2),
                 'holding': new_holdings.get(target, holding[target]), 'source_file': source_files.get(source_pid, 'game_start.txt')})
with (OUT / 'special_building_locations.csv').open('w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
report = {'backup': str(BACKUP), 'sites': len(rows), 'history_sites': len(source_nodes), 'startup_scopes': len(on_start_scopes),
          'building_families': len({r['building_family'] for r in rows}), 'preserved_silk_road_sites': len(locked),
          'removed_undefined_wonder_keys': sorted(undefined), 'slot_conflicts_resolved': relocations,
          'developed_sites': developed, 'placements': rows, 'legacy_university_locations': university_sites,
          'landmark_city_sources': {'sankore_university': 'https://whc.unesco.org/en/list/119', 'qutb_minar_01': 'https://whc.unesco.org/en/list/233'},
          'duchy_capital_correction': {'title': 'd_lazio', 'from': 'c_patrimonio', 'to': rome_county}}
(OUT / 'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps({k: v for k, v in report.items() if k not in ('placements', 'slot_conflicts_resolved', 'developed_sites')}, indent=2, ensure_ascii=False))
print('Conflicts resolved:', len(relocations), '| new settlements:', len(developed))
print('Largest mapping distances:', sorted([(r['building_family'], r['target_barony'], r['distance_pixels']) for r in rows], key=lambda x: -x[2])[:15])
if '--apply' in sys.argv:
    for rel in outputs:
        original = BACKUP / 'mod' / rel
        assert (MOD / rel).read_bytes() == original.read_bytes() if original.exists() else not (MOD / rel).exists(), ('Changed since backup', rel)
    for rel in outputs:
        (MOD / rel).parent.mkdir(parents=True, exist_ok=True)
        (MOD / rel).write_bytes((OUT / rel).read_bytes())
    print('Applied special-building province history and startup locations.')
