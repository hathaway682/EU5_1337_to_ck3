---
name: ck3-religion-pipeline
description: 本 mod（EU5_Modern_Borders_noshape）的宗教改动流水线。当需要改某个/某批省的 faith 或 rite、改角色的 religion 或 rite、调整 EU5 宗教到 CK3 信仰的映射、补或修宗派（道教三分支/佛教各宗/伊斯兰学派/基督教礼/印度教支派）、按 CU 数据转换中日朝三教省、修圣地块落点、增改 faith/rite 定义与宗教领袖、排查「为什么这里显示这个教派」、或者要跑宗教体检与保存点还原时使用。
agent_created: true
---

# CK3 宗教流水线

## 用途

本 mod 的宗教分**两层**：`faith`（信仰，地图上色单位）+ `rite`（礼/宗派，faith 内的细分）。
产物落在四个地方：

| 层 | 文件 | 字段 |
|---|---|---|
| 省份 | `history/provinces/00_generated_provinces.txt` | `faith =` / `rite =` |
| 角色 | `history/characters/*.txt` | `religion =` / `rite =` |
| 圣地块 | `common/religion/holy_site_types/*.txt` | `county =` / `barony =` |
| 信仰史 / 宗教领袖 | `history/faiths/*.txt`、`common/landed_titles/zzz_eu5_faith_heads.txt` | 教义 / `main_rite` / 头衔 |

本 skill 提供：改省份与角色的标准工具、宗教体检、保存点、映射口径速查、踩过的坑、CU 取数链路、圣地与 faith 定义的说明。

## 何时使用

- 「XX 省改成 YY 派」→ `religion_set.py`
- 「XX 这个人改成 YY 派 / 这个国家的人全改」→ `religion_chars.py`
- 「为什么这里显示上清派 / 禅宗 / 全真派」→ `religion_audit.py` + `references/rites.md`
- 「某个 EU5 宗教映射错了」→ 改 `_build_faith_map.py` 的 `CURATED`（见 `references/pitfalls.md` 第 15 条）
- 「补/修宗派」→ `references/pipeline.md` 第三节的执行顺序
- 「中日朝按 CU 转」→ `references/cu-source.md`
- 「圣地位置不对 / 还剩多少没修」→ `references/holy-sites.md`
- 「新增 faith / rite / 宗教领袖 / 教义」→ `references/faith-defs.md`
- 「宗教图不对，整体体检」→ `religion_audit.py`
- 「改之前先存一份 / 改坏了要还原」→ `religion_snapshot.py`

## 核心事实（先记住这几条）

1. **判 rite 能不能挂到某省，看 religion 不看 faith。** 基督教 9 个礼全绑在伞形 faith `christian_faith` 上，而省份写 `orthodox`/`catholic` —— 正常。跨 religion 才是错。
2. **只有 21 个 faith 有多个 rite**，其余都是「一 faith 一同名 rite」，**不用写 rite 行**（靠 `main_rite` 回落）。当前 21046 个省份块里只有 4066 个写了 rite。
3. **`shangqing_faith` = 上清派（faith 名），`quanzhen` = 全真派（rite 名）**。省 `faith = shangqing_faith` 时游戏显示「上清派」。
4. **`confucian_faith` / `maitreya_faith` 没有 main_rite**，靠 `history/faiths/00_eastern_misc.txt` 按日期定（1337 = `daoxue` / `maitreya`）。
5. **12 个省只有 `rite = acharya`、没有 faith 行**，这是既定写法（有 rite 就不写 faith），不是漏数据。
6. **EU5 religion → CK3 faith 的唯一真源是 `eu5_ck3_faith_map.csv`**，生成器 `_build_faith_map.py`。改映射改 `CURATED`，别改 CSV。
7. **mod 没有 `common/religion/faith_types/` 和 `rite_types/`**，faith/rite 定义全部继承原版。改教义必须整块抄，见 `references/faith-defs.md`。
8. **文件是 UTF-8 BOM + 纯 CRLF**。裸 LF 必须为 0，括号必须平衡。
9. **本地化从原版找**：`E:\SteamLibrary\steamapps\common\Crusader Kings III\game\localization\simp_chinese\religion\`。mod 的 loc 只覆盖少量 key。

## 脚本

先设好解释器（下文用 `$PY`）：

```bash
PY="C:/Users/DELL/.workbuddy-ai/binaries/python/versions/3.13.12/python.exe"
SK="<MOD>/.workbuddy-ai/skills/ck3-religion-pipeline/scripts"
```

### `religion_audit.py` — 省份层只读体检

```bash
$PY $SK/religion_audit.py                          # 全量概览
$PY $SK/religion_audit.py --top 40                 # 更长的榜
$PY $SK/religion_audit.py --faith mahayana_faith   # 该 faith 的省按 rite 细分
$PY $SK/religion_audit.py --rite dhyana            # 该 rite 的省按 faith 细分
$PY $SK/religion_audit.py --county c_ninghai       # 整个伯爵领
$PY $SK/religion_audit.py --provs quanzhen         # 列出省 id
```

回答四件事：① 文件有没有坏（BOM/CRLF/括号）；② faith/rite 分布（带中文名）；
③ **rite 与省 faith 是否跨 religion**（真错）；④ 多少省靠 main_rite 回落。

### `religion_set.py` — 外科手术式改省份 faith / rite（默认 dry-run）

```bash
# 单省
$PY $SK/religion_set.py --prov 8839 --rite daoxue
$PY $SK/religion_set.py --prov 8839 --rite daoxue --apply

