import io, re, sys, shutil, datetime

def extract_duchy_lieges(path):
    raw = io.open(path, encoding="utf-8-sig").read()
    lines = raw.splitlines(keepends=True)
    dmap = {}
    depth = 0
    cur_title = None
    in_d = False
    date_open_depth = None
    in_date = False
    for line in lines:
        s = line.strip()
        m_title = re.match(r'^([A-Za-z][\w.]*)\s*=\s*\{', s)
        m_date = re.match(r'^1337\.1\.1\s*=\s*\{', s)
        opens = s.count('{'); closes = s.count('}')
        if depth == 0 and m_title:
            cur_title = m_title.group(1)
            in_d = cur_title.startswith('d_')
        if depth == 1 and m_date and in_d:
            date_open_depth = depth + 1
            in_date = True
        if in_d and in_date and s.startswith('liege = '):
            dmap[cur_title] = line  # raw line incl. indent + CRLF
        depth += opens - closes
        if depth < 0: depth = 0
        if date_open_depth is not None and depth < date_open_depth:
            in_date = False; date_open_depth = None
        if depth == 0:
            in_d = False; cur_title = None
    return dmap

def restore(path, dmap):
    raw = io.open(path, encoding="utf-8-sig").read()
    lines = raw.splitlines(keepends=True)
    out = []
    depth = 0
    cur_title = None
    in_d = False
    date_open_depth = None
    in_date = False
    done = set()
    restored = 0
    for line in lines:
        s = line.strip()
        m_title = re.match(r'^([A-Za-z][\w.]*)\s*=\s*\{', s)
        m_date = re.match(r'^1337\.1\.1\s*=\s*\{', s)
        opens = s.count('{'); closes = s.count('}')
        if depth == 0 and m_title:
            cur_title = m_title.group(1)
            in_d = cur_title.startswith('d_')
        if depth == 1 and m_date and in_d:
            date_open_depth = depth + 1
            in_date = True
        out.append(line)
        # detect the closing brace of the 1337.1.1 block
        if in_date and date_open_depth is not None and (depth + opens - closes) < date_open_depth \
           and cur_title in dmap and cur_title not in done:
            out.insert(len(out) - 1, dmap[cur_title])
            done.add(cur_title)
            restored += 1
        depth += opens - closes
        if depth < 0: depth = 0
        if date_open_depth is not None and depth < date_open_depth:
            in_date = False; date_open_depth = None
        if depth == 0:
            in_d = False; cur_title = None
    new = ''.join(out)
    io.open(path, 'w', encoding='utf-8-sig', newline='').write(new)
    return restored, len(dmap)

if __name__ == '__main__':
    args = sys.argv[1:]
    for i in range(0, len(args), 2):
        cur, pre = args[i], args[i+1]
        shutil.copy2(cur, cur + ".bak_overreverted_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
        dmap = extract_duchy_lieges(pre)
        n, total = restore(cur, dmap)
        print(cur)
        print("   pre-existing duchy lieges in pre-liege backup:", total, "| restored into current:", n)
