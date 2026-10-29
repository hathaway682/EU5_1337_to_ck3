# -*- coding: utf-8 -*-
"""一次性播种 gen_debug/_title_overrides.csv（人工决定表）。

播种完之后这张表**归手工维护**，不要再跑这个脚本覆盖它——
它是把散落在各处的既有决定（原版 key 映射、贝伊国、18 个单伯爵领公国、
SWB、荷尔斯泰因/丹麦、神罗同名首府）搬进一张表的搬运工，不是生成器。

只读源：
  gen_debug/eu5_ck3_title_map.csv        —— 当前 ck3_key，用来反查 tag
  history/titles/zz_eu5_titles.txt       —— 当前 1337.4.1 的 holder/gov/liege（回滚后的好状态）
  gen_debug/_apply_vanilla_keys.py       —— 原版 key 映射（只读它的 MAP，不执行）
  gen_debug/_upgrade_beyliks_csv.py      —— 9 个贝伊国（同上）
"""
import ast
import csv
import io
import os
import re

MOD = r'D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape'
CSV_IN = os.path.join(MOD, 'gen_debug', 'eu5_ck3_title_map.csv')
CSV_OUT = os.path.join(MOD, 'gen_debug', '_title_overrides.csv')
HT = os.path.join(MOD, 'history', 'titles', 'zz_eu5_titles.txt')


def literal(path, name):
    """只取脚本里的字面量常量，不 import、不执行。"""
    tree = ast.parse(io.open(path, encoding='utf-8-sig').read())
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == name:
                    return ast.literal_eval(node.value)
    raise SystemExit('!! %s 里找不到 %s' % (path, name))


def county_state(key):
    """zz_eu5_titles.txt 里该 key 的 1337.4.1 holder / government / liege。"""
    t = io.open(HT, encoding='utf-8-sig', newline='').read()
    m = re.search(r'(?m)^%s = \{' % key, t)
    if not m:
        return None, None, None
    j, d = m.end(), 1
    while j < len(t) and d:
        if t[j] == '{':
            d += 1
        elif t[j] == '}':
            d -= 1
        j += 1
    segs = re.findall(r'1337\.4\.1\s*=\s*\{([^}]*)\}', t[m.start():j])
    if not segs:
        return None, None, None
    s = segs[-1]
    g = lambda f: (re.search(r'%s\s*=\s*(\S+)' % f, s) or [None, None])[1]
    return g('holder'), g('government'), g('liege')


rows = []
add = lambda scope, key, field, value, note: rows.append(
    {'scope': scope, 'key': key, 'field': field, 'value': value, 'note': note})

# ---------------------------------------------------------------- 1. country / title_key
VANILLA = literal(os.path.join(MOD, 'gen_debug', '_apply_vanilla_keys.py'), 'MAP')
BEYLIK = literal(os.path.join(MOD, 'gen_debug', '_upgrade_beyliks_csv.py'), 'BEY')

csv_rows = list(csv.DictReader(io.open(CSV_IN, encoding='utf-8-sig')))
by_key = {}
for r in csv_rows:
    if r['kind'] == 'country' and r['ck3_key']:
        by_key.setdefault(r['ck3_key'], r['eu5_tag'])

NOTE_A = '原版同名，改挂原版 key'
NOTE_B = '同一实体、名字不同，改挂原版 key'
A_CLASS = ['e_eu5_chi', 'k_eu5_dan', 'k_eu5_yem', 'e_eu5_bul', 'k_eu5_cro', 'e_eu5_kbo',
           'k_eu5_hun', 'k_eu5_cha', 'k_eu5_cas', 'k_eu5_tib', 'k_eu5_mam', 'k_eu5_ser',
           'k_eu5_cyp', 'k_eu5_dai', 'k_eu5_chg', 'k_eu5_vlr', 'k_eu5_dlh', 'k_eu5_nor',
           'e_eu5_jap', 'k_eu5_geo', 'k_eu5_fra', 'k_eu5_pol', 'k_eu5_boh', 'k_eu5_maj',
           'e_eu5_tre', 'k_eu5_swe', 'k_eu5_nav', 'k_eu5_sco', 'k_eu5_eng', 'k_eu5_por',
           'k_eu5_sic', 'k_eu5_nap', 'k_eu5_ara', 'k_eu5_aju', 'e_eu5_mal']
