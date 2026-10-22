import io, sys

def find_matching_brace(text, brace_idx):
    depth = 0
    i = brace_idx
    while i < len(text):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1

def revert_landed(path):
    text = io.open(path, encoding="utf-8-sig", newline="").read()
    marker = "c_swabian_alb = {"
    i = text.find(marker)
    assert i != -1, "c_swabian_alb not found in " + path
    b_start = text.find("b_balingen = {", i)
    assert b_start != -1, "b_balingen not found in " + path
    b_brace = text.find("{", b_start)
    b_end = find_matching_brace(text, b_brace)
    h_start = text.find("b_hohenberg = {", b_end)
    assert h_start != -1, "b_hohenberg not found in " + path
    h_brace = text.find("{", h_start)
    h_end = find_matching_brace(text, h_brace)
    b_block = text[b_start:b_end+1]
    h_block = text[h_start:h_end+1]
    sep = text[b_end+1:h_start]
    # restore original order: hohenberg first, then balingen
    new_region = h_block + sep + b_block
    text = text[:b_start] + new_region + text[h_end+1:]
    io.open(path, "w", encoding="utf-8-sig", newline="").write(text)
    print("landed reverted:", path)

def revert_title(path):
    text = io.open(path, encoding="utf-8-sig", newline="").read()
    marker = "c_swabian_alb = {"
    i = text.find(marker)
    assert i != -1, "c_swabian_alb not found in " + path
    rest = text[i:]
    j = rest.find("1337.4.1 = {")
    assert j != -1, "1337 block not found in " + path
    k = j
    depth = 0
    while k < len(rest):
        if rest[k] == '{':
            depth += 1
        elif rest[k] == '}':
            depth -= 1
            if depth == 0:
                break
        k += 1
    block = rest[j:k+1]
    new_block = block.replace("holder = hoh_friedrich_ix_von_zollern",
                              "holder = hhb_margaretha_hohenberg_rotenburg")
    assert new_block != block, "holder not replaced in " + path
    text = text[:i] + rest[:j] + new_block + rest[k+1:]
    io.open(path, "w", encoding="utf-8-sig", newline="").write(text)
    print("title reverted:", path)

for p in sys.argv[1:]:
    if "landed_titles" in p:
        revert_landed(p)
    else:
        revert_title(p)
