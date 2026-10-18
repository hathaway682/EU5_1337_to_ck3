# -*- coding: utf-8 -*-
"""只读：统计 CK3 原版 history/province_mapping 覆盖的省，能否解析出真实 faith/culture。

机制：province_mapping 里 `目标省 = 代表省`，被映射省继承代表省的 history（culture/rite）。
      若代表省自己也链到别处，继续跟；成环则记 cycle。
输出：gen_debug/ck3_province_mapping_coverage.csv + .txt
不写任何游戏/mod 文件。
"""
import io, os, re, csv
from collections import defaultdict, Counter

GAME = r'E:\SteamLibrary\steamapps\common\Crusader Kings III\game'
PMDIR = os.path.join(GAME, 'history', 'province_mapping')
PHDIR = os.path.join(GAME, 'history', 'provinces')
OUTDIR = r'D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape\gen_debug'
CSV_OUT = os.path.join(OUTDIR, 'ck3_province_mapping_coverage.csv')
TXT_OUT = os.path.join(OUTDIR, 'ck3_province_mapping_coverage.txt')

START = (1337, 12, 31)  # 取该日期及之前的最新历史


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


def parse_history():
    hist = {}
    for fn in sorted(os.listdir(PHDIR)):
        if not fn.endswith('.txt'):
            continue
        txt = read(os.path.join(PHDIR, fn))
        for m in re.finditer(r'(?m)^(\d+)\s*=\s*\{', txt):
            pid = int(m.group(1))
            body = block_body(txt, m.end() - 1)
            rec = hist.get(pid)
            if rec is None:
                rec = {'base': None, 'dated': [], 'culture': None}
                hist[pid] = rec
            depth = 0
            cur_date = None
            for raw in body.splitlines():
                s = raw.strip()
                if not s:
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
                depth += s.count('{') - s.count('}')
                if depth <= 1:
                    cur_date = None
    return hist


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
    return best[1] if best else None  # (kind, val)


def faith_of(pid, hist, smap, seen=None):
    if seen is None:
        seen = []
    if pid in seen:
        return None, seen
    seen = seen + [pid]
    f = eff_faith(pid, hist)
    if f:
        return f, seen
    r = smap.get(pid)
    if r is not None:
        return faith_of(r, hist, smap, seen)
    return None, seen


def culture_of(pid, hist, smap, seen=None):
    if seen is None:
        seen = []
    if pid in seen:
        return None
    seen = seen + [pid]
    h = hist.get(pid)
    if h and h['culture']:
        return h['culture']
    r = smap.get(pid)
    if r is not None:
        return culture_of(r, hist, smap, seen)
    return None


def parse_mapping(path):
    mp = defaultdict(list)
    commented = 0
    for line in read(path).splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith('#'):
            if re.match(r'^#\s*\d+\s*=\s*\d+', s):
                commented += 1
            continue
        m = re.match(r'^(\d+)\s*=\s*(\d+)', s)
        if m:
            mp[int(m.group(1))].append(int(m.group(2)))
    return mp, commented


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    hist = parse_history()
    rows = []
    summary = []
    grand = Counter()
    grand_faiths = Counter()
    gaps = defaultdict(lambda: {'no-data': [], 'conflict': []})
    for fn in sorted(os.listdir(PMDIR)):
        if not fn.endswith('.txt'):
            continue
        mp, commented = parse_mapping(os.path.join(PMDIR, fn))
        smap = {t: reps[0] for t, reps in mp.items() if len(reps) == 1}
        c = Counter()
        faiths = Counter()
        idcount = 0
        for t, reps in sorted(mp.items()):
            if len(reps) > 1:
                rows.append([fn, t, '|'.join(map(str, reps)), 'N', '', '', 'conflict', ''])
                c['conflict'] += 1
                gaps[fn]['conflict'].append('%d=%s' % (t, '|'.join(map(str, reps))))
                continue
            r = reps[0]
            f, chain = faith_of(t, hist, smap)
            cul = culture_of(t, hist, smap)
            val = f[1] if f else ''
            is_id = 'Y' if r == t else 'N'
            if is_id == 'Y':
                idcount += 1
            status = 'ok' if f else 'no-data'
            rows.append([fn, t, str(r), is_id, cul or '', val, status, '>'.join(map(str, chain))])
            c[status] += 1
            if f:
                faiths[f[1]] += 1
            else:
                gaps[fn]['no-data'].append(t)
        total = len(mp)
        summary.append((fn, total, c['ok'], c['no-data'], c['conflict'], idcount, commented, len(faiths)))
        grand['targets'] += total
        grand['ok'] += c['ok']
        grand['no_data'] += c['no-data']
        grand['conflict'] += c['conflict']
        grand['identity'] += idcount
        grand['commented'] += commented
        for k, v in faiths.items():
            grand_faiths[k] += v

    with io.open(CSV_OUT, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['file', 'target_province', 'rep_province', 'identity', 'culture', 'faith', 'status', 'chain'])
        for row in rows:
            w.writerow(row)

    lines = []
    lines.append('CK3 vanilla province_mapping faith coverage (effective at %d.%d.%d)' % START)
    lines.append('')
    lines.append('%-16s %8s %6s %8s %9s %9s %10s %8s' % (
        'file', 'targets', 'ok', 'no-data', 'conflict', 'identity', 'commented', 'faiths'))
    for s in summary:
        lines.append('%-16s %8d %6d %8d %9d %9d %10d %8d' % (
            s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7]))
    lines.append('')
    lines.append('TOTAL targets=%d ok=%d no_data=%d conflict=%d identity=%d commented=%d'
                 % (grand['targets'], grand['ok'], grand['no_data'], grand['conflict'],
                    grand['identity'], grand['commented']))
    lines.append('')
    lines.append('distinct faiths across all mapped provinces:')
    for k, v in grand_faiths.most_common():
        lines.append('  %-42s %d' % (k, v))
    lines.append('')
    lines.append('--- gaps by file (province ids) ---')
    for s in summary:
        fn = s[0]
        nd = gaps[fn]['no-data']
        cf = gaps[fn]['conflict']
        if nd or cf:
            lines.append('%s: no-data=%s conflict=%s' % (fn, nd, cf))
    lines.append('')
    lines.append('CSV: ' + CSV_OUT)
    io.open(TXT_OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
    print('OK targets=%d ok=%d no_data=%d conflict=%d identity=%d'
          % (grand['targets'], grand['ok'], grand['no_data'], grand['conflict'], grand['identity']))


if __name__ == '__main__':
    main()
