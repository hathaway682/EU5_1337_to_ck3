"""Build the 1178 roster plus EU5's 1337 orders and documented leaders.

The reviewed manifest is the input, not a claim that every order survived to 1337.
Default: validate and stage. --apply --backup PATH requires a verified F: backup.
Existing territorial Hospitallers reuse their living grandmaster and Rhodes realm.
"""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'gen_debug/historical_orders_1337_20261105'
EFFECT = Path('common/scripted_effects/zz_eu5_1337_historical_orders.txt')
START = Path('common/on_action/game_start.txt')
GAME = Path(r'E:/SteamLibrary/steamapps/common/Crusader Kings III/game')

# Vanilla's historical 1178+ setup; 0 reflects Benedict XII’s 1336 reform.
# Except 18 and 48–50, which have no
# corresponding vanilla startup assignment and use the traditions noted below.
ORDER_TENETS = {
    0:'scholasticism', 1:'confession', 2:'transubstantiation', 3:'mortification_of_the_flesh',
    4:'divine_liturgy', 5:'philanthropia', 6:'sanctity_of_nature', 7:'celestial_hierarchy',
    8:'ora_et_labora', 9:'scholasticism', 10:'communion', 11:'asceticism',
    12:'love_thy_neighbour', 13:'anachoresis', 14:'ora_et_labora', 15:'hyperdulia',
    16:'mendicant_preachers', 17:'divine_liturgy', 18:'ora_et_labora',
    19:'celestial_hierarchy', 20:'holy_myron', 21:'hesychasm', 22:'dulia',
    23:'philanthropia', 24:'acts_of_apostles', 25:'ora_et_labora', 26:'adaptive',
    27:'confession', 28:'scholasticism', 29:'hyperdulia', 30:'esotericism',
    31:'anachoresis', 32:'communal_identity', 33:'alexandrian_catechism',
    34:'literalism', 35:'pastoral_isolation', 36:'ritual_hospitality',
    48:'mendicant_preachers', 49:'vows_of_poverty', 50:'confession',
}


def additional_products(data):
    """Native CK3 has Alcantara, Franciscans and Dominicans, but not these three."""
    products = {}
    types, titles = [], []
    new = [r for r in data['orders'] if r['type_key'].startswith('ho_eu5_')]
    coas = {
        'ho_eu5_order_of_christ': ('eu5_order_christ', 'eu5_order_cross_christ.dds', 'red', 'red', 'white'),
        'ho_eu5_order_of_montesa': ('eu5_order_montesa', 'eu5_order_cross_montesa.dds', 'black', 'red', 'red'),
    }
    coa_text = '# EU5 OPX/MTS presets, using the original EU5 cross textures.\n'
    for r in new:
        military = r['ORDER_TYPE'] == 'military'
        government = 'holy_order_government' if military else 'monastic_holy_order_government'
        name = r['type_key'] + '_name'
        lines = [r['type_key'] + ' = {', f'\ttype = {r["ORDER_TYPE"]}',
                 f'\tgovernment = {government}', f'\ttitle = {r["title"]}', f'\tname = {name}',
                 '\ttrigger = { current_date >= 1337.4.1 scope:founder.faith = { has_doctrine_parameter = is_western_christian_faith } }',
                 '\tweight = { value = 10 }']
        if military:
            lines += ['\tmen_at_arms = { caballero }']
        if r['type_key'] in coas:
            coa, texture, c1, c2, c3 = coas[r['type_key']]
            lines += [f'\tcoat_of_arms = {coa}']
            coa_text += f'''{coa} = {{
\tpattern = "pattern_solid.dds"
\tcolor1 = white
\tcolored_emblem = {{
\t\ttexture = "{texture}"
\t\tcolor1 = {c1}
\t\tcolor2 = {c2}
\t\tcolor3 = {c3}
\t\tinstance = {{ scale = {{ 1.5 1.0 }} }} # EU5 384x256 -> CK3 square
\t}}
}}
'''
            products[Path('gfx/coat_of_arms/colored_emblems') / texture] = (OUT / 'inputs' / texture).read_bytes()
        lines += ['}', '']
        types.append('\n'.join(lines))
        color = '190 45 45' if military else '70 70 70'
        titles.append(f'''{r['title']} = {{
\tcolor = {{ {color} }}
\tcapital = {r['capital_county']}
\tlandless = yes
\tdefinite_form = yes
\tno_automatic_claims = yes
\tcan_create = {{ always = no }}
\tcan_create_on_partition = {{ always = no }}
}}
''')
    products[Path('common/holy_orders/zz_eu5_1337_religious_orders.txt')] = (
        '# EU5 1337 additions. Augustinian Hermits are distinct from Augustinian Canons.\n'
        '# Like native Franciscans/Dominicans, the EU5 mendicant order uses CK3 monastic mechanics.\n'
        + '\n'.join(types))
    products[Path('common/landed_titles/zzzz_eu5_1337_religious_orders.txt')] = '\n'.join(titles)
    products[Path('common/coat_of_arms/coat_of_arms/zz_eu5_1337_religious_orders.txt')] = coa_text
    for lang, col in [('english', 'en'), ('simp_chinese', 'zh')]:
        loc = []
        for r in new:
            loc += [f' {r["title"]}:0 "{r["name_" + col]}"',
                    f' {r["type_key"]}_name:0 "{r["name_" + col]}"']
        for r in data['orders']:
            if r.get('leader_name_key'):
                loc.append(f' {r["leader_name_key"]}:0 "{r["leader_name_" + col]}"')
        products[Path(f'localization/{lang}/eu5_religious_orders_1337_l_{lang}.yml')] = (
            'l_' + lang + ':\n' + '\n'.join(loc) + '\n')
    return products

