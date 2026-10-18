# -*- coding: utf-8 -*-
"""
最终版 v4 —— 完整锚定 + 分级

parent 锚定三条独立证据：
  E1 本地化名匹配：mod 家族英文名 vs vanilla dynn_XXX 英文名（去重音 + 规范化 + 相似度≥0.85）
  E2 结构反推：该 parent 下多个 child 的 vanilla house parent 都指向同一 dynasty
  E3 史实映射：日本源氏/平氏
  E4 v2 数字 ID 匹配（已有）
任一成立即锚定；E1/E2 互相印证时标记为「强锚定」。
"""
import os, re, json, unicodedata, difflib
from collections import defaultdict, Counter

VAN = r"E:/SteamLibrary/steamapps/common/Crusader Kings III/game"
BASE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(BASE)

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

# ---------- vanilla ----------
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
        van_houses[key] = {'name': nm.group(1) if nm else '', 'parent': dy.group(1) if dy else ''}

# vanilla 本地化
van_loc = {}
locdir = os.path.join(VAN, 'localization', 'english')
for root, _, files in os.walk(locdir):
    for fn in files:
        if not fn.endswith('.yml'): continue
        try:
            txt = open(os.path.join(root, fn), 'r', encoding='utf-8-sig').read()
        except Exception:
            continue
        for m in re.finditer(r'^\s*(dynn_\S+?):\d*\s*"([^"]*)"', txt, re.M):
            van_loc.setdefault(m.group(1), m.group(2))

# ---------- mod 本地化 ----------
mod_loc = {}
modloc = os.path.join(MOD, 'localization', 'english')
for fn in os.listdir(modloc):
    if not fn.endswith('.yml'): continue
    txt = read_text(os.path.join(modloc, fn))
    for m in re.finditer(r'^\s*([A-Za-z_][\w]*):\d*\s*"([^"]*)"', txt, re.M):
        mod_loc.setdefault(m.group(1), m.group(2))

# ---------- mod 数据 ----------
merge_map = json.load(open(os.path.join(BASE, 'dynasty_merge_map.json'), encoding='utf-8'))['merge_map']
cc = json.load(open(os.path.join(BASE, 'dynasty_cross_check_loc.json'), encoding='utf-8'))
matches = {m['mod_dyn']: m for m in cc['matches']}

# mod dynasty 的 culture（用于判断文化圈）
# 注意：被归并的 dynasty 已在主文件中注释，必须从备份读原始定义
mod_dyn_culture = {}
_cand_files = [
    os.path.join(MOD, '_backup_dynasty_merge_20261018_141112', 'zz_eu5_dynasties.txt'),
    os.path.join(MOD, 'common', 'dynasties', 'zz_eu5_dynasties.txt'),
]
for _f in _cand_files:
    if not os.path.exists(_f):
        continue
    _mtxt = read_text(_f)
    for m in re.finditer(r'^#?\s*([a-z0-9_]+_dynasty)\s*=\s*\{([^}]*)\}', _mtxt, re.M):
        k = m.group(1)
        if k in mod_dyn_culture:
            continue
        cu = re.search(r'culture\s*=\s*"?([a-z_]+)"?', m.group(2))
        mod_dyn_culture[k] = cu.group(1) if cu else ''

# mod 的日本文化（细分三块）
JP_CULTURES = {'saigoku_culture', 'tougoku_culture', 'touhoku_culture', 'kyushu_culture'}
def is_jp(mod_dyn):
    return mod_dyn_culture.get(mod_dyn, '') in JP_CULTURES

