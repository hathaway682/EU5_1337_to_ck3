# -*- coding: utf-8 -*-
"""按地形/史实重新分配美洲-大洋洲文化的三个传统槽位。
只重写 traditions = { } 块，不动其它字段。默认 dry run。
"""
import re, sys, io, os, collections

FILES = [
    'common/culture/cultures/zz_eu5_culture_americas.txt',
    'common/culture/cultures/zz_eu5_culture_group.txt',
    'common/culture/cultures/zz_eu5_culture_new.txt',
]

# culture -> [3 条 tradition]
NEW = {
    # ---- 北美东部林地 ----
    'abenakian':      ['tradition_forest_folk', 'tradition_gardening', 'tradition_esteemed_hospitality'],
    'anishinabe':     ['tradition_forest_folk', 'tradition_medicinal_plants', 'tradition_storytellers'],
    'massachusett':   ['tradition_collective_lands', 'tradition_charitable', 'tradition_forest_folk'],
    'lenape':         ['tradition_forest_folk', 'tradition_welcoming', 'tradition_collective_lands'],
    'myaamia':        ['tradition_forest_folk', 'tradition_equitable', 'tradition_collective_lands'],
    'shawnee':        ['tradition_forest_fighters', 'tradition_loyal_soldiers', 'tradition_collective_lands'],
    'powhatan':       ['tradition_wetlanders', 'tradition_staunch_traditionalists', 'tradition_tribe_unity'],
    # ---- 东南密西西比 ----
    'chickasaw_choctaw': ['tradition_tribe_unity', 'tradition_ruling_caste', 'tradition_esteemed_hospitality'],
    'chitimacha':     ['tradition_wetlanders', 'tradition_storytellers', 'tradition_brewery'],
    'timucua':        ['tradition_wetlanders', 'tradition_ruling_caste', 'tradition_gardening'],
    'atakapa':        ['tradition_wetlanders', 'tradition_sacred_hunts', 'tradition_medicinal_plants'],
    # ---- 大平原 / 草原 ----
    'caddoan':        ['tradition_tribe_unity', 'tradition_astute_diplomats', 'tradition_agrarian'],
    'dakota':         ['tradition_tribe_unity', 'tradition_forest_fighters', 'tradition_battlefield_looters'],
    'dhegiha':        ['tradition_horse_breeder', 'tradition_hard_working', 'tradition_warriors_by_merit'],
    'chiwere':        ['tradition_pastoralists', 'tradition_brewery', 'tradition_warriors_by_merit'],
    # ---- 大盆地 / 高原 ----
    'shoshoni':       ['tradition_hunters', 'tradition_dryland_dwellers', 'tradition_forbearing'],
    'nuuchi_nuwu':    ['tradition_hunters', 'tradition_dryland_dwellers', 'tradition_mountain_homes'],
    'ktunaxa':        ['tradition_hunters', 'tradition_mountain_homes', 'tradition_strength_in_numbers'],
    'coahuilteco':    ['tradition_hunters', 'tradition_pastoralists', 'tradition_forbearing'],
    # ---- 加州 / 太平洋西北 ----
    'malibu':         ['tradition_seafaring', 'tradition_storytellers', 'tradition_sacred_groves'],
    'chumashan':      ['tradition_fishermen', 'tradition_seafaring', 'tradition_maritime_mercantilism'],
    'salishan':       ['tradition_fishermen', 'tradition_hill_dwellers', 'tradition_seafaring'],
    'tsimshian':      ['tradition_fishermen', 'tradition_seafaring', 'tradition_artisans'],
    'wakashan':       ['tradition_fishermen', 'tradition_seafaring', 'tradition_artisans'],
    'penutian':       ['tradition_hill_dwellers', 'tradition_storytellers', 'tradition_sacred_groves'],
    'seeptsa':        ['tradition_hill_dwellers', 'tradition_language_scholars', 'tradition_sacred_groves'],
    'takic':          ['tradition_mountain_homes', 'tradition_sacred_groves', 'tradition_isolationist'],
    'hokan':          ['tradition_hill_dwellers', 'tradition_gardening', 'tradition_warriors_of_the_dry'],
    # ---- 西南 ----
    'tanoan':         ['tradition_city_keepers', 'tradition_agrarian', 'tradition_hard_working'],
    # ---- 极北 ----
    'inuit':          ['tradition_hunters', 'tradition_fishermen', 'tradition_seafaring'],
    'yupik':          ['tradition_fishermen', 'tradition_seafaring', 'tradition_festivities'],
    'cree':           ['tradition_hunters', 'tradition_forest_folk', 'tradition_winter_warriors'],
    'nadene':         ['tradition_hunters', 'tradition_forest_folk', 'tradition_winter_warriors'],
    'tshon':          ['tradition_hunters', 'tradition_dryland_dwellers', 'tradition_winter_warriors'],
    # ---- 安第斯 ----
    'quechuan':       ['tradition_RICE_andean_hydraulic_engineering', 'tradition_mountain_homes', 'tradition_pastoralists'],
    'aymara':         ['tradition_RICE_andean_hydraulic_engineering', 'tradition_mountain_homes', 'tradition_pastoralists'],
    'pukina':         ['tradition_RICE_andean_hydraulic_engineering', 'tradition_mountain_homes', 'tradition_dryland_dwellers'],
    'ckunsa':         ['tradition_dryland_dwellers', 'tradition_RICE_andean_hydraulic_engineering', 'tradition_mountain_homes'],
    'cuicas':         ['tradition_hard_working', 'tradition_highland_warriors', 'tradition_artisans'],
    'chicham':        ['tradition_jungle_warriors', 'tradition_mountain_homes', 'tradition_only_the_strong'],
    # ---- 中美洲 ----
    'eastern_otomanguean': ['tradition_mountain_homes', 'tradition_artisans', 'tradition_festivities'],
    'otopamean':      ['tradition_hill_dwellers', 'tradition_artisans', 'tradition_religious_patronage'],
    'cuitlatec':      ['tradition_mountain_homes', 'tradition_culinary_art', 'tradition_hard_working'],
    'totozoquean':    ['tradition_hill_dwellers', 'tradition_hereditary_hierarchy', 'tradition_fervent_temple_builders'],
    'misumalpan':     ['tradition_hill_dwellers', 'tradition_artisans', 'tradition_wetlanders'],
    'chibchan':       ['tradition_hill_dwellers', 'tradition_ruling_caste', 'tradition_metal_craftsmanship'],
    # ---- 加勒比 / 南美北部 ----
    'caribe':         ['tradition_jungle_warriors', 'tradition_warrior_culture', 'tradition_quarrelsome'],
    'tayrona':        ['tradition_hill_dwellers', 'tradition_city_keepers', 'tradition_metal_craftsmanship'],
    'jirajaran':      ['tradition_hill_dwellers', 'tradition_modest', 'tradition_hard_working'],
    'cacan':          ['tradition_hill_dwellers', 'tradition_ancient_miners', 'tradition_metal_craftsmanship'],
    'calima':         ['tradition_mountain_homes', 'tradition_artisans', 'tradition_ruling_caste'],
    'panche':         ['tradition_mountain_homes', 'tradition_only_the_strong', 'tradition_metal_craftsmanship'],
    'pijao':          ['tradition_mountain_homes', 'tradition_warriors_by_merit', 'tradition_quarrelsome'],
    'sinu':           ['tradition_metal_craftsmanship', 'tradition_fortune_seekers', 'tradition_wetlanders'],
    'choco':          ['tradition_jungle_dwellers', 'tradition_music_theory', 'tradition_medicinal_plants'],
    'guahibo':        ['tradition_pastoralists', 'tradition_modest', 'tradition_battlefield_looters'],
    'warao':          ['tradition_fishermen', 'tradition_wetlanders', 'tradition_medicinal_plants'],
    'ta_arawakan':    ['tradition_gardening', 'tradition_xenophilic', 'tradition_maritime_mercantilism'],
    'besiro':         ['tradition_forest_fighters', 'tradition_gardening', 'tradition_isolationist'],
    'atallan':        ['tradition_seafaring', 'tradition_maritime_mercantilism', 'tradition_fortune_seekers'],
    'barbakoan':      ['tradition_artisans', 'tradition_hard_working', 'tradition_highland_warriors'],
    # ---- 亚马逊 ----
    'macro_je':       ['tradition_hill_dwellers', 'tradition_sacred_groves', 'tradition_forest_fighters'],
    'tupi':           ['tradition_jungle_warriors', 'tradition_sacred_groves', 'tradition_gardening'],
    'tucanoan':       ['tradition_jungle_dwellers', 'tradition_medicinal_plants', 'tradition_brewery'],
    'txapakura':      ['tradition_jungle_dwellers', 'tradition_isolationist', 'tradition_forest_fighters'],
    'napuruna':       ['tradition_jungle_dwellers', 'tradition_isolationist', 'tradition_medicinal_plants'],
    'movima':         ['tradition_wetlanders', 'tradition_gardening', 'tradition_artisans'],
    'tarairiu':       ['tradition_pastoralists', 'tradition_isolationist', 'tradition_battlefield_looters'],
    'pume':           ['tradition_pastoralists', 'tradition_modest', 'tradition_forest_folk'],
    'zamuco':         ['tradition_hunters', 'tradition_forest_folk', 'tradition_isolationist'],
    # ---- 南锥体 ----
    'charrua':        ['tradition_hunters', 'tradition_pastoralists', 'tradition_stalwart_defenders'],
    'mataco_guaicuru': ['tradition_hunters', 'tradition_pastoralists', 'tradition_sacred_hunts'],
    'warpe':          ['tradition_pastoralists', 'tradition_gardening', 'tradition_hard_working'],
    'henia_kamiare':  ['tradition_gardening', 'tradition_pastoralists', 'tradition_artisans'],
    'waqha':          ['tradition_brewery', 'tradition_pastoralists', 'tradition_hard_working'],
    'chono':          ['tradition_fishermen', 'tradition_seafaring', 'tradition_isolationist'],
    'kawesqar':       ['tradition_fishermen', 'tradition_seafaring', 'tradition_modest'],
    'yaghan':         ['tradition_fishermen', 'tradition_seafaring', 'tradition_isolationist'],
    'muchik':         ['tradition_fishermen', 'tradition_city_keepers', 'tradition_legalistic'],
    'quingnam':       ['tradition_fishermen', 'tradition_city_keepers', 'tradition_artisans'],
    # ---- 北美东岸留用 / 其它 ----
    'haudenosaunee':  ['tradition_tribe_unity', 'tradition_collective_lands', 'tradition_astute_diplomats'],
    'iroquoian':      ['tradition_warriors_by_merit', 'tradition_collective_lands', 'tradition_tribe_unity'],
    'wendat':         ['tradition_ruling_caste', 'tradition_tribe_unity', 'tradition_hereditary_hierarchy'],
    'skarureh':       ['tradition_tribe_unity', 'tradition_forest_fighters', 'tradition_strength_in_numbers'],
    'muskogee':       ['tradition_tribe_unity', 'tradition_ruling_caste', 'tradition_festivities'],
    'natchez':        ['tradition_tribe_unity', 'tradition_ruling_caste', 'tradition_mystical_ancestors'],
    'tutelo':         ['tradition_hill_dwellers', 'tradition_gardening', 'tradition_binding_oaths'],
    'mapudungun':     ['tradition_forest_fighters', 'tradition_tribe_unity', 'tradition_stalwart_defenders'],
    'puebloan':       ['tradition_city_keepers', 'tradition_artisans', 'tradition_parochialism'],
    # ---- 大洋洲 ----
    'polynesian':     ['tradition_fishermen', 'tradition_maritime_way_of_life', 'tradition_ruling_caste'],
    'micronesian':    ['tradition_fishermen', 'tradition_maritime_way_of_life', 'tradition_artisans'],
    # ---- 非洲新文化 ----
}