HELPERS = '''# Vanilla 1178 roster plus the EU5 1337 religious-order setup and its leaders.
# Monastic orders require PAM, as in vanilla. Military orders do not.
# Headquarters and branch houses are all non-capital baronies.
# Landed county ownership is retained; only the barony leases are established.

eu5_1337_prepare_order_barony_effect = {
	title:$BARONY$ = {
		if = {
			limit = { title_province = { has_holding = no } }
			title_province = { set_holding_type = $HOLDING$ }
		}
		# Vanilla startup likewise consolidates baronies under their county holder.
		county.holder = { get_title = title:$BARONY$ }
	}
}

eu5_1337_found_order_effect = {
	eu5_1337_prepare_order_barony_effect = { BARONY = $CAPITAL$ HOLDING = $HOLDING$ }
	$LEADER$ = { save_scope_as = eu5_1337_order_founder }
	# Prefer a local patron of the same faith; minority enclaves can found themselves.
	title:$CAPITAL$.county.holder = {
		if = {
			limit = { faith = $LEADER$.faith }
			save_scope_as = eu5_1337_order_founder
		}
	}
	scope:eu5_1337_order_founder = {
		set_variable = { name = $STARTUP_FLAG$ days = 1 }
		add_character_flag = eu5_1337_historical_order_setup
	}
	# Explicit type preserves the historical name, arms, tenet and succession setup.
	create_holy_order = {
		leader = $LEADER$
		founder = scope:eu5_1337_order_founder
		holy_order_type = $TYPE$
		capital = title:$CAPITAL$
		save_scope_as = $ORDER_SCOPE$
	}
	scope:eu5_1337_order_founder = { remove_variable = $STARTUP_FLAG$ remove_character_flag = eu5_1337_historical_order_setup }
	if = {
		limit = { exists = scope:$ORDER_SCOPE$ }
		set_global_variable = $FLAG$
		$LEADER$ = {
			add_trait = $TRAIT$
			add_piety_level = 2
			add_gold = holy_order_starting_gold
			every_courtier = { add_trait = $TRAIT$ }
		}
	}
}

eu5_1337_lease_order_branch_effect = {
	if = {
		limit = {
			exists = $ORDER$
			title:$BARONY$ = {
				exists = county.holder
				is_under_holy_order_lease = no
				title_province = { is_county_capital = no }
			}
		}
		eu5_1337_prepare_order_barony_effect = { BARONY = $BARONY$ HOLDING = $HOLDING$ }
		title:$BARONY$ = { lease_out_to_holy_order = $ORDER$ }
	}
}

'''


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def validate(data, additions):
    # Use the project's existing balanced-brace parser to audit actual inputs.
    import rebuild_geographical_regions_20261031 as syntax
    rows = data['orders']
    assert Counter(r['ORDER_TYPE'] for r in rows) == data['expected_counts'] == {'monastic': 40, 'military': 10}
    assert len({r['id'] for r in rows}) == 50
    assert set(ORDER_TENETS) == {r['id'] for r in rows if r['ORDER_TYPE'] == 'monastic'}
    tenet_keys = set()
    for base in (GAME, ROOT):
        for path in (base / 'common/religion/tenet_types').glob('*.txt'):
            tenet_keys.update(k for k, v in syntax.parse(syntax.read(path))[0])
    assert {'tenet_' + t for t in ORDER_TENETS.values()} <= tenet_keys
    baseline = json.loads((OUT / 'inputs/baseline_trace.json').read_text(encoding='utf-8'))
    assert [(r['id'], r['LEADER'], r['CAPITAL']) for r in rows if r['id'] < 45] == [
        (r['id'], r['LEADER'], r['CAPITAL']) for r in baseline if r['id'] != 37]
    previous = json.loads((Path(data['backup']) / 'mod/gen_debug/historical_orders_1337_20261105/inputs/orders.json').read_text(encoding='utf-8'))['orders']
    assert all(r['capital'] == next(x for x in previous if x['id'] == r['id'])['capital'] and set(next(x for x in previous if x['id'] == r['id'])['branches']) <= set(r['branches']) for r in rows if r['id'] < 45 and r['id'] not in (11, 39, 40, 41, 42, 43, 44))
    meta = json.loads((OUT / 'inputs/map_metadata.json').read_text(encoding='utf-8'))
    _, baronies, ancestry = syntax.titles(ROOT / 'common/landed_titles')
    title_keys = set()
    for p in (ROOT / 'common/landed_titles').glob('*.txt'):
        title_keys.update(re.findall(r'\b([hkedcb]_[\w-]+)\s*=\s*\{', syntax.read(p)))
    for rel, body in additions.items():
        if rel.parent == Path('common/landed_titles'):
            title_keys.update(k for k, v in syntax.parse(body)[0])
    rites = {}
    for p in (ROOT / 'common/religion/rite_types').glob('*.txt'):
        rites.update(dict(syntax.parse(syntax.read(p))[0]))
    cultures = set()
    effective_cultures = {}
    for base in (GAME, ROOT):
        effective_cultures.update({p.name: p for p in (base / 'common/culture/cultures').glob('*.txt')})
    for p in effective_cultures.values():
        cultures.update(k for k, v in syntax.parse(syntax.read(p))[0])
    definitions = {}
    effective_types = {}
    for base in (GAME, ROOT):
        effective_types.update({p.name: p for p in (base / 'common/holy_orders').glob('*.txt')})
    for p in effective_types.values():
        definitions.update(dict(syntax.parse(syntax.read(p))[0]))
    for rel, body in additions.items():
        if rel.parent == Path('common/holy_orders'):
            definitions.update(dict(syntax.parse(body)[0]))
    used = set()
    for r in rows:
        assert r['type_key'] in definitions, r['type_key']
        props = dict(definitions[r['type_key']][0])
        assert props['type'] == r['ORDER_TYPE']
        assert props.get('title') == r['title']
        assert not r['title'] or r['title'] in title_keys, r['title']
        assert r['rite'] in rites, r['rite']
        assert r['culture'] in cultures, r['culture']
        assert r['gender'] in ('female', 'male')
        for b in [r['capital']] + r['branches']:
            assert b not in used, ('duplicate lease', b)
            used.add(b)
            assert b in baronies, b
            assert baronies[b] == int(meta[b]['province'])
            assert not meta[b]['capital'], ('county capital', b)
            assert meta[b]['county'] in ancestry[b], b
            holding = meta[b]['state'].get('holding', 'none')
            allowed = ('none', 'church_holding', 'temple_citadel_holding') if r['ORDER_TYPE'] == 'monastic' else ('none', 'castle_holding', 'city_holding', 'temple_citadel_holding')
            assert holding in allowed, (b, holding)
    assert len(used) == 171
    for r in rows:
        if r['id'] in (39, 40, 41, 45, 46, 47):
            counties = [meta[b]['county'] for b in [r['capital']] + r['branches']]
            assert len(counties) == len(set(counties)), (r['id'], counties)
    assert meta['b_rodos']['capital'] and meta['b_rodos']['county'] == 'c_rodos'
    chars = (ROOT / 'history/characters/zz_eu5_characters.txt').read_text(encoding='utf-8-sig')
    assert 'kni_helion_de_villeneuve = {' in chars
    # Match all eleven EU5 records by their character keys, never just by name.
    eu5 = dict(syntax.parse(syntax.read(OUT / 'inputs/eu5_04_religious_orders.txt'))[0])
    source_heads = {k: dict(n[0])['head_character'] for k, n in eu5['religious_order_manager'][0]}
    assert source_heads == data['eu5_source_heads']
    assert digest(OUT / 'inputs/eu5_04_religious_orders.txt') == data['eu5_source_sha256']
    assert {r['eu5_source_key']: r['existing_leader'] for r in rows if r.get('eu5_source_key')} == source_heads
    expected = set(source_heads.values()) | {'kni_helion_de_villeneuve'}
    people = {}
    for p in (ROOT / 'history/characters').glob('*.txt'):
        for k, n in syntax.parse(syntax.read(p))[0]:
            if k in expected:
                people.setdefault(k, []).extend(n[0])
    assert set(people) == expected
    for key, entries in people.items():
        born = False
        for date, node in entries:
            if re.fullmatch(r'\d+\.\d+\.\d+', date) and tuple(map(int, date.split('.'))) <= (1337, 4, 1):
                props = dict(node[0])
                born |= 'birth' in props
                assert 'death' not in props, ('dead head', key)
        assert born, ('unborn head', key)
    return syntax


