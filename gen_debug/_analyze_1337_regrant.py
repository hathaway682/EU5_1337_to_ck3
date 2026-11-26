# -*- coding: utf-8 -*-
"""只读分析：1337 重复授予块的具体形态，供外科手术式删除 holder 行使用。"""
import os, re, json

TITLES_DIR = r"D:/Documents/Paradox Interactive/Crusader Kings III/mod/EU5_Modern_Borders_noshape/history/titles"
DATE_RE = re.compile(r'^(\s*)(\d{1,4})\.(\d{1,2})\.(\d{1,2})\s*=\s*\{')
HOLDER_RE = re.compile(r'(?<![a-z_])holder\s*=\s*([A-Za-z0-9_\-]+)')
KEY_RE = re.compile(r'^([A-Za-z0-9_\-]+)\s*=\s*\{')

def analyze(path):
    with open(path, 'rb') as f:
        raw = f.read()
    enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    crlf = raw.count(b'\r\n')
    lf = raw.count(b'\n')
    text = raw.decode(enc)
    lines = text.split('\n')
    titles = []
    cur_title = None
    title_depth = None
    depth = 0
    cur_date = None
    date_depth = None
    date_start = None
    date_holder = None
    date_holder_line = None
    date_entries = []
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if s.startswith('#'):
            continue
        if cur_title is None:
            m = KEY_RE.match(line)
            if m:
                cur_title = m.group(1)
                depth += line.count('{') - line.count('}')
                title_depth = depth
                date_entries = []
            continue
        m = DATE_RE.match(line)
        if m and depth == title_depth:
            cur_date = (int(m.group(2)), int(m.group(3)), int(m.group(4)))
            date_start = i
            date_depth = depth + 1
            date_holder = None
            date_holder_line = None
            depth = date_depth
            hm = HOLDER_RE.search(line)
            if hm:
                date_holder = hm.group(1)
                date_holder_line = i
            if '}' in line[line.index('{')+1:]:
                date_entries.append({'date': cur_date, 'holder': date_holder,
                                     'holder_line': date_holder_line,
                                     'start': date_start, 'end': i})
                cur_date = None
                depth = title_depth
            continue
        if cur_date is not None:
            hm = HOLDER_RE.search(line)
            if hm and date_holder is None:
                date_holder = hm.group(1)
                date_holder_line = i
        depth += line.count('{') - line.count('}')
        if cur_date is not None and depth <= title_depth:
            date_entries.append({'date': cur_date, 'holder': date_holder,
                                 'holder_line': date_holder_line,
                                 'start': date_start, 'end': i})
            cur_date = None
            depth = title_depth
        elif cur_date is None and depth <= title_depth:
            titles.append({'title': cur_title, 'entries': date_entries})
            cur_title = None
            depth = 0
            date_entries = []
    if cur_title is not None:
        titles.append({'title': cur_title, 'entries': date_entries})
    return {'enc': enc, 'crlf': crlf, 'lf': lf, 'lines': lines, 'titles': titles}

def main():
    report = []
    shapes = {'single_line': 0, 'multi_line': 0, 'empty_after_remove': 0, 'holder_zero': 0}
    for fn in sorted(f for f in os.listdir(TITLES_DIR) if f.endswith('.txt')):
        path = os.path.join(TITLES_DIR, fn)
        info = analyze(path)
        for t in info['titles']:
            seq = sorted(t['entries'], key=lambda e: e['date'])
            prev = None
            for e in seq:
                if e['holder'] is None:
                    continue
                if e['date'][0] == 1337 and prev is not None and prev['holder'] == e['holder']:
                    if e['holder'] == '0':
                        shapes['holder_zero'] += 1
                    if e['start'] == e['end']:
                        shapes['single_line'] += 1
                    else:
                        shapes['multi_line'] += 1
                    # 块内除 holder 行外还有哪些内容
                    body = info['lines'][e['start']-1:e['end']]
                    others = []
                    for j, bl in enumerate(body):
                        bs = bl.strip()
                        if j == 0 or bs in ('}', '') or not bs:
                            continue
                        if HOLDER_RE.search(bs):
                            continue
                        others.append(bs)
                    if not others:
                        shapes['empty_after_remove'] += 1
                    report.append({
                        'file': fn, 'title': t['title'],
                        'prev_date': '%d.%d.%d' % prev['date'],
                        'date': '%d.%d.%d' % e['date'],
                        'holder': e['holder'],
                        'holder_line': e['holder_line'],
                        'block_start': e['start'], 'block_end': e['end'],
                        'others': others,
                    })
                prev = e
    print('encodings:')
    for fn in sorted(f for f in os.listdir(TITLES_DIR) if f.endswith('.txt')):
        info = analyze(os.path.join(TITLES_DIR, fn))
        if info['crlf']:
            pass
    print('shape:', shapes, 'total', len(report))
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_regrant_detail.json'), 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    from collections import Counter
    c = Counter()
    for r in report:
        for o in r['others']:
            c[o.split('=')[0].strip()] += 1
    print('块内其它字段:', dict(c))
    for r in report[:5]:
        print(r['file'], r['title'], r['holder_line'], r['others'])

if __name__ == '__main__':
    main()
