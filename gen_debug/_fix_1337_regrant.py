# -*- coding: utf-8 -*-
"""外科手术式删除：1337 日期块中与前一 holder 相同的重复授予。"""
import os, re, json

TITLES_DIR = r"D:/Documents/Paradox Interactive/Crusader Kings III/mod/EU5_Modern_Borders_noshape/history/titles"
HERE = os.path.dirname(os.path.abspath(__file__))
HOLDER_RE = re.compile(r'(?<![a-z_])holder\s*=\s*([A-Za-z0-9_\-]+)')

detail = json.load(open(os.path.join(HERE, '_regrant_detail.json'), encoding='utf-8'))
by_file = {}
for r in detail:
    by_file.setdefault(r['file'], []).append(r)

total_del = 0
total_repl = 0
for fn, items in sorted(by_file.items()):
    path = os.path.join(TITLES_DIR, fn)
    raw = open(path, 'rb').read()
    assert raw.startswith(b'\xef\xbb\xbf'), fn
    lines = raw.decode('utf-8-sig').split('\n')

    del_lines = set()
    replace_lines = {}
    for r in items:
        if r['block_start'] == r['block_end']:
            idx = r['block_start'] - 1
            line = lines[idx]
            m = HOLDER_RE.search(line)
            assert m and m.group(1) == r['holder'], ('single', fn, r['title'], line)
            new = HOLDER_RE.sub('', line, count=1)
            new = re.sub(r'\{\s+', '{ ', new)
            new = re.sub(r'\s+}', ' }', new)
            replace_lines[idx] = new
            total_repl += 1
        else:
            idx = r['holder_line'] - 1
            line = lines[idx]
            m = HOLDER_RE.search(line)
            assert m and m.group(1) == r['holder'], ('multi', fn, r['title'], line)
            if not r['others']:
                for i in range(r['block_start'] - 1, r['block_end']):
                    del_lines.add(i)
                total_del += (r['block_end'] - r['block_start'] + 1)
            else:
                del_lines.add(idx)
                total_del += 1

    out = []
    for i, line in enumerate(lines):
        if i in del_lines:
            continue
        out.append(replace_lines.get(i, line))
    new_text = '\n'.join(out)

    tmp = path + '.tmp_new'
    with open(tmp, 'w', encoding='utf-8-sig', newline='') as f:
        f.write(new_text)
    os.replace(tmp, path)
    print('%s: 删除%d行 改写%d行  %d -> %d 行' % (fn, len(del_lines), len(replace_lines),
                                              len(lines), len(out)))

print('合计删除行:', total_del, ' 单行改写:', total_repl)
