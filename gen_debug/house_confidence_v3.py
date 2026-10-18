# -*- coding: utf-8 -*-
"""
最终版 v3 —— 支系关系能提升多少置信度

修正：
  1. house 匹配改用精确后缀判定（house_<parent>_<short> / house_<short>），不用相似度阈值
  2. parent 前缀用父姓（minamoto/taira/fujiwara），不是完整 key
  3. A 级拆两类：
       A1 结构对齐  : vanilla 本来就是 house 且父宗族一致 → 可无损复用 house key
       A2 同名独立  : vanilla 是独立 dynasty，但 mod 已降级为 house → 结构冲突，需裁决
"""
import os, re, json
from collections import defaultdict, Counter

VAN = r"E:/SteamLibrary/steamapps/common/Crusader Kings III/game"
BASE = os.path.dirname(os.path.abspath(__file__))

def read_text(p):
    for enc in ('utf-8-sig', 'utf-8', 'cp1252', 'latin-1'):
        try:
            return open(p, 'r', encoding=enc).read()
        except UnicodeDecodeError:
            continue
    return ''

def parse_blocks(txt, key_pat):
    res = []
    for m in re.finditer(key_pat, txt, re.M):
        i = m.end() - 1
        depth, j = 0, i
        while j < len(txt):
            if txt[j] == '{': depth += 1
            elif txt[j] == '}':
                depth -= 1
                if depth == 0: break
            j += 1
        res.append((m.group(1), txt[i:j+1]))
    return res

van_dyns = {}
for fn in os.listdir(os.path.join(VAN, 'common', 'dynasties')):
    if not fn.endswith('.txt'): continue
    txt = read_text(os.path.join(VAN, 'common', 'dynasties', fn))
    for key, body in parse_blocks(txt, r'^(\d+|[a-z_]\w*)\s*=\s*\{'):
        nm = re.search(r'\bname\s*=\s*"([^"]+)"', body)
        cu = re.search(r'\bculture\s*=\s*"?([a-z_]+)"?', body)
        van_dyns[key] = {'name': nm.group(1) if nm else '', 'culture': cu.group(1) if cu else ''}

van_houses = {}
for fn in os.listdir(os.path.join(VAN, 'common', 'dynasty_houses')):
    if not fn.endswith('.txt'): continue
    txt = read_text(os.path.join(VAN, 'common', 'dynasty_houses', fn))
    for key, body in parse_blocks(txt, r'^(house_\w+)\s*=\s*\{'):
        nm = re.search(r'\bname\s*=\s*"([^"]+)"', body)
        dy = re.search(r'\bdynasty\s*=\s*(\d+|[a-z_]\w*)', body)
        van_houses[key] = {'name': nm.group(1) if nm else '', 'parent': dy.group(1) if dy else ''}

merge_map = json.load(open(os.path.join(BASE, 'dynasty_merge_map.json'), encoding='utf-8'))['merge_map']
cc = json.load(open(os.path.join(BASE, 'dynasty_cross_check_loc.json'), encoding='utf-8'))
matches = {m['mod_dyn']: m for m in cc['matches']}

def norm(s):
    s = s.lower().replace('-', '_').replace("'", '')
    for a, b in (('ou', 'o'), ('uu', 'u'), ('oo', 'o')):
        s = s.replace(a, b)
    return s

# 索引
named_norm = defaultdict(set)
for k in van_dyns:
    if not k.isdigit():
        named_norm[norm(k)].add(k)
        if k.startswith('japanese_'):
            named_norm[norm(k[len('japanese_'):])].add(k)
house_by_tail = defaultdict(set)     # 尾段 -> houses
house_exact = set(van_houses)
for k in van_houses:
    house_by_tail[norm(k.split('_')[-1])].add(k)

def find_named_dyn(short):
    """同名独立 dynasty"""
    out = set()
    for probe in (norm(short), 'japanese_' + norm(short)):
        out |= named_norm.get(probe, set())
    return sorted(out)

def find_house(short, parent_van_keys):
    """精确 house 匹配：优先 house_<父姓>_<short>，其次 house_<short>，最后尾段匹配"""
    ns = norm(short)
    # 1) 精确 house_<short>
    if 'house_' + short in house_exact:
        return 'house_' + short, 'exact'
    # 2) house_<父姓>_<short>
    for pk in parent_van_keys:
        surname = pk.split('_')[1] if pk.startswith('japanese_') and len(pk.split('_')) > 1 else pk
        for cand in ('house_%s_%s' % (surname, short), 'house_%s_%s' % (surname, ns)):
            if cand in house_exact:
                return cand, 'parent_prefix'
    # 3) 尾段精确（house_xxx_<short>），只接受唯一或父姓匹配的
    tails = house_by_tail.get(ns, set())
    tails = {t for t in tails if norm(t.split('_')[-1]) == ns}
    if len(tails) == 1:
        return next(iter(tails)), 'tail_unique'
    if tails:
        # 多个同名 house，按父姓挑
        for pk in parent_van_keys:
            surname = pk.split('_')[1] if pk.startswith('japanese_') else pk
            for t in tails:
                if t.startswith('house_' + surname + '_'):
                    return t, 'tail_by_parent'
        return sorted(tails)[0], 'tail_ambiguous'
    return '', ''