# 明确不改的文化（保持原样，仅用于统计对照）
KEEP_AS_IS = {
    'apsaalooke_hiraaca', 'hinonoeitiit', 'siksika', 'tsehesenestsestotse',
    'paiute', 'puebloan', 'purepecha', 'nahua', 'maya', 'yutonahua',
    'otopamean2', 'chumashan2',
}


def blocks(txt):
    for m in re.finditer(r'^([a-z0-9_]+)\s*=\s*\{', txt, re.M):
        c = m.group(1); i = m.start(); d = 0; j = i
        while j < len(txt):
            if txt[j] == '{': d += 1
            elif txt[j] == '}':
                d -= 1
                if d == 0: break
            j += 1
        yield c, i, j + 1


def main():
    apply = '--apply' in sys.argv
    total_before = collections.Counter()
    total_after = collections.Counter()
    changes = []
    seen = set()

    for f in FILES:
        raw = open(f, 'rb').read()
        txt = raw.decode('utf-8-sig')
        bom = raw.startswith(b'\xef\xbb\xbf')
        crlf = b'\r\n' in raw
        nl = '\r\n' if crlf else '\n'

        # 收集原始传统
        cur = {}
        spans = {}
        for c, i, j in blocks(txt):
            blk = txt[i:j]
            tm = re.search(r'traditions\s*=\s*\{([^}]*)\}', blk)
            if not tm:
                continue
            trs = re.findall(r'(?:tradition_|tgp_|RICE_)[A-Za-z0-9_]+', tm.group(1))
            cur[c] = trs
            spans[c] = (i + tm.start(), i + tm.end())

        edits = []
        for c, old in cur.items():
            total_before.update(old)
            new = NEW.get(c)
            if new is None:
                total_after.update(old)
                continue
            seen.add(c)
            total_after.update(new)
            if old == new:
                continue
            changes.append((os.path.basename(f), c, old, new))
            if apply:
                a, b = spans[c]
                body = ''.join('\t\t%s%s' % (t, nl) for t in new)
                edits.append((a, b, 'traditions = {' + nl + body + '\t}'))
        # 从后往前替换，避免前面的长度变化导致后面的偏移失效
        for a, b, rep in sorted(edits, key=lambda x: -x[0]):
            txt = txt[:a] + rep + txt[b:]

        if apply:
            out = txt.encode('utf-8')
            if bom:
                out = b'\xef\xbb\xbf' + out
            tmp = f + '.tmp'
            with open(tmp, 'wb') as fh:
                fh.write(out)
            os.replace(tmp, f)

    for f, c, old, new in changes:
        print('%-28s %-34s -> %s' % (c, ','.join(x.replace('tradition_', '') for x in old),
                                     ','.join(x.replace('tradition_', '') for x in new)))
    print('\n改动文化数:', len(changes), '| 表中未命中的文化:', sorted(set(NEW) - seen))

    print('\n=== 频次对照 ===')
    keys = ['tribe_unity', 'hunters', 'fishermen', 'hill_dwellers', 'mountain_homes', 'strong_kinship']
    for k in keys:
        b = total_before['tradition_' + k]; a = total_after['tradition_' + k]
        print('%-18s %3d -> %3d' % (k, b, a))
    print('\n=== 新高频(>5) ===')
    for k, v in total_after.most_common(20):
        print('%-46s %d' % (k, v))
    print('\napply =', apply)


main()
