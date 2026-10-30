# -*- coding: utf-8 -*-
"""Align every EU5-driven *native* CK3 title's `capital` with that country's EU5 capital.

Scope: only titles bound in gen_debug/eu5_ck3_title_map.csv whose ck3_key is a native
d/k/e/h key (no `_eu5_` in it). For each, the EU5 capital is a location name; its CK3
barony is `b_<location>` and the owning county is that barony's parent `c_`.

- title has `capital = X` and X != that county  -> rewrite X
- title has no `capital`                        -> insert one right after the `X = {` line
- title already points at it                    -> untouched

Never touches `_eu5_` titles (their capital is written by the generator) and never
touches a title whose EU5 capital has no CK3 barony (reported, skipped).

Usage: python _fix_title_capital.py <mod_dir> [--dry-run]
"""
import io
import os
import re
import sys
import csv
import json
import glob
import collections

KEY_RE = re.compile(r'^([A-Za-z0-9_]+)\s*=\s*\{\s*(#.*)?$')
CAP_RE = re.compile(r'^capital\s*=\s*([A-Za-z0-9_]+)')


def load(p):
    raw = io.open(p, 'rb').read()
    return raw, raw.decode('utf-8-sig').replace('\r\n', '\n').split('\n')


def scan(paths):
    """key -> {file, line, indent, capital, cap_line}; later files win (load order)."""
    allk = {}
    b2c = {}
    for p in paths:
        _raw, lines = load(p)
        stack = []
        for i, line in enumerate(lines, 1):
            s = line.rstrip()
            if not s:
                continue
            body = s.lstrip('\t')
            d = len(s) - len(body)
            mk = KEY_RE.match(body)
            if mk:
                stack = stack[:d]
                stack.append(mk.group(1))
                k = mk.group(1)
                allk[k] = {'file': p, 'line': i, 'indent': d,
                           'capital': None, 'cap_line': None}
                if k.startswith('b_'):
                    par = [x for x in reversed(stack[:-1]) if x.startswith('c_')]
                    if par:
                        b2c.setdefault(k, par[0])
                continue
            if body.startswith('}'):
                stack = stack[:d]
                continue
            mc = CAP_RE.match(body)
            if mc and stack:
                cur = allk.get(stack[-1])
                if cur is not None and cur['capital'] is None:
                    cur['capital'] = mc.group(1)
                    cur['cap_line'] = i
    return allk, b2c


def main():
    mod = sys.argv[1] if len(sys.argv) > 1 else '.'
    dry = '--dry-run' in sys.argv
    export = os.path.join(os.path.dirname(os.path.abspath(mod)), 'Global_modern_map', 'eu5_export')
    if not os.path.isdir(export):
        export = os.path.join(mod, '..', 'Global_modern_map', 'eu5_export')

    paths = [p for p in sorted(glob.glob(os.path.join(mod, 'common', 'landed_titles', '*.txt')))
             if '.bak' not in p]
    allk, b2c = scan(paths)

    pol = json.load(io.open(os.path.join(export, 'eu5_politics.json'), encoding='utf-8'))
    countries = pol['countries']
    rows = [r for r in csv.DictReader(io.open(
        os.path.join(mod, 'gen_debug', 'eu5_ck3_title_map.csv'),
        encoding='utf-8-sig', newline='')) if r['kind'] == 'country']

    # which EU5 country actually holds each county (title_map county rows)
    county_owner = {}
    for r in csv.DictReader(io.open(
            os.path.join(mod, 'gen_debug', 'eu5_ck3_title_map.csv'),
            encoding='utf-8-sig', newline='')):
        k = (r['ck3_key'] or '').strip()
        if r['kind'] == 'county' and k.startswith('c_'):
            county_owner.setdefault(k, r['eu5_tag'])

    todo = []      # (tag, key, old, new, file, line_or_capline, is_insert)
    skipped = []
    for r in rows:
        key = (r['ck3_key'] or '').strip()
        if not key or '_eu5_' in key or key.split('_')[0] not in ('d', 'k', 'e', 'h'):
            continue
        tag = r['eu5_tag']
        cap = (countries.get(tag) or {}).get('capital')
        meta = allk.get(key)
        if meta is None:
            skipped.append((tag, key, 'not declared'))
            continue
        if not cap:
            skipped.append((tag, key, 'country has no EU5 capital'))
            continue
        want = b2c.get('b_' + cap)
        if not want:
            skipped.append((tag, key, f'no CK3 barony for location {cap}'))
            continue
        have = meta['capital']
        if have == want:
            continue
        owner = county_owner.get(want)
        if owner and owner != tag:
            skipped.append((tag, key, f'{want} belongs to {owner}, not {tag} '
                                     f'(EU5 capital {cap} lands outside its realm)'))
            continue
        todo.append((tag, key, have, want, meta['file'],
                     meta['cap_line'] if meta['cap_line'] else meta['line'],
                     meta['cap_line'] is None, meta['indent']))

    print(f'titles to fix: {len(todo)}   skipped: {len(skipped)}')
    for x in skipped:
        print('   skip', x)
    for tag, key, have, want, f, ln, ins, ind in sorted(todo):
        print(f'   {tag:4s} {key:22s} {str(have):18s} -> {want:20s} '
              f'{"INSERT" if ins else "rewrite"} {os.path.basename(f)}:{ln}')

    if dry or not todo:
        return

    by_file = collections.defaultdict(list)
    for t in todo:
        by_file[t[4]].append(t)

    for p, items in by_file.items():
        raw, lines = load(p)
        items.sort(key=lambda x: x[5], reverse=True)
        for tag, key, have, want, f, ln, ins, ind in items:
            if ins:
                lines.insert(ln, '\t' * (ind + 1) + f'capital = {want}')
            else:
                lines[ln - 1] = re.sub(r'capital\s*=\s*[A-Za-z0-9_]+',
                                       f'capital = {want}', lines[ln - 1], count=1)
        out = '\r\n'.join(lines).encode('utf-8')
        if raw.startswith(b'\xef\xbb\xbf'):
            out = b'\xef\xbb\xbf' + out
        io.open(p, 'wb').write(out)
        print(f'  wrote {os.path.basename(p)} ({len(items)} titles)')


if __name__ == '__main__':
    main()