# 整县
$PY $SK/religion_set.py --county c_ninghai --rite daoxue --apply

# 一批省（空格/逗号分隔，或文件）
$PY $SK/religion_set.py --provs "7364 7384 7418" --rite daoxue --apply
$PY $SK/religion_set.py --prov-file ids.txt --rite dhyana --apply

# 某个值的全部省
$PY $SK/religion_set.py --all-faith confucian_faith --rite daoxue --apply
$PY $SK/religion_set.py --all-rite dhyana --rite vinaya --apply

# 同时改 faith（同 religion 内换 faith）
$PY $SK/religion_set.py --prov 8839 --faith shangqing_faith --rite quanzhen --apply

# 跨 religion 写礼：删掉 faith 行只留 rite（这是既定写法）
$PY $SK/religion_set.py --prov 9368 --rite acharya --drop-faith --apply

# 全库替换某个值
$PY $SK/religion_set.py --rename-rite shangqing=quanzhen --apply
```

特性：
- 只改目标省的 `faith =` / `rite =` 行，culture/holding/注释一个字节不动；
- BOM + 原行尾符保留，写盘后自动校验裸 LF / 括号；
- 内容无变化不写盘（连 mtime 都不动）；
- 写盘前自动备份 `.bak_religionset_<ts>`；
- **校验**：faith/rite 必须有定义；rite 的 religion 必须与省 faith 的 religion 相同，否则拒绝（`--force` 绕过，`--drop-faith` 走既定写法）。

### `religion_chars.py` — 角色层体检 + 改 religion / rite（默认 dry-run）

```bash
# 概览
$PY $SK/religion_chars.py
$PY $SK/religion_chars.py --religion shia
$PY $SK/religion_chars.py --rite maliki
$PY $SK/religion_chars.py --char bkz_sayf_al_din_abu_abdallah_muhammad

# 跨宗教执政（角色 religion 与 tag 国教的 religion 不同）
$PY $SK/religion_chars.py --cross

