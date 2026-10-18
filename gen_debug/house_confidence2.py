# -*- coding: utf-8 -*-
"""
用支系(house)结构提升家族复用置信度  —— 完整版

核心洞察：
  vanilla CK3 的日本家族用【命名 key】(japanese_fujiwara / japanese_minamoto_seiwa ...)，
  不是数字 ID。v2 的 272 条匹配只处理数字 ID，所以日本系整体缺失。
  而 vanilla 已经把日本支系做成 house（house_fujiwara_ashikaga 等），
  与 mod 现在的 house 结构天然同构 —— 这是最强的置信度来源。

判定层级：
  S1 铁证  : vanilla 有同名 house，且其 parent dynasty == mod 认定 parent 对应的 vanilla dynasty
  S1b 强证 : vanilla 有同名 house，parent 也对得上（但 parent 映射靠语义推断）
  S2 同名  : vanilla 有同名 house，但 parent 不一致
  S3 父锚  : child 自身无证据，parent 在 vanilla 有强证据
  S4 兄弟锚: 同一 parent 下有兄弟是强证据
"""
import os, re, json
from collections import Counter, defaultdict

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

def parse_blocks(txt, key_pat):
    """返回 [(key, body)]"""
    res = []
    for m in re.finditer(key_pat, txt, re.M):
        key = m.group(1)
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
        res.append((key, txt[i:j+1]))
    return res

# ---------- vanilla houses ----------
van_houses = {}
for fn in os.listdir(os.path.join(VAN, 'common', 'dynasty_houses')):
    if not fn.endswith('.txt'):
        continue
    txt = read_text(os.path.join(VAN, 'common', 'dynasty_houses', fn))
    for key, body in parse_blocks(txt, r'^(house_\w+)\s*=\s*\{'):
        nm = re.search(r'\bname\s*=\s*"([^"]+)"', body)
        dy = re.search(r'\bdynasty\s*=\s*(\d+|[a-z_]\w*)', body)
        van_houses[key] = {
            'name': nm.group(1) if nm else '',
            'parent': dy.group(1) if dy else '',
            'file': fn,
        }

# ---------- vanilla dynasties (数字 ID + 命名 key 都要) ----------
van_dyns = {}   # key_or_id -> name_key
for fn in os.listdir(os.path.join(VAN, 'common', 'dynasties')):
    if not fn.endswith('.txt'):
        continue
    txt = read_text(os.path.join(VAN, 'common', 'dynasties', fn))
    for key, body in parse_blocks(txt, r'^(\d+|[a-z_]\w*)\s*=\s*\{'):
        nm = re.search(r'\bname\s*=\s*"([^"]+)"', body)
        van_dyns[key] = nm.group(1) if nm else ''

# ---------- mod 数据 ----------
merge_data = json.load(open(os.path.join(BASE, 'dynasty_merge_map.json'), encoding='utf-8'))
merge_map = merge_data['merge_map']

cc = json.load(open(os.path.join(BASE, 'dynasty_cross_check_loc.json'), encoding='utf-8'))
matches = {m['mod_dyn']: m for m in cc['matches']}

def lv(m):
    if m is None: return 'NONE'
    if m.get('strong_hits', 0) >= 1: return 'STRONG'
    if m.get('name_hits', 0) >= 1: return 'NAME'
    return 'WEAK'

# ---------- mod parent -> vanilla dynasty key 手工映射（仅日本系 + 已由 matches 覆盖的） ----------
# 依据：mod 本地化英文名 + vanilla dynasty key 的构词 + vanilla motto
JP_PARENT_MAP = {
    'seiwa_genji_dynasty':     'japanese_minamoto_seiwa',      # Seiwa Genji = 清和源氏
    'murakami_genji_dynasty':  'japanese_minamoto_murakami',   # Murakami Genji = 村上源氏
    'uda_genji_dynasty':       'japanese_minamoto_uda',        # Uda Genji = 宇多源氏
    'saga_genji_dynasty':      'japanese_minamoto_saga',       # Saga Genji = 嵯峨源氏
    'taira_dynasty':           'japanese_taira_kanmu',         # 桓武平氏（mod 只留一个 taira）
    'fujiwara_dynasty':        'japanese_fujiwara',            # 藤原
    'yamato_dynasty':          'japanese_yamato',              # 大和
    'takashina_dynasty':       'japanese_takashina',           # 高階
    'kiyohara_dynasty':        'japanese_kiyohara',            # 清原
}

