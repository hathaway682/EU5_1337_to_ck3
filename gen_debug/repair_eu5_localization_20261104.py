"""Repair EU5-derived names and literal localization references.

Sources and every modified file are captured in the F-drive backup. This audit
repairs malformed compound names, source-backed Chinese generated regent names,
missing character names, seven literal consul names, and EU5 text references.
Default is dry-run; --apply writes only after all consistency checks succeed.
After this step, repair_eu5_last_character_names_20261105.py corrects three
additional characters whose original names were truncated or left untranslated.
"""
from pathlib import Path
from collections import defaultdict
import json
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
BACKUP = Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261104_234338_localization_audit')
LANGS = ['english', 'simp_chinese', 'french', 'german', 'spanish', 'russian',
         'polish', 'braz_por', 'japanese', 'korean', 'turkish']
COMPOSITES = ['Baba.name_bahadur', 'Nahwi.name_mansur', 'Shahab.name_al_din',
              'Abu_al_Hasan.name_ali', 'Turan.name_shah', 'Shuja.name_al_din.Abu_Bakr']
MISSING_NAMES = ['name_julius', 'name_ariadne', 'name_nissim', 'name_bahya',
                 'name_asher', 'name_judah', 'name_samuel', 'Abu-l_Abbas',
                 'Abd_al-Haqq', 'Abd_al-Wahid']
REFS = {'fair_isle_gap_SHORT', 'pentland_firth_SHORT', 'sumburgh_head_SHORT',
        'cape_wrath_SHORT', 'humber_estuary_SHORT', 'flamborough_head_SHORT',
        'kinnaird_head_SHORT', 'firth_of_tay_SHORT', 'firth_of_lorne_SHORT',
        'butt_of_lewis_SHORT', 'lewis', 'ayodhya', 'liege', 'Ceva', 'Hanover',
        'Hohenberg', 'Laval', 'Orleans', 'vijaya', 'Bar'}
CONSULS = {'NOV': 'Velikiy Novgorod Consul', 'MND': 'Mondovi Consul',
           'PRA': 'Prato Consul', 'PES': 'Pesaro Consul', 'PAD': 'Padua Consul',
           'PAR': 'Parma Consul', 'LUC': 'Lucca Consul'}
line_re = re.compile(r'(?m)^([ \t]*)([\w.\-]+)(:\d*[ \t]*")([^"\r\n]*)("[^\r\n]*)(?=\r?$)')
src_re = re.compile(r'(?m)^[ \t]*([\w.\-]+):\d*[ \t]*"([^"\r\n]*)"')

def read(path):
    return path.read_text(encoding='utf-8-sig')

def source_dict(path):
    return {m.group(1): m.group(2) for m in src_re.finditer(read(path))}

def eu_path(lang, stem):
    return BACKUP / 'eu5' / lang / (stem + '_l_' + lang + '.yml')

eu = {}
for lang in LANGS:
    # Preserve separate namespaces: place references must not resolve to an
    # unrelated similarly spelled personal name.
    data = {}
    for stem in ['character_names_dynamic', 'character_names', 'location_names/location_names',
                 'country_names', 'province_names', 'area', 'region_names', 'government_names']:
        p = eu_path(lang, stem)
        data[stem] = source_dict(p) if p.exists() else {}
    eu[lang] = data

outputs = {}
def original(rel):
    path, snap = ROOT / rel, BACKUP / 'mod' / rel
    if path.read_bytes() != snap.read_bytes():
        raise RuntimeError('File changed since backup: ' + str(path))
    data = snap.read_bytes()
    return data.decode('utf-8-sig'), data.startswith(b'\xef\xbb\xbf')

def save_existing(rel, body, bom):
    outputs[ROOT / rel] = (b'\xef\xbb\xbf' if bom else b'') + body.encode('utf-8')

def replace_values(text, replacements):
    counts = defaultdict(int)
    def repl(m):
        key = m.group(2)
        if key not in replacements: return m.group(0)
        counts[key] += 1
        return m.group(1) + key + m.group(3) + replacements[key] + m.group(5)
    out = line_re.sub(repl, text)
    bad = {k: counts[k] for k in replacements if counts[k] != 1}
    if bad: raise ValueError('Expected one occurrence of each changed localization: ' + repr(bad))
    return out

