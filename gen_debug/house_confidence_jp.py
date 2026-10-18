# -*- coding: utf-8 -*-
"""
补齐 v2 的盲区：vanilla 日本家族用命名 key（japanese_*），不是数字 ID。
做长音规范化（ou->o, uu->u, oo->o）后匹配。
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

# vanilla 全部 dynasty（命名 key + 数字 ID）
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
    """长音规范化：ou->o, uu->u, oo->o, 去除连字符"""
    s = s.lower().replace('-', '_').replace("'", '')
    s = s.replace('ou', 'o').replace('uu', 'u').replace('oo', 'o')
    return s

# vanilla 命名 dynasty 按 norm 建索引
van_named_norm = defaultdict(list)
for k, v in van_dyns.items():
    if not k.isdigit():
        van_named_norm[norm(k)].append(k)
# house 按 norm(去掉 house_ 前缀) 建索引，同时建后缀索引
van_house_norm = defaultdict(list)
van_house_suffix = defaultdict(list)
for k in van_houses:
    short = k[len('house_'):]
    van_house_norm[norm(short)].append(k)
    van_house_suffix[norm(short.split('_')[-1])].append(k)

rows = []
for child, info in sorted(merge_map.items()):
    parent = info['parent_dyn']
    short = child[:-len('_dynasty')] if child.endswith('_dynasty') else child
    nshort = norm(short)

    # A. 同名独立 dynasty（日本系命名 key）
    cand_dyn = []
    for probe in ('japanese_' + nshort, 'japanese_' + short, nshort, short):
        for k in van_named_norm.get(norm(probe), []):
            if k not in cand_dyn:
                cand_dyn.append(k)
        if probe in van_dyns and probe not in cand_dyn:
            cand_dyn.append(probe)

    # B. 同名 house
    cand_house = []
    for probe in (nshort, short):
        for k in van_house_norm.get(norm(probe), []):
            if k not in cand_house:
                cand_house.append(k)
        for k in van_house_suffix.get(norm(probe), []):
            if k not in cand_house:
                cand_house.append(k)
    # 也按 parent 前缀找 house_<parent>_<short>
    for k in van_house_suffix.get(nshort, []):
        if k not in cand_house:
            cand_house.append(k)

    rows.append({
        'child': child, 'short': short, 'house_key': 'house_' + short, 'parent': parent,
        'cand_dyn': cand_dyn, 'cand_house': cand_house,
        'van_dyn_names': [van_dyns[k]['name'] for k in cand_dyn],
        'van_dyn_cultures': [van_dyns[k]['culture'] for k in cand_dyn],
        'self_lv': ('STRONG' if (matches.get(child) or {}).get('strong_hits', 0) >= 1
                    else 'NAME' if (matches.get(child) or {}).get('name_hits', 0) >= 1
                    else 'WEAK' if child in matches else 'NONE'),
    })

# 统计
jp = [r for r in rows if any(k.startswith('japanese_') for k in r['cand_dyn'])]
hit_dyn = [r for r in rows if r['cand_dyn']]
hit_house = [r for r in rows if r['cand_house']]
both = [r for r in rows if r['cand_dyn'] and r['cand_house']]
neither = [r for r in rows if not r['cand_dyn'] and not r['cand_house']]

out = []
def w(s=''): out.append(s)

w("=" * 80)
w("补齐 v2 盲区：vanilla 日本家族是命名 key（japanese_*），不是数字 ID")
w("=" * 80)
w(f"vanilla dynasty 总数（含命名 key）: {len(van_dyns)}")
w(f"  其中 japanese_* 命名 dynasty   : {sum(1 for k in van_dyns if k.startswith('japanese_'))}")
w(f"vanilla house 总数               : {len(van_houses)}")
w(f"168 个被归并 child")
w()
w(f"【A】能在 vanilla 找到同名独立 dynasty : {len(hit_dyn)} 个")
w(f"      其中日本系 japanese_*          : {len(jp)} 个")
w(f"【B】能在 vanilla 找到同名 house       : {len(hit_house)} 个")
w(f"【C】两类都有（vanilla 既有 dynasty 又有 house）: {len(both)} 个")
w(f"【D】两类都没有                       : {len(neither)} 个")
w()

w("=" * 80)
w("【A】同名独立 dynasty 清单（→ 可直接用 vanilla 命名 key 复用）")
w("=" * 80)
hit_dyn.sort(key=lambda r: (r['child']))
for r in hit_dyn:
    tag = 'JP' if any(k.startswith('japanese_') for k in r['cand_dyn']) else '  '
    w(f"[{tag}] {r['child']:<34} -> {','.join(r['cand_dyn'])}")
    w(f"      vanilla name={r['van_dyn_names']} culture={r['van_dyn_cultures']}   自身证据={r['self_lv']}  mod_parent={r['parent']}")
w()

w("=" * 80)
w("【B】同名 house 清单（→ 可复用 vanilla house key，保留归并结构）")
w("=" * 80)
hit_house.sort(key=lambda r: r['child'])
for r in hit_house:
    vh = r['cand_house'][0]
    hp = van_houses[vh]['parent']
    hpname = van_dyns.get(hp, {}).get('name', '')
    w(f"{r['child']:<34} -> {','.join(r['cand_house'])}")
    w(f"      vanilla house name={van_houses[vh]['name']}  parent={hp}({hpname})  mod_parent={r['parent']}")
w()

w("=" * 80)
w(f"【D】两边都找不到的 {len(neither)} 个")
w("=" * 80)
for r in neither:
    w(f"  {r['child']:<34} parent={r['parent']}")
w()

report = '\n'.join(out)
open(os.path.join(BASE, 'house_confidence_jp.txt'), 'w', encoding='utf-8').write(report)
json.dump(rows, open(os.path.join(BASE, 'house_confidence_jp.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f"hit_dyn={len(hit_dyn)} (jp={len(jp)}) hit_house={len(hit_house)} both={len(both)} neither={len(neither)}")
