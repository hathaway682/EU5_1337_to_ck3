# -*- coding: utf-8 -*-
"""
最终版 v2：加入日本史实确定的源氏/平氏映射 + 相似度打分

确定映射（基于日本史实，非猜测）：
  X_genji = X 天皇后裔的源氏（Minamoto）
    seiwa_genji    = 清和源氏 = Seiwa Genji
    uda_genji      = 宇多源氏 = Uda Genji
    saga_genji     = 嵯峨源氏 = Saga Genji
    murakami_genji = 村上源氏 = Murakami Genji
  taira = 平氏 = Taira（mod 仅一个 taira，对应最主流的桓武平氏 Kanmu Heishi）
"""
import os, re, json, difflib
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
        van_dyns[key] = {'name': nm.group(1) if nm else '', 'file': fn}

van_houses = {}
for fn in os.listdir(os.path.join(VAN, 'common', 'dynasty_houses')):
    if not fn.endswith('.txt'): continue
    txt = read_text(os.path.join(VAN, 'common', 'dynasty_houses', fn))
    for key, body in parse_blocks(txt, r'^(house_\w+)\s*=\s*\{'):
        nm = re.search(r'\bname\s*=\s*"([^"]+)"', body)
        dy = re.search(r'\bdynasty\s*=\s*(\d+|[a-z_]\w*)', body)
        van_houses[key] = {'name': nm.group(1) if nm else '', 'parent': dy.group(1) if dy else '', 'file': fn}

merge_map = json.load(open(os.path.join(BASE, 'dynasty_merge_map.json'), encoding='utf-8'))['merge_map']
cc = json.load(open(os.path.join(BASE, 'dynasty_cross_check_loc.json'), encoding='utf-8'))
matches = {m['mod_dyn']: m for m in cc['matches']}

def variants(s):
    """生成拼写变体（长音 ou/uu/oo 的多种写法）"""
    s = s.lower().replace('-', '_').replace("'", '')
    vs = {s}
    for a, b in (('ou', 'o'), ('uu', 'u'), ('oo', 'o'), ('oh', 'o'), ('ū', 'u'), ('ō', 'o')):
        vs |= {x.replace(a, b) for x in list(vs)}
    return vs

# vanilla 索引：变体 -> key
dyn_index = defaultdict(set)
for k in van_dyns:
    if k.isdigit(): continue
    for v in variants(k):
        dyn_index[v].add(k)
house_index = defaultdict(set)
house_suffix = defaultdict(set)
for k in van_houses:
    s = k[len('house_'):]
    for v in variants(s):
        house_index[v].add(k)
    for v in variants(s.split('_')[-1]):
        house_suffix[v].add(k)

def best(cands, target):
    """按相似度取最优"""
    if not cands: return None, 0.0
    scored = sorted(((difflib.SequenceMatcher(None, target, c).ratio(), c) for c in cands), reverse=True)
    return scored[0][1], scored[0][0]

def find_dyn(short):
    cands = set()
    for v in variants(short):
        for probe in ('japanese_' + v, v):
            cands |= dyn_index.get(probe, set())
    if not cands: return None, 0.0
    return best(cands, 'japanese_' + short)

def find_house(short, parent_van_keys=()):
    cands = set()
    for v in variants(short):
        cands |= house_index.get(v, set())
        cands |= house_suffix.get(v, set())
    # parent 前缀优先
    pref = set()
    for pk in parent_van_keys:
        ps = pk[len('japanese_'):] if pk.startswith('japanese_') else pk
        for v in variants(short):
            for k in house_suffix.get(v, set()):
                if k.startswith('house_' + ps + '_'):
                    pref.add(k)
    if pref:
        return best(pref, 'house_' + short)
    return best(cands, 'house_' + short)

def self_lv(m):
    if not m: return 'NONE'
    if m.get('strong_hits', 0) >= 1: return 'STRONG'
    if m.get('name_hits', 0) >= 1: return 'NAME'
    return 'WEAK'

# 日本史实确定映射
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
    k, sc = find_dyn(short)
    hist = HIST_MAP.get(short)
    m = matches.get(p)
    num = m['van_ids'] if m else []
    keys = set()
    if hist: keys.add(hist)
    if k and sc >= 0.85: keys.add(k)
    keys |= set(num)
    pinfo[p] = {'parent': p, 'short': short, 'found': k, 'score': round(sc, 2),
                'hist': hist, 'num': num, 'level': self_lv(m),
                'keys': sorted(keys),
                'children': [c for c, v in merge_map.items() if v['parent_dyn'] == p]}

rows = []
for child, info in sorted(merge_map.items()):
    parent = info['parent_dyn']
    short = child[:-len('_dynasty')] if child.endswith('_dynasty') else child
    pv = pinfo[parent]
    dk, dsc = find_dyn(short)
    hk, hsc = find_house(short, pv['keys'])

    named_ok = bool(dk) and dsc >= 0.85
    house_ok = bool(hk) and hsc >= 0.80
    house_parent = van_houses[hk]['parent'] if house_ok else ''
    s1 = house_ok and house_parent in pv['keys']
    s2 = house_ok and house_parent not in pv['keys']

    rows.append({'child': child, 'short': short, 'parent': parent,
                 'self_lv': self_lv(matches.get(child)),
                 'named': dk if named_ok else '', 'named_score': round(dsc, 2),
                 'house': hk if house_ok else '', 'house_score': round(hsc, 2),
                 'house_parent': house_parent,
                 'S1': s1, 'S2': s2,
                 'parent_anchored': bool(pv['keys']),
                 'parent_keys': pv['keys']})