def van_parent_keys(mod_parent):
    """mod parent 可能对应的 vanilla dynasty key 集合"""
    keys = set()
    if mod_parent in JP_PARENT_MAP:
        keys.add(JP_PARENT_MAP[mod_parent])
    m = matches.get(mod_parent)
    if m:
        keys.update(m['van_ids'])
    return keys

# vanilla house 后缀索引：  ashikaga -> [house_fujiwara_ashikaga, ...]
suffix_index = defaultdict(list)
for hk in van_houses:
    short = hk[len('house_'):]
    suffix_index[short].append(hk)
    # 也索引最后一段
    parts = short.split('_')
    if len(parts) > 1:
        suffix_index[parts[-1]].append(hk)

rows = []
for child, info in sorted(merge_map.items()):
    parent = info['parent_dyn']
    short = child[:-len('_dynasty')] if child.endswith('_dynasty') else child
    mod_house = 'house_' + short

    cands = []
    # 精确 key 匹配 house_<short>
    if mod_house in van_houses:
        cands.append(mod_house)
    # 后缀匹配
    for hk in suffix_index.get(short, []):
        if hk not in cands:
            cands.append(hk)

    pkeys = van_parent_keys(parent)
    self_lv = lv(matches.get(child))

    best = None
    for hk in cands:
        vh = van_houses[hk]
        aligned = bool(vh['parent']) and (vh['parent'] in pkeys)
        score = (100 if aligned else 50) - abs(len(hk) - len(mod_house))
        if best is None or score > best[0]:
            best = (score, hk, vh, aligned)

    rows.append({
        'child': child, 'short': short, 'house_key': mod_house, 'parent': parent,
        'self_level': self_lv,
        'self_strong': (matches.get(child) or {}).get('strong_hits', 0),
        'self_name_hits': (matches.get(child) or {}).get('name_hits', 0),
        'self_mod_n': (matches.get(child) or {}).get('mod_n', 0),
        'self_van_n': (matches.get(child) or {}).get('van_n', 0),
        'parent_level': lv(matches.get(parent)),
        'parent_van_keys': sorted(pkeys),
        'van_house': best[1] if best else '',
        'van_house_name': best[2]['name'] if best else '',
        'van_house_parent': best[2]['parent'] if best else '',
        'van_house_parent_name': van_dyns.get(best[2]['parent'], '') if best else '',
        'aligned': best[3] if best else False,
        'cand_count': len(cands),
    })

# S3/S4
by_parent = defaultdict(list)
for r in rows:
    by_parent[r['parent']].append(r)
for p, sibs in by_parent.items():
    strong = [s['child'] for s in sibs if s['self_level'] == 'STRONG']
    for r in sibs:
        r['sib_strong'] = [c for c in strong if c != r['child']]

# ---------- 报告 ----------
out = []
def w(s=''): out.append(s)

w("=" * 80)
w("支系(house)关系对家族复用置信度的提升  —— 完整分析")
w("=" * 80)
w(f"vanilla house 总数        : {len(van_houses)}")
w(f"vanilla dynasty 总数      : {len(van_dyns)}")
w(f"被归并 child 总数         : {len(rows)}")
w(f"归并 parent 宗族数        : {len(by_parent)}")
w()
w("【关键背景】v2 的 272 条匹配只覆盖「数字 ID 型」vanilla dynasty。")
w("           vanilla 的日本家族全部是命名 key（japanese_fujiwara / japanese_minamoto_*），")
w("           因此日本系在 v2 里 100% 缺失。本分析补上这一块。")
w()

jp_children = [r for r in rows if r['parent'] in JP_PARENT_MAP]
w(f"168 个被归并 child 中，日本系 = {len(jp_children)} 个，非日本系 = {len(rows)-len(jp_children)} 个")
w()

c_self = Counter(r['self_level'] for r in rows)
w("【一】原始证据等级（v2 口径）")
for k in ('STRONG', 'NAME', 'WEAK', 'NONE'):
    w(f"    {k:<8}: {c_self.get(k,0)}")
w()

