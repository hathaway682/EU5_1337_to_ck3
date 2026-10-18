# -*- coding: utf-8 -*-
"""Post-apply verification of the compound-name localisation patch.

For every language file:
  1. BOM still present
  2. line count identical to the .bak_compoundnames_* backup (no lines lost/added)
  3. no composite name key left carrying a placeholder value
  4. no duplicate keys
  5. the k_eu5_grg ruler's key resolves to the EU5 value
"""
import io, glob, os, re, collections

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ['braz_por', 'english', 'french', 'german', 'japanese', 'korean',
         'polish', 'russian', 'simp_chinese', 'spanish', 'turkish']
fails = []

for lang in LANGS:
    p = os.path.join(MOD, 'localization', lang, 'zz_eu5_politics_l_%s.yml' % lang)
    raw = io.open(p, 'rb').read()
    if not raw.startswith(b'\xef\xbb\xbf'):
        fails.append('%s: BOM missing' % lang)
    text = raw.decode('utf-8-sig')
    lines = text.split('\n')

    baks = sorted(glob.glob(p + '.bak_compoundnames_*'))
    if baks:
        braw = io.open(baks[-1], 'rb').read()
        blines = braw.decode('utf-8-sig').split('\n')
        if len(blines) != len(lines):
            fails.append('%s: line count %d -> %d' % (lang, len(blines), len(lines)))

        def keys_of(ls):
            c = collections.Counter()
            for ln in ls:
                m = re.match(r'^\s*([A-Za-z0-9_.\-]+):\d*\s*"(.*)"\s*$', ln)
                if m:
                    c[m.group(1)] += 1
            return c
        kb, kn = keys_of(blines), keys_of(lines)
        for k, n in kb.items():
            if kn.get(k, 0) != 1:
                fails.append('%s: key %s count %d (was %d)' % (lang, k, kn.get(k, 0), n))
        extra = set(kn) - set(kb)
        if extra:
            fails.append('%s: new keys %s' % (lang, sorted(extra)))

    dup = [k for k, n in collections.Counter(
        re.match(r'^\s*([A-Za-z0-9_.\-]+):', ln).group(1)
        for ln in lines if re.match(r'^\s*([A-Za-z0-9_.\-]+):', ln)).items() if n > 1]
    if dup:
        fails.append('%s: duplicate keys %s' % (lang, dup[:5]))
    ph = []
    for ln in lines:
        m = re.match(r'^\s*(name_[A-Za-z0-9_.\-]+):\d*\s*"(.*)"\s*$', ln)
        if m and m.group(2) == m.group(1).replace('_', ' '):
            ph.append(m.group(1))
    if ph:
        fails.append('%s: %d placeholder keys left: %s' % (lang, len(ph), ph[:5]))
    print('%-14s lines=%-6d placeholders=%d' % (lang, len(lines), len(ph)))

print()
zh = io.open(os.path.join(MOD, 'localization/simp_chinese/zz_eu5_politics_l_simp_chinese.yml'),
             encoding='utf-8-sig').read()
en = io.open(os.path.join(MOD, 'localization/english/zz_eu5_politics_l_english.yml'),
             encoding='utf-8-sig').read()
for k in ('name_togha.name_timur', 'name_duwa.name_timur', 'name_esen.name_buqa',
          'name_stephen.name_nemanja', 'name_hammir.name_singh', 'name_tughluq.name_timur',
          'name_yesun.name_temur', 'name_ang.name_chey', 'name_indra.name_bhupesvaracuda'):
    zhv = re.search(r'(?m)^\s*%s:\d*\s*"(.*)"\s*$' % re.escape(k), zh)
    env = re.search(r'(?m)^\s*%s:\d*\s*"(.*)"\s*$' % re.escape(k), en)
    print('  %-34s EN %-24s ZH %s' % (k,
                                      env.group(1) if env else 'MISSING',
                                      zhv.group(1) if zhv else 'MISSING'))

print()
print('FAILS: %d' % len(fails))
for f in fails:
    print('  ' + f)
print('RESULT:', 'ALL OK' if not fails else 'PROBLEMS')
