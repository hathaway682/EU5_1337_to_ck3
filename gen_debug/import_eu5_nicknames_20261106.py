"""Import source-backed 1337 EU5 nicknames. Dry run by default; --apply writes.

Inputs are frozen in the verified F-drive backup. Character IDs must match
exactly. Existing CK3 keys are reused; other names have a private namespace.
EU5 supplies no acquisition dates, so its static nicknames are initialized in
the existing birth history block, including for deceased family members.
"""
from pathlib import Path
from collections import Counter, defaultdict
import json
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
BACKUP = Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261106_121301_eu5_nicknames')
LANGS = ['english', 'simp_chinese', 'french', 'german', 'spanish', 'russian',
         'polish', 'braz_por', 'japanese', 'korean', 'turkish']
TOK = re.compile(r'#[^\r\n]*|"(?:\\.|[^"\\])*"|[{}=]|[^\s{}=\"#]+')
LOC = re.compile(r'^\s*([\w.\-]+):\d*\s*"((?:\\.|[^"\\])*)"', re.M)


def read(p):
    return p.read_bytes().decode('utf-8-sig')


def fields(s):
    """Direct fields, with source spans; ignore comments and nested fields."""
    ts = [m for m in TOK.finditer(s) if not m[0].startswith('#')]
    result = []
    i = 0
    while i < len(ts):
        if i + 2 >= len(ts) or ts[i + 1][0] != '=':
            i += 1
            continue
        key, value = ts[i][0].strip('"'), ts[i + 2]
        j = i + 3
        if value[0] == '{':
            depth = 1
            while j < len(ts) and depth:
                depth += (ts[j][0] == '{') - (ts[j][0] == '}')
                j += 1
            assert depth == 0, key
            result.append((key, s[value.end():ts[j - 1].start()], value.start(), ts[j - 1].end()))
        else:
            result.append((key, value[0].strip('"'), value.start(), value.end()))
        i = j
    return result


def data(s):
    return {k: v for k, v, _, _ in fields(s)}


def load_loc(folder):
    out = {}
    for p in sorted(folder.rglob('*.yml')):
        out.update({m[1]: m[2] for m in LOC.finditer(read(p))})
    return out


