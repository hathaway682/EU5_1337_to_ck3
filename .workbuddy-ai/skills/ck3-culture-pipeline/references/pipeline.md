# 四层产物与同步流程

## 文化要落到四层

| 层 | 文件 | 谁负责 |
|---|---|---|
| 省份 | `history/provinces/00_generated_provinces.txt` | `gen_debug/_apply_province_pop_culture.py` |
| 角色 | `history/characters/00_generated_characters.txt`、`zz_eu5_characters.txt`、`zz_eu5_missing_characters.txt`、`zz_eu5_regents.txt`、`zz_gen_adventurers.txt` | `gen_debug/_apply_people_culture.py` |
| 宗族 | `common/dynasties/00_generated_dynasties.txt`、`zz_eu5_dynasties.txt`、`zz_gen_adventurers.txt` | 同上 |
| 支系 | `common/dynasty_houses/zz_eu5_merged_houses.txt` | 同上 |

文化定义：`common/culture/cultures/00_generated_cultures.txt`（生成物，勿手改）
+ `zz_eu5_culture_new.txt`（手写新文化）+ `zz_eu5_culture_group.txt`（按组归并产物）。

本地化：`localization/simp_chinese/zz_eu5_culture_new_l_simp_chinese.yml`、
`zz_eu5_culture_group_l_simp_chinese.yml`；旧文化的中文名在 `gen_cultures_l_simp_chinese.yml`。

## 改一个文化的完整流程

```bash
cd <MOD>

# 0) 先看清楚现状
python .workbuddy-ai/skills/ck3-culture-pipeline/scripts/culture_audit.py

# 1) 改规则文件 gen_debug/_classify_cultures.py（用编辑工具，CULT_RULE 优先）

# 2) 同步 CSV + 省份 + 人物层（脚本会打印规则文件里要改哪几行）
python .workbuddy-ai/skills/ck3-culture-pipeline/scripts/culture_remap.py arpitan french
python .workbuddy-ai/skills/ck3-culture-pipeline/scripts/culture_remap.py arpitan french --apply

# 3) 复检
python .workbuddy-ai/skills/ck3-culture-pipeline/scripts/culture_audit.py --brief
```

省份层口径：**按 EU5 province 的人口多数**（`06_pops.txt` 的 `size` 累加，不是 location 个数），
同一个 province 下的所有男爵领写同一个值。`culture_remap.py` 已内置这个口径。

## 批量：按文化组合并

适用于「某个大洲还剩一堆 NEW:」。美洲 + 大洋洲那次 983 → 129 就是这个流程。

```bash
python .workbuddy-ai/skills/ck3-culture-pipeline/scripts/culture_group_merge.py \
    --continents 北美洲,南美洲,大洋洲            # 先看分组方案
# 确认后 --apply，它会写 zz_eu5_culture_group.txt + 本地化 + 改 CSV
# 再按它打印的命令跑省份和人物层
```

分组口径：`eu5_groups` 的**首位组**；没有 `culture_groups` 的文化按 `eu5_language` 反推。
组文化 key = 组名去掉 `_group`，中文名取 EU5 `culture_groups_l_simp_chinese.yml`。

## 省份脚本的三个可选参数

`gen_debug/_apply_province_pop_culture.py` 默认只跑 `category` 1-9（图内）。图外批次要：

| 参数 | 作用 |
|---|---|
| `--cats 10,11` | 允许改写图外行；**`cmap` 仍始终包含 cat 1-9 全量映射**，否则会把旧世界写成裸 EU5 key |
| `--continents 北美洲,...` | 限定大洲 |
| `--only-selected` | 只改 EU5 主体文化落在白名单内的县，其余县一律不碰（防误伤 prussian 那类） |

三个参数默认值等于原行为，不加时行为不变。

## 硬性纪律

- **一切文本文件 BOM + CRLF**。写完用 `_common.check_format()` 复核，裸 LF 必须是 0。
  坑：`io.open(p, encoding=...)` 读进来会把 `\r\n` 规整成 `\n`，再 `newline=''` 写出去就丢了 CRLF。
  要用 `open(p,'rb').read().decode('utf-8-sig')` → 按 `\n` 切 → `'\r\n'.join()` → 加 BOM 写字节。
- **CSV 必须保 BOM + CRLF**：`csv.writer(..., lineterminator="\r\n")`，写 `utf-8-sig`。
- **游戏安装目录只读**。EU5 / CK3 的 `game/` 下只当参考数据源，产物一律放 mod 工作区。
- **非必要不全量重建**。产物上叠着后续补丁层（手改、其他脚本后打的层），全量工具会把它们冲掉。
  要改就外科手术式只改目标行。
- **生成器只生成「从上游数据算出来的东西」，不生成「接线」**。文件挂在哪、排谁后面、界面文案键表
  一律当手写文件，脚本不碰。
- **同一份产物里不要混「机械重算」和「人手定稿」**。已有的键保留原行，只补缺失项。
- **写前比对内容**：没变化就完全不碰文件（连 mtime 都不动），有变化才先备份。
- **诊断类任务默认只读**：报告结论 + 改法，等用户说「改」才动手。
- **行号一律用文件绝对行号**（从第 1 行数起），不用定义内相对行号。
