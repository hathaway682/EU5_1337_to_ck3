"""Repair three remaining literal/incorrectly parsed EU5 character names."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
BACKUP = Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261105_000321_last_character_names')
LANGS = ['english', 'simp_chinese', 'french', 'german', 'spanish', 'russian',
         'polish', 'braz_por', 'japanese', 'korean', 'turkish']
loc_re = re.compile(r'(?m)^[ \t]*([\w.\-]+):\d*[ \t]*"([^"\r\n]*)"')
read = lambda p: p.read_text(encoding='utf-8-sig')
outputs = {}
def original(rel):
    live, snapshot = ROOT / rel, BACKUP / 'mod' / rel
    data = snapshot.read_bytes()
    if live.read_bytes() != data: raise RuntimeError('Input changed: ' + str(live))
    return data.decode('utf-8-sig'), data.startswith(b'\xef\xbb\xbf')
def existing(rel, data, bom):
    outputs[ROOT / rel] = (b'\xef\xbb\xbf' if bom else b'') + data.encode('utf-8')
def lookup(path, key):
    values = dict(loc_re.findall(read(path)))
    if key not in values: raise ValueError('Missing source key ' + key + ' in ' + str(path))
    value = values[key]
    if '$' in value or '[' in value: raise ValueError('Dynamic source: ' + key)
    return value

rel = Path('history/characters/zz_eu5_characters.txt')
text, bom = original(rel)
for character, old, new in [('bos_shishman_wife_stephen_kotromanic', 'random', 'name_eu5_unknown_bosnian_wife'),
                             ('fadl', 'Al', 'Al-Fadl')]:
    block = re.compile(r'(?ms)^(' + re.escape(character) + r'\s*=\s*\{.*?^[ \t]*name\s*=\s*")' + re.escape(old) + r'("[^\r\n]*)')
    text, count = block.subn(lambda m: m.group(1) + new + m.group(2), text)
    if count != 1: raise ValueError('Unexpected character name for ' + character)
existing(rel, text, bom)

for lang in LANGS:
    rel = Path('localization') / lang / ('zz_eu5_politics_l_' + lang + '.yml')
    text, bom = original(rel)
    eu = BACKUP / 'eu5/localization' / lang
    taiping = lookup(eu / 'location_names' / ('location_names_l_' + lang + '.yml'), 'taiping')
    pat = re.compile(r'(?m)^([ \t]*taiping:\d*[ \t]*")([^"\r\n]*)("[^\r\n]*)(?=\r?$)')
    text, count = pat.subn(lambda m: m.group(1) + taiping + m.group(3), text)
    if count != 1: raise ValueError('Unexpected taiping localization in ' + lang)
    existing(rel, text, bom)
    fadl = lookup(eu / ('character_names_l_' + lang + '.yml'), 'Al-Fadl')
    ck = BACKUP / 'ck3/localization' / lang / ('war_results_window_l_' + lang + '.yml')
    if not ck.exists(): ck = BACKUP / 'ck3/localization/english/war_results_window_l_english.yml'
    unknown = lookup(ck, 'WAR_RESULTS_UNKNOWN')
    body = 'l_' + lang + ':\n Al-Fadl:0 "' + fadl + '"\n name_eu5_unknown_bosnian_wife:0 "' + unknown + '"\n'
    dst = ROOT / 'localization' / lang / ('zzzz_eu5_last_character_names_l_' + lang + '.yml')
    if dst.exists(): raise FileExistsError(dst)
    outputs[dst] = b'\xef\xbb\xbf' + body.encode('utf-8')
print('Two character name references corrected; taiping and two labels prepared in', len(LANGS), 'languages')
if '--apply' in sys.argv:
    for path, data in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (ROOT / 'gen_debug/eu5_last_character_names_20261105.json').write_text(
        json.dumps({'characters': ['bos_shishman_wife_stephen_kotromanic', 'fadl', 'oge_taiping_borjigin'],
                    'unknown_fallback_english': ['braz_por', 'turkish']}, indent=2) + '\n', encoding='utf-8')
