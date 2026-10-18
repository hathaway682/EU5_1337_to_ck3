# -*- coding: utf-8 -*-
"""Verify zz_eu5_house_coas.txt: syntax, key existence, alias chains, conflicts. ASCII out."""
import os, re, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
VAN = 'E:/SteamLibrary/steamapps/common/Crusader Kings III/game'
MINE = 'common/coat_of_arms/coat_of_arms/zz_eu5_house_coas.txt'

problems, info = [], []


def parse_coa(path):
    """Return {key: ('block'|('alias', target))} for top-level entries."""
    out = {}
    with open(path, 'rb') as f:
        lines = f.read().decode('utf-8-sig', 'ignore').splitlines()
    depth = 0
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith('#'):
            continue
        if depth == 0:
            m = re.match(r'^([A-Za-z0-9_.\-]+)\s*=\s*(\{|([A-Za-z0-9_.\-]+))\s*(#.*)?$', s)
            if m:
                if m.group(2) == '{':
                    out[m.group(1)] = ('block', None)
                    depth = 1
                else:
                    out[m.group(1)] = ('alias', m.group(3))
            continue
        depth += s.count('{') - s.count('}')
        if depth < 0:
            depth = 0
    return out


van = {}
coa_dir = os.path.join(VAN, 'common/coat_of_arms/coat_of_arms')
for f in os.listdir(coa_dir):
    if f.endswith('.txt'):
        van.update(parse_coa(os.path.join(coa_dir, f)))

mod = {}
moddir = 'common/coat_of_arms/coat_of_arms'
for f in os.listdir(moddir):
    if f.endswith('.txt') and os.path.join(moddir, f).replace('\\', '/') != MINE:
        mod.update(parse_coa(os.path.join(moddir, f)))

# ---- our file ----
with open(MINE, 'rb') as f:
    raw = f.read()
if not raw.startswith(b'\xef\xbb\xbf'):
    problems.append('missing BOM')
lines = raw.decode('utf-8-sig').splitlines()

entries, dups = [], []
seen = set()
for i, ln in enumerate(lines, 1):
    s = ln.strip()
    if not s or s.startswith('#'):
        continue
    m = re.match(r'^([A-Za-z0-9_.\-]+)\s*=\s*([A-Za-z0-9_.\-]+)$', s)
    if not m:
        problems.append('line %d bad syntax: %r' % (i, s))
        continue
    k, t = m.group(1), m.group(2)
    if k in seen:
        dups.append(k)
    seen.add(k)
    entries.append((i, k, t))

if dups:
    problems.append('duplicate keys: %s' % dups)
info.append('entries: %d' % len(entries))

# ---- resolve alias chains ----
def resolve(t):
    chain = [t]
    for _ in range(10):
        if t in mod:
            kind, tgt = mod[t]
        elif t in van:
            kind, tgt = van[t]
        else:
            return None, chain
        if kind == 'block':
            return t, chain
        t = tgt
        chain.append(t)
    return 'LOOP', chain


for i, k, t in entries:
    if k == t:
        problems.append('line %d self reference %s' % (i, k))
        continue
    if k not in mod and k not in van:
        pass  # key itself is new, fine
    final, chain = resolve(t)
    if final is None:
        problems.append('line %d %s -> %s : target not defined' % (i, k, t))
    elif final == 'LOOP':
        problems.append('line %d %s -> alias loop %s' % (i, k, chain))
    else:
        src = 'mod' if final in mod else 'vanilla'
        if len(chain) > 2:
            info.append('  chain %s: %s' % (k, ' -> '.join(chain)))

# ---- do our house keys already exist in COA? ----
clash = [k for _, k, _ in entries if k in van or k in mod]
if clash:
    problems.append('these house keys already had a COA definition (we override): %s' % clash)

# ---- house keys must exist in the house file ----
with open('common/dynasty_houses/zz_eu5_merged_houses.txt', 'rb') as f:
    ht = f.read().decode('utf-8-sig')
defined = set(re.findall(r'^(house_[A-Za-z0-9_]+)\s*=\s*\{', ht, re.M))
bad = [k for _, k, _ in entries if k not in defined]
if bad:
    problems.append('house keys not defined in house file: %s' % bad)

print('=== INFO ===')
for i in info:
    print(i)
print()
print('=== PROBLEMS: %d ===' % len(problems))
for p in problems:
    print(' ! ' + p)
print()
print('RESULT: ' + ('ALL OK' if not problems else 'NEEDS ATTENTION'))
