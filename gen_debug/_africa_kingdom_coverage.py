# -*- coding: utf-8 -*-
"""只读：CK3 非洲完整信仰覆盖（区分荒地 vs 有人口缺信仰）。
口径 = 非洲王国历史文件(k_*)里的省 ∪ 00_guinea/00_egypt 映射涉及的省。
source: own / mapped / conflict / none(再拆 waste=无人省, missing=有块但无信仰)
输出 gen_debug。不写任何游戏/mod 文件。
"""
import io, os, re, csv
from collections import defaultdict, Counter

GAME = r'E:\SteamLibrary\steamapps\common\Crusader Kings III\game'
PMDIR = os.path.join(GAME, 'history', 'province_mapping')
PHDIR = os.path.join(GAME, 'history', 'provinces')
OUTDIR = r'D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape\gen_debug'
CSV_OUT = os.path.join(OUTDIR, 'ck3_africa_kingdom_coverage.csv')
TXT_OUT = os.path.join(OUTDIR, 'ck3_africa_kingdom_coverage.txt')

START = (1337, 12, 31)

AFRICAN = [
    'k_maghreb', 'k_africa', 'k_tahert', 'k_sahara', 'k_egypt',
    'k_nubia', 'k_anbiya', 'k_blemmyia', 'k_darfur', 'k_abyssinia', 'k_adal',
    'k_ajuraan', 'k_damot', 'k_bale', 'k_zanj',
    'k_guinea', 'k_ghana', 'k_mali', 'k_jenne', 'k_takrur', 'k_songhay',
    'k_gur', 'k_gurma', 'k_hausaland', 'k_igbo-benue', 'k_yorubaland',
    'k_akan', 'k_kanem', 'k_borgu', 'k_sao', 'k_kongo', 'k_kong',
]


def is_pagan(f):
    if not f:
        return False
    fl = f.lower()
    return ('pagan' in fl) or f in {
        'hantuism', 'kaharingan', 'dayawism', 'bilikuism', 'satsana_phi',
        'tolotang', 'aluk', 'megalithism', 'marapu', 'animism'}


def read(p):
    return io.open(p, encoding='utf-8-sig', errors='ignore').read()


def block_body(txt, start):
    d = 0
    for j in range(start, len(txt)):
        c = txt[j]
        if c == '{':
            d += 1
        elif c == '}':
            d -= 1
            if d == 0:
                return txt[start:j + 1]
    return txt[start:]


def parse_file(path):
    out = {}
    txt = read(path)
    for m in re.finditer(r'(?m)^(\d+)\s*=\s*\{', txt):
        pid = int(m.group(1))
        body = block_body(txt, m.end() - 1)
        rec = out.get(pid)
        if rec is None:
            rec = {'base': None, 'dated': [], 'culture': None, 'holding': None}
            out[pid] = rec
        depth = 0
        cur_date = None
        for raw in body.splitlines():
            s = raw.strip()
            if not s or s.startswith('#'):
                continue
            dm = re.match(r'^(\d+)\.(\d+)\.(\d+)\s*=\s*\{', s)
            if dm and depth == 1:
                cur_date = (int(dm.group(1)), int(dm.group(2)), int(dm.group(3)))
                rest = s[dm.end():]
                km2 = re.search(r'(rite|faith|religion)\s*=\s*(\S+)', rest)
                if km2:
                    rec['dated'].append((cur_date, (km2.group(1), km2.group(2))))
            km = re.match(r'^(rite|faith|religion)\s*=\s*(\S+)', s)
            if km:
                if depth == 1 and rec['base'] is None:
                    rec['base'] = (km.group(1), km.group(2))
                elif depth == 2 and cur_date:
                    rec['dated'].append((cur_date, (km.group(1), km.group(2))))
            cm = re.match(r'^culture\s*=\s*(\S+)', s)
            if cm and depth == 1 and rec['culture'] is None:
                rec['culture'] = cm.group(1)
            hm = re.match(r'^holding\s*=\s*(\S+)', s)
            if hm and depth == 1 and rec['holding'] is None:
                rec['holding'] = hm.group(1)
            depth += s.count('{') - s.count('}')
            if depth <= 1:
                cur_date = None
    return out


def eff_faith(pid, hist):
    h = hist.get(pid)
    if not h:
        return None
    best = None
    if h['base']:
        best = ((0, 0, 0), h['base'])
    for date, v in h['dated']:
        if date <= START and (best is None or date >= best[0]):
            best = (date, v)
    return best[1] if best else None


