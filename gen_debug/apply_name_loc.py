# -*- coding: utf-8 -*-
"""
补齐人名本地化 —— 执行

1. 1382 个坏键 -> name_eu5_<slug> 新 key
2. 1300 个 "X Regent"：英=地名，中=中文地名（查不到则用英文）
3. 82 个亲属/家族描述：手工中文映射（OTHER_ZH）
4. 写英中本地化文件，改两个角色文件的 name 字段
"""
import os, re, json, unicodedata
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(BASE)
VAN = r"E:/SteamLibrary/steamapps/common/Crusader Kings III/game/localization"

def load_dir(d):
    out = {}
    if not os.path.isdir(d):
        return out
    for root, _, fs in os.walk(d):
        for fn in fs:
            if not fn.endswith('.yml'):
                continue
            try:
                t = open(os.path.join(root, fn), 'r', encoding='utf-8-sig').read()
            except Exception:
                continue
            for m in re.finditer(r'^\s*([A-Za-z0-9_\.\-]+):\d*\s*"([^"]*)"', t, re.M):
                out.setdefault(m.group(1), m.group(2))
    return out

en = load_dir(os.path.join(VAN, 'english'))
en.update(load_dir(os.path.join(MOD, 'localization', 'english')))
zh = load_dir(os.path.join(VAN, 'simp_chinese'))
zh.update(load_dir(os.path.join(MOD, 'localization', 'simp_chinese')))

en2zh = {}
for k, v in en.items():
    if k in zh and v:
        en2zh.setdefault(v.strip().lower(), zh[k])

def zh_by_slug(slug):
    for pref in ('b_', 'c_', 'd_', 'k_', 'e_', 'b_a_'):
        k = pref + slug
        if k in zh and k in en:
            return zh[k]
    return ''