def person_name(lang, component):
    folded = component.casefold()
    sources = eu[lang]
    for spelling in (folded, 'name_' + folded if not folded.startswith('name_') else folded):
        for stem in ('character_names_dynamic', 'character_names'):
            lookup = {k.casefold(): v for k, v in sources[stem].items()}
            if spelling in lookup:
                value = lookup[spelling]
                if any(c in value for c in '$[]'): raise ValueError('Dynamic name: ' + component)
                return value
    raise KeyError((lang, component))

def place_ref(lang, key):
    for stem in ('location_names/location_names', 'country_names', 'province_names', 'area', 'region_names'):
        lookup = {k.casefold(): v for k, v in eu[lang][stem].items()}
        if key.casefold() in lookup:
            value = lookup[key.casefold()]
            if any(c in value for c in '$[]'): raise ValueError('Dynamic reference: ' + key)
            return value
    raise KeyError((lang, key))

reference_changes = {}
for lang in LANGS:
    rel = Path('localization') / lang / ('zz_eu5_politics_l_' + lang + '.yml')
    text, bom = original(rel)
    joiner = '·' if lang == 'simp_chinese' else '・' if lang == 'japanese' else ' '
    composite_values = {key: joiner.join(person_name(lang, p) for p in key.split('.')) for key in COMPOSITES}
    text = replace_values(text, composite_values)
    refcounts = [0]
    def expand(m):
        token = m.group(1)
        if token not in REFS: return m.group(0)
        refcounts[0] += 1
        return place_ref(lang, token)
    text = re.sub(r'\$([\w.\-]+)\$', expand, text)
    save_existing(rel, text, bom)
    sea_rel = Path('localization') / lang / ('eu5_sea_names_l_' + lang + '.yml')
    sea, sea_bom = original(sea_rel)
    sea = re.sub(r'\$([\w.\-]+)\$', expand, sea)
    save_existing(sea_rel, sea, sea_bom)
    reference_changes[lang] = refcounts[0]

# Resolve untranslated generated regent names: first match their country tag,
# then use an exact English match only where EU5 gives a unique Chinese value.
zh_rel = Path('localization/simp_chinese/zz_eu5_names_l_simp_chinese.yml')
zh, zh_bom = original(zh_rel)
en_rel = Path('localization/english/zz_eu5_names_l_english.yml')
en, _ = original(en_rel)
zh_names = {m.group(2): m.group(4) for m in line_re.finditer(zh)}
en_names = {m.group(2): m.group(4) for m in line_re.finditer(en)}
latin = {k: v for k, v in zh_names.items() if re.search('[A-Za-z]', v) and not re.search('[\u3400-\u9fff]', v)}
regent_tags = defaultdict(set)
for p in (BACKUP / 'mod/history/characters').glob('*.txt'):
    for m in re.finditer(r'(?m)^eu5_regent_([a-z0-9]+)\s*=\s*\{\s*\n\s*name\s*=\s*"([^"\r\n]+)"', read(p)):
        regent_tags[m.group(2)].add(m.group(1).upper())
country_en, country_zh = eu['english']['country_names'], eu['simp_chinese']['country_names']
english_index = defaultdict(set)
for stem in ('country_names', 'location_names/location_names', 'province_names', 'area',
             'region_names', 'character_names', 'character_names_dynamic'):
    for key, value in eu['english'][stem].items():
        translated = eu['simp_chinese'][stem].get(key)
        if translated and re.search('[\u3400-\u9fff]', translated) and not any(c in translated for c in '$[]'):
            english_index[value.casefold()].add(translated)
name_replacements, unresolved, methods = {}, {}, {}
for key, old in latin.items():
    en_value = en_names.get(key, '')
    by_tag = {country_zh[tag] for tag in regent_tags.get(key, set())
              if tag in country_en and tag in country_zh and country_en[tag].casefold() == en_value.casefold()
              and re.search('[\u3400-\u9fff]', country_zh[tag])}
    if len(by_tag) == 1:
        name_replacements[key] = next(iter(by_tag)); methods[key] = 'country_tag'
    else:
        candidates = english_index[en_value.casefold()]
        if len(candidates) == 1:
            name_replacements[key] = next(iter(candidates)); methods[key] = 'unique_exact_english'
        else:
            unresolved[key] = {'english': en_value, 'candidates': sorted(candidates)}
