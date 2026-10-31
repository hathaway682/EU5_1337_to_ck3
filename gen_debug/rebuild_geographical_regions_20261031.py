"""Rebuild CK3 regions from CU barony geometry and EU5 definitions.

Default is a dry run into gen_debug/geographical_regions_rebuild_20261031.
--apply writes map_data/geographical_regions after all assertions pass.
Inputs are snapshotted on F: before this script was created.
"""
from pathlib import Path
from collections import defaultdict, Counter
import csv
import json
import re
import sys
import numpy as np
from PIL import Image

MOD = Path(__file__).resolve().parents[1]
BACKUP = Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261031_134214_geographical_regions')
OUT = MOD / 'gen_debug/geographical_regions_rebuild_20261031'
TOKEN = re.compile(r'#[^\n]*|"(?:\\.|[^"\\])*"|[^\s{}=]+|[{}=]')


def read(p):
    return p.read_text(encoding='utf-8-sig')


def parse(text):
    tokens = [m.group() for m in TOKEN.finditer(text) if not m.group().startswith('#')]
    def block(i, nested=False):
        pairs, bare = [], []
        while i < len(tokens):
            key = tokens[i]
            if key == '}':
                assert nested
                return (pairs, bare), i + 1
            if i + 1 < len(tokens) and tokens[i + 1] == '=':
                if tokens[i + 2] == '{':
                    val, i = block(i + 3, True)
                else:
                    val, i = tokens[i + 2], i + 3
                pairs.append((key, val))
            elif key == '{':
                val, i = block(i + 1, True)
                pairs.append(('_anonymous', val))
            else:
                bare.append(key)
                i += 1
        assert not nested, 'Unclosed block'
        return (pairs, bare), i
    return block(0)[0]


def titles(folder):
    descendants = defaultdict(set)
    bpid, ancestry = {}, {}
    def visit(node, parents=()):
        for key, val in node[0]:
            if not isinstance(val, tuple):
                continue
            chain = parents + (key,) if re.fullmatch(r'[hkedcb]_[\w-]+', key) else parents
            if key.startswith('b_'):
                props = dict(val[0])
                if 'province' in props:
                    pid = int(props['province'])
                    assert key not in bpid, ('Duplicate barony', key)
                    bpid[key] = pid
                    ancestry[key] = chain
                    for title in chain:
                        descendants[title].add(pid)
            visit(val, chain)
    for p in sorted(folder.glob('*.txt')):
        visit(parse(read(p)))
    assert len(set(bpid.values())) == len(bpid)
    return descendants, bpid, ancestry


def definitions(p):
    lut = np.zeros(1 << 24, dtype=np.uint32)
    with p.open(encoding='utf-8-sig') as f:
        for row in csv.reader(f, delimiter=';'):
            if len(row) >= 4 and row[0].isdigit():
                pid, r, g, b = map(int, row[:4])
                lut[(r << 16) | (g << 8) | b] = pid
    return lut


def pixels(im, lut, y, rows=128):
    a = np.asarray(im.crop((0, y, im.width, min(y + rows, im.height))).convert('RGB'), dtype=np.uint32)
    return lut[(a[:, :, 0] << 16) | (a[:, :, 1] << 8) | a[:, :, 2]]


