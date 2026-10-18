# -*- coding: utf-8 -*-
"""Resolve the 154 compound ruler-name placeholders, using EU5's own name
localisation as the authority (the user asked for "按 EU5 本地化修名字").

Where EU5 localises the composite key itself (e.g. name_ang.name_chey) its value
is used verbatim.  Otherwise the name is composed from the parts, each part
taken from EU5 first.  EU5 composes Chinese names by plain concatenation with
no separator - see its own `name_indra.name_bhupesvaracuda: "因陀罗普佩斯瓦拉朱达"`
= 因陀罗 + 普佩斯瓦拉朱达 - while English joins with a space.

Word sources, in priority order:
  EN  : EU5 character_names[_dynamic]_l_english.yml  `name_*`
        mod zz_eu5_politics_l_english.yml `name_*`
        mod gen_cultures_l_english.yml      `cul_*`
        HAND_EN (below)
  ZH  : EU5 character_names[_dynamic]_l_simp_chinese.yml `name_*` (or composite)
        mod zz_eu5_politics_l_simp_chinese.yml `name_*`
        vanilla .../localization/simp_chinese/names/character_names_l_simp_chinese.yml
        HAND_ZH (below)

The other 9 languages ship a verbatim English copy, so they get the English value.

Dry run by default; --apply rewrites the placeholder lines in place.
"""
import re, os, sys, json, collections, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
APPLY = '--apply' in sys.argv
VAN = 'E:/SteamLibrary/steamapps/common/Crusader Kings III/game'
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"

# ---------------------------------------------------------------- hand tables
# Only used as a last resort: parts EU5 itself does not ship a word for.
HAND_EN = {
    'name_al_din': 'al-Din', 'name_annan': 'Annan', 'name_arjun': 'Arjun',
    'name_arpa': 'Arpa', 'name_bibi': 'Bibi', 'name_boke': 'Boke',
    'name_borwin': 'Borwin', 'name_buqa': 'Buqa', 'name_cherik': 'Cherik',
    'name_damascus': 'Damascus', 'name_dev': 'Dev', 'name_emas': 'Emas',
    'name_emugen': 'Emugen', 'name_ezz': 'Ezz', 'name_gharsi': 'Gharsi',
    'name_ghiyath': 'Ghiyath', 'name_haidar': 'Haidar', 'name_hir': 'Hir',
    'name_iyakan': 'Iyakan', 'name_jansi': 'Jansi', 'name_jas': 'Jas',
    'name_jay_singh': 'Jai Singh', 'name_keun': 'Keun', 'name_madana': 'Madana',
    'name_muizz': 'Muizz', 'name_nadir': 'Nadir', 'name_pal': 'Pal',
    'name_qaim': 'Qaim', 'name_raghuraj': 'Raghuraj', 'name_rukn': 'Rukn',
    'name_sau': 'Sau', 'name_shaikh': 'Shaikh', 'name_shamshir': 'Shamshir',
    'name_sharaf': 'Sharaf', 'name_shoja': 'Shoja', 'name_sinhat': 'Sinhat',
    'name_someshwara': 'Someshwara', 'name_tash': 'Tash', 'name_tekuder': 'Tekuder',
    'name_tode': 'Tode', 'name_togha': 'Togha', 'name_tole': 'Tole',
    'name_tugh': 'Tugh', 'name_varman': 'Varman', 'name_virsingh': 'Virsingh',
    'name_yesu': 'Yesu',
}

