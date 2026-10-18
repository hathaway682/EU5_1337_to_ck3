import io, sys, shutil, datetime

def reorder(path):
    rb = io.open(path, 'rb').read()
    has_bom = rb.startswith(b'\xef\xbb\xbf')
    has_crlf = b'\r\n' in rb
    enc = 'utf-8-sig' if has_bom else 'utf-8'
    text = io.open(path, encoding=enc).read()  # universal newlines -> \n
    lines = text.split('\n')

    start = None
    for i, l in enumerate(lines):
        if l.strip() == 'c_swabian_alb = {':
            start = i
            break
    if start is None:
        return "c_swabian_alb not found"

    depth = 0
    end = None
    for i in range(start, len(lines)):
        depth += lines[i].count('{') - lines[i].count('}')
        if depth == 0:
            end = i
            break
    if end is None:
        return "unbalanced county block"

    block = lines[start:end + 1]

    bs = None
    for i, l in enumerate(block):
        if l.strip() == 'b_balingen = {':
            bs = i
            break
    if bs is None:
        return "b_balingen not inside c_swabian_alb"

    bd = 0
    be = None
    for i in range(bs, len(block)):
        bd += block[i].count('{') - block[i].count('}')
        if bd == 0:
            be = i
            break
    if be is None:
        return "unbalanced b_balingen block"

    balingen = block[bs:be + 1]
    del block[bs:be + 1]

    cs = None
    for i, l in enumerate(block):
        if l.strip().startswith('color'):
            cs = i
            break
    if cs is None:
        return "no county color line"

    first_before = None
    for l in block[cs + 1:]:
        if l.strip().startswith('b_'):
            first_before = l.strip()
            break

    newblock = block[:cs + 1] + balingen + block[cs + 1:]
    newlines = lines[:start] + newblock + lines[end + 1:]

    out = '\n'.join(newlines)
    if has_crlf:
        out = out.replace('\n', '\r\n')

    shutil.copy2(path, path + ".bak_balingen_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    io.open(path, 'w', encoding=enc, newline='').write(out)

    # report first barony after
    first_after = None
    for l in newblock[cs + 1:]:
        if l.strip().startswith('b_'):
            first_after = l.strip()
            break
    return "BOM=%s CRLF=%s | first barony before: %s | after: %s" % (has_bom, has_crlf, first_before, first_after)

for p in sys.argv[1:]:
    print(p)
    print("   ", reorder(p))