def self_lv(m):
    if not m: return 'NONE'
    if m.get('strong_hits', 0) >= 1: return 'STRONG'
    if m.get('name_hits', 0) >= 1: return 'NAME'
    return 'WEAK'

HIST_MAP = {
    'seiwa_genji': 'japanese_minamoto_seiwa',
    'uda_genji': 'japanese_minamoto_uda',
    'saga_genji': 'japanese_minamoto_saga',
    'murakami_genji': 'japanese_minamoto_murakami',
    'taira': 'japanese_taira_kanmu',
}

parents = sorted({v['parent_dyn'] for v in merge_map.values()})
pinfo = {}
for p in parents:
    short = p[:-len('_dynasty')] if p.endswith('_dynasty') else p
    hist = HIST_MAP.get(short)
    nd = find_named_dyn(short)
    m = matches.get(p)
    num = m['van_ids'] if m else []
    keys = set()
    if hist: keys.add(hist)
    keys |= set(nd)
    keys |= set(num)
    pinfo[p] = {'parent': p, 'short': short, 'hist': hist, 'named': nd, 'num': num,
                'level': self_lv(m), 'keys': sorted(keys),
                'children': [c for c, v in merge_map.items() if v['parent_dyn'] == p]}

rows = []
for child, info in sorted(merge_map.items()):
    parent = info['parent_dyn']
    short = child[:-len('_dynasty')] if child.endswith('_dynasty') else child
    pv = pinfo[parent]
    nd = find_named_dyn(short)
    hk, how = find_house(short, pv['keys'])
    hp = van_houses[hk]['parent'] if hk else ''

    aligned = bool(hk) and hp in pv['keys']
    mismatch = bool(hk) and hp not in pv['keys']
    downgrade = bool(nd) and not hk     # vanilla 是独立 dynasty，mod 降级为 house

    rows.append({'child': child, 'short': short, 'parent': parent,
                 'self_lv': self_lv(matches.get(child)),
                 'named': nd, 'house': hk, 'house_how': how, 'house_parent': hp,
                 'aligned': aligned, 'mismatch': mismatch, 'downgrade': downgrade,
                 'parent_anchored': bool(pv['keys']), 'parent_keys': pv['keys']})

by_parent = defaultdict(list)
for r in rows: by_parent[r['parent']].append(r)
for p, sibs in by_parent.items():
    strong = [s['child'] for s in sibs if s['self_lv'] == 'STRONG']
    for r in sibs:
        r['sib_strong'] = [c for c in strong if c != r['child']]

def grade(r):
    if r['aligned']: return 'A1'
    if r['mismatch']: return 'B1'
    if r['downgrade']: return 'B2'
    if r['parent_anchored']: return 'C'
    if r['sib_strong']: return 'C'
    return 'D'
for r in rows: r['grade'] = grade(r)

out = []
def w(s=''): out.append(s)
g = Counter(r['grade'] for r in rows)
anch = [p for p in parents if pinfo[p]['keys']]

w("=" * 86)
w("支系关系能提升多少置信度 —— 最终结论")
w("=" * 86)
w(f"vanilla dynasty 总数            : {len(van_dyns)}   (japanese_* : {sum(1 for k in van_dyns if k.startswith('japanese_'))})")
w(f"vanilla house 总数              : {len(van_houses)}")
w(f"mod 被归并 child                : {len(rows)}")
w(f"mod 归并 parent                 : {len(parents)}")
w(f"parent 锚定到 vanilla           : {len(anch)} / {len(parents)}")
w()
w("【v2 原分析的盲区】272 条匹配只覆盖「数字 ID」型 dynasty；")
w("                  vanilla 日本家族全部是命名 key（japanese_*），日本系 0 覆盖。")
w()
w("【本轮新增锚定依据】")
w("  史实映射（非猜测）：")
w("    seiwa_genji_dynasty    = 清和源氏 = japanese_minamoto_seiwa")
w("    uda_genji_dynasty      = 宇多源氏 = japanese_minamoto_uda")
w("    saga_genji_dynasty     = 嵯峨源氏 = japanese_minamoto_saga")
w("    murakami_genji_dynasty = 村上源氏 = japanese_minamoto_murakami")
w("    taira_dynasty          = 平氏     = japanese_taira_kanmu（桓武平氏，最主流）")
w("  其余：vanilla 命名 key 与 mod 短名做长音规范化后精确比对")
w()