def render_order(r):
    n = r['id']
    leader = f'eu5_1337_order_{n}_leader'
    scope = f'eu5_1337_order_{n}'
    kind = r['ORDER_TYPE']
    trait = 'devoted' if kind == 'monastic' else 'order_member'
    holding = 'church_holding' if kind == 'monastic' else 'castle_holding'
    lines = [f'\t# {r["name_en"]}', '\tif = {', '\t\tlimit = {',
             f'\t\t\tNOT = {{ has_global_variable = {scope}_created }}',
             f'\t\t\ttitle:{r["capital"]} = {{', '\t\t\t\texists = county.holder',
             '\t\t\t\tis_under_holy_order_lease = no',
             '\t\t\t\ttitle_province = { is_county_capital = no }', '\t\t\t}']
    if r['title']:
        lines += [f'\t\t\tNOT = {{ exists = title:{r["title"]}.holder }}']
    lines += ['\t\t}']
    if r['existing_leader']:
        # Reuse the exact imported 1337 character; no duplicate historical person.
        lines += ['\t\tif = {', f'\t\t\tlimit = {{ exists = character:{r["existing_leader"]} character:{r["existing_leader"]} = {{ is_alive = yes }} }}',
                  f'\t\t\tcharacter:{r["existing_leader"]} = {{ save_scope_as = {leader} }}',
                  '\t\t}', '\t\telse = {']
        indent = '\t\t\t'
    else:
        indent = '\t\t'
    lines += [indent + 'create_character = {', indent + '\tage = 45',
              indent + f'\tgender = {r["gender"]}', indent + '\tdynasty = none',
              indent + '\trandom_traits = yes', indent + f'\tfaith = rite:{r["rite"]}.faith',
              indent + f'\trite = rite:{r["rite"]}', indent + f'\tculture = culture:{r["culture"]}',
              indent + f'\tlocation = title:{r["capital"]}.title_province',
              indent + f'\ttrait = {trait}', indent + '\ttrait = celibate',
              indent + '\ttrait = ' + ('education_learning_3' if kind == 'monastic' else 'education_martial_3'),
              indent + f'\tsave_scope_as = {leader}', indent + '}']
    if r['existing_leader']:
        lines += ['\t\t}']
    if r.get('leader_name_key'):
        # The source imports only given names; retain identity and display the full name.
        lines += [f'\t\tscope:{leader} = {{ change_first_name = {r["leader_name_key"]} }}']
    if r.get('integrate_hospitaller'):
        # An already-landed grandmaster cannot found a lease to himself as leader.
        # Create the order with an unlanded acting head, then use vanilla's
        # title-transfer procedure to install the existing 1337 grandmaster.
        lines += ['\t\tcreate_character = {', '\t\t\tage = 45', '\t\t\tgender = male',
                  '\t\t\tdynasty = none', '\t\t\trandom_traits = yes',
                  '\t\t\tfaith = rite:roman_rite.faith', '\t\t\trite = rite:roman_rite',
                  '\t\t\tculture = culture:occitan', '\t\t\tlocation = title:b_kos.title_province',
                  '\t\t\ttrait = order_member', '\t\t\ttrait = celibate',
                  '\t\t\ttrait = education_martial_3', '\t\t\tsave_scope_as = eu5_1337_hospitaller_acting_leader',
                  '\t\t}']
    founding_leader = 'eu5_1337_hospitaller_acting_leader' if r.get('integrate_hospitaller') else leader
    lines += ['\t\teu5_1337_found_order_effect = {',
              f'\t\t\tLEADER = scope:{founding_leader}', f'\t\t\tCAPITAL = {r["capital"]}',
              f'\t\t\tTYPE = {r["type_key"]}', f'\t\t\tHOLDING = {holding}',
              f'\t\t\tSTARTUP_FLAG = {"monastic_game_start_founder" if kind == "monastic" else "military_order_game_start_founder"}',
              f'\t\t\tORDER_SCOPE = {scope}', f'\t\t\tFLAG = {scope}_created',
              f'\t\t\tTRAIT = {trait}', '\t\t}']
    if n in (1, 6):
        lines += [f'\t\tif = {{ limit = {{ exists = scope:{scope} }} scope:{scope} = {{ set_order_rite = rite:roman_rite }} }}']
    if n in ORDER_TENETS:
        lines += [f'\t\tif = {{ limit = {{ exists = scope:{scope} }} scope:{scope} = {{ set_order_tenet = tenet:tenet_{ORDER_TENETS[n]} }} }}']
    if r.get('integrate_hospitaller'):
        lines += ['\t\tif = {', f'\t\t\tlimit = {{ exists = scope:{scope} scope:{leader} = {{ has_title = title:c_rodos }} }}',
                  f'\t\t\tscope:{scope}.leader.primary_title = {{',
                  '\t\t\t\tcreate_title_and_vassal_change = { type = granted save_scope_as = eu5_1337_hospitaller_transfer add_claim_on_loss = no }',
                  f'\t\t\t\tchange_title_holder_include_vassals = {{ holder = scope:{leader} change = scope:eu5_1337_hospitaller_transfer }}',
                  '\t\t\t\tresolve_title_and_vassal_change = scope:eu5_1337_hospitaller_transfer',
                  '\t\t\t}',
                  f'\t\t\tscope:{leader} = {{',
                  '\t\t\t\tchange_government = ecclesiastical_government',
                  '\t\t\t\tset_primary_title_to = title:d_eu5_kni', '\t\t\t}',
                  '\t\t\ttitle:d_eu5_kni = { set_always_follows_primary_heir = yes }', '\t\t}']
    for b in r['branches']:
        lines += [f'\t\teu5_1337_lease_order_branch_effect = {{ BARONY = {b} ORDER = scope:{scope} HOLDING = {holding} }}']
    lines += ['\t}', '']
    return '\n'.join(lines)