# 改写
$PY $SK/religion_chars.py --set --char a,b --religion sunni --rite maliki
$PY $SK/religion_chars.py --set --char a,b --religion sunni --rite maliki --apply
$PY $SK/religion_chars.py --set --tag BKZ --religion sunni --rite maliki --apply
$PY $SK/religion_chars.py --set --all-religion shia --religion sunni --rite maliki --apply
$PY $SK/religion_chars.py --set --char x --drop-rite --apply
```

要点：
- 按**大括号深度**切块（角色块里有 `1234.1.1 = { ... }` 日期块，不能按空行切）；
- **跳过 `zz_eu5_government.txt` 那类纯 effect 块**（同 key 二次出现、没有 name/culture），往里塞 `religion =` 会写出畸形数据；
- `--cross` 会先把 EU5 `religion_definition` 用 `eu5_ck3_faith_map.csv` 翻成 CK3 faith 再比，否则 `theravada` vs `theravada_faith` 全是假阳性；同 religion 的兄弟 faith 单列，不算错；
- 校验同 `religion_set.py`：跨 religion 的 rite 拒绝，除非 `--force`。

### `religion_snapshot.py` — 宗教地图保存点 / 一键还原（faith + rite）

```bash
$PY $SK/religion_snapshot.py save 改宗派前
$PY $SK/religion_snapshot.py list
$PY $SK/religion_snapshot.py restore latest              # 干跑
$PY $SK/religion_snapshot.py restore latest --apply      # 真写
$PY $SK/religion_snapshot.py restore latest --apply --faith-only
```

保存点在 `gen_debug/religion_checkpoints/`。还原是外科手术式的：只改与快照不一致的行，
快照里没有 rite 的省若多出 `rite =` 行会被删掉，其它字节不动；无变化不写盘。

## 标准流程

### A. 改几个省的宗派（最常见）

```bash
cd <MOD>
$PY $SK/religion_audit.py --provs <目标省>              # 1) 先看现状
$PY $SK/religion_snapshot.py save 改宗派前              # 2) 打保存点
$PY $SK/religion_set.py --prov <省> --rite <礼>         # 3) dry run 看清改动
$PY $SK/religion_set.py --prov <省> --rite <礼> --apply
$PY $SK/religion_audit.py --provs <省>                  # 4) 复核
```

### B. 改一批人或一个国家的宗教

```bash
$PY $SK/religion_chars.py --tag <TAG>                   # 1) 先看这些人现在信什么
$PY $SK/religion_chars.py --set --tag <TAG> --religion <faith> --rite <rite>          # 2) dry run
$PY $SK/religion_chars.py --set --tag <TAG> --religion <faith> --rite <rite> --apply
```

### C. 改 EU5 宗教 → CK3 信仰的映射

1. 改 `Global_modern_map/eu5_export/_build_faith_map.py` 的 `CURATED`（加注释写日期和理由）
2. `python _build_faith_map.py` 重生成 CSV
3. 检查三处同步：`CURATED` / `eu5_ck3_faith_map.csv` / 各 `_apply_*` 脚本里的硬编码表
4. **不要重跑 `_apply_faith_map.py`**——它会把已经修好的原始宗教又冲掉。用 `religion_set.py` 改目标省。

### D. 补/改某一层宗派

按 `references/pipeline.md` 第三节的顺序，找到对应脚本，**默认 dry run 先看计划**，再 `--apply`。
注意后面的层会盖前面的层，重跑低层之前先想清楚会冲掉什么。

### E. 排查「为什么这里显示这个教派」

1. `religion_audit.py --provs <省>` 看文件里实际写的值
2. 如果是 rite，查 `references/rites.md` 确认它绑哪个 faith、中文名是什么
3. 如果文件里只有 faith 没有 rite → 显示的是该 faith 的 `main_rite`
4. 如果都没有 → 查 `history/faiths/*.txt` 的日期块和 `common/religion/` 的默认值

## 参考文件

| 文件 | 内容 |
|---|---|
| `references/pipeline.md` | 两层结构、唯一真源、**10 层执行顺序表**、三个传播算法、角色层 |
| `references/rites.md` | 多 rite 的 faith 全表（带中文名）、各地区既定口径、查名字的方法 |
| `references/pitfalls.md` | 坑清单：CRLF / religion 判据 / 有 rite 不写 faith / CU 漏层 / 全量重建风险 |
| `references/cu-source.md` | CU 四层取数、质心匹配容差、三教转换规则、CU 数据本身的偏差 |
| `references/holy-sites.md` | 圣地三层结构、孤儿判定、7 个工具的用法、现状（270 个 / 未确认 72） |
| `references/faith-defs.md` | faith/rite 定义在哪、信仰史日期块、宗教领袖 5 个头衔、新建 faith 的最小写法、本地化 key |

## 纪律

- **动手前先跑 audit**。文件状态可能和记忆里的不一样（用户会自己回滚）。
- **改之前打保存点**。
- **非必要不全量重建**（`eu5_to_ck3.py` 会冲掉所有补丁层），要改就外科手术式只改目标行。
- **诊断类任务默认只读**：先报告结论 + 改法，等用户说「改」才动手。
- **游戏安装目录只读**，产物一律放工作区。
- 用户手改过的文件不许覆盖；写前比对内容，无变化不动 mtime。
- **改完必须跟备份比字节数和 md5。** 只查 BOM/CRLF/括号不够——缩进丢了括号照样平衡
  （见 `references/pitfalls.md` 的「按第一个 `}` 切块」条）。