zh = replace_values(zh, name_replacements)
save_existing(zh_rel, zh, zh_bom)

# The seven added republican characters currently have literal English names
# containing spaces. Give them localizable keys and provide EU5-sourced labels.
character_rel = Path('history/characters/zz_eu5_missing_characters.txt')
characters, char_bom = original(character_rel)
for tag, old_name in CONSULS.items():
    block = re.compile(r'(?ms)^(eu5_rep_' + tag.lower() + r'\s*=\s*\{\s*\n[ \t]*name\s*=\s*")' + re.escape(old_name) + r'("[^\r\n]*)')
    characters, n = block.subn(lambda m: m.group(1) + 'name_eu5_republic_consul_' + tag.lower() + m.group(2), characters)
    if n != 1: raise ValueError('Missing expected consul: ' + tag)
save_existing(character_rel, characters, char_bom)

new_counts = {}
for lang in LANGS:
    existing = set()
    for directory in (BACKUP / 'mod/localization' / lang, BACKUP / 'mod/localization/replace' / lang):
        if directory.exists():
            for p in directory.rglob('*.yml'):
                existing.update(m.group(1) for m in src_re.finditer(read(p)))
    lines = ['l_' + lang + ':']
    for key in MISSING_NAMES:
        if key not in existing:
            lines.append(' ' + key + ':0 "' + person_name(lang, key) + '"')
    title = eu[lang]['government_names'].get('rank_duchy_republic_ruler_male')
    if not title or any(c in title for c in '$[]'): raise ValueError('Missing consul label: ' + lang)
    for tag in CONSULS:
        key = 'name_eu5_republic_consul_' + tag.lower()
        if key in existing: raise ValueError('Consul name key already exists: ' + key)
        country = eu[lang]['country_names'].get(tag)
        if not country or any(c in country for c in '$[]'): raise ValueError('Missing country: ' + tag)
        sep = '' if lang in ('simp_chinese', 'japanese') else ' '
        lines.append(' ' + key + ':0 "' + country + sep + title + '"')
    if lang == 'simp_chinese':
        for key, value in {'ruins_holder_name': '废墟', 'gen_culture_unsettled': '无人定居',
                           'gen_culture_unsettled_collective_noun': '无人定居',
                           'gen_culture_unsettled_prefix': '无人定居',
                           'gen_wilderness_culture': '荒野',
                           'gen_wilderness_culture_collective_noun': '荒野',
                           'gen_wilderness_culture_prefix': '荒野',
                           'gen_wilderness_faith': '荒野信仰'}.items():
            if key not in existing: lines.append(' ' + key + ':0 "' + value + '"')
    dest = ROOT / 'localization' / lang / ('zzzz_eu5_character_repair_l_' + lang + '.yml')
    if dest.exists(): raise FileExistsError('Output already exists: ' + str(dest))
    outputs[dest] = b'\xef\xbb\xbf' + ('\n'.join(lines) + '\n').encode('utf-8')
    new_counts[lang] = len(lines)-1

report = {'composite_names_per_language': len(COMPOSITES), 'expanded_eu5_refs': reference_changes,
          'chinese_regent_names_repaired': len(name_replacements), 'regent_name_methods': methods,
          'unresolved_regent_names': unresolved, 'consul_names': list(CONSULS),
          'new_localization_keys': new_counts}
print('compound names:', len(COMPOSITES), 'in', len(LANGS), 'languages')
print('EU5 text references expanded:', reference_changes)
print('Chinese generated names:', len(name_replacements), 'unresolved:', len(unresolved), unresolved)
print('consul characters:', len(CONSULS), 'new keys:', new_counts)
print('example screenshot:', person_name('simp_chinese', 'Abu_al_Hasan') + '·' + person_name('simp_chinese', 'name_ali'))
if '--apply' in sys.argv:
    for path, data in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (ROOT / 'gen_debug/eu5_localization_repair_20261104.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