HAND_ZH = {
    'name_al_din': '丁', 'name_annan': '安南', 'name_arjun': '阿周',
    'name_arpa': '阿尔帕', 'name_bibi': '比比', 'name_boke': '伯克',
    'name_borwin': '博尔温', 'name_buqa': '不花', 'name_cherik': '彻里克',
    'name_damascus': '大马士革', 'name_dev': '提夫', 'name_emas': '埃马斯',
    'name_emugen': '埃穆根', 'name_ezz': '埃兹', 'name_gharsi': '加尔西',
    'name_ghiyath': '吉亚特', 'name_haidar': '海达尔', 'name_hir': '希尔',
    'name_iyakan': '伊亚坎', 'name_jansi': '让西', 'name_jas': '雅斯',
    'name_jay_singh': '杰辛格', 'name_keun': '克温', 'name_madana': '马达纳',
    'name_muizz': '穆伊兹', 'name_nadir': '纳迪尔', 'name_pal': '帕尔',
    'name_qaim': '卡伊姆', 'name_raghuraj': '拉古拉杰', 'name_rukn': '鲁昆',
    'name_sau': '绍', 'name_shaikh': '谢赫', 'name_shamshir': '沙姆希尔',
    'name_sharaf': '沙拉夫', 'name_shoja': '舒贾', 'name_sinhat': '辛哈特',
    'name_someshwara': '苏梅什瓦拉', 'name_tash': '塔什', 'name_tekuder': '贴古迭儿',
    'name_tode': '托德', 'name_togha': '脱合', 'name_tole': '托勒',
    'name_tugh': '图赫', 'name_varman': '瓦尔曼', 'name_virsingh': '维尔辛格',
    'name_yesu': '也速',
}

LANGS = ['braz_por', 'english', 'french', 'german', 'japanese', 'korean',
         'polish', 'russian', 'simp_chinese', 'spanish', 'turkish']


# ---------------------------------------------------------------- loaders
def load_yml(path):
    d = {}
    try:
        with open(path, 'rb') as f:
            lines = f.read().decode('utf-8-sig').splitlines()
    except FileNotFoundError:
        return d
    for ln in lines:
        m = re.match(r'^\s*([A-Za-z0-9_.\-]+):\d*\s+"(.*)"\s*$', ln)
        if m:
            d.setdefault(m.group(1), m.group(2))
    return d


def load_yml_plain(path):
    """EU5 / vanilla style: ' KEY: "value"' (no version number, trailing comment ok)."""
    d = {}
    try:
        with open(path, 'rb') as f:
            lines = f.read().decode('utf-8-sig').splitlines()
    except FileNotFoundError:
        return d
    for ln in lines:
        m = re.match(r'^\s*([A-Za-z0-9_.\-]+):\s*"([^"]*)"', ln)
        if m:
            d.setdefault(m.group(1), m.group(2))
    return d


def load_eu5_names(lang):
    d = {}
    for fn in ('character_names_dynamic_l_%s.yml' % lang, 'character_names_l_%s.yml' % lang):
        d.update(load_yml_plain(os.path.join(EU5, 'main_menu', 'localization', lang, fn)))
    return d


eu5_en = load_eu5_names('english')
eu5_zh = load_eu5_names('simp_chinese')
print('EU5 name loc: EN %d keys, ZH %d keys' % (len(eu5_en), len(eu5_zh)))

en_src = load_yml('localization/english/zz_eu5_politics_l_english.yml')
en_src.update(load_yml('localization/english/gen_cultures_l_english.yml'))
zh_src = load_yml('localization/simp_chinese/zz_eu5_politics_l_simp_chinese.yml')
zh_van = load_yml_plain(VAN + '/localization/simp_chinese/names/character_names_l_simp_chinese.yml')
print('EN source keys: %d   ZH source keys: %d   vanilla ZH name keys: %d'
      % (len(en_src), len(zh_src), len(zh_van)))

# every composite name key in our politics file, placeholder or not
compound = sorted(k for k in en_src if k.startswith('name_') and '.' in k)
placeholder = [k for k in compound if en_src[k] == k.replace('_', ' ')]
print('compound keys: %d  (placeholders: %d)' % (len(compound), len(placeholder)))


def en_word(part):
    for d in (eu5_en, en_src):
        if part in d:
            return d[part]
    if part.startswith('name_'):
        alt = 'cul_' + part[len('name_'):]
        if alt in en_src:
            return en_src[alt]
    return HAND_EN.get(part)


def zh_word(part):
    for d in (eu5_zh, zh_src):
        if part in d:
            return d[part]
    if part.startswith('name_'):
        alt = 'cul_' + part[len('name_'):]
        if alt in zh_src:
            return zh_src[alt]
        # vanilla Chinese name list is keyed by capitalised given name
        slug = part[len('name_'):]
        for cand in (slug.capitalize(), slug.upper(), slug):
            if cand in zh_van:
                return zh_van[cand]
    return HAND_ZH.get(part)


