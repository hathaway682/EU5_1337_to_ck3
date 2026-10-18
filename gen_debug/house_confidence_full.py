# -*- coding: utf-8 -*-
"""
最终版：用支系结构 + 命名 key 补齐，给出 168 child / 42 parent 的置信度全景

关键：
  vanilla 有 173 个 japanese_* 命名 dynasty，v2 完全没覆盖。
  mod 的 42 个 parent 里多数能直接对上；一旦 parent 锚定，
  其下所有支系的归并就有了基础（父系锚定）。
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
        van_dyns[key] = {'name': nm.group(1) if nm else '', 'culture': cu.group(1) if cu else '', 'file': fn}

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

def norm(s):
    s = s.lower().replace('-', '_').replace("'", '')
    s = s.replace('ou', 'o').replace('uu', 'u').replace('oo', 'o')
    return s

named_norm = defaultdict(list)
for k in van_dyns:
    if not k.isdigit():
        named_norm[norm(k)].append(k)
house_norm = defaultdict(list)
house_suffix = defaultdict(list)
for k in van_houses:
    s = k[len('house_'):]
    house_norm[norm(s)].append(k)
    house_suffix[norm(s.split('_')[-1])].append(k)

def find_dyn(short):
    """mod 短名 -> vanilla 命名 dynasty 候选"""
    out = []
    for probe in ('japanese_' + norm(short), 'japanese_' + short, norm(short), short):
        for k in named_norm.get(norm(probe), []):
            if k not in out: out.append(k)
        if probe in van_dyns and probe not in out: out.append(probe)
    return out

def find_house(short, parent_van_keys=()):
    out = []
    for probe in (norm(short), short):
        for k in house_norm.get(norm(probe), []):
            if k not in out: out.append(k)
        for k in house_suffix.get(norm(probe), []):
            if k not in out: out.append(k)
    # parent 前缀： house_<parent>_<short>
    for pk in parent_van_keys:
        pshort = pk[len('japanese_'):] if pk.startswith('japanese_') else pk
        for k in house_suffix.get(norm(short), []):
            if k.startswith('house_' + pshort + '_') and k not in out:
                out.insert(0, k)
    return out

def self_lv(mod_dyn):
    m = matches.get(mod_dyn)
    if not m: return 'NONE'
    if m.get('strong_hits', 0) >= 1: return 'STRONG'
    if m.get('name_hits', 0) >= 1: return 'NAME'
    return 'WEAK'

# ---------- parent 分析 ----------
parents = sorted({v['parent_dyn'] for v in merge_map.values()})
pinfo = {}
for p in parents:
    short = p[:-len('_dynasty')] if p.endswith('_dynasty') else p
    cd = find_dyn(short)
    m = matches.get(p)
    pkeys = set(cd) | set(m['van_ids'] if m else [])
    pinfo[p] = {
        'parent': p, 'short': short,
        'named_dyn': cd,
        'num_ids': m['van_ids'] if m else [],
        'level': self_lv(p),
        'children': [c for c, v in merge_map.items() if v['parent_dyn'] == p],
        'van_keys': sorted(pkeys),
    }

# ---------- child 分析 ----------
rows = []
for child, info in sorted(merge_map.items()):
    parent = info['parent_dyn']
    short = child[:-len('_dynasty')] if child.endswith('_dynasty') else child
    pv = pinfo[parent]
    cd = find_dyn(short)
    ch = find_house(short, pv['van_keys'])

    # 结构判定
    s1 = s2 = False
    vh_key = ''
    vh_parent = ''
    if ch:
        vh_key = ch[0]
        vh_parent = van_houses[vh_key]['parent']
        if vh_parent in pv['van_keys']:
            s1 = True
        else:
            s2 = True

    rows.append({
        'child': child, 'short': short, 'parent': parent,
        'self_lv': self_lv(child),
        'named_dyn': cd,
        'house': ch,
        'house_parent': vh_parent,
        'S1': s1, 'S2': s2,
        'parent_anchored': bool(pv['van_keys']),
        'parent_keys': pv['van_keys'],
    })

by_parent = defaultdict(list)
for r in rows: by_parent[r['parent']].append(r)
for p, sibs in by_parent.items():
    strong = [s['child'] for s in sibs if s['self_lv'] == 'STRONG']
    for r in sibs:
        r['sib_strong'] = [c for c in strong if c != r['child']]

# ---------- 分级 ----------
def grade(r):
    """A=可直接复用, B=结构+父系佐证, C=仅父系, D=无"""
    if r['S1']: return 'A'
    if r['named_dyn'] and r['parent_anchored']: return 'A'   # 同名独立 dynasty + 父能对上
    if r['S2']: return 'B'
    if r['parent_anchored']: return 'C'
    if r['sib_strong']: return 'C'
    return 'D'
for r in rows: r['grade'] = grade(r)

out = []
def w(s=''): out.append(s)

w("=" * 82)
w("家族复用置信度全景（补齐 vanilla 命名 key 盲区后）")
w("=" * 82)
w(f"vanilla dynasty 总数        : {len(van_dyns)}")
w(f"  └ japanese_* 命名 dynasty : {sum(1 for k in van_dyns if k.startswith('japanese_'))}")
w(f"vanilla house 总数          : {len(van_houses)}")
w(f"mod 被归并 child            : {len(rows)}")
w(f"mod 归并 parent             : {len(parents)}")
w()
w("【v2 的盲区】v2 的 272 条匹配只覆盖「数字 ID」型 vanilla dynasty。")
w("            vanilla 的日本家族全部是命名 key，日本系在 v2 里 0 覆盖。")
w()

w("=" * 82)
w("【一】42 个 parent 宗族 在 vanilla 的锚定情况")
w("=" * 82)
anch = [p for p in parents if pinfo[p]['van_keys']]
w(f"能锚定到 vanilla 的 parent : {len(anch)} / {len(parents)}")
w()
for p in sorted(parents, key=lambda x: (-len(pinfo[x]['children']), x)):
    d = pinfo[p]
    mark = 'OK ' if d['van_keys'] else '-- '
    w(f"{mark}{p:<30} 支系={len(d['children']):<3} v2={d['level']:<7} vanilla={','.join(d['van_keys']) or '-'}")
w()

w("=" * 82)
w("【二】168 个 child 分级")
w("=" * 82)
g = Counter(r['grade'] for r in rows)
w(f"  A 可直接复用（结构或同名+父锚）: {g.get('A',0)}")
w(f"  B 同名 house 但父不一致（冲突） : {g.get('B',0)}")
w(f"  C 仅靠父系/兄弟锚定            : {g.get('C',0)}")
w(f"  D 无任何新证据                 : {g.get('D',0)}")
w()

w("=" * 82)
w("【三】A 级清单：置信度明确提升")
w("=" * 82)
A = [r for r in rows if r['grade'] == 'A']
A.sort(key=lambda r: (r['child']))
for r in A:
    if r['S1']:
        w(f"{r['child']:<34} [A-结构] vanilla house = {r['house'][0]}  parent={r['house_parent']}")
    else:
        w(f"{r['child']:<34} [A-同名] vanilla dynasty = {','.join(r['named_dyn'])}  (parent {r['parent']} 已锚定)")
w()

w("=" * 82)
w("【四】B 级清单：vanilla 有同名 house，但父宗族与 mod 归并结果不一致（需裁决）")
w("=" * 82)
B = [r for r in rows if r['grade'] == 'B']
for r in sorted(B, key=lambda r: r['child']):
    w(f"{r['child']:<30} mod_parent={r['parent']:<24} vanilla_house={r['house'][0]:<30} vanilla_parent={r['house_parent']}")
w()

w("=" * 82)
w("【五】C 级清单：靠 parent/兄弟锚定获得间接支持")
w("=" * 82)
C = [r for r in rows if r['grade'] == 'C']
for r in sorted(C, key=lambda r: (r['parent'], r['child'])):
    why = []
    if r['parent_anchored']: why.append('父锚定:' + ','.join(r['parent_keys']))
    if r['sib_strong']: why.append('兄弟强证据:' + ','.join(r['sib_strong'][:3]))
    w(f"{r['child']:<30} -> {r['parent']:<24} {' | '.join(why)}")
w()

w("=" * 82)
w(f"【六】D 级：无新证据 {g.get('D',0)} 个")
w("=" * 82)
D = [r for r in rows if r['grade'] == 'D']
for r in sorted(D, key=lambda r: r['parent']):
    w(f"{r['child']:<30} -> {r['parent']}")
w()

report = '\n'.join(out)
open(os.path.join(BASE, 'house_confidence_full.txt'), 'w', encoding='utf-8').write(report)
json.dump({'children': rows, 'parents': list(pinfo.values())},
          open(os.path.join(BASE, 'house_confidence_full.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f"parent_anchored={len(anch)}/{len(parents)}  A={g.get('A',0)} B={g.get('B',0)} C={g.get('C',0)} D={g.get('D',0)}")
