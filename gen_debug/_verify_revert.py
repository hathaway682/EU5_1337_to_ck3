import io, re, sys

def count(path):
    raw = io.open(path, encoding="utf-8-sig").read()
    lines = raw.splitlines(keepends=True)
    depth = 0
    cur_title = None
    in_d = False
    date_open_depth = None
    in_date = False
    d_with_liege = 0
    non_d_with_liege = 0
    d_total = 0
    for line in lines:
        s = line.strip()
        m_title = re.match(r'^([A-Za-z][\w.]*)\s*=\s*\{', s)
        m_date = re.match(r'^1337\.1\.1\s*=\s*\{', s)
        opens = s.count('{'); closes = s.count('}')
        if depth == 0 and m_title:
            cur_title = m_title.group(1)
            in_d = cur_title.startswith('d_')
            if in_d:
                d_total += 1
        if depth == 1 and m_date and in_d:
            date_open_depth = depth + 1
            in_date = True
        if in_d and in_date and s.startswith('liege = ') and not s.startswith('liege ='):
            pass
        if in_d and in_date and s.startswith('liege = '):
            d_with_liege += 1
        elif (not in_d) and depth == 2 and in_date and s.startswith('liege = '):
            non_d_with_liege += 1
        out = line
        depth += opens - closes
        if depth < 0: depth = 0
        if date_open_depth is not None and depth < date_open_depth:
            in_date = False; date_open_depth = None
        if depth == 0:
            in_d = False; cur_title = None
    return d_total, d_with_liege, non_d_with_liege

for p in sys.argv[1:]:
    d_total, d_l, nd_l = count(p)
    print(p)
    print("   d_ blocks total:", d_total, "| d_ with liege:", d_l, "| non-d_ with liege:", nd_l)
