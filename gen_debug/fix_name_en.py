# -*- coding: utf-8 -*-
"""修正英文本地化值：清洗国家前缀/尾部数字，首字母大写，罗马数字大写"""
import os, re, json

BASE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(BASE)

PREFIX = r'^(ach|bkz|bos|bul|byz|cha|chz|cma|cnn|geo|grm|hcn|jap|lav|mrm|mtr|orm|peg|ser|spn|tar|tre|try|tur)\s+'

def clean_en(s):
    s = s.strip().replace('$', '')
    s = re.sub(PREFIX, '', s, flags=re.I)
    s = re.sub(r'\s+\d+$', '', s)
    # 罗马数字
    s = re.sub(r'\bii\b', 'II', s)
    s = re.sub(r'\biii\b', 'III', s)
    s = re.sub(r'\biv\b', 'IV', s)
    if s and s[0].islower():
        s = s[0].upper() + s[1:]
    return s or 'Unknown'

mapping = json.load(open(os.path.join(BASE, 'name_loc_mapping.json'), encoding='utf-8'))
changed = 0
for k, v in mapping.items():
    new = clean_en(v['en'])
    if new != v['en']:
        v['en'] = new
        changed += 1
print(f"修正英文值: {changed} 条")

# 重写英文本地化
lines = ['l_english:']
for v in mapping.values():
    lines.append(' %s:0 "%s"' % (v['key'], v['en'].replace('"', "'")))
data = '\r\n'.join(lines) + '\r\n'
open(os.path.join(MOD, 'localization', 'english', 'zz_eu5_names_l_english.yml'), 'wb').write(
    b'\xef\xbb\xbf' + data.encode('utf-8'))
print(f"重写英文: {len(mapping)} 条")

json.dump(mapping, open(os.path.join(BASE, 'name_loc_mapping.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

# 抽样
for k in ['$merv$ Regent', 'byz apokauka', 'tur spouse of abraham', 'jap ashikaga takayoshi no musume', 'cma joyce 1']:
    if k in mapping:
        print(f"  {k:<38} -> {mapping[k]['en']:<32} | {mapping[k]['zh']}")