def strip_acc(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def canon(s):
    s = strip_acc(s).lower()
    s = re.sub(r'[^a-z0-9]', '', s)
    return s

def norm_longa(s):
    s = canon(s)
    for a, b in (('ou', 'o'), ('uu', 'u'), ('oo', 'o')):
        s = s.replace(a, b)
    return s

# vanilla dynasty 名字索引
van_by_canon = defaultdict(set)
for k, v in van_dyns.items():
    nm = van_loc.get(v['name'], '')
    if nm:
        van_by_canon[canon(nm)].add(k)
        van_by_canon[norm_longa(nm)].add(k)

def name_match(mod_key, short, jp_only=False):
    """用本地化名匹配 vanilla dynasty
    jp_only=True 时只接受 japanese_* 候选（日本文化圈）
    jp_only=False 时只接受数字 ID 候选（非日本）
    """
    nm = mod_loc.get(mod_key, '') or mod_loc.get(short + '_dynasty', '')
    if not nm:
        return [], 0.0, ''
    cs = {canon(nm), norm_longa(nm)}
    hit = set()
    for c in cs:
        hit |= van_by_canon.get(c, set())
    if jp_only:
        hit = {k for k in hit if k.startswith('japanese_')}
    else:
        hit = {k for k in hit if not k.startswith('japanese_')}
    if hit:
        return sorted(hit), 1.0, nm
    # 模糊：只在精确未中时用，阈值提高 + 长度约束 + 文化圈约束
    target = norm_longa(nm)
    if len(target) < 5:
        return [], 0.0, nm
    best_k, best_r = '', 0.0
    for k, v in van_dyns.items():
        if jp_only and not k.startswith('japanese_'):
            continue
        if not jp_only and k.startswith('japanese_'):
            continue
        vn = van_loc.get(v['name'], '')
        if not vn: continue
        cand = norm_longa(vn)
        if len(cand) < 5: continue
        # 长度差超过 30% 直接跳过
        if abs(len(cand) - len(target)) > max(2, int(0.3 * len(target))):
            continue
        r = difflib.SequenceMatcher(None, target, cand).ratio()
        if r > best_r:
            best_r, best_k = r, k
    if best_r >= 0.93 and abs(len(best_k) - len(target)) <= 3:
        return [best_k], best_r, nm
    return [], best_r, nm

def find_house(short, parent_keys):
    ns = norm_longa(short)
    if 'house_' + short in van_houses:
        return 'house_' + short, 'exact'
    for pk in parent_keys:
        sur = pk.split('_')[1] if pk.startswith('japanese_') and len(pk.split('_')) > 1 else pk
        for cand in ('house_%s_%s' % (sur, short), 'house_%s_%s' % (sur, ns)):
            if cand in van_houses:
                return cand, 'parent_prefix'
    tails = {h for h in van_houses if norm_longa(h.split('_')[-1]) == ns}
    if len(tails) == 1:
        return next(iter(tails)), 'tail_unique'
    if tails:
        for pk in parent_keys:
            sur = pk.split('_')[1] if pk.startswith('japanese_') else pk
            for t in tails:
                if t.startswith('house_' + sur + '_'):
                    return t, 'tail_by_parent'
        return sorted(tails)[0], 'tail_ambig'
    return '', ''

def self_lv(m):
    if not m: return 'NONE'
    if m.get('strong_hits', 0) >= 1: return 'STRONG'
    if m.get('name_hits', 0) >= 1: return 'NAME'
    return 'WEAK'

HIST_MAP = {
    'seiwa_genji': 'japanese_minamoto_seiwa', 'uda_genji': 'japanese_minamoto_uda',
    'saga_genji': 'japanese_minamoto_saga', 'murakami_genji': 'japanese_minamoto_murakami',
    'taira': 'japanese_taira_kanmu',
}

parents = sorted({v['parent_dyn'] for v in merge_map.values()})

# 第一轮：不用结构反推，先算每个 parent 的候选
pinfo = {}
for p in parents:
    short = p[:-len('_dynasty')] if p.endswith('_dynasty') else p
    ev = []
    keys = set()
    hist = HIST_MAP.get(short)
    if hist:
        keys.add(hist); ev.append('史实')
    nm_hit, nm_r, nm = name_match(p, short, jp_only=is_jp(p))
    if nm_hit:
        keys |= set(nm_hit); ev.append('名匹配%.2f' % nm_r if nm_r < 1 else '名匹配')
    m = matches.get(p)
    num = m['van_ids'] if m else []
    if num:
        keys |= set(num); ev.append('v2数字ID')
    pinfo[p] = {'parent': p, 'short': short, 'keys': set(keys), 'ev': ev,
                'nm': nm, 'nm_hit': nm_hit, 'num': num,
                'children': [c for c, v in merge_map.items() if v['parent_dyn'] == p]}

# 第二轮：结构反推（用第一轮已锚定的 parent 给 child 找 house，再统计众数）
child_house = {}
for child, info in merge_map.items():
    p = info['parent_dyn']
    short = child[:-len('_dynasty')] if child.endswith('_dynasty') else child
    hk, how = find_house(short, pinfo[p]['keys'])
    child_house[child] = (hk, how)

for p, d in pinfo.items():
    parents_cnt = Counter()
    for c in d['children']:
        hk = child_house[c][0]
        if hk:
            hp = van_houses[hk]['parent']
            if hp and hp not in d['keys']:
                parents_cnt[hp] += 1
    if parents_cnt:
        hp, n = parents_cnt.most_common(1)[0]
        if n >= 2:
            d['struct'] = hp
            d['struct_n'] = n
            # 结构反推的 dynasty 名字是否与 mod 本地化名一致？
            vn = van_loc.get(van_dyns.get(hp, {}).get('name', ''), '')
            agree = bool(d['nm']) and norm_longa(d['nm']) == norm_longa(vn)
            d['struct_agree'] = agree
            if agree or n >= 2:
                d['keys'].add(hp)
                d['ev'].append('结构反推x%d%s' % (n, '(名一致)' if agree else ''))

# ---------- child 分级 ----------
rows = []
for child, info in sorted(merge_map.items()):
    parent = info['parent_dyn']
    short = child[:-len('_dynasty')] if child.endswith('_dynasty') else child
    pv = pinfo[parent]
    hk, how = child_house[child]
    hp = van_houses[hk]['parent'] if hk else ''
    nm_hit, nm_r, nm = name_match(child, short, jp_only=is_jp(child))

    aligned = bool(hk) and hp in pv['keys']
    mismatch = bool(hk) and hp not in pv['keys']
    downgrade = bool(nm_hit) and not hk

    rows.append({'child': child, 'short': short, 'parent': parent,
                 'self_lv': self_lv(matches.get(child)),
                 'named': nm_hit, 'named_name': nm, 'named_r': round(nm_r, 2),
                 'house': hk, 'house_how': how, 'house_parent': hp,
                 'aligned': aligned, 'mismatch': mismatch, 'downgrade': downgrade,
                 'parent_anchored': bool(pv['keys']), 'parent_keys': sorted(pv['keys']),
                 'parent_ev': pv['ev']})

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

# ---------- 报告 ----------
out = []
def w(s=''): out.append(s)
g = Counter(r['grade'] for r in rows)
anch = [p for p in parents if pinfo[p]['keys']]
strong_anch = [p for p in parents if pinfo[p]['keys'] and len(pinfo[p]['ev']) >= 2]

w("=" * 88)
w("支系关系能提升多少置信度 —— 最终结论 v4")
w("=" * 88)
w(f"vanilla dynasty {len(van_dyns)} / house {len(van_houses)} / 本地化 dynn_ 条目 {len(van_loc)}")
w(f"mod 被归并 child {len(rows)} / parent {len(parents)}")
w(f"parent 锚定 {len(anch)}/{len(parents)}（其中 ≥2 条独立证据的强锚定 {len(strong_anch)} 个）")
w()
w("【v2 盲区】272 条匹配只覆盖数字 ID 型 dynasty；vanilla 日本家族全是命名 key（japanese_*），")
w("          173 个日本 dynasty 在 v2 里 0 覆盖。")
w()

w("=" * 88)
w("【一】168 个 child 分级")
w("=" * 88)
w(f"  A1 结构对齐     {g.get('A1',0):>3}  vanilla 本就是 house 且父宗族一致 → 可无损复用 house key")
w(f"  B1 父宗族冲突   {g.get('B1',0):>3}  vanilla 有同名 house 但挂别的宗族 → 同姓不同流")
w(f"  B2 结构降级冲突 {g.get('B2',0):>3}  vanilla 认为它是独立 dynasty，mod 已降成支系")
w(f"  C  间接支持     {g.get('C',0):>3}  靠 parent 锚定 / 兄弟强证据")
w(f"  D  无新证据     {g.get('D',0):>3}")
w()
w(f"  → {g.get('A1',0)+g.get('B1',0)+g.get('B2',0)} 个拿到具体 vanilla 对应物 + {g.get('C',0)} 个间接支持 = {g.get('A1',0)+g.get('B1',0)+g.get('B2',0)+g.get('C',0)}/168")
w()

w("=" * 88)
w("【二】A1 结构对齐（最可信，可无损复用 vanilla house key）")
w("=" * 88)
for r in sorted([x for x in rows if x['grade'] == 'A1'], key=lambda x: x['child']):
    w(f"{r['child']:<30} -> {r['house']:<28} parent={r['house_parent']:<26} ({r['house_how']})")
w()

w("=" * 88)
w("【三】B1 父宗族冲突")
w("=" * 88)
for r in sorted([x for x in rows if x['grade'] == 'B1'], key=lambda x: x['child']):
    vn = van_loc.get(van_dyns.get(r['house_parent'], {}).get('name', ''), '')
    w(f"{r['child']:<28} mod→{r['parent']:<22} / vanilla: {r['house']} → {r['house_parent']}({vn})")
w()

w("=" * 88)
w("【四】B2 结构降级冲突：vanilla 独立 dynasty vs mod 支系")
w("=" * 88)
for r in sorted([x for x in rows if x['grade'] == 'B2'], key=lambda x: x['child']):
    names = [van_loc.get(van_dyns.get(k, {}).get('name', ''), '') for k in r['named']]
    w(f"{r['child']:<28} mod→{r['parent']:<22} / vanilla 独立: {','.join(r['named'])} ({'/'.join(names)})")
w()

w("=" * 88)
w("【五】C 间接支持")
w("=" * 88)
for r in sorted([x for x in rows if x['grade'] == 'C'], key=lambda x: (x['parent'], x['child'])):
    why = []
    if r['parent_anchored']: why.append('父=' + ','.join(r['parent_keys']))
    if r['sib_strong']: why.append('兄弟强证=' + ','.join(r['sib_strong'][:2]))
    w(f"{r['child']:<30} -> {r['parent']:<24} {' | '.join(why)}")
w()

w("=" * 88)
w(f"【六】D 无新证据 {g.get('D',0)}")
w("=" * 88)
for r in sorted([x for x in rows if x['grade'] == 'D'], key=lambda x: (x['parent'], x['child'])):
    w(f"{r['child']:<30} -> {r['parent']}")
w()

w("=" * 88)
w("【七】42 个 parent 锚定明细")
w("=" * 88)
for p in sorted(parents, key=lambda x: (-len(pinfo[x]['children']), x)):
    d = pinfo[p]
    w(f"{'OK' if d['keys'] else '--'} {p:<30} 支系={len(d['children']):<3} {'; '.join(d['ev']) or '-':<34} {','.join(sorted(d['keys'])) or '-'}")
w()

open(os.path.join(BASE, 'house_confidence_v4.txt'), 'w', encoding='utf-8').write('\n'.join(out))
json.dump({'children': rows,
           'parents': [{k: (sorted(v) if isinstance(v, set) else v) for k, v in d.items()} for d in pinfo.values()]},
          open(os.path.join(BASE, 'house_confidence_v4.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f"anch={len(anch)}/{len(parents)} strong={len(strong_anch)}  A1={g.get('A1',0)} B1={g.get('B1',0)} B2={g.get('B2',0)} C={g.get('C',0)} D={g.get('D',0)}")
