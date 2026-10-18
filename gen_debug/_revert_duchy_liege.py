import io, re, sys, shutil, datetime

def revert_duchy_liege(path):
    # safety copy of the CURRENT (with-liege) state so it can be restored if needed
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = path + ".bak_with_liege_" + stamp
    shutil.copy2(path, bak)

    raw = io.open(path, encoding="utf-8-sig").read()
    lines = raw.splitlines(keepends=True)
    out = []
    depth = 0
    cur_title = None
    in_d = False
    date_open_depth = None
    in_date = False
    removed = 0

    for line in lines:
        s = line.strip()
        m_title = re.match(r'^([A-Za-z][\w.]*)\s*=\s*\{', s)
        m_date = re.match(r'^1337\.1\.1\s*=\s*\{', s)
        opens = s.count('{')
        closes = s.count('}')

        if depth == 0 and m_title:
            cur_title = m_title.group(1)
            in_d = cur_title.startswith('d_')

        if depth == 1 and m_date and in_d:
            date_open_depth = depth + 1
            in_date = True

        # only remove liege lines that sit inside a duchy title's 1337.1.1 block
        if in_d and in_date and s.startswith('liege = '):
            removed += 1
            continue

        out.append(line)

        depth += opens - closes
        if depth < 0:
            depth = 0
        if date_open_depth is not None and depth < date_open_depth:
            in_date = False
            date_open_depth = None
        if depth == 0:
            in_d = False
            cur_title = None

    new = ''.join(out)
    # preserve BOM + CRLF convention
    io.open(path, 'w', encoding='utf-8-sig', newline='').write(new)
    return removed, bak

if __name__ == '__main__':
    for p in sys.argv[1:]:
        n, bak = revert_duchy_liege(p)
        print(p, '-> removed', n, 'liege lines; backup:', bak)
