# -*- coding: utf-8 -*-
"""
修复两个致命错误：
  1. zz_eu5_merged_houses.txt 第 7 行 `l_english:/n` —— 非法语法，导致 168 个 house 全部解析失败
  2. 角色文件用 `dynasty = house_xxx` —— CK3 角色指定支系必须用 `dynasty_house = house_xxx`
"""
import os, re

BASE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(BASE)

HOUSE = os.path.join(MOD, 'common', 'dynasty_houses', 'zz_eu5_merged_houses.txt')
CHARS = os.path.join(MOD, 'history', 'characters', 'zz_eu5_characters.txt')

# ---------- 1. house 文件：删掉 l_english:/n ----------
raw = open(HOUSE, 'rb').read()
text = raw.decode('utf-8-sig')
lines = text.split('\n')
before = len(lines)
removed = []
clean = []
for ln in lines:
    if ln.strip() in ('l_english:/n', 'l_english:/N', 'l_english:'):
        removed.append(ln)
        continue
    clean.append(ln)
print(f"[house] 删除非法行: {removed}")
text2 = '\n'.join(clean)
# 保持 BOM + CRLF
out = b'\xef\xbb\xbf' + text2.replace('\r\n', '\n').replace('\n', '\r\n').encode('utf-8')
open(HOUSE, 'wb').write(out)
print(f"[house] 行数 {before} -> {len(clean)}，写入 {len(out)} 字节")

# ---------- 2. 角色文件：dynasty = house_xxx -> dynasty_house = house_xxx ----------
craw = open(CHARS, 'rb').read()
ctext = craw.decode('utf-8-sig')
n_before = ctext.count('dynasty = house_')
ctext = ctext.replace('dynasty = house_', 'dynasty_house = house_')
n_after = ctext.count('dynasty_house = house_')
print(f"[chars] dynasty = house_ 出现 {n_before} 次，替换后 dynasty_house = house_ {n_after} 次")
# 检查是否有误伤（dynasty_house_house_ 之类）
bad = ctext.count('dynasty_house_house_') + ctext.count('dynasty_dynasty')
print(f"[chars] 误伤检查: {bad}")
cout = b'\xef\xbb\xbf' + ctext.encode('utf-8')
open(CHARS, 'wb').write(cout)
print(f"[chars] 写入 {len(cout)} 字节")