def main():
    OUT.mkdir(exist_ok=True)
    inputs = BACKUP / 'inputs'
    our_titles, our_b, ancestors = titles(inputs / 'our_titles')
    cu_titles, cu_b, _ = titles(inputs / 'cu_titles')
    cu_land = set(cu_b.values())
    land = set(our_b.values())
    Image.MAX_IMAGE_PIXELS = None
    our_im = Image.open(inputs / 'our_map/provinces.png')
    cu_im = Image.open(inputs / 'cu_map/provinces.png')
    assert our_im.size == cu_im.size
    our_lut = definitions(inputs / 'our_map/definition.csv')
    cu_lut = definitions(inputs / 'cu_map/definition.csv')
    counts = Counter()
    ncu = int(cu_lut.max()) + 1
    allowed = np.zeros(int(our_lut.max()) + 1, dtype=bool)
    allowed[1:] = True
    for y in range(0, our_im.height, 128):
        a = pixels(our_im, our_lut, y)
        b = pixels(cu_im, cu_lut, y)
        mask = allowed[a]
        codes, nums = np.unique(a[mask].astype(np.uint64) * ncu + b[mask], return_counts=True)
        counts.update({int(k): int(v) for k, v in zip(codes, nums)})
        if y % 2048 == 0:
            print('Raster rows', y, '/', our_im.height, flush=True)
    overlap = defaultdict(Counter)
    for code, count in counts.items():
        overlap[code // ncu][code % ncu] = count
    match = {p: votes.most_common(1)[0][0] for p, votes in overlap.items()}
    assert land <= set(match)
    with (OUT / 'barony_spatial_mapping.csv').open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['barony', 'our_province', 'cu_province', 'overlap_fraction', 'cu_has_barony'])
        for key, p in sorted(our_b.items()):
            w.writerow([key, p, match[p], overlap[p][match[p]] / sum(overlap[p].values()), match[p] in cu_land])
    # Inverse province mapping: every source title is expanded to its barony land.
    cu_to_our = defaultdict(set)
    for p, q in match.items():
        cu_to_our[q].add(p)
    sources, regions, metadata, missing = {}, {}, {}, []
    for p in sorted((inputs / 'cu_map/geographical_regions').glob('*.txt')):
        for key, body in parse(read(p))[0]:
            assert isinstance(body, tuple)
            assert key not in sources, ('Duplicate region', key)
            sources[key] = (p.name, body)
    resolving = set()
    def resolve(key):
        if key in regions:
            return regions[key]
        assert key not in resolving, ('Cyclic region', key)
        resolving.add(key)
        result = set()
        extra = []
        for prop, value in sources[key][1][0]:
            if prop in ('kingdoms', 'duchies', 'counties', 'baronies'):
                for title in value[1]:
                    if title not in cu_titles:
                        missing.append((key, title))
                    for pid in cu_titles.get(title, set()):
                        result.update(cu_to_our[pid])
            elif prop == 'provinces':
                for pid in value[1]:
                    result.update(cu_to_our[int(pid)])
            elif prop == 'regions':
                for child in value[1]:
                    assert child in sources, ('Missing region', key, child)
                    result.update(resolve(child))
            else:
                extra.append((prop, value))
        regions[key] = result
        metadata[key] = extra
        resolving.remove(key)
        return result
    for key in sources:
        resolve(key)

    # EU5 map hierarchy is continent > subcontinent > region > area > province.
    eu_defs = parse(read(inputs / 'eu5_definitions.txt'))
    loc_units = {}
    continents, subs, sub_parent = defaultdict(set), defaultdict(set), {}
    def eu_visit(node, chain=()):
        for key, val in node[0]:
            if isinstance(val, tuple):
                path = chain + (key,)
                if len(path) == 2:
                    sub_parent[key] = path[0]
                if len(path) == 5:
                    for loc in val[1]:
                        loc = loc.casefold()
                        assert loc not in loc_units, ('Duplicate EU5 location', loc)
                        loc_units[loc] = path[:2]
                else:
                    eu_visit(val, path)
    eu_visit(eu_defs)
    unmatched = []
    for barony, pid in our_b.items():
        name = barony[2:]
        if name not in loc_units:
            unmatched.append(barony)
            continue
        cont, sub = loc_units[name]
        continents[cont].add(pid)
        subs[sub].add(pid)
    assert not unmatched, ('Unmapped EU5 baronies', unmatched)
    assert set.union(*continents.values()) == land
    assert sum(map(len, continents.values())) == len(land)
    assert sum(map(len, subs.values())) == len(land)
    # Namespaced keys keep CK3's compatibility regions at their source extent.
    eu_keys = {}
    for prefix, units in [('continent', continents), ('subcontinent', subs)]:
        for unit, members in units.items():
            key = 'eu5_' + prefix + '_' + unit
            assert key not in regions
            regions[key] = members
            metadata[key] = []
            eu_keys[key] = unit

    by_pid = {p: b for b, p in our_b.items()}
    compression = {}
    def compress(members):
        rest = set(members)
        result = {}
        for tier, prop in [('d_', 'duchies'), ('c_', 'counties')]:
            chosen = []
            for title in sorted(our_titles):
                chunk = our_titles[title]
                if title.startswith(tier) and chunk and chunk <= rest:
                    chosen.append(title)
                    rest -= chunk
            if chosen:
                result[prop] = chosen
        if rest:
            result['provinces'] = sorted(rest)
        expanded = set(rest)
        for prop in ('duchies', 'counties'):
            for title in result.get(prop, []):
                assert not (expanded & our_titles[title])
                expanded.update(our_titles[title])
        assert expanded == members, 'Compression changed region boundaries'
        return result

    def render_value(value):
        if isinstance(value, str):
            return value
        return '{ ' + ' '.join(k + ' = ' + render_value(v) for k, v in value[0]) + ' ' + ' '.join(value[1]) + ' }'

    files = defaultdict(list)
    for key, members in regions.items():
        filename = sources[key][0] if key in sources else '20_eu5_continents_subcontinents.txt'
        refs = compress(members)
        compression[key] = refs
        lines = [key + ' = {']
        for prop, value in metadata[key]:
            lines.append('\t' + prop + ' = ' + render_value(value))
        if not members:
            lines.append('\t# No playable baronies in the source extent.')
        for prop, values in refs.items():
            lines.append('\t' + prop + ' = {')
            for i in range(0, len(values), 8):
                lines.append('\t\t' + ' '.join(map(str, values[i:i + 8])))
            lines.append('\t}')
        lines.append('}\n')
        files[filename].append('\n'.join(lines))
    header = '# Rebuilt from CU barony geometry / EU5 definitions, 2026-10-31.\n# Maximum title tier: duchy. Partial counties use province IDs.\n\n'
    for filename, blocks in files.items():
        (OUT / filename).write_text(header + '\n'.join(blocks), encoding='utf-8-sig')
    old_keys = set()
    for p in (BACKUP / 'original_regions').glob('*.txt'):
        old_keys.update(k for k, _ in parse(read(p))[0])
    assert old_keys <= regions.keys(), ('Lost original keys', old_keys - regions.keys())
    report = {
        'baronies': len(land), 'cu_source_regions': len(sources), 'total_regions': len(regions),
        'eu5_continents': {k: len(v) for k, v in sorted(continents.items())},
        'eu5_subcontinents': {k: len(v) for k, v in sorted(subs.items())},
        'subcontinent_parent': sub_parent,
        'empty_regions': [k for k, v in regions.items() if not v],
        'unresolved_cu_titles': missing,
        'spatial_below_90_percent': sum(overlap[p][match[p]] / sum(overlap[p].values()) < .9 for p in land),
        'regions': {k: {'baronies': len(v & land), 'provinces': len(v), 'references': {t: len(a) for t, a in compression[k].items()}} for k, v in regions.items()},
    }
    (OUT / 'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    (OUT / 'region_provinces.json').write_text(json.dumps({k: sorted(v) for k, v in regions.items()}), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'regions'}, indent=2, ensure_ascii=False), flush=True)
    if '--apply' in sys.argv:
        dest = MOD / 'map_data/geographical_regions'
        for filename in files:
            (dest / filename).write_bytes((OUT / filename).read_bytes())
        print('Applied', len(files), 'region files.', flush=True)


if __name__ == '__main__':
    main()
