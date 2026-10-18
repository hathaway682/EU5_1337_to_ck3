# -*- coding: utf-8 -*-
"""
用支系（house）关系提升家族复用置信度

三层新证据：
  S1 结构对齐：vanilla 里 child 本来就是 house，且其 parent dynasty == mod 认定的 parent 对应的 vanilla dynasty
  S2 父系锚定：child 自己没证据，但 parent 在 vanilla 有强证据（strong_hits>=1）
  S3 兄弟锚定：同一 parent 下至少一个兄弟有强证据
"""
import os, re, json, sys

VAN = r"E:/SteamLibrary/steamapps/common/Crusader Kings III/game"
BASE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(BASE)

def read_text(p):
    for enc in ('utf-8-sig', 'utf-8', 'cp1252', 'latin-1'):
        try:
            with open(p, 'r', encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    return ''

# ---------- 1. 解析 vanilla houses ----------
van_houses = {}   # house_key -> {'name':..., 'dynasty': id}
for fn in os.listdir(os.path.join(VAN, 'common', 'dynasty_houses')):
    if not fn.endswith('.txt'):
        continue
    txt = read_text(os.path.join(VAN, 'common', 'dynasty_houses', fn))
    for m in re.finditer(r'^(house_\w+)\s*=\s*\{', txt, re.M):
        key = m.group(1)
        # 取到匹配的右括号
        i = m.end() - 1
        depth = 0
        j = i
        while j < len(txt):
            if txt[j] == '{':
                depth += 1
            elif txt[j] == '}':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        body = txt[i:j+1]
        nm = re.search(r'\bname\s*=\s*"([^"]+)"', body)
        dy = re.search(r'\bdynasty\s*=\s*(\d+)', body)
        van_houses[key] = {
            'name': nm.group(1) if nm else '',
            'dynasty': dy.group(1) if dy else '',
            'file': fn,
        }

# ---------- 2. 解析 vanilla dynasties: id -> name ----------
van_dyns = {}
for fn in os.listdir(os.path.join(VAN, 'common', 'dynasties')):
    if not fn.endswith('.txt'):
        continue
    txt = read_text(os.path.join(VAN, 'common', 'dynasties', fn))
    for m in re.finditer(r'^(\d+)\s*=\s*\{', txt, re.M):
        did = m.group(1)
        i = m.end() - 1
        depth = 0
        j = i
        while j < len(txt):
            if txt[j] == '{':
                depth += 1
            elif txt[j] == '}':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        body = txt[i:j+1]
        nm = re.search(r'\bname\s*=\s*"([^"]+)"', body)
        van_dyns[did] = nm.group(1) if nm else ''

# ---------- 3. 加载已有分析 ----------
with open(os.path.join(BASE, 'dynasty_merge_map.json'), 'r', encoding='utf-8') as f:
    merge_data = json.load(f)
merge_map = merge_data['merge_map']          # child -> {parent_dyn, root, desc_count}

with open(os.path.join(BASE, 'dynasty_cross_check_loc.json'), 'r', encoding='utf-8') as f:
    cc = json.load(f)
matches = {}
for m in cc['matches']:
    matches[m['mod_dyn']] = m

def level(m):
    """把 matches 记录转成等级"""
    if m is None:
        return 'NONE'
    if m.get('strong_hits', 0) >= 1:
        return 'STRONG'
    if m.get('name_hits', 0) >= 1:
        return 'NAME'
    return 'WEAK'   # 有对但没角色撞上

# ---------- 4. 逐个 child 分析 ----------
rows = []
for child, info in sorted(merge_map.items()):
    parent = info['parent_dyn']
    short = child[:-len('_dynasty')] if child.endswith('_dynasty') else child
    mod_house_key = 'house_' + short

    self_lv = level(matches.get(child))
    self_m = matches.get(child)
    parent_lv = level(matches.get(parent))
    parent_m = matches.get(parent)

    # S1: vanilla 里同名 house 存在吗？parent 对得上吗？
    vh = van_houses.get(mod_house_key)
    s1 = False
    vh_parent_id = ''
    vh_parent_name = ''
    parent_van_ids = parent_m['van_ids'] if parent_m else []
    if vh:
        vh_parent_id = vh['dynasty']
        vh_parent_name = van_dyns.get(vh_parent_id, '')
        if vh_parent_id and vh_parent_id in parent_van_ids:
            s1 = True

    # S2: parent 有强证据
    s2 = (parent_lv == 'STRONG')
    # S3: 兄弟有强证据（稍后补）
    rows.append({
        'child': child,
        'house_key': mod_house_key,
        'parent': parent,
        'self_level': self_lv,
        'self_strong': (self_m or {}).get('strong_hits', 0),
        'self_name_hits': (self_m or {}).get('name_hits', 0),
        'self_mod_n': (self_m or {}).get('mod_n', 0),
        'self_van_n': (self_m or {}).get('van_n', 0),
        'parent_level': parent_lv,
        'parent_van_ids': ','.join(parent_van_ids),
        'van_house_exists': bool(vh),
        'van_house_name': vh['name'] if vh else '',
        'van_house_parent_id': vh_parent_id,
        'van_house_parent_name': vh_parent_name,
        'S1_structure': s1,
        'S2_parent_anchor': s2,
    })

# S3 兄弟锚定
by_parent = {}
for r in rows:
    by_parent.setdefault(r['parent'], []).append(r)
for parent, sibs in by_parent.items():
    strong_sibs = [s['child'] for s in sibs if s['self_level'] == 'STRONG']
    for r in sibs:
        others = [c for c in strong_sibs if c != r['child']]
        r['siblings_strong'] = others
        r['S3_sibling_anchor'] = len(others) > 0

# ---------- 5. 统计与输出 ----------
out = []
def w(s=''):
    out.append(s)

w("=" * 78)
w("支系关系对家族复用置信度的提升分析")
w("=" * 78)
w(f"vanilla house 总数: {len(van_houses)}")
w(f"vanilla dynasty 总数: {len(van_dyns)}")
w(f"归并 child 总数: {len(rows)}")
w(f"归并 parent 总数: {len(by_parent)}")
w()

from collections import Counter
c_self = Counter(r['self_level'] for r in rows)
w("【一】168 个被归并家族自身的原始证据等级")
for k in ('STRONG', 'NAME', 'WEAK', 'NONE'):
    w(f"  {k:<8}: {c_self.get(k,0)}")
w()

s1_rows = [r for r in rows if r['S1_structure']]
w(f"【二】S1 结构对齐（铁证）：vanilla 里本来就是 house 且父 dynasty 对得上 → {len(s1_rows)} 个")
w()

vh_rows = [r for r in rows if r['van_house_exists']]
w(f"【三】vanilla 存在同名 house（不论父是否对上）→ {len(vh_rows)} 个")
not_aligned = [r for r in vh_rows if not r['S1_structure']]
if not_aligned:
    w(f"      其中父 dynasty 对不上 → {len(not_aligned)} 个（需人工看）")
w()

# 提升：原本是 WEAK/NONE 的，因 S1 或 S2 或 S3 得到佐证
upgraded = []
for r in rows:
    if r['self_level'] in ('STRONG',):
        continue
    reasons = []
    if r['S1_structure']:
        reasons.append('S1结构对齐')
    if r['S2_parent_anchor']:
        reasons.append('S2父系锚定')
    if r['S3_sibling_anchor']:
        reasons.append('S3兄弟锚定')
    if reasons:
        r['reasons'] = reasons
        upgraded.append(r)

w(f"【四】可以提升置信度的家族：{len(upgraded)} 个")
w()
buckets = {}
for r in upgraded:
    key = (r['self_level'], '+'.join(r['reasons']))
    buckets.setdefault(key, []).append(r)
for key in sorted(buckets, key=lambda x: (-len(buckets[x]), x)):
    lv, reason = key
    lst = buckets[key]
    w(f"  {lv:<6} + {reason:<20} : {len(lst)} 个")
w()

# 详细清单
w("=" * 78)
w("【五】提升清单（按证据强度排序）")
w("=" * 78)
def score(r):
    s = 0
    if r['S1_structure']: s += 100
    if r['S2_parent_anchor']: s += 30
    if r['S3_sibling_anchor']: s += 10
    s += {'STRONG': 50, 'NAME': 20, 'WEAK': 5, 'NONE': 0}[r['self_level']]
    return s
upgraded.sort(key=score, reverse=True)
for r in upgraded:
    w(f"{r['child']:<38} -> {r['parent']:<28} [{r['self_level']}] {'+'.join(r['reasons'])}")
    w(f"    house_key={r['house_key']}  vanilla_house={'YES(' + r['van_house_name'] + ' -> dyn ' + r['van_house_parent_id'] + ' ' + r['van_house_parent_name'] + ')' if r['van_house_exists'] else 'no'}")
    w(f"    自身证据: strong={r['self_strong']} name_hits={r['self_name_hits']} mod_n={r['self_mod_n']} van_n={r['self_van_n']}")
    w(f"    parent 证据: {r['parent_level']} van_ids={r['parent_van_ids']}")
    if r['S3_sibling_anchor']:
        w(f"    强证据兄弟: {', '.join(r['siblings_strong'][:5])}")
    w()

# 父 dynasty 层面的统计
w("=" * 78)
w("【六】42 个 parent 宗族的证据等级（决定其下支系的可信度）")
w("=" * 78)
for parent in sorted(by_parent, key=lambda p: -len(by_parent[p])):
    sibs = by_parent[parent]
    pm = matches.get(parent)
    plv = level(pm)
    n_strong = sum(1 for s in sibs if s['self_level'] == 'STRONG')
    n_s1 = sum(1 for s in sibs if s['S1_structure'])
    w(f"{parent:<30} {plv:<7} 支系={len(sibs):<3} 自身强证据支系={n_strong:<3} S1对齐={n_s1:<3} van_ids={','.join(pm['van_ids']) if pm else '-'}")
w()

report = '\n'.join(out)
with open(os.path.join(BASE, 'house_confidence_upgrade.txt'), 'w', encoding='utf-8') as f:
    f.write(report)

# JSON
with open(os.path.join(BASE, 'house_confidence_upgrade.json'), 'w', encoding='utf-8') as f:
    json.dump({
        'van_house_total': len(van_houses),
        'children': rows,
        'upgraded_count': len(upgraded),
    }, f, ensure_ascii=False, indent=1)

print(f"OK  rows={len(rows)}  upgraded={len(upgraded)}  S1={len(s1_rows)}  van_house_match={len(vh_rows)}")
