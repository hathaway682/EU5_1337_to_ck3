# -*- coding: utf-8 -*-
"""Read-only check: do all house `name = "..."` keys resolve in mod loc? ASCII output."""
import re, os, glob, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# collect all loc keys from mod + vanilla-ish dirs present in mod
loc_keys = set()
files = glob.glob('localization/**/*.yml', recursive=True)
for p in files:
    try:
        with open(p, 'rb') as f:
            t = f.read().decode('utf-8-sig', 'ignore')
    except Exception:
        continue
    for ln in t.splitlines():
        m = re.match(r'^\s*([A-Za-z0-9_.\-]+):\d*\s+"', ln)
        if m:
            loc_keys.add(m.group(1))

print('loc files scanned: %d, keys: %d' % (len(files), len(loc_keys)))

# parse house file
with open('common/dynasty_houses/zz_eu5_merged_houses.txt', 'rb') as f:
    txt = f.read().decode('utf-8-sig')

houses = re.findall(r'^(house_[A-Za-z0-9_]+)\s*=\s*\{', txt, re.M)
names = re.findall(r'^\s*name\s*=\s*"([^"]*)"', txt, re.M)
print('houses: %d, name lines: %d' % (len(houses), len(names)))

missing = [n for n in names if n not in loc_keys]
print('house name keys NOT in any mod loc file: %d' % len(missing))
for n in missing[:20]:
    print('  MISSING ' + n)
if len(missing) > 20:
    print('  ...')

ok = len(names) - len(missing)
print('resolved: %d / %d' % (ok, len(names)))
