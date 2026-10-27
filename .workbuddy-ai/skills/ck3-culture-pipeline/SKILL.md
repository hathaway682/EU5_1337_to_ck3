---
name: ck3-culture-pipeline
description: 本 mod（EU5_Modern_Borders_noshape）的文化改动流水线。当需要新增/调整/合并 EU5→CK3 文化落点、改单个文化的目标、按文化组批量归并、新建文化定义与本地化、把改动同步到省份层或人物层（角色/宗族/支系）、或排查文化覆盖与一致性问题时使用。
agent_created: true
---

# CK3 文化流水线

## 用途

本 mod 把 EU5 的 2088 个文化映射到 CK3 文化，产物分布在四层（省份 / 角色 / 宗族 / 支系）。
所有映射的唯一真源是 `gen_debug/_classify_cultures.py` 的四张规则表，
`gen_debug/_culture_classification.csv` 是它的产物。本 skill 提供改落点的标准流程、
批量归并流程和体检工具。

## 何时使用

- 「XX 文化改成 YY」——单个文化的落点调整
- 「某个大洲还剩一堆文化，按文化组合并一下」——批量归并
- 「新建一个 XX 文化」——新文化定义 + 本地化 + 支柱
- 「把人物文化也改了」——把已定映射同步到角色/宗族/支系层
- 「文化怎么没覆盖到 / 为什么这里是这个文化」——排查

## 核心事实（先记住这几条）

1. **判定优先级**：`CULT_RULE > 自动同名 > GROUP_RULE_STRONG > LANG_RULE > GROUP_RULE > 自动`。
   要压住语言级/组级判定，只能写 `CULT_RULE`。
2. **`CULT_RULE` 优先级最高**，它会把同组的 `GROUP_RULE_STRONG` 顶掉。想让整组走一条规则，
   必须先把该组的文化级规则删掉。
3. **`GROUP_RULE_STRONG` 只认 `eu5_groups` 的第一位**。
4. **省份层口径 = 按 EU5 province 的人口多数**（`06_pops.txt` 的 `size` 累加），
   同一 province 下所有男爵领写同一个值。**不是 location 个数**。
5. **`category` 1-9 = CU 地图范围内**（默认会落地），**10-11 = 图外**（默认不碰）。
6. **一切文本文件 BOM + CRLF**，裸 LF 必须为 0。

## 标准流程：改一个文化的落点

```bash
cd <MOD>

# 0) 现状体检（只读）
python .workbuddy-ai/skills/ck3-culture-pipeline/scripts/culture_audit.py

# 1) 改规则文件（用编辑工具，不要用脚本改代码）
#    gen_debug/_classify_cultures.py 的 CULT_RULE 里改或新增一行：
#    "xxx_culture":  r(cat, "目标文化", "说明")
#    如果该文化还会被 LANG_RULE 收走，两条都改保持一致。
#    改完必须用 ast 扫重复 key（写法见 references/pitfalls.md）。

# 2) 同步 CSV + 省份 + 人物层（脚本会打印规则文件里需要改哪几行）
python .workbuddy-ai/skills/ck3-culture-pipeline/scripts/culture_remap.py <eu5_culture> <ck3_target>
python .workbuddy-ai/skills/ck3-culture-pipeline/scripts/culture_remap.py <eu5_culture> <ck3_target> --apply

# 3) 复检
python .workbuddy-ai/skills/ck3-culture-pipeline/scripts/culture_audit.py --brief
```

`culture_remap.py` 默认 dry run，`--apply` 才写，每个被改文件先备份 `.bak_remap_<时间戳>`。
它**不改规则文件**——规则必须自己用编辑工具改，否则下次重跑分类会把改动冲掉。

## 批量流程：按文化组归并

```bash
python .workbuddy-ai/skills/ck3-culture-pipeline/scripts/culture_group_merge.py \
    --continents 北美洲,南美洲,大洋洲           # 先看分组方案
python .workbuddy-ai/skills/ck3-culture-pipeline/scripts/culture_group_merge.py \
    --continents 北美洲,南美洲,大洋洲 --apply   # 写定义 + 本地化 + 改 CSV
# 再按它打印的两条命令跑省份层和人物层
```

分组口径：`eu5_groups` 首位组；没有 `culture_groups` 的按 `eu5_language` 反推。
组文化 key = 组名去掉 `_group`，中文名取 EU5 的 `culture_groups_l_simp_chinese.yml`。
定义体克隆组内 barony 最多的成员（`heritage = <group>_group`、
`language = eu5_heritage_<group>_group`），不手写 tradition。

## 脚本

| 脚本 | 作用 |
|---|---|
| `scripts/culture_audit.py` | 只读体检：剩余 NEW:、未同步的省份/人物、未定义文化、county 一致性、BOM/CRLF、分布 |
| `scripts/culture_remap.py` | 单个文化改落点：CSV + 省份 + 人物层一次到位，并打印规则文件要改的行号 |
| `scripts/culture_group_merge.py` | 按文化组批量归并：生成组文化定义 + 本地化 + 改 CSV |
| `scripts/_common.py` | 公共层：路径、EU5/CK3 数据加载、BOM/CRLF 读写、county 结构、改写器 |

脚本全部默认 dry run，`--apply` 才落盘。路径可用环境变量 `MOD_ROOT` / `EU5_GAME` / `CK3_GAME` 覆盖。

## 参考

| 文件 | 内容 |
|---|---|
| `references/rules.md` | 判据层级、四张规则表的作用域与生效条件、规则行写法、常见误判 |
| `references/pipeline.md` | 四层产物清单、改单个/批量的完整命令、省份脚本的三个开关、硬性纪律 |
| `references/pitfalls.md` | 踩坑清单：解析、字典重复 key、prussian 双义、CRLF 丢失、tradition DLC、颜色去重等 |

## 边界

- 游戏安装目录（EU5 / CK3 的 `game/`）**只读**，产物一律放 mod 工作区。
- 诊断类请求默认只读：先报告结论 + 改法，等用户明确说「改」才动手。
- 非必要不全量重建；只改目标行。写完复检格式，不要跑无谓的干跑仪式。
- 行号一律用文件绝对行号。