def strip_acc(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def slugify(s):
    s = strip_acc(s).lower()
    s = re.sub(r"[^a-z0-9]+", '_', s).strip('_')
    return s or 'x'

# ---------- 82 个非 Regent 的中文映射 ----------
OTHER_ZH = {
    "ach ghisi wife martino zaccaria": "马尔蒂诺·扎卡里亚之妻",
    "bkz daughter nasr": "纳斯尔之女",
    "bos prijezda i father": "普里耶兹达一世之父",
    "bul asen ancestor": "阿森先祖",
    "bul boril mother": "博里尔之母",
    "bul terter ancestor": "特尔特尔先祖",
    "byz angelina vatatzes": "安格利娜·瓦塔策斯",
    "byz apokauka": "阿波考卡斯",
    "byz apokauka ii": "阿波考卡斯二世",
    "byz kantakouzenos uncle": "坎塔库泽诺斯之叔",
    "byz kantakouzenos uncle ii": "坎塔库泽诺斯之叔二世",
    "byz tarchaneiotissa": "塔尔哈尼奥提萨",
    "cha jaya ananda consort": "贾亚·阿难陀之妃",
    "cha maha sawa mother": "摩诃沙瓦之母",
    "chz tamagusuku spouse": "玉城之配偶",
    "cma joyce 1": "乔伊斯",
    "cma joyce 2": "乔伊斯二世",
    "cnn toirdelbach o conchobair wife": "托尔德尔巴赫·奥康纳之妻",
    "geo rulers wife": "格鲁吉亚统治者之妻",
    "grm first daughter": "长女",
    "hcn munanzi son borjigin": "木难子（孛儿只斤氏）",
    "jap ashikaga takayoshi no musume": "足利高义之女",
    "jap ashina morimune spouse": "芦名盛宗之配偶",
    "jap chiba munetane no musume": "千叶宗胤之女",
    "jap ema ruler": "江马当主",
    "jap houjou muneyori no musume": "北条宗赖之女",
    "jap imagawa kuniuji no musume": "今川国氏之女",
    "jap kousaka akishu": "高坂秋秀",
    "jap kousaka dewashu": "高坂出羽守",
    "jap kyougoku douyo no musume": "京极道誉之女",
    "jap miya ruler": "宫氏当主",
    "jap ooba ruler": "大庭当主",
    "jap ootomo chikatoki no musume": "大友亲时之女",
    "jap oyama hidetomo spouse": "小山秀朝之配偶",
    "jap samukawa no ama": "寒川尼",
    "jap tamura ruler": "田村当主",
    "jap uesugi shigefusa no musume": "上杉重房之女",
    "jap yamaguchi ruler": "山口当主",
    "jap yuuki tomosuke spouse": "结城朝助之配偶",
    "lav king phraek si racha": "帕耶锡拉差王",
    "mrm unknown yaroslavich rurikovich": "无名（雅罗斯拉维奇·留里克氏）",
    "mtr father vlash mataranga": "弗拉什·马塔兰加之父",
    "mtr mataranga ancestor": "马塔兰加先祖",
    "orm fulan bin shadi": "富兰·本·沙迪",
    "peg wareru father": "瓦鲁之父",
    "ser pribac hrebeljanovic spouse": "普里巴茨·赫雷贝利亚诺维奇之配偶",
    "ser son of ivan dragushin": "伊万·德拉古辛之子",
    "ser vratko nemanjic spouse": "弗拉特科·内曼伊奇之配偶",
    "spn borommarachathirat father": "波隆摩罗阇提拉特之父",
    "spn borommarachathirat sister": "波隆摩罗阇提拉特之妹",
    "spn phraya loe thai daughter": "帕耶洛泰之女",
    "spn ramathibodi sister": "拉玛铁菩提之妹",
    "tar curatame mother": "库拉塔梅之母",
    "tar pauacume ii mother": "保阿库梅二世之母",
    "tar pauacume ii spouse": "保阿库梅二世之配偶",
    "tar uapeani mother": "瓦佩阿尼之母",
    "tre komnene": "科穆宁娜",
    "try connor o donnell wife": "康纳·奥唐奈之妻",
    "tur daughter fifth nephew": "侄孙之五女",
    "tur daughter fourth nephew": "侄孙之四女",
    "tur daughter second nephew": "侄孙之次女",
    "tur daughter third brother": "兄弟之三女",
    "tur daughter third nephew": "侄孙之三女",
    "tur fulan": "富兰",
    "tur fulane hatun": "富兰可敦",
    "tur grandnephew": "侄孙",
    "tur grandnephew 2": "侄孙二世",
    "tur grandniece": "侄孙女",
    "tur second daughter third brother": "兄弟之次女",
    "tur second son second nephew": "侄孙之次子",
    "tur sister in law": "姻亲姊妹",
    "tur son fourth nephew": "侄孙之四子",
    "tur son second nephew": "侄孙之次子",
    "tur son third nephew": "侄孙之三子",
    "tur spouse of abraham": "亚伯拉罕之配偶",
    "tur spouse of hizir": "希兹尔之配偶",
    "tur spouse of muhammad": "穆罕默德之配偶",
    "tur spouse of murad arslan": "穆拉德·阿尔斯兰之配偶",
    "tur spouse of nephew": "侄孙之配偶",
    "tur spouse of pazarli": "帕扎尔利之配偶",
    "tur spouse of sahi": "萨希之配偶",
    "tur spouse of savci": "萨夫奇之配偶",
}

FILES = ['history/characters/zz_eu5_characters.txt',
         'history/characters/zz_eu5_regents.txt']

bad = {}
for f in FILES:
    p = os.path.join(MOD, f)
    if not os.path.exists(p):
        continue
    s = open(p, 'r', encoding='utf-8-sig').read()
    for n in re.findall(r'^\s*name\s*=\s*"([^"]*)"', s, re.M):
        if n not in en:
            bad.setdefault(n, set()).add(f)

# 生成映射（处理 slug 冲突）
mapping = {}
used = {}
for k in sorted(bad):
    if k.lower().endswith(' regent'):
        place = k[:-len(' Regent')].strip().replace('$', '')
        sl = slugify(place)
        zhv = en2zh.get(place.lower(), '') or zh_by_slug(sl)
        ent = place
        kind = 'regent'
    else:
        sl = slugify(k)
        zhv = OTHER_ZH.get(k, '')
        ent = k
        kind = 'other'
    base_key = 'name_eu5_' + sl
    key = base_key
    i = 2
    while key in used and used[key] != k:
        key = f'{base_key}_{i}'
        i += 1
    used[key] = k
    mapping[k] = {'key': key, 'en': ent, 'zh': zhv or ent, 'kind': kind}

# ---------- 写本地化 ----------
def write_yml(path, lang, pairs):
    lines = [f'l_{lang}:']
    for k, v in pairs:
        v = v.replace('"', "'")
        lines.append(f' {k}:0 "{v}"')
    data = '\r\n'.join(lines) + '\r\n'
    with open(path, 'wb') as f:
        f.write(b'\xef\xbb\xbf' + data.encode('utf-8'))

pairs = [(v['key'], v['en']) for v in mapping.values()]
write_yml(os.path.join(MOD, 'localization', 'english', 'zz_eu5_names_l_english.yml'), 'english', pairs)
pairs_zh = [(v['key'], v['zh']) for v in mapping.values()]
write_yml(os.path.join(MOD, 'localization', 'simp_chinese', 'zz_eu5_names_l_simp_chinese.yml'), 'simp_chinese', pairs_zh)
print(f"本地化写入: {len(mapping)} 条 (英/中)")

# ---------- 改角色文件 ----------
total_repl = 0
for f in FILES:
    p = os.path.join(MOD, f)
    if not os.path.exists(p):
        continue
    raw = open(p, 'rb').read()
    s = raw.decode('utf-8-sig')
    cnt = 0
    for old, v in mapping.items():
        pat = 'name = "%s"' % old
        if pat in s:
            cnt += s.count(pat)
            s = s.replace(pat, 'name = "%s"' % v['key'])
    open(p, 'wb').write(b'\xef\xbb\xbf' + s.encode('utf-8'))
    print(f"{f}: 替换 {cnt} 处")
    total_repl += cnt

print(f"总替换: {total_repl}")

# 统计
reg = [v for v in mapping.values() if v['kind'] == 'regent']
oth = [v for v in mapping.values() if v['kind'] == 'other']
zh_hit = sum(1 for v in reg if v['zh'] != v['en'])
print(f"\nRegent: {len(reg)}  中文命中 {zh_hit}  用英文 {len(reg)-zh_hit}")
print(f"其他  : {len(oth)}  有中文 {sum(1 for v in oth if v['zh']!=v['en'])}")

json.dump(mapping, open(os.path.join(BASE, 'name_loc_mapping.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
