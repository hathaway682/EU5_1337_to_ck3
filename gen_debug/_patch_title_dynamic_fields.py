# -*- coding: utf-8 -*-
"""
补回原版 rank>=k 头衔块里的「动态称呼 / AI 优先级 / 命名 / 机制」类字段。

背景：本 mod 的 h/e/k 法理树重建后只保留了 color / capital，原版头衔上的
cultural_names（文化动态称呼）、ai_primary_priority（AI 主头衔权重）、
definite_form（定冠词形式）、can_be_named_after_dynasty、can_use_nomadic_naming、
ruler_uses_title_name、regnal 名号、can_create / can_destroy、landless、dlc_feature
等全部丢失。本脚本按 key 从游戏原版 landed_titles 原样搬回。

只跳过 color / color2 / capital（本 mod 有自己的取值）。

安全设计（2026-11-18 两次事故后）：
  1. 行尾一律按 '\\n' 切、每行 rstrip('\\r')，不再用 '\\r\\n' 做 split（混行尾文件会粘行）。
  2. 每个搬出的字段单元必须括号自平衡，不平衡直接跳过并报错。
  3. 全部改动先在内存里构造，校验「原有头衔块 depth 不变 + 全文括号平衡」通过后才落盘；
     校验不过就退出，磁盘文件一个字节都不动。

用法:
  python gen_debug/_patch_title_dynamic_fields.py --dry-run
  python gen_debug/_patch_title_dynamic_fields.py --apply
"""
import os
import re
import sys
import glob
import argparse
import collections

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = r"D:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III Beta\game\common\landed_titles"
MOD_LT = os.path.join(MOD, 'common', 'landed_titles')