def faith_of(pid, hist, smap, seen=None):
    if seen is None:
        seen = []
    if pid in seen:
        return None
    seen = seen + [pid]
    f = eff_faith(pid, hist)
    if f:
        return f[1]
    r = smap.get(pid)
    if r is not None:
        return faith_of(r, hist, smap, seen)
    return None


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    hist = {}
    for fn in sorted(os.listdir(PHDIR)):
        if fn.endswith('.txt'):
            hist.update(parse_file(os.path.join(PHDIR, fn)))

    multi = defaultdict(list)
    for fn in sorted(os.listdir(PMDIR)):
        if not fn.endswith('.txt'):
            continue
        for line in read(os.path.join(PMDIR, fn)).splitlines():
            s = line.strip()
            if not s or s.startswith('#'):
                continue
            m = re.match(r'^(\d+)\s*=\s*(\d+)', s)
            if m:
                multi[int(m.group(1))].append(int(m.group(2)))
    smap = {t: reps[0] for t, reps in multi.items() if len(reps) == 1}

    A = {}
    for k in AFRICAN:
        p = os.path.join(PHDIR, k + '.txt')
        if os.path.exists(p):
            for pid in parse_file(p):
                A.setdefault(pid, k)
    B = set()
    for fn in ('00_guinea.txt', '00_egypt.txt'):
        p = os.path.join(PMDIR, fn)
        if os.path.exists(p):
            for line in read(p).splitlines():
                s = line.strip()
                if not s or s.startswith('#'):
                    continue
                m = re.match(r'^(\d+)\s*=\s*(\d+)', s)
                if m:
                    B.add(int(m.group(1)))
                    B.add(int(m.group(2)))

    allpids = sorted(set(A) | B)
    rows = []
    per = defaultdict(Counter)
    faiths = Counter()
    missing_by = defaultdict(list)
    order = AFRICAN + ['(mapping-only)']
    for pid in allpids:
        k = A.get(pid, '(mapping-only)')
        h = hist.get(pid)
        own = eff_faith(pid, hist)
        if own:
            src = 'own'; fv = own[1]
        elif len(multi.get(pid, [])) > 1:
            src = 'conflict'; fv = None
        else:
            fv = faith_of(pid, hist, smap)
            src = 'mapped' if fv else 'none'
        cul = (h or {}).get('culture') or ''
        hold = (h or {}).get('holding')
        # none 再拆：有块且(holding=none 或 无culture无faith) = 荒地; 其余 = 缺信仰
        if src == 'none':
            if h is not None and (hold == 'none' or (not cul and not fv)):
                src = 'waste'
            else:
                src = 'missing'
                missing_by[k].append(pid)
        pg = 'Y' if is_pagan(fv) else 'N'
        rows.append([k, pid, src, cul, fv or '', pg])
        per[k][src] += 1
        if pg == 'Y':
            per[k]['pagan'] += 1
        if fv:
            faiths[fv] += 1

    with io.open(CSV_OUT, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['kingdom', 'province', 'source', 'culture', 'faith', 'pagan'])
        for r in rows:
            w.writerow(r)

    lines = []
    lines.append('CK3 vanilla AFRICA province faith coverage (effective at %d.%d.%d)' % START)
    lines.append('scope = 非洲王国历史文件(k_*)里的省  UNION  00_guinea/00_egypt 映射涉及的省')
    lines.append('source: own=自带块  mapped=靠映射继承  conflict=映射冲突')
    lines.append('        waste=无人省(holding=none/空块)  missing=有块但无信仰(真正的缺口)')
    lines.append('')
    lines.append('%-16s %6s %5s %7s %8s %6s %8s %7s'
                 % ('kingdom', 'provs', 'own', 'mapped', 'conflict', 'waste', 'missing', 'pagan'))
    g = Counter()
    for k in order:
        c = per.get(k)
        if not c:
            continue
        tot = sum(c[s] for s in ('own', 'mapped', 'conflict', 'waste', 'missing'))
        if tot == 0:
            continue
        lines.append('%-16s %6d %5d %7d %8d %6d %8d %7d'
                     % (k, tot, c['own'], c['mapped'], c['conflict'], c['waste'], c['missing'], c['pagan']))
        for s in ('own', 'mapped', 'conflict', 'waste', 'missing', 'pagan'):
            g[s] += c[s]
        g['total'] += tot
    lines.append('')
    has = g['own'] + g['mapped']
    lines.append('TOTAL provs=%d  has_faith=%d (%.1f%%)  own=%d mapped=%d conflict=%d waste=%d missing=%d  pagan=%d'
                 % (g['total'], has, 100.0 * has / g['total'] if g['total'] else 0,
                    g['own'], g['mapped'], g['conflict'], g['waste'], g['missing'], g['pagan']))
    lines.append('')
    lines.append('distinct faiths across African provinces:')
    for f, v in faiths.most_common():
        lines.append('  %-42s %d' % (f, v))
    lines.append('')
    lines.append('--- missing (有块但无信仰，真正缺口) by kingdom ---')
    for k in order:
        lst = missing_by.get(k)
        if lst:
            lines.append('%s (%d): %s' % (k, len(lst), lst))
    lines.append('')
    lines.append('CSV: ' + CSV_OUT)
    io.open(TXT_OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
    print('OK provs=%d has=%d own=%d mapped=%d conflict=%d waste=%d missing=%d pagan=%d'
          % (g['total'], has, g['own'], g['mapped'], g['conflict'], g['waste'], g['missing'], g['pagan']))


if __name__ == '__main__':
    main()