B_CLASS = ['e_eu5_eth', 'e_eu5_byz', 'k_eu5_mor', 'k_eu5_jmb', 'k_eu5_kor', 'k_eu5_qch',
           'e_eu5_khm']

missing = []
for old, note in ([(k, NOTE_A) for k in A_CLASS] + [(k, NOTE_B) for k in B_CLASS]
                  + [('k_eu5_glh', '用户指定：术赤 = 金帐')]):
    new = VANILLA[old]
    tag = by_key.get(new)
    if not tag:
        missing.append((old, new))
        continue
    add('country', tag, 'title_key', new, '%s（原 %s）' % (note, old))
for tag, (old, new) in sorted(BEYLIK.items()):
    add('country', tag, 'title_key', new, '贝伊国升王国级（原 %s）' % old)
if missing:
    print('!! 反查不到 tag 的原版 key:', missing)

# ---------------------------------------------------------------- 2. country / liege
# 单伯爵领公国保不保留不在这张表里：`_fix_politics_output.py` 的降级判据已改成「liege 是同级头衔才降」，
# 18 个公国自动保住。这里只有 SWB 一条——它挂的是马格德堡公国，而 10-22 的 politics 把关系的
# `liege_title` 丢了，只剩 `type = hre`，重算会算成 liege 直接是神罗，同级判据就判不出来。
add('country', 'SWB', 'liege', 'd_eu5_mag',
    '10-22 politics 丢了 liege_title；c_flaming 实际的 liege 是马格德堡公国（用户决定 2026-10-28）')

# ---------------------------------------------------------------- 3. county / barony 覆盖
OVERRIDES = [
    ('county', 'c_holstein', 'holder', 'shl_gerhard_iii_holstein_rendsburg',
     '用户决定 2026-10-20：荷尔斯泰因改附丹麦，伯爵领归 Gerhard III'),
    ('county', 'c_holstein', 'liege', 'k_denmark', '同上：liege 由 e_hre 改丹麦（DAN 的 key 已是原版 k_denmark）'),
    ('barony', 'b_kiel', 'holder', 'shl_johann_iii_holstein_kiel', '同上：基尔降为男爵'),
    ('county', 'c_hanover', 'holder', 'bru_otto_i_braunschweig_gottingen',
     '神罗同名首府 hildesheim→hanover，县随首府走（HDH→BRU）'),
    ('county', 'c_hanover', 'government', 'feudal_government', '同上：教权转封建'),
    ('county', 'c_lippe', 'holder', 'pdb_bernhard_v',
     '神罗同名首府 soest→paderborn，县随首府走（KOL→PDB）'),
    ('county', 'c_lippe', 'government', 'theocracy_government',
     '同上：首府 paderborn 是帕德博恩主教区，政体跟首府持有者（PDB 是 theocracy），'
     '不跟县在 politics 里的 owner（LPP 是世俗的利珀）'),
]
for scope, key, field, value, note in OVERRIDES:
    h, g, l = county_state(key)
    cur = {'holder': h, 'government': g, 'liege': l}[field]
    if cur != value:
        print('!! %s 当前 %s=%s，表里写 %s' % (key, field, cur, value))
    add(scope, key, field, value, note)

# ---------------------------------------------------------------- 写出
with io.open(CSV_OUT, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['scope', 'key', 'field', 'value', 'note'],
                       lineterminator='\r\n')
    w.writeheader()
    w.writerows(rows)
print('写出 %s：%d 行（country %d / title %d / county %d / barony %d）' % (
    CSV_OUT, len(rows),
    sum(1 for r in rows if r['scope'] == 'country'),
    sum(1 for r in rows if r['scope'] == 'title'),
    sum(1 for r in rows if r['scope'] == 'county'),
    sum(1 for r in rows if r['scope'] == 'barony')))