def main():
    eu = data(read(BACKUP / 'eu5/setup/1337/05_characters.txt'))['character_db']
    source = {}
    for cid, body, _, _ in fields(eu):
        fs = data(body)
        if 'nickname' in fs:
            n = fs['nickname']
            if '=' in n:
                n = data(n)['name']
            source[cid] = {'source_nickname': n, 'source_birth': fs.get('birth_date')}

    native = {}
    for p in (BACKUP / 'ck3/common/nicknames').glob('*.txt'):
        native.update(data(read(p)))
    eu_loc = {lang: load_loc(BACKUP / 'eu5/localization' / lang) for lang in LANGS}
    native_loc = {lang: load_loc(BACKUP / 'ck3/localization' / lang) for lang in LANGS}
    mod = defaultdict(list)
    texts = {}
    for p in sorted((ROOT / 'history/characters').glob('*.txt')):
        rel = p.relative_to(ROOT)
        text = read(p)
        texts[rel] = text
        for cid, body, start, end in fields(text):
            if cid in source and re.search(r'\bbirth\s*=\s*yes\b', body):
                mod[cid].append((rel, body, start, end))

    keys = sorted({v['source_nickname'] for v in source.values()})
    english_index = defaultdict(list)
    for key in native:
        if key in native_loc['english']:
            english_index[native_loc['english'][key].casefold()].append(key)
    keymap = {}
    for key in keys:
        # Exact keys first. Prefix variants are accepted only when their English
        # meanings agree; no matching by character name or guessed identity.
        candidate = key if key in native else 'nick_' + key.lower()
        en = eu_loc['english'].get(key)
        same = en and en.casefold() == native_loc['english'].get(candidate, '').casefold()
        if key in native or (candidate in native and same):
            keymap[key] = candidate
        elif key == 'nick_the_conquerer':
            keymap[key] = 'nick_the_conqueror'
        elif en and len(english_index.get(en.casefold(), [])) == 1:
            keymap[key] = english_index[en.casefold()][0]
        else:
            keymap[key] = 'eu5_nick_' + re.sub('[^a-z0-9_]', '_', key.lower())
    custom = {k: v for k, v in keymap.items() if v.startswith('eu5_nick_')}
    assert len(custom) == len(set(custom.values())), 'Namespace collision'

    rows, edits, missing, conflicts = [], defaultdict(list), [], []
    for cid, info in source.items():
        matches = mod.get(cid, [])
        if not matches:
            missing.append(cid)
            continue
        assert len(matches) == 1, (cid, matches)
        rel, body, start, end = matches[0]
        nickname = keymap[info['source_nickname']]
        existing = re.findall(r'\bgive_nickname\s*=\s*([\w.-]+)', body)
        if existing and existing != [nickname]:
            conflicts.append((cid, existing, nickname))
            continue
        dates = [(d, b, a, z) for d, b, a, z in fields(body)
                 if re.fullmatch(r'\d+\.\d+\.\d+', d) and re.search(r'\bbirth\s*=\s*yes\b', b)]
        assert len(dates) == 1, cid
        date, birthbody, a, z = dates[0]
        assert date == info['source_birth'], (cid, date, info['source_birth'])
        if not existing:
            # Scalar yes ends at this offset within the enclosing character.
            birth = re.search(r'\bbirth\s*=\s*yes\b', body[a:z])
            position = start + 1 + a + birth.end()
            edits[rel].append((position, ' give_nickname = ' + nickname))
        rows.append(dict(character=cid, file=str(rel), birth=date, nickname=nickname,
                         **info, english=eu_loc['english'].get(info['source_nickname']),
                         chinese=eu_loc['simp_chinese'].get(info['source_nickname'])))
    assert not conflicts, conflicts
    assert not missing, missing

    outputs = {}
    for rel, inserts in edits.items():
        current = (ROOT / rel).read_bytes()
        assert current == (BACKUP / 'mod' / rel).read_bytes(), 'Changed since backup: ' + str(rel)
        text = texts[rel]
        for offset, insert in sorted(inserts, reverse=True):
            text = text[:offset] + insert + text[offset:]
        # No original field or whitespace is altered by this patch.
        restored = re.sub(r' give_nickname = (?:eu5_nick_|nick_)[\w]+', '', text)
        assert restored == texts[rel]
        outputs[rel] = (b'\xef\xbb\xbf' if current.startswith(b'\xef\xbb\xbf') else b'') + text.encode('utf-8')

    lines = ['# Historical EU5 1337 nicknames; assigned only by character history.',
             '# No random nickname-granting rules are added.', '']
    for key, target in custom.items():
        lines += ['# EU5: ' + key, target + ' = {}']
    outputs[Path('common/nicknames/zz_eu5_historical_nicknames.txt')] = ('\n'.join(lines) + '\n').encode('utf-8-sig')

    unresolved, fallbacks = [], []
    for lang in LANGS:
        lines = ['l_' + lang + ':', ' # Nicknames from EU5 1337 character data.']
        localized_keys = dict(custom)
        for key, target in keymap.items():
            if not target.startswith('eu5_nick_') and target not in native_loc[lang]:
                # CK3 has no built-in Portuguese/Turkish localization. Supply
                # EU5's corresponding text without overriding supported languages.
                if target not in localized_keys.values():
                    localized_keys[key] = target
        for key, target in localized_keys.items():
            value = eu_loc[lang].get(key)
            if value is None:
                fallbacks.append((lang, key))
                value = eu_loc['english'].get(key)
            if value is None:
                unresolved.append((lang, key))
                value = key
            # Resolve simple source references; EU5 script expressions need review.
            for _ in range(8):
                newer = re.sub(r'\$([\w.-]+)\$', lambda m: eu_loc[lang].get(m[1], eu_loc['english'].get(m[1], m[0])), value)
                if newer == value:
                    break
                value = newer
            # CK3 nicknames expose CHARACTER, rather than EU5's Character or
            # the country's current ruler (which may be a different person).
            value = value.replace('ROOT.GetCountry.GetGovernment.GetRuler.IsFemale', 'CHARACTER.IsFemale')
            value = value.replace('Character.IsFemale', 'CHARACTER.IsFemale')
            remaining = re.sub(r"\[Select_CString\(\s*CHARACTER\.IsFemale\s*,\s*'[^']*'\s*,\s*'[^']*'\s*\)\]", '', value)
            if '$' in remaining or '[' in remaining or ']' in remaining:
                unresolved.append((lang, key, value))
            lines.append(' ' + target + ':0 "' + value + '"')
        outputs[Path(f'localization/{lang}/eu5_historical_nicknames_l_{lang}.yml')] = ('\n'.join(lines) + '\n').encode('utf-8-sig')

    report = dict(source_count=len(source), matched=len(rows), unique_source_nicknames=len(keys),
                  native_keys=len(set(keymap.values()) - set(custom.values())), custom_keys=len(custom),
                  files=dict(Counter(r['file'] for r in rows)), missing=missing, conflicts=conflicts,
                  unresolved_localization=unresolved, fallback_localization=fallbacks,
                  mapping=keymap, characters=rows, backup=str(BACKUP))
    report_path = ROOT / 'gen_debug/eu5_nicknames_20261106.json'
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ['characters','mapping']},ensure_ascii=False,indent=2))
    if '--apply' in sys.argv:
        assert not unresolved, 'Unresolved localizations; inspect report before applying'
        for rel, payload in outputs.items():
            dest = ROOT / rel
            if dest.exists() and rel not in edits:
                snapshot = BACKUP / 'pre_localization_completion/mod' / rel
                assert (dest.read_bytes() == payload or
                        (snapshot.exists() and snapshot.read_bytes() == dest.read_bytes())), 'Refusing to overwrite existing output: ' + str(rel)
        for rel, payload in outputs.items():
            dest = ROOT / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(payload)
        print('Applied',len(outputs),'files; initialized',sum(map(len,edits.values())),'characters')


if __name__ == '__main__':
    main()
