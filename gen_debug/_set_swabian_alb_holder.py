import io, sys, shutil, datetime

def set_holder(path, county='c_swabian_alb', old='hhb_margaretha_hohenberg_rotenburg',
               new='hoh_friedrich_ix_von_zollern'):
    rb = io.open(path, 'rb').read()
    has_bom = rb.startswith(b'\xef\xbb\xbf')
    has_crlf = b'\r\n' in rb
    enc = 'utf-8-sig' if has_bom else 'utf-8'
    text = io.open(path, encoding=enc).read()  # universal newlines -> \n
    lines = text.split('\n')

    start = None
    for i, l in enumerate(lines):
        if l.strip() == county + ' = {':
            start = i
            break
    if start is None:
        return 'county block not found'

    depth = 0
    end = None
    for i in range(start, len(lines)):
        depth += lines[i].count('{') - lines[i].count('}')
        if depth == 0:
            end = i
            break
    if end is None:
        return 'unbalanced county block'

    changed = 0
    for i in range(start, end + 1):
        s = lines[i].strip()
        if s == 'holder = ' + old:
            indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
            lines[i] = indent + 'holder = ' + new
            changed += 1
    if changed != 1:
        return 'expected exactly 1 holder replacement in block, got %d' % changed

    out = '\n'.join(lines)
    if has_crlf:
        out = out.replace('\n', '\r\n')
    shutil.copy2(path, path + '.bak_swabian_holder_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    io.open(path, 'w', encoding=enc, newline='').write(out)
    return 'holder -> ' + new + ' (BOM=%s CRLF=%s)' % (has_bom, has_crlf)

for p in sys.argv[1:]:
    print(p)
    print('   ', set_holder(p))
