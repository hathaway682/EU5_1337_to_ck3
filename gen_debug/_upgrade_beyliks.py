# -*- coding: utf-8 -*-
"""把安纳托利亚 9 个贝伊国从公国/伯爵级升到王国级（用 CK3 原版 k_ 头衔 key）。

改两个文件：
  common/landed_titles/zz_eu5_titular.txt  —— 删 4 个 d_eu5_* 定义，k 段开头插 9 个 k_ 定义
  history/titles/zz_eu5_titles.txt         —— 删 4 个 d_eu5_* 块，k 段开头插 9 个 k_ 块；liege 联动

用法：python _upgrade_beyliks.py [--apply]
"""
import re
import sys
import os

MOD = r'D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape'
TITULAR = os.path.join(MOD, 'common', 'landed_titles', 'zz_eu5_titular.txt')
TITLES = os.path.join(MOD, 'history', 'titles', 'zz_eu5_titles.txt')

# 4 个由 d_eu5_* 改名而来：key 原名 -> 新 k key
RENAME = {
    'd_eu5_ayd': 'k_aydin',
    'd_eu5_ere': 'k_eretnid',
    'd_eu5_men': 'k_mentese',
    'd_eu5_tur': 'k_ottoman',
}

# 5 个新建：新 k key -> (原版颜色, capital, 照抄 history 的 c_ key)
NEW = {
    'k_saruhan':  ((144, 171, 225), 'c_saruhan',  'c_saruhan'),
    'k_karaman':  ((120, 41, 92),   'c_konya',    'c_konya'),
    'k_germiyan': ((255, 180, 180), 'c_kutahya',  'c_kutahya'),
    'k_tekke':    ((244, 153, 189), 'c_antalya',  'c_antalya'),
    'k_candar':   ((238, 79, 182),  'c_kastamonu', 'c_kastamonu'),
}

ANCHOR = 'k_eu5_aju = {'   # k 段开头，新块插它前面


def read(path):
    raw = open(path, 'rb').read()
    bom = raw.startswith(b'\xef\xbb\xbf')
    if bom:
        raw = raw[3:]
    return raw.decode('utf-8'), bom


def write(path, text, bom):
    data = (b'\xef\xbb\xbf' if bom else b'') + text.encode('utf-8')
    open(path, 'wb').write(data)


def find_block(text, key):
    """返回顶层块 (start, end) 的字符区间，块后紧跟的空行一并算进去。"""
    m = re.search(r'^%s = \{\r?\n' % re.escape(key), text, re.M)
    if not m:
        return None
    i = m.end()
    depth = 1
    while i < len(text):
        c = text[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                j = i + 1
                if text[j:j + 2] == '\r\n':
                    j += 2
                if text[j:j + 2] == '\r\n':
                    j += 2
                return (m.start(), j)
        i += 1
    return None


def main():
    apply = '--apply' in sys.argv

    # ---------- titular ----------
    t, tbom = read(TITULAR)
    nl = '\r\n' if '\r\n' in t else '\n'
    removed = {}
    for old in RENAME:
        r = find_block(t, old)
        if not r:
            print('!! titular 找不到块:', old)
            continue
        removed[old] = t[r[0]:r[1]]
    # 新建 9 个定义文本
    blocks = []
    for old, new in RENAME.items():
        body = removed[old]
        body = re.sub(r'^%s = \{' % re.escape(old), '%s = {' % new, body, count=1, flags=re.M)
        blocks.append(body)
    for new, (color, cap, _) in NEW.items():
        blocks.append('{k} = {{{n}\tcolor = {{ {c[0]} {c[1]} {c[2]} }}{n}\tcapital = {cap}{n}}}{n}{n}'.format(
            k=new, n=nl, c=color, cap=cap))
    blocks.sort(key=lambda s: s.split(' = ')[0])
    insert = ''.join(blocks)

    t2 = t
    for old in RENAME:
        if old in removed:
            t2 = t2.replace(removed[old], '', 1)
    if ANCHOR not in t2:
        print('!! titular 找不到锚点', ANCHOR)
        return
    t2 = t2.replace(ANCHOR, insert + ANCHOR, 1)
    print('titular: 删 %d 块，插 %d 块，%d -> %d 字符' % (len(removed), len(blocks), len(t), len(t2)))

    # ---------- titles ----------
    s, sbom = read(TITLES)
    sremoved = {}
    for old in RENAME:
        r = find_block(s, old)
        if not r:
            print('!! titles 找不到块:', old)
            continue
        sremoved[old] = s[r[0]:r[1]]
    sblocks = []
    for old, new in RENAME.items():
        body = sremoved[old]
        body = re.sub(r'^%s = \{' % re.escape(old), '%s = {' % new, body, count=1, flags=re.M)
        sblocks.append(body)
    for new, (_, _, csrc) in NEW.items():
        r = find_block(s, csrc)
        if not r:
            print('!! titles 找不到源块:', csrc)
            return
        body = s[r[0]:r[1]]
        body = re.sub(r'^%s = \{' % re.escape(csrc), '%s = {' % new, body, count=1, flags=re.M)
        sblocks.append(body)
    sblocks.sort(key=lambda x: x.split(' = ')[0])
    sinsert = ''.join(sblocks)

    s2 = s
    for old in RENAME:
        if old in sremoved:
            s2 = s2.replace(sremoved[old], '', 1)
    if ANCHOR not in s2:
        print('!! titles 找不到锚点', ANCHOR)
        return
    s2 = s2.replace(ANCHOR, sinsert + ANCHOR, 1)
    # liege 联动
    n_liege = s2.count('liege = d_eu5_men')
    s2 = s2.replace('liege = d_eu5_men', 'liege = k_mentese')
    print('titles: 删 %d 块，插 %d 块，liege 改 %d 处，%d -> %d 字符' % (
        len(sremoved), len(sblocks), n_liege, len(s), len(s2)))

    # ---------- 预览 ----------
    print('\n--- 新块预览（titular） ---')
    print(insert[:900])
    print('\n--- 新块预览（titles） ---')
    print(sinsert[:1200])

    # ---------- 校验 ----------
    for name, txt in (('titular', t2), ('titles', s2)):
        print('%s 花括号: { %d 个, } %d 个' % (name, txt.count('{'), txt.count('}')))

    if apply:
        write(TITULAR, t2, tbom)
        write(TITLES, s2, sbom)
        print('\n已写入。')


if __name__ == '__main__':
    main()
