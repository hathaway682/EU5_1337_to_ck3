"""Use vanilla's authored duchy granularity on the current EU5 region geometry.

The workshop flattened all regions to counties. This postprocess uses the CK3
region declarations to identify duchy-only regions and restores their tier.
Mixed county/province regions and EU5 continent boundaries remain precise.
"""
from pathlib import Path
from collections import defaultdict
import importlib.util
import json
import re
import sys

MOD = Path(__file__).resolve().parents[1]
BACKUP = Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261031_184125_region_granularity')
OUT = MOD / 'gen_debug/region_granularity_20261031'
OUT.mkdir(exist_ok=True)
spec = importlib.util.spec_from_file_location('g', BACKUP / 'inputs/rebuild_geographical_regions_20261031.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
MEMBERSHIP = {'duchies', 'counties', 'kingdoms', 'hegemonies', 'empires', 'provinces', 'regions'}


def load_regions(folder):
    result, files = {}, {}
    for p in sorted(folder.glob('*.txt')):
        for key, node in g.parse(g.read(p))[0]:
            assert key not in result, ('Duplicate region', key)
            result[key], files[key] = node, p.name
    return result, files


current, filenames = load_regions(BACKUP / 'original_regions')
vanilla, _ = load_regions(BACKUP / 'inputs/vanilla_regions')
title_land, baronies, _ = g.titles(BACKUP / 'inputs/landed_titles')
duchies = {key: value for key, value in title_land.items() if key.startswith('d_') and value}
land = set(baronies.values())


def expand_regions(nodes):
    cache, resolving = {}, set()
    def expand(key, depth=0):
        if key in cache:
            return cache[key]
        assert depth < 20 and key not in resolving, ('Cyclic/deep region', key)
        resolving.add(key)
        result = set()
        for prop, value in nodes[key][0]:
            if prop not in MEMBERSHIP:
                continue
            if prop == 'regions':
                for child in value[1]:
                    assert child in nodes
                    result.update(expand(child, depth + 1))
            elif prop == 'provinces':
                result.update(map(int, value[1]))
            else:
                for title in value[1]:
                    assert title in title_land, ('Unresolved landed title', key, title)
                    result.update(title_land[title])
        resolving.remove(key)
        cache[key] = result
        return result
    for key in nodes:
        expand(key)
    return cache


baseline = expand_regions(current)
props = {key: {prop: value[1] for prop, value in body[0] if prop in MEMBERSHIP and value[1]} for key, body in vanilla.items()}
coarse = {key for key, value in props.items() if key in current and 'duchies' in value and not ({'counties', 'provinces'} & value.keys())}
children = {key: value['regions'] for key, value in props.items() if key in current and 'regions' in value}
assert all(child in current for values in children.values() for child in values)
fallbacks, selections, own_land = [], {}, {}
for key in current:
    child_land = set().union(*(baseline[child] for child in children.get(key, [])))
    own = baseline[key] - child_land
    own_land[key] = own
    if key not in coarse:
        continue
    chosen, scores = [], []
    for title, members in duchies.items():
        eligible = members - child_land
        overlap = len(eligible & own)
        if not overlap:
            continue
        scores.append((overlap, overlap / len(eligible), title))
        if overlap * 2 >= len(eligible):
            chosen.append(title)
    if own and not chosen:
        # A small vanilla duchy can fit into part of one larger EU5 duchy.
        _, _, title = max(scores, key=lambda row: (row[0], row[1], row[2]))
        chosen = [title]
        fallbacks.append({'region': key, 'duchy': title, 'covered_baronies': len(duchies[title] & own), 'duchy_baronies': len(duchies[title])})
    selections[key] = set(chosen)

# A vanilla duchy can be much smaller than any current EU5 duchy (e.g. Gotland
# versus all of Gotaland). Keep those explicit geographic exceptions precise.
vanilla_duchy_count = len(coarse)
exceptions = {row['region'] for row in fallbacks}
coarse -= exceptions
for key in exceptions:
    selections.pop(key)

# Resolve exact half/half votes between sibling duchy regions that were disjoint.
tie_resolutions = []
for parent, child_keys in children.items():
    for i, left in enumerate(child_keys):
        for right in child_keys[i + 1:]:
            if left not in coarse or right not in coarse or baseline[left] & baseline[right]:
                continue
            for title in sorted(selections[left] & selections[right]):
                def priority(key):
                    return len(duchies[title] & baseline[key]), title in props.get(key, {}).get('duchies', []), key
                winner = max((left, right), key=priority)
                loser = right if winner == left else left
                selections[loser].remove(title)
                tie_resolutions.append({'parent': parent, 'duchy': title, 'winner': winner, 'loser': loser})


def compress(members):
    rest, fields = set(members), []
    for prefix, prop in (('d_', 'duchies'), ('c_', 'counties')):
        chosen = []
        for title in sorted(title_land):
            chunk = title_land[title]
            if title.startswith(prefix) and chunk and chunk <= rest:
                chosen.append(title)
                rest -= chunk
        if chosen:
            fields.append((prop, ([], chosen)))
    if rest:
        fields.append(('provinces', ([], list(map(str, sorted(rest))))))
    return fields


updated = {}
for key, body in current.items():
    if key not in coarse and key not in children:
        updated[key] = body
        continue
    fields = [(prop, value) for prop, value in body[0] if prop not in MEMBERSHIP]
    if key in coarse:
        if selections[key]:
            fields.append(('duchies', ([], sorted(selections[key]))))
    else:
        fields.extend(compress(own_land[key]))
    if key in children:
        fields.append(('regions', ([], list(children[key]))))
    updated[key] = fields, []
new_members = expand_regions(updated)
fine_border_adjustments = defaultdict(set)


def region_leaves(key):
    if key not in children:
        return [key]
    return [leaf for child in children[key] for leaf in region_leaves(child)]


# Keep authored world partitions disjoint after duchy expansion. A fine-grained
# neighboring region yields only the small border fragments inside whole duchies.
for parent, child_keys in children.items():
    if not parent.startswith('world_'):
        continue
    for i, left in enumerate(child_keys):
        for right in child_keys[i + 1:]:
            if baseline[left] & baseline[right]:
                continue
            overlap = new_members[left] & new_members[right]
            if not overlap:
                continue
            left_whole = set().union(*(duchies[d] for leaf in region_leaves(left) if leaf in coarse for d in selections[leaf]))
            right_whole = set().union(*(duchies[d] for leaf in region_leaves(right) if leaf in coarse for d in selections[leaf]))
            assert not (overlap & left_whole & right_whole), ('Conflicting whole-duchy world assignments', left, right)
            for owner, trimmed in ((left_whole, right), (right_whole, left)):
                removed = overlap & owner
                if not removed:
                    continue
                for leaf in region_leaves(trimmed):
                    affected = removed & new_members[leaf]
                    if affected:
                        assert leaf not in coarse
                        fine_border_adjustments[leaf].update(affected)
                        fields = [(k, v) for k, v in updated[leaf][0] if k not in MEMBERSHIP]
                        fields.extend(compress(new_members[leaf] - affected))
                        updated[leaf] = fields, []
            new_members = expand_regions(updated)
            assert not (new_members[left] & new_members[right]), ('World sibling overlap', parent, left, right)
assert current.keys() == updated.keys()
for key in coarse:
    actual = {p for p, _ in updated[key][0] if p in MEMBERSHIP}
    assert actual <= {'duchies', 'regions'}
for key in current:
    if key not in coarse and key not in children and key not in fine_border_adjustments:
        assert new_members[key] == baseline[key]
    if key.startswith('eu5_continent_') or key.startswith('eu5_subcontinent_'):
        assert new_members[key] == baseline[key]
for parent, child_keys in children.items():
    assert all(new_members[child] <= new_members[parent] for child in child_keys)
assert not [key for key in current if baseline[key] and not new_members[key]]


def render_value(value, indent):
    if isinstance(value, str):
        return value
    return '{ ' + ' '.join(k + ' = ' + render_value(v, indent) for k, v in value[0]) + ' ' + ' '.join(value[1]) + ' }'


def render_region(key, node):
    lines = [key + ' = {']
    for prop, value in node[0]:
        if prop in MEMBERSHIP:
            lines.append('\t' + prop + ' = {')
            for i in range(0, len(value[1]), 8):
                lines.append('\t\t' + ' '.join(value[1][i:i + 8]))
            lines.append('\t}')
        else:
            lines.append('\t' + prop + ' = ' + render_value(value, 1))
    lines.append('}\n')
    return '\n'.join(lines)


by_file = defaultdict(list)
for key, body in updated.items():
    by_file[filenames[key]].append(render_region(key, body))
changed_files = []
for filename, bodies in by_file.items():
    changed = any(updated[k] != current[k] for k in current if filenames[k] == filename)
    if changed:
        text = '# Region granularity follows CK3 vanilla declarations, adapted to current EU5 duchies.\n# No kingdom, empire or hegemony references. Original fine-grained regions stay precise.\n\n' + '\n'.join(bodies)
        (OUT / filename).write_text(text, encoding='utf-8-sig')
        changed_files.append(filename)
rows = []
for key in sorted(coarse | children.keys()):
    rows.append({'region': key, 'vanilla_duchy_granularity': key in coarse, 'before_provinces': len(baseline[key]),
                 'after_provinces': len(new_members[key]), 'added': len(new_members[key] - baseline[key]),
                 'removed': len(baseline[key] - new_members[key]), 'duchy_references': len(selections.get(key, [])),
                 'subregions': children.get(key, [])})
summary = {'backup': str(BACKUP), 'duchy_granularity_regions': len(coarse), 'restored_parent_region_links': len(children),
           'vanilla_duchy_regions': vanilla_duchy_count, 'retained_boundary_exceptions': sorted(exceptions),
           'changed_files': changed_files, 'fallback_duchies': fallbacks, 'sibling_tie_resolutions': tie_resolutions,
           'world_border_adjustments': {k: sorted(v) for k, v in fine_border_adjustments.items()},
           'new_empty_regions': [], 'eu5_continents_unchanged': True, 'regions': rows}
(OUT / 'report.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
(OUT / 'region_provinces.json').write_text(json.dumps({k: sorted(v) for k, v in new_members.items()}), encoding='utf-8')
print(json.dumps({k: v for k, v in summary.items() if k != 'regions'}, ensure_ascii=False, indent=2))
if '--apply' in sys.argv:
    dest = MOD / 'map_data/geographical_regions'
    for filename in changed_files:
        assert (dest / filename).read_bytes() == (BACKUP / 'original_regions' / filename).read_bytes(), ('Changed since backup', filename)
    for filename in changed_files:
        (dest / filename).write_bytes((OUT / filename).read_bytes())
    print('Applied', len(changed_files), 'region files.')
