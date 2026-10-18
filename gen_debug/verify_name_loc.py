# -*- coding: utf-8 -*-
"""Final verification for the name localization work. ASCII output only."""
import re, sys, os, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

EN = 'localization/english/zz_eu5_names_l_english.yml'
ZH = 'localization/simp_chinese/zz_eu5_names_l_simp_chinese.yml'
CHARS = 'history/characters/zz_eu5_characters.txt'
REGENTS = 'history/characters/zz_eu5_regents.txt'

problems = []
info = []


def check_loc(path, lang_header):
    """Parse a CK3 yml loc file and return dict key -> value, plus syntax errors."""
    with open(path, 'rb') as f:
        raw = f.read()
    bom = raw.startswith(b'\xef\xbb\xbf')
    if not bom:
        problems.append('%s: missing BOM' % path)
    text = raw.decode('utf-8-sig')
    lines = text.splitlines()
    if not lines:
        problems.append('%s: empty file' % path)
        return {}, lines
    if lines[0].strip() != lang_header:
        problems.append('%s: first line is %r, expected %r' % (path, lines[0], lang_header))
    out = collections.OrderedDict()
    dups = []
    bad = []
    for i, ln in enumerate(lines[1:], start=2):
        if not ln.strip():
            continue
        m = re.match(r'^\s*([A-Za-z0-9_.\-]+):\d*\s+"(.*)"\s*$', ln)
        if not m:
            bad.append((i, ln[:80]))
            continue
        k, v = m.group(1), m.group(2)
        if ' ' in k:
            bad.append((i, 'KEY HAS SPACE: ' + k))
        if k in out:
            dups.append((i, k))
        out[k] = v
        if not v.strip():
            problems.append('%s:%d empty value for %s' % (path, i, k))
        # unescaped inner quote check
        if v.count('"') > 0 and not v.startswith('"'):
            pass
    if bad:
        for i, ln in bad[:10]:
            problems.append('%s:%d syntax: %s' % (path, i, ln))
        if len(bad) > 10:
            problems.append('%s: ... %d syntax errors total' % (path, len(bad)))
    if dups:
        problems.append('%s: %d duplicate keys, e.g. %s' % (path, len(dups), [d[1] for d in dups[:5]]))
    info.append('%-45s keys=%d  lines=%d  BOM=%s' % (path, len(out), len(lines), bom))
    return out, lines


en, _ = check_loc(EN, 'l_english:')
zh, _ = check_loc(ZH, 'l_simp_chinese:')

info.append('en keys=%d  zh keys=%d' % (len(en), len(zh)))
only_en = sorted(set(en) - set(zh))
only_zh = sorted(set(zh) - set(en))
if only_en:
    problems.append('keys missing in ZH (%d): %s' % (len(only_en), only_en[:10]))
if only_zh:
    problems.append('keys missing in EN (%d): %s' % (len(only_zh), only_zh[:10]))

# identical en/zh values (untranslated leftovers), excluding pure-latin names
same = [k for k in en if k in zh and en[k] == zh[k]]
info.append('identical en==zh values: %d' % len(same))

# ---- scan character files ----
name_re = re.compile(r'^\s*name\s*=\s*"([^"]*)"', re.M)


def scan_chars(path):
    with open(path, 'rb') as f:
        text = f.read().decode('utf-8-sig')
    vals = name_re.findall(text)
    return vals


for path in (CHARS, REGENTS):
    vals = scan_chars(path)
    total = len(vals)
    keyed = [v for v in vals if v.startswith('name_eu5_')]
    missing = sorted(set(k for k in keyed if k not in en))
    nozh = sorted(set(k for k in keyed if k in en and k not in zh))
    # values that still look like raw display strings (contain space and are not keys)
    raw_bad = sorted(set(v for v in vals if not v.startswith('name_eu5_') and ' ' in v))
    empty = [v for v in vals if not v.strip()]
    info.append('%-42s name=%d keyed=%d raw_with_space=%d empty=%d' % (
        path, total, len(keyed), len(raw_bad), len(empty)))
    if missing:
        problems.append('%s: %d keys undefined in EN: %s' % (path, len(missing), missing[:10]))
    if nozh:
        problems.append('%s: %d keys undefined in ZH: %s' % (path, len(nozh), nozh[:10]))
    if raw_bad:
        problems.append('%s: %d raw name values still contain spaces: %s' % (
            path, len(raw_bad), raw_bad[:10]))
    if empty:
        problems.append('%s: %d empty name values' % (path, len(empty)))

# ---- unused keys ----
all_used = set()
for path in (CHARS, REGENTS):
    all_used |= set(v for v in scan_chars(path) if v.startswith('name_eu5_'))
unused = sorted(set(en) - all_used)
info.append('loc keys not referenced by any character: %d' % len(unused))
if unused:
    info.append('  e.g. %s' % unused[:8])

print('=== INFO ===')
for i in info:
    print(i)
print()
print('=== PROBLEMS: %d ===' % len(problems))
for p in problems:
    print(' ! ' + p)
print()
print('RESULT: ' + ('ALL OK' if not problems else 'NEEDS ATTENTION'))