aligned = [r for r in rows if r['aligned']]
same_house = [r for r in rows if r['van_house']]
not_aligned = [r for r in rows if r['van_house'] and not r['aligned']]
w(f"【二】S1 铁证：vanilla 有同名 house 且 parent 对得上 → {len(aligned)} 个")
w(f"【三】vanilla 有同名 house（含 parent 对不上的）→ {len(same_house)} 个")
w(f"      其中 parent 对不上 → {len(not_aligned)} 个")
w()

upgraded = []
for r in rows:
    if r['self_level'] == 'STRONG':
        continue
    reasons = []
    if r['aligned']:
        reasons.append('S1铁证')
    elif r['van_house']:
        reasons.append('S2同名house')
    if r['parent_level'] == 'STRONG':
        reasons.append('S3父锚定')
    if r['sib_strong']:
        reasons.append('S4兄弟锚定')
    if reasons:
        r['reasons'] = reasons
        upgraded.append(r)

w(f"【四】可提升置信度的家族：{len(upgraded)} 个（原有强证据的 {c_self.get('STRONG',0)} 个不算在内）")
w()
buckets = defaultdict(list)
for r in upgraded:
    buckets[(r['self_level'], '+'.join(r['reasons']))].append(r)
for k in sorted(buckets, key=lambda x: -len(buckets[x])):
    w(f"    {k[0]:<6} + {k[1]:<26} : {len(buckets[k])} 个")
w()

w("=" * 80)
w("【五】S1 铁证清单（vanilla house 已存在 + 父宗族一致 → 可直接复用 vanilla house key）")
w("=" * 80)
aligned.sort(key=lambda r: (r['self_level'] != 'STRONG', r['child']))
for r in aligned:
    w(f"{r['child']:<34} -> {r['parent']:<24} [{r['self_level']}]")
    w(f"    复用目标 : {r['van_house']}  (name={r['van_house_name']}, parent={r['van_house_parent']} {r['van_house_parent_name']})")
    w(f"    自身证据 : strong={r['self_strong']} name_hits={r['self_name_hits']} mod_n={r['self_mod_n']} van_n={r['self_van_n']}")
    w()
w()

w("=" * 80)
w("【六】S2 同名 house 但父宗族不一致（需人工判定，可能是同姓不同流）")
w("=" * 80)
for r in sorted(not_aligned, key=lambda r: r['child']):
    w(f"{r['child']:<34} mod_parent={r['parent']:<22} vanilla_house={r['van_house']}")
    w(f"    vanilla parent = {r['van_house_parent']} ({r['van_house_parent_name']})   mod parent 对应 = {','.join(r['parent_van_keys']) or '-'}")
    w()

w("=" * 80)
w("【七】S3/S4 间接提升（无同名 house，靠父/兄弟传递）")
w("=" * 80)
indirect = [r for r in upgraded if not r['van_house']]
indirect.sort(key=lambda r: (r['self_level'], r['child']))
for r in indirect:
    w(f"{r['child']:<34} -> {r['parent']:<24} [{r['self_level']}] {'+'.join(r['reasons'])}")
    if r['sib_strong']:
        w(f"    强证据兄弟: {', '.join(r['sib_strong'][:6])}")
    w()

w("=" * 80)
w("【八】42 个 parent 宗族：vanilla 对应 + 支系覆盖")
w("=" * 80)
for p in sorted(by_parent, key=lambda x: -len(by_parent[x])):
    sibs = by_parent[p]
    n_s1 = sum(1 for s in sibs if s['aligned'])
    n_s2 = sum(1 for s in sibs if s['van_house'])
    pkeys = sorted(van_parent_keys(p))
    w(f"{p:<28} {lv(matches.get(p)):<7} 支系={len(sibs):<3} S1={n_s1:<3} 同名house={n_s2:<3} vanilla={','.join(pkeys) or '-'}")
w()

report = '\n'.join(out)
open(os.path.join(BASE, 'house_confidence_upgrade.txt'), 'w', encoding='utf-8').write(report)
json.dump({'rows': rows, 'aligned': len(aligned), 'upgraded': len(upgraded)},
          open(os.path.join(BASE, 'house_confidence_upgrade.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

print(f"rows={len(rows)} aligned(S1)={len(aligned)} same_house={len(same_house)} upgraded={len(upgraded)}")
print(f"JP children={len(jp_children)}")
