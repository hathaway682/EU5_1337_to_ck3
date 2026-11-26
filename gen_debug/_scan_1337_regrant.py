# -*- coding: utf-8 -*-
"""只读扫描：同一头衔内，1337 日期块把 holder 又授予给此前已持有该头衔的同一人。"""
import os, re, json

TITLES_DIR = r"D:/Documents/Paradox Interactive/Crusader Kings III/mod/EU5_Modern_Borders_noshape/history/titles"
DATE_RE = re.compile(r'^\s*(\d{1,4})\.(\d{1,2})\.(\d{1,2})\s*=\s*\{')
HOLDER_RE = re.compile(r'(?<![a-z_])holder\s*=\s*([A-Za-z0-9_\-]+)')
KEY_RE = re.compile(r'^\s*([A-Za-z0-9_\-]+)\s*=\s*\{')

def parse_file(path):
    """返回 [(title_key, [(date_tuple, holder_or_None, lineno), ...]), ...]"""
    with open(path, 'r', encoding='utf-8-sig') as f:
        lines = f.read().split('\n')
    titles = []
    cur_title = None
    depth = 0
    title_depth = None
    cur_date = None
    date_depth = None
    date_holder = None
    date_line = None
    date_entries = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith('#'):
            continue
        if cur_title is None:
            m = KEY_RE.match(line)
            if m and depth == 0:
                cur_title = m.group(1)
                title_depth = depth + line.count('{') - line.count('}')
                depth = title_depth
                date_entries = []
                continue
        else:
            m = DATE_RE.match(line)
            if m and depth == title_depth:
                cur_date = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
                date_line = i
                date_depth = depth + 1
                date_holder = None
                depth = date_depth
                # 单行块
                if '}' in line:
                    hm = HOLDER_RE.search(line)
                    if hm:
                        date_holder = hm.group(1)
                    date_entries.append((cur_date, date_holder, date_line))
                    cur_date = None
                    depth = title_depth
                continue
            if cur_date is not None:
                hm = HOLDER_RE.search(line)
                if hm and date_holder is None:
                    date_holder = hm.group(1)
            depth += line.count('{') - line.count('}')
            if cur_date is not None and depth <= title_depth:
                date_entries.append((cur_date, date_holder, date_line))
                cur_date = None
                depth = title_depth
            elif cur_date is None and depth <= title_depth:
                titles.append((cur_title, date_entries))
                cur_title = None
                depth = 0
                date_entries = []
    if cur_title is not None:
        titles.append((cur_title, date_entries))
    return titles

def main():
    dup_same = []       # 1337 块 holder 与紧邻前一 holder 相同
    seen_titles = {}
    files = [f for f in sorted(os.listdir(TITLES_DIR)) if f.endswith('.txt')]
    for fn in files:
        path = os.path.join(TITLES_DIR, fn)
        for title, entries in parse_file(path):
            if not entries:
                continue
            # 按日期稳定排序
            seq = sorted(entries, key=lambda e: e[0])
            prev_holder = None
            prev_date = None
            for date, holder, ln in seq:
                if holder is None:
                    continue
                is_1337 = (date[0] == 1337)
                if is_1337 and prev_holder == holder:
                    dup_same.append({
                        'file': fn, 'title': title,
                        'prev_date': '%d.%d.%d' % prev_date,
                        'date': '%d.%d.%d' % date,
                        'holder': holder, 'line': ln,
                    })
                prev_holder = holder
                prev_date = date
            seen_titles.setdefault(title, []).append(fn)

    print('扫描文件数:', len(files))
    print('1337 重复授予(同一人)数量:', len(dup_same))
    with open(os.path.join(os.path.dirname(__file__), '_scan_1337_regrant.json'), 'w', encoding='utf-8') as f:
        json.dump(dup_same, f, ensure_ascii=False, indent=1)
    by_file = {}
    for d in dup_same:
        by_file.setdefault(d['file'], 0)
        by_file[d['file']] += 1
    print('按文件分布:', by_file)
    for d in dup_same[:30]:
        print('  %s | %s | %s->%s | %s | 行%d' % (d['file'], d['title'], d['prev_date'], d['date'], d['holder'], d['line']))

main()
