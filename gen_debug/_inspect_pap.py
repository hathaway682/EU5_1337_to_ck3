# -*- coding: utf-8 -*-
"""看 d_lazio / d_marche / d_provance 下到底有哪些县、各自的 1337 持有者是谁。"""
import re, io, sys, os

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
LT = os.path.join(MOD, 'common', 'landed_titles', '00_landed_titles.txt')
KEY = re.compile(r'^[ \t]*([a-z]_[A-Za-z0-9_]+)\s*=\s*\{')

out = io.StringIO()
def P(*a): print(*a, file=out)

# 1) 解析 landed_titles 的层级，抓目标 d_ 下的直接 c_ 子
targets = {'d_lazio', 'd_marche', 'd_provence'}
cur = None
res = {t: [] for t in targets}
with open(LT, 'r', encoding='utf-8-sig', errors='replace') as fh:
    stack = []
    for line in fh:
        s = line.rstrip('\n')
        m = KEY.match(s)
        if m:
            ind = len(s) - len(s.lstrip('\t'))
            while stack and stack[-1][1] >= ind:
                stack.pop()
            key = m.group(1)
            if stack and stack[-1][0] in targets and key.startswith('c_'):
                res[stack[-1][0]].append(key)
            stack.append((key, ind))
        d = s.count('{') - s.count('}')
        if d < 0 and stack:
            stack.pop()

for t in ['d_lazio', 'd_marche', 'd_provence']:
    P("%s 下的县 (%d): %s" % (t, len(res[t]), ", ".join(res[t])))
P()

# 2) 这些县在 history 里的 1337 holder
hist_root = os.path.join(MOD, 'history', 'titles')
holders = {}
KEYC = re.compile(r'^([a-z]_[A-Za-z0-9_]+)\s*=\s*\{')
want = set(sum(res.values(), []))
for dp, dn, fn in os.walk(hist_root):
    for f in fn:
        if not f.lower().endswith('.txt'): continue
        p = os.path.join(dp, f)
        with open(p, 'r', encoding='utf-8-sig', errors='replace') as fh:
            cur = None
            curdate = None
            last1337 = None
            for line in fh:
                s = line.rstrip('\n')
                m = KEYC.match(s)
                if m:
                    if cur in want and last1337 and cur not in holders:
                        holders[cur] = last1337
                    cur = m.group(1)
                    last1337 = None
                    curdate = None
                    continue
                dm = re.match(r'^\t(1337\.1\.1)\s*=\s*\{', s)
                if dm:
                    curdate = '1337'
                    continue
                hm = re.match(r'^\t\tholder\s*=\s*([A-Za-z0-9_]+)', s)
                if hm and curdate == '1337':
                    last1337 = hm.group(1)
            if cur in want and last1337 and cur not in holders:
                holders[cur] = last1337

P("=== 这些县的 1337 持有者 ===")
for t in ['d_lazio', 'd_marche', 'd_provence']:
    for c in res[t]:
        P("  %-22s %s" % (c, holders.get(c, '??')))

sys.stdout.buffer.write(out.getvalue().encode('utf-8'))