OLD = '''\t\tif = {
\t\t\tlimit = {
\t\t\t\thas_pam_dlc_trigger = yes
\t\t\t}
\t\t\tset_up_historical_monastic_orders_effect = yes
\t\t}
\t\tset_up_historical_military_orders_effect = yes'''

NEW = '''\t\t# Adapt the vanilla 1178 roster to our 1337 people and map.
\t\tif = {
\t\t\tlimit = { game_start_date = 1337.4.1 current_date = 1337.4.1 }
\t\t\tif = {
\t\t\t\tlimit = { has_pam_dlc_trigger = yes }
\t\t\t\teu5_1337_historical_monastic_orders_effect = yes
\t\t\t}
\t\t\teu5_1337_historical_military_orders_effect = yes
\t\t}
\t\telse = {
\t\t\tif = {
\t\t\t\tlimit = { has_pam_dlc_trigger = yes }
\t\t\t\tset_up_historical_monastic_orders_effect = yes
\t\t\t}
\t\t\tset_up_historical_military_orders_effect = yes
\t\t}'''


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--backup', type=Path)
    args = ap.parse_args()
    data = json.loads((OUT / 'inputs/orders.json').read_text(encoding='utf-8'))
    additions = additional_products(data)
    syntax = validate(data, additions)
    effects = HELPERS
    for kind in ('monastic', 'military'):
        effects += f'eu5_1337_historical_{kind}_orders_effect = {{\n'
        effects += '\tif = {\n\t\tlimit = { game_start_date = 1337.4.1 current_date = 1337.4.1 }\n'
        if kind == 'military':
            effects += '\t\teu5_1337_setup_baltic_landed_orders_effect = yes\n'
        body = ''.join(render_order(r) for r in data['orders'] if r['ORDER_TYPE'] == kind)
        effects += '\n'.join('\t' + line if line else '' for line in body.splitlines()) + '\n\t}\n}\n\n'
    start = (ROOT / START).read_text(encoding='utf-8-sig')
    if OLD in start:
        assert start.count(OLD) == 1
        start = start.replace(OLD, NEW)
    else:
        assert start.count(NEW) == 1, 'Unexpected startup code; review before rewriting.'
    products = {EFFECT: effects, START: start, **additions}
    for rel, body in products.items():
        if rel.suffix == '.txt':
            syntax.parse(body)
    assert effects.count('holy_order_type = $TYPE$') == 1
    assert effects.count('eu5_1337_found_order_effect = {') == 51  # helper + 50 calls
    # Expanded helpers must have no unresolved parameters or invalid syntax.
    effect_nodes = dict(syntax.parse(effects)[0])
    helpers = {k: v for k, v in effect_nodes.items() if k.endswith(('_barony_effect', '_found_order_effect', '_branch_effect'))}
    def substitute(node, args):
        def replace(value):
            for name, target in args.items():
                value = value.replace('$' + name + '$', target)
            return value
        pairs, bare = node
        return ([(replace(k), substitute(v, args) if isinstance(v, tuple) else replace(v)) for k, v in pairs],
                [replace(v) for v in bare])

    def expand(node):
        pairs, bare = node
        result = []
        for key, value in pairs:
            if key in helpers:
                args = dict(value[0])
                required = set(re.findall(r'\$([A-Z_]+)\$', json.dumps(helpers[key])))
                assert set(args) == required, (key, set(args), required)
                assert not value[1] and all(isinstance(v, str) for v in args.values())
                inner = expand(substitute(helpers[key], args))
                assert not inner[1]
                result.extend(inner[0])
            else:
                result.append((key, expand(value) if isinstance(value, tuple) else value))
        return result, bare

    expanded = [expand(effect_nodes[f'eu5_1337_historical_{kind}_orders_effect']) for kind in ('monastic', 'military')]
    assert not re.search(r'\$[A-Z_]+\$', json.dumps(expanded)), 'Unexpanded script parameter'
    def count_native(node, name):
        return sum((k == name) + (count_native(v, name) if isinstance(v, tuple) else 0) for k, v in node[0])
    assert sum(count_native(n, 'create_holy_order') for n in expanded) == 50
    assert sum(count_native(n, 'lease_out_to_holy_order') for n in expanded) == 121
    assert 'character:benedictine_4' not in effects
    historical_heads = set(data['eu5_source_heads'].values()) | {'kni_helion_de_villeneuve'}
    assert set(re.findall(r'character:([\w]+)', effects)) == historical_heads
    assert effects.count('change_first_name = eu5_order_head_') == 11
    assert effects.count('set_order_tenet = tenet:tenet_') == 40
    assert 'title:b_rodos.title_province = { set_holding_type = castle_holding }' not in effects
    # Verify the startup patch touches exactly this initialization block.
    baseline_path = Path(data['backup']) / 'mod' / START
    baseline = baseline_path.read_text(encoding='utf-8-sig')
    assert start == baseline.replace(OLD, NEW)
    report = {'orders': 50, 'monastic_orders': 40, 'military_orders': 10,
              'headquarters': 50, 'branch_houses': 121, 'leased_baronies': 171,
              'female_heads': sum(r['gender'] == 'female' for r in data['orders']),
              'generated_heads': sum(not r['existing_leader'] for r in data['orders']),
              'existing_heads': sorted(historical_heads), 'eu5_documented_heads': 11,
              'new_orders_from_eu5': 6,
              'undefined_references': 0, 'duplicate_leases': 0, 'leased_county_capitals': 0,
              'in_game_tested': False, 'backup': data['backup']}
    products[Path('gen_debug/historical_orders_1337_20261105/validation.json')] = json.dumps(report, indent=2, ensure_ascii=False) + '\n'
    md = ['# 1337 修会与骑士团', '', '现有 50 个组织：40 个修会、10 个军事修会；171 处租借驻地（50 总部、121 分院）。',
          '', '在原版 1178 的 45 个组织上，按 EU5 `setup/1337/04_religious_orders.txt` 新增 6 个组织，并为文件内全部 11 个组织接入指定领导人。',
          '新增：阿尔坎塔拉、基督、蒙特萨骑士团，道明会、方济各会、奥斯定隐修会。奥斯定隐修会与现有奥斯定咏礼会分别保留；EU5 的托钵修会采用 CK3 原版方济各会/道明会使用的 monastic 机制。',
          '11 位人物均复用现有角色 ID、出生日期和能力；不复制人物。仅补充中英文全名显示。另沿用现有医院骑士团团长，剩余 39 个组织仍使用动态生成的当代首领。',
          '修会保留 PAM DLC 门槛，军事修会不要求 PAM。仅在 1337.4.1 新开局初始化，逐团有创建成功标记和重复租借防护。',
          '', '本笃会地点按地区修会和改革传统分配；萨尔茨堡、美因茨、锡洛斯复用原有修院，不再在同一伯爵领另建代理。按照 EU5 locations 为本笃会及圣地亚哥、卡拉特拉瓦、阿维什骑士团补充地产；熙笃会按 EU5 地点缩减为 10 处；完整对应见 inputs/eu5_lease_supplement_mapping.json。新增 6 个组织的 38 处驻地按 EU5 locations 映射。伊比利亚骑士团保留总部，其他伯爵领只保留 EU5 人口最多的来源地点；首府及不兼容地产使用同伯爵领代理。详见 inputs/eu5_location_mapping.json。',
          '基督和蒙特萨骑士团使用 EU5 OPX/MTS 原始十字纹理与配色，未覆盖其他纹章。',
          '医院骑士团继续保留上一轮的处理：科斯岛总部、现有罗德岛团长、教会制、保留罗德岛首府教堂。新接入的其他 11 位领导人不会执行这段罗德岛专属逻辑。',
          '圣殿骑士团于 1312 年撤销，已从 1337 开局移除；安达卢斯加齐总部迁至洛哈、分驻瓜迪克斯。',
          '', '**验证：静态语法、参数展开、头衔/礼仪/文化/人物引用、171 处非首府租借和重复项检查通过。尚未游戏内新开局/过日/存读档测试。**',
          '', f'本次备份：`{data["backup"]}`', f'前次备份：`{data["previous_backup"]}`',
          '', '| 组织 | 类型 | 领导人 | 总部地块 | 分院数 |', '|---|---|---|---|---:|']
    for r in data['orders']:
        head = r.get('leader_name_zh') or ('埃利翁·德·维尔纳夫' if r['existing_leader'] else '动态生成')
        md.append(f'| {r["name_zh"]} | {"修会" if r["ORDER_TYPE"] == "monastic" else "军事修会"} | {head} | `{r["capital"]}` | {len(r["branches"])} |')
    products[Path('gen_debug/historical_orders_1337_20261105/修会与骑士团_1337.md')] = '\n'.join(md) + '\n'
    if args.apply:
        assert args.backup and args.backup.is_dir(), '--apply requires the announced backup directory'
        assert str(args.backup.resolve()).lower().startswith('f:'), 'Backups must be on F:'
        # Verify all currently existing products before any overwrites.
        for rel in products:
            current = ROOT / rel
            if current.exists():
                saved = args.backup / 'mod' / rel
                if not saved.exists():
                    saved.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(current, saved)
                assert digest(current) == digest(saved), ('backup mismatch', rel)
        dest = ROOT
    else:
        dest = OUT / 'staged'
    for rel, body in products.items():
        p = dest / rel
        encoded = body if isinstance(body, bytes) else b'\xef\xbb\xbf' + body.replace('\r\n', '\n').replace('\n', '\r\n').encode('utf-8')
        if not p.exists() or p.read_bytes() != encoded:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(encoded)
    print(json.dumps(report, ensure_ascii=False))
    print('Applied' if args.apply else 'Staged', dest)


if __name__ == '__main__':
    main()