rows = []
unresolved_en, unresolved_zh = [], []
stats = collections.Counter()
for k in compound:
    parts = k.split('.')
    # EU5 localises some composites as whole names; prefer that verbatim
    z_direct, e_direct = k in eu5_zh, k in eu5_en
    zw = [zh_word(p) for p in parts]
    ew = [en_word(p) for p in parts]
    if z_direct:
        zh = eu5_zh[k]
        stats['zh_direct'] += 1
    else:
        zh = ''.join(w for w in zw if w)
        if any(w is None for w in zw):
            stats['zh_gap'] += 1
            unresolved_zh += [p for p, w in zip(parts, zw) if w is None]
    if e_direct:
        en = eu5_en[k]
        stats['en_direct'] += 1
    else:
        en = ' '.join(w for w in ew if w)
        if any(w is None for w in ew):
            stats['en_gap'] += 1
            unresolved_en += [p for p, w in zip(parts, ew) if w is None]
    rows.append({'key': k, 'en': en, 'zh': zh,
                 'placeholder': en_src[k] == k.replace('_', ' '),
                 'src_zh': 'eu5-direct' if z_direct else 'parts',
                 'src_en': 'eu5-direct' if e_direct else 'parts'})

print('EU5 direct composite values: ZH %d, EN %d' % (stats['zh_direct'], stats['en_direct']))
print('unresolved EN parts: %d  -> %s' % (len(set(unresolved_en)), sorted(set(unresolved_en))))
print('unresolved ZH parts: %d  -> %s' % (len(set(unresolved_zh)), sorted(set(unresolved_zh))))
print()

lut = {r['key']: r for r in rows}
changed = 0
for k in compound:
    r = lut[k]
    old_en, old_zh = en_src[k], zh_src.get(k, '')
    new_en, new_zh = r['en'], r['zh']
    if old_en != new_en or old_zh != new_zh:
        changed += 1
print('compound keys whose value changes: %d / %d' % (changed, len(compound)))
print()
print('  %-46s %-30s %-30s %s' % ('key', 'old EN', 'new EN', 'new ZH'))
for k in compound:
    r = lut[k]
    old_en, old_zh = en_src[k], zh_src.get(k, '')
    if old_en != r['en'] or old_zh != r['zh']:
        print('  %-46s %-30s %-30s %s' % (k, old_en[:30], r['en'][:30], r['zh']))

json.dump(rows, open('gen_debug/compound_name_resolved.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

if not APPLY:
    sys.exit(0)

# ---------------------------------------------------------------- apply
placeholder_hits = []
for lang in LANGS:
    p = 'localization/%s/zz_eu5_politics_l_%s.yml' % (lang, lang)
    with open(p, 'rb') as f:
        raw = f.read()
    text = raw.decode('utf-8-sig')
    lines = text.split('\n')
    changed = 0
    for i, ln in enumerate(lines):
        m = re.match(r'^\s*([A-Za-z0-9_.\-]+):\d*\s+"(.*)"\s*$', ln)
        if not m:
            continue
        k, old = m.group(1), m.group(2)
        if k not in lut:
            continue
        new = lut[k]['zh'] if lang == 'simp_chinese' else lut[k]['en']
        if new == old:
            continue
        lines[i] = ln.replace('"%s"' % old, '"%s"' % new, 1)
        changed += 1
        placeholder_hits.append((lang, k, old, new))
    if changed:
        stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        bak = p + '.bak_compoundnames_' + stamp
        with open(bak, 'wb') as f:
            f.write(raw)
        out = '\n'.join(lines)
        with open(p, 'wb') as f:
            f.write(b'\xef\xbb\xbf' + out.encode('utf-8'))
        print('%s: %d lines patched (backup %s)' % (lang, changed, bak))
    else:
        print('%s: nothing to patch' % lang)

print()
print('total patched lines: %d' % len(placeholder_hits))
for lang, k, old, new in placeholder_hits:
    if lang == 'simp_chinese':
        print('  %-46s %-28s -> %s' % (k, old, new))