by_parent = defaultdict(list)
for r in rows: by_parent[r['parent']].append(r)
for p, sibs in by_parent.items():
    strong = [s['child'] for s in sibs if s['self_lv'] == 'STRONG']
    for r in sibs:
        r['sib_strong'] = [c for c in strong if c != r['child']]

def grade(r):
    if r['S1']: return 'A'
    if r['named'] and r['parent_anchored']: return 'A'
    if r['S2']: return 'B'
    if r['parent_anchored']: return 'C'
    if r['sib_strong']: return 'C'
    return 'D'
for r in rows: r['grade'] = grade(r)

out = []
def w(s=''): out.append(s)
g = Counter(r['grade'] for r in rows)
anch = [p for p in parents if pinfo[p]['keys']]

w("=" * 84)
w("家族复用置信度全景 v2（补齐 vanilla 命名 key + 日本史实映射）")
w("=" * 84)
w(f"vanilla dynasty 总数        : {len(van_dyns)}  (其中 japanese_* : {sum(1 for k in van_dyns if k.startswith('japanese_'))})")
w(f"vanilla house 总数          : {len(van_houses)}")
w(f"mod 被归并 child            : {len(rows)}")
w(f"mod 归并 parent             : {len(parents)}")
w(f"parent 能锚定到 vanilla     : {len(anch)} / {len(parents)}")
w()
w("【v2 原分析的盲区】272 条匹配只覆盖数字 ID 型 dynasty；")
w("                  vanilla 的日本家族全是命名 key（japanese_*），日本系 0 覆盖。")
w()
w("【本轮新增的映射依据】")
w("  · japanese_minamoto_seiwa    = 清和源氏 (Seiwa Genji)     ← mod seiwa_genji_dynasty")
w("  · japanese_minamoto_uda      = 宇多源氏 (Uda Genji)       ← mod uda_genji_dynasty")
w("  · japanese_minamoto_saga     = 嵯峨源氏 (Saga Genji)      ← mod saga_genji_dynasty")
w("  · japanese_minamoto_murakami = 村上源氏 (Murakami Genji)  ← mod murakami_genji_dynasty")
w("  · japanese_taira_kanmu       = 桓武平氏 (Kanmu Heishi)    ← mod taira_dynasty")
w("  · 其余按 key 变体匹配 + 相似度 ≥0.85 自动锚定")
w()

w("=" * 84)
w("【一】42 个 parent 宗族 锚定情况")
w("=" * 84)
for p in sorted(parents, key=lambda x: (-len(pinfo[x]['children']), x)):
    d = pinfo[p]
    mark = 'OK ' if d['keys'] else '-- '
    how = []
    if d['hist']: how.append('史实映射')
    if d['found'] and d['score'] >= 0.85: how.append(f'key匹配{d["score"]}')
    if d['num']: how.append('v2数字ID')
    w(f"{mark}{p:<30} 支系={len(d['children']):<3} {'/'.join(how) or '-':<22} vanilla={','.join(d['keys']) or '-'}")
w()

w("=" * 84)
w("【二】168 个 child 分级")
w("=" * 84)
w(f"  A 可直接复用（vanilla house 结构对齐 / 同名 dynasty + 父锚定）: {g.get('A',0)}")
w(f"  B vanilla 有同名 house 但父宗族与 mod 归并不一致（需裁决）   : {g.get('B',0)}")
w(f"  C 靠 parent/兄弟锚定获得间接支持                            : {g.get('C',0)}")
w(f"  D 无新证据                                                  : {g.get('D',0)}")
w()

w("=" * 84)
w("【三】A 级：置信度明确提升（可直接复用 vanilla key）")
w("=" * 84)
for r in sorted([x for x in rows if x['grade'] == 'A'], key=lambda x: x['child']):
    if r['S1']:
        w(f"{r['child']:<32} [结构对齐] {r['house']}  (parent={r['house_parent']})")
    else:
        w(f"{r['child']:<32} [同名dyn]  {r['named']}  (mod parent {r['parent']} 已锚定)")
w()

w("=" * 84)
w("【四】B 级：vanilla 有同名 house 但父宗族不一致 —— 必须人工裁决")
w("=" * 84)
for r in sorted([x for x in rows if x['grade'] == 'B'], key=lambda x: x['child']):
    w(f"{r['child']:<30} mod_parent={r['parent']:<24} vanilla: {r['house']:<32} parent={r['house_parent']}")
w()

w("=" * 84)
w("【五】C 级：间接支持")
w("=" * 84)
for r in sorted([x for x in rows if x['grade'] == 'C'], key=lambda x: (x['parent'], x['child'])):
    why = []
    if r['parent_anchored']: why.append('父=' + ','.join(r['parent_keys']))
    if r['sib_strong']: why.append('兄弟强证=' + ','.join(r['sib_strong'][:2]))
    w(f"{r['child']:<30} -> {r['parent']:<24} {' | '.join(why)}")
w()

w("=" * 84)
w(f"【六】D 级：{g.get('D',0)} 个")
w("=" * 84)
for r in sorted([x for x in rows if x['grade'] == 'D'], key=lambda x: (x['parent'], x['child'])):
    w(f"{r['child']:<30} -> {r['parent']}")
w()

open(os.path.join(BASE, 'house_confidence_v2.txt'), 'w', encoding='utf-8').write('\n'.join(out))
json.dump({'children': rows, 'parents': list(pinfo.values())},
          open(os.path.join(BASE, 'house_confidence_v2.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f"anch={len(anch)}/{len(parents)} A={g.get('A',0)} B={g.get('B',0)} C={g.get('C',0)} D={g.get('D',0)}")