w("=" * 86)
w("【一】168 个 child 分级")
w("=" * 86)
w(f"  A1 结构对齐   : {g.get('A1',0):>3}  vanilla 本来就是 house 且父宗族一致 → 可无损复用 house key")
w(f"  B1 父宗族冲突 : {g.get('B1',0):>3}  vanilla 有同名 house，但挂在别的宗族下 → 同姓不同流，需裁决")
w(f"  B2 结构降级冲突: {g.get('B2',0):>3}  vanilla 认为它是独立 dynasty，mod 却降成了支系 → 需裁决")
w(f"  C  间接支持   : {g.get('C',0):>3}  靠 parent 锚定 / 兄弟强证据传递")
w(f"  D  无新证据   : {g.get('D',0):>3}")
w()
w(f"  → 相比 v2 原来的「强证据 8 / 中 5 / 待核 90 / 无法判定 64」口径，")
w(f"    现在有 {g.get('A1',0)+g.get('B1',0)+g.get('B2',0)} 个拿到了具体 vanilla 对应物，")
w(f"    另有 {g.get('C',0)} 个拿到间接支持。")
w()

w("=" * 86)
w("【二】A1 结构对齐（最可信，可无损复用 vanilla house key）")
w("=" * 86)
for r in sorted([x for x in rows if x['grade'] == 'A1'], key=lambda x: x['child']):
    w(f"{r['child']:<32} -> {r['house']:<30} parent={r['house_parent']}  ({r['house_how']})")
w()

w("=" * 86)
w("【三】B1 父宗族冲突：vanilla 有同名 house 但挂在别的宗族下")
w("=" * 86)
for r in sorted([x for x in rows if x['grade'] == 'B1'], key=lambda x: x['child']):
    w(f"{r['child']:<30} mod 归到 {r['parent']:<24} / vanilla 挂在 {r['house']} → {r['house_parent']}")
w()

w("=" * 86)
w("【四】B2 结构降级冲突：vanilla 是独立 dynasty，mod 已降成支系")
w("=" * 86)
for r in sorted([x for x in rows if x['grade'] == 'B2'], key=lambda x: x['child']):
    dn = van_dyns.get(r['named'][0], {}).get('name', '') if r['named'] else ''
    w(f"{r['child']:<30} mod 归到 {r['parent']:<24} / vanilla 独立 dynasty = {','.join(r['named'])} ({dn})")
w()

w("=" * 86)
w("【五】C 间接支持")
w("=" * 86)
for r in sorted([x for x in rows if x['grade'] == 'C'], key=lambda x: (x['parent'], x['child'])):
    why = []
    if r['parent_anchored']: why.append('父=' + ','.join(r['parent_keys']))
    if r['sib_strong']: why.append('兄弟强证=' + ','.join(r['sib_strong'][:2]))
    w(f"{r['child']:<30} -> {r['parent']:<24} {' | '.join(why)}")
w()

w("=" * 86)
w(f"【六】D 无新证据 {g.get('D',0)} 个")
w("=" * 86)
for r in sorted([x for x in rows if x['grade'] == 'D'], key=lambda x: (x['parent'], x['child'])):
    w(f"{r['child']:<30} -> {r['parent']}")
w()

w("=" * 86)
w("【七】42 个 parent 宗族锚定明细")
w("=" * 86)
for p in sorted(parents, key=lambda x: (-len(pinfo[x]['children']), x)):
    d = pinfo[p]
    how = []
    if d['hist']: how.append('史实')
    if d['named'] and not d['hist']: how.append('key同名')
    if d['num']: how.append('v2数字ID')
    w(f"{'OK' if d['keys'] else '--'} {p:<30} 支系={len(d['children']):<3} {'/'.join(how) or '-':<16} {','.join(d['keys']) or '-'}")
w()

open(os.path.join(BASE, 'house_confidence_v3.txt'), 'w', encoding='utf-8').write('\n'.join(out))
json.dump({'children': rows, 'parents': list(pinfo.values())},
          open(os.path.join(BASE, 'house_confidence_v3.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f"anch={len(anch)}/{len(parents)}  A1={g.get('A1',0)} B1={g.get('B1',0)} B2={g.get('B2',0)} C={g.get('C',0)} D={g.get('D',0)}")
