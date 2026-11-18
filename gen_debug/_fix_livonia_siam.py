# -*- coding: utf-8 -*-
"""把 k_livonia / k_siam 从 Ck3MapGen 的 landless 占位壳改成真正的法理王国。

依据：
1. common/on_action/1337_de_jure_set.txt 明确给两者设 de jure liege：
     title:d_baltic = { set_de_jure_liege_title = title:k_livonia }
     title:k_livonia = { set_de_jure_liege_title = title:e_west_slavia }
     title:k_siam    = { set_de_jure_liege_title = title:e_suvarnabhumi }
   landless 头衔不能持有 de jure 领地，这两条设置本来会失效。
2. history/titles/zz_eu5_titles.txt 里两者都有完整 holder 世系
   （k_livonia 自 1328，k_siam 自 1238），不是空壳。
3. k_siam 的块内容按用户 2026-11-18 给定原样写入。
4. k_livonia 按原版 00_landed_titles.txt:23555 的 ai_primary_priority 写回；
   原版首府 c_vidzeme 在本 mod 法理树里不存在，里加在 b_riga 的父县
   c_south_livonia（父链 e_west_slavia > k_lithuania > d_baltic > c_south_livonia）。
5. @ 变量是文件级作用域，原版每个 landed_titles 文件顶部各自定义一遍；
   本文件此前没有，补上 correct_culture_primary_score / better_than_the_alternatives_score。
"""
import os
import re
import sys

PATH = os.path.join('common', 'landed_titles', 'zz_vanilla_titulars.txt')

LIVONIA_NEW = """k_livonia = {
	color = { 110 80 168 }
	capital = c_south_livonia
	ai_primary_priority = {
		if = {
			limit = {
				culture = culture:latgalian
			}
			add = @correct_culture_primary_score
		}
		if = {
			limit = {
				NOT = {
					culture = culture:latgalian
				}
			}
			add = @better_than_the_alternatives_score
		}
	}
}"""

SIAM_NEW = """k_siam = {
	color = { 88 137 172 }
	capital = c_sukhothai
	can_create = {
		trigger_if = {
			limit = {
				is_ai = yes
			}
			culture = { has_cultural_pillar = heritage_tai }
		}
	}
	ai_primary_priority = {
		if = {
			limit = {
				culture = culture:tai
			}
			add = @correct_culture_primary_score
		}
		if = {
			limit = {
				culture = { has_cultural_pillar = heritage_tai }
			}
			add = @better_than_the_alternatives_score
		}
	}
}"""

VAR_DEFS = [
    '@correct_culture_primary_score = 100',
    '@better_than_the_alternatives_score = 50',
]


def find_block(lines, key):
    """返回顶层块 key 的 [start, end] 行索引（含）。"""
    pat = re.compile(r'^' + re.escape(key) + r'\s*=\s*\{')
    for i, l in enumerate(lines):
        if pat.match(l):
            depth = 0
            for j in range(i, len(lines)):
                s = lines[j].split('#')[0]
                depth += s.count('{') - s.count('}')
                if depth <= 0:
                    return i, j
            raise RuntimeError('%s 块括号不平衡' % key)
    raise RuntimeError('找不到 %s 块' % key)


def main():
    apply = '--apply' in sys.argv
    raw = open(PATH, 'rb').read()
    bom = raw.startswith(b'\xef\xbb\xbf')
    text = raw.decode('utf-8-sig')
    crlf = '\r\n' in text
    lines = text.replace('\r\n', '\n').split('\n')

    # 幂等：已经改过就什么都不做
    if '@correct_culture_primary_score' in text:
        print('已存在 @ 变量定义，跳过（幂等）')
        return

    changed = 0
    for key, new in (('k_livonia', LIVONIA_NEW), ('k_siam', SIAM_NEW)):
        s, e = find_block(lines, key)
        old = '\n'.join(lines[s:e + 1])
        if old.strip() == new.strip():
            print('%s 已是目标内容，跳过' % key)
            continue
        print('== %s 第 %d-%d 行，%d 行 -> %d 行' % (key, s + 1, e + 1, e - s + 1, new.count('\n') + 1))
        lines[s:e + 1] = new.split('\n')
        changed += 1

    # 顶部补 @ 变量：插在第一个头衔块之前
    first = next(i for i, l in enumerate(lines) if re.match(r'^[hedcbk]_[A-Za-z0-9_.\-]+\s*=\s*\{', l))
    # 回退掉紧邻的空行，避免出现双空行
    insert_at = first
    while insert_at > 0 and not lines[insert_at - 1].strip():
        insert_at -= 1
    block = [''] + VAR_DEFS + ['']
    lines[insert_at:insert_at] = block
    print('== 顶部插入 @ 变量：原第 %d 行前' % (first + 1))

    new_text = '\n'.join(lines)

    # 结构校验：括号平衡
    bal = 0
    for l in new_text.split('\n'):
        s = l.split('#')[0]
        bal += s.count('{') - s.count('}')
    if bal != 0:
        raise SystemExit('括号不平衡: %d，已中止' % bal)

    # 行尾还原
    out = new_text.replace('\n', '\r\n') if crlf else new_text
    data = (b'\xef\xbb\xbf' if bom else b'') + out.encode('utf-8')

    if not apply:
        print('干跑：%d 个块待改，未写盘' % changed)
        return

    tmp = PATH + '.tmp'
    with open(tmp, 'wb') as f:
        f.write(data)
    os.replace(tmp, PATH)
    print('已写入 %s（%d 字节）' % (PATH, len(data)))


if __name__ == '__main__':
    main()