KEY_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_.\-]*)\s*=\s*\{')
TITLE_RE = re.compile(r'^([hedcbk])_')
RANK = ('h_', 'e_', 'k_')
SKIP_FIELDS = {'color', 'color2', 'capital'}

AT_VARS = collections.OrderedDict([
    ('correct_culture_primary_score', '100'),
    ('correct_government_primary_score', '200'),
    ('better_than_the_alternatives_score', '50'),
    ('always_primary_score', '1000'),
    ('never_primary_score', '-1000'),
])


def read_lines(path):
    with open(path, 'rb') as f:
        raw = f.read()
    bom = raw.startswith(b'\xef\xbb\xbf')
    text = raw.decode('utf-8-sig')
    crlf = text.count('\r\n') * 2 >= text.count('\n')
    lines = [l.rstrip('\r') for l in text.split('\n')]
    if lines and lines[-1] == '':
        lines.pop()
    return lines, bom, crlf


def write_lines(path, lines, bom, crlf):
    data = ('\r\n' if crlf else '\n').join(lines) + ('\r\n' if crlf else '\n')
    tmp = path + '.wbtmp'
    with open(tmp, 'wb') as f:
        if bom:
            f.write(b'\xef\xbb\xbf')
        f.write(data.encode('utf-8'))
    os.replace(tmp, path)


def strip_comment(line):
    return line.split('#')[0] if '#' in line else line


def parse(lines):
    """key -> [ {start, depth, units:[{name,start}], children:[node]} ]"""
    out = collections.defaultdict(list)
    stack = []
    depth = 0
    for i, raw in enumerate(lines):
        line = strip_comment(raw).strip()
        if not line:
            continue
        opens, closes = line.count('{'), line.count('}')
        m = KEY_RE.match(line)
        if m and opens > closes:
            node = {'key': m.group(1), 'depth': depth, 'start': i,
                    'units': [], 'children': []}
            if stack:
                stack[-1]['children'].append(node)
            stack.append(node)
            depth += 1
            continue
        fm = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*[=<]', line)
        if fm and stack:
            stack[-1]['units'].append({'name': fm.group(1), 'start': i})
        depth += opens - closes
        while stack and depth <= stack[-1]['depth']:
            node = stack.pop()
            if TITLE_RE.match(node['key']):
                out[node['key']].append(node)
    while stack:
        node = stack.pop()
        if TITLE_RE.match(node['key']):
            out[node['key']].append(node)
    return out


def block_end(lines, start):
    depth = 0
    for i in range(start, len(lines)):
        s = strip_comment(lines[i])
        depth += s.count('{') - s.count('}')
        if depth <= 0:
            return i
    return len(lines) - 1


def balanced(seg):
    n = 0
    for l in seg:
        s = strip_comment(l)
        n += s.count('{') - s.count('}')
    return n == 0


def unit_text(lines, node, start, next_start=None):
    """字段单元原文，边界 = min(下一个字段单元, 下一个子头衔块, 块尾)，不含块尾 }"""
    cands = [block_end(lines, node['start'])]
    if next_start is not None:
        cands.append(next_start)
    for c in node['children']:
        if c['start'] > start:
            cands.append(c['start'])
            break
    end = min(cands)
    seg = lines[start:end]
    while seg and not seg[-1].strip():
        seg.pop()
    return seg


def reindent(seg, delta):
    out = []
    for l in seg:
        if not l.strip():
            out.append('')
        elif delta >= 0:
            out.append('\t' * delta + l)
        else:
            k = min(-delta, len(l) - len(l.lstrip('\t')))
            out.append(l[k:])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()
    if not (args.dry_run or args.apply):
        ap.error('需要 --dry-run 或 --apply')

    # ---- 原版 ----
    game = collections.defaultdict(list)
    for f in sorted(glob.glob(os.path.join(GAME, '*.txt'))):
        glines, _, _ = read_lines(f)
        for key, recs in parse(glines).items():
            for rec in recs:
                rec['file'] = os.path.basename(f)
                rec['lines'] = glines
                game[key].append(rec)

    # ---- mod ----
    files = {}
    for f in sorted(glob.glob(os.path.join(MOD_LT, '*.txt'))):
        lines, bom, crlf = read_lines(f)
        files[os.path.basename(f)] = {'path': f, 'lines': lines,
                                      'bom': bom, 'crlf': crlf}

    mod_index = {}
    for fn, info in files.items():
        for key, recs in parse(info['lines']).items():
            if key.startswith(RANK):
                mod_index.setdefault(key, (fn, recs[0]))

    # ---- 计划 ----
    by_file = collections.defaultdict(list)
    stats = collections.Counter()
    bad_units = []
    skipped = []
    for key in sorted(game):
        if not key.startswith(RANK):
            continue
        if key not in mod_index:
            skipped.append(key)
            continue
        fn, mrec = mod_index[key]
        glines = game[key][0]['lines']
        grec = game[key][0]

        have = {u['name'] for u in mrec['units']}
        have |= {c['key'] for c in mrec['children'] if not TITLE_RE.match(c['key'])}

        add = []
        # 单行 / 多行字段
        for idx, u in enumerate(grec['units']):
            name = u['name']
            if name in SKIP_FIELDS or name in have:
                continue
            nxt = grec['units'][idx + 1]['start'] if idx + 1 < len(grec['units']) else None
            seg = unit_text(glines, grec, u['start'], nxt)
            if not seg or not balanced(seg):
                bad_units.append((key, name, 'unbalanced' if seg else 'empty'))
                continue
            add.append((name, seg))
        # 块形式字段
        for c in grec['children']:
            if TITLE_RE.match(c['key']) or c['key'] in SKIP_FIELDS or c['key'] in have:
                continue
            end = block_end(glines, c['start'])
            seg = glines[c['start']:end + 1]
            while seg and not seg[-1].strip():
                seg.pop()
            if not balanced(seg):
                bad_units.append((key, c['key'], 'unbalanced-block'))
                continue
            add.append((c['key'], seg))

        if not add:
            continue
        delta = (mrec['depth'] + 1) - (grec['depth'] + 1)
        block = []
        for name, seg in add:
            block.extend(reindent(seg, delta))
            block.append('')
            stats[name] += 1

        ins = mrec['children'][0]['start'] if mrec['children'] else block_end(files[fn]['lines'], mrec['start'])
        by_file[fn].append((ins, block, key, [n for n, _ in add]))

    # ---- 内存插入 ----
    for fn, items in by_file.items():
        lines = files[fn]['lines']
        items.sort(key=lambda x: -x[0])
        for ins, block, key, names in items:
            prefix = [] if (ins > 0 and not lines[ins - 1].strip()) else ['']
            lines[ins:ins] = prefix + block

    # ---- @ 变量 ----
    main_file = '00_landed_titles.txt'
    lines = files[main_file]['lines']
    defined = set()
    for l in lines:
        m = re.match(r'^\ufeff?@([A-Za-z0-9_]+)\s*=', l)
        if m:
            defined.add(m.group(1))
    missing_vars = [(k, v) for k, v in AT_VARS.items() if k not in defined]
    if missing_vars:
        idx = 0
        while idx < len(lines) and not lines[idx].strip():
            idx += 1
        lines[idx:idx] = ['@%s = %s' % (k, v) for k, v in missing_vars]

    # ---- 校验 ----
    problems = []
    for fn, info in files.items():
        new_depth = {k: r[0]['depth'] for k, r in parse(info['lines']).items()}
        old_depth = {k: r[0]['depth'] for k, r in parse(read_lines(info['path'])[0]).items()}
        for k, d in old_depth.items():
            if k in new_depth and new_depth[k] != d:
                problems.append('%s: %s depth %d -> %d' % (fn, k, d, new_depth[k]))
        n = 0
        for l in info['lines']:
            s = strip_comment(l)
            n += s.count('{') - s.count('}')
        if n != 0:
            problems.append('%s: 括号不平衡 %d' % (fn, n))

    print('待补头衔 %d 个，文件 %d 个' % (sum(len(v) for v in by_file.values()), len(by_file)))
    for f, c in stats.most_common():
        print('  %-38s %d' % (f, c))
    if bad_units:
        print('跳过的不平衡/空字段 %d 处：' % len(bad_units))
        for k, n, why in bad_units[:20]:
            print('  %-24s %-34s %s' % (k, n, why))
    if skipped:
        print('mod 无对应头衔 %d 个：%s' % (len(skipped), skipped))
    print('@ 变量缺失：%s' % (missing_vars or '无'))

    if problems:
        print('\n校验失败，未写盘：')
        for p in problems[:20]:
            print('  ' + p)
        sys.exit(1)
    print('\n校验通过')

    if args.apply:
        for fn, info in files.items():
            if fn in by_file or (fn == main_file and missing_vars):
                write_lines(info['path'], info['lines'], info['bom'], info['crlf'])
                print('写入', fn)
        print('已写入')
    else:
        print('DRY RUN，未写入')


if __name__ == '__main__':
    main()
