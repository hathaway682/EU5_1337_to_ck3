---
name: ck3-title-history-pipeline
description: 本 mod（EU5_Modern_Borders_noshape）头衔历史（世系）的生成与重建流程。当需要重建/补回头衔 holder 序列、排查"某国头衔没历史了"、改挂原版 key、处理组织与国际组织抢 key、或判断某一步该跑哪个生成器时使用。关键词：头衔历史、世系、reign list、holder、zz_eu5_titles、没历史、改名、io_titles、鞑靼枷锁、天朝。
agent_created: true
---

# CK3 头衔历史流水线

## 用途

`history/titles/zz_eu5_titles.txt` 是本 mod 的头衔历史文件（约 4727 个块），每个块是一串
`日期 = { holder = … government = … liege = … }`。本 skill 说明这个文件由谁写、重建时该跑哪几个
脚本、以及"世系整条消失"这类事故怎么补。

## 何时使用

- 「某国头衔没历史了 / 只剩开局一条」
- 「重建一下头衔历史」
- 「改挂原版 key 之后历史丢了」
- 「这一步要跑哪个生成器」
- 排查 liege 悬空、holder 缺失、重复块

## 核心事实（先记住这几条）

1. **这个文件是原地改，不是重建。** `_patch_title_history.py` 的原则是"never rewrites a block it
   has nothing to say about"——它只补缺的字段、只加缺的条目，不重排已有世系。所以它安全，
   但**它也不会把已经丢掉的世系变回来**。
2. **整条世系不是这两段脚本生成的。** 早期的生成器写好了每个头衔的完整 reign list，
   `_patch_title_history.py` 只负责在 1337.4.1 那条上补 holder / government / liege。
   因此**一旦某个块被删，没有任何脚本会重建它**，只能从备份搬回来（见「世系补回」）。
3. **`_fix_politics_output.py` 不是头衔历史脚本。** 它是总装，一次写 20 多个产物。修头衔历史时
   **绝不要跑它**，否则会连带重写：
   - `history/provinces/00_generated_provinces.txt` 的 21046 条 culture / faith / holding
   - `history/characters/zz_eu5_government.txt` 的政体与 832 个 regent
   - `common/landed_titles/zz_eu5_titular.txt` 的 243 个颜色
   - `zz_eu5_tributaries.txt`、`zz_eu5_primary_titles.txt`、两种语言的本地化

   2026-10-28 就是为修两个头衔的历史跑了它，把地块的文化宗教一起冲掉了（用户自行回滚）。
4. **`io_titles` 只能放"EU5 里没有对应国家的组织"。** 见「组织抢 key」。
5. **一切文本文件 BOM×1 + CRLF**，裸 LF 必须为 0。

## 三个脚本的职责

| 脚本 | 输入 | 输出 | 修头衔历史时要跑吗 |
|---|---|---|---|
| `export_politics.py` | EU5 `main_menu/setup/start/*` | `eu5_politics.json` | **要**（改了 politics 的输入才需要） |
| `_fix_politics_output.py` | politics.json + peoples.json + csv + mapping | 20+ 产物（含头衔**声明**、不含历史） | **不要** |
| `_patch_title_history.py` | politics.json + `zz_eu5_titles.txt` | 只改 `zz_eu5_titles.txt` | **要** |

`export_politics.py` 的输出目录由 `--export` 指定，默认 `Global_modern_map/eu5_export`。这个目录必须
**完整**（含 `eu5_peoples.json`、`csv/definition.csv`、`mapping.json`、`landed_titles/`），
不完整会在 `csv/definition.csv` 处直接报 FileNotFoundError。

## 标准流程：重建头衔历史

```bash
cd "<GLOBAL_MOD>/eu5_export"
PY="C:/Users/DELL/.workbuddy-ai/binaries/python/versions/3.13.12/python.exe"
MOD="D:/Documents/Paradox Interactive/Crusader Kings III/mod/EU5_Modern_Borders_noshape"
EXP="D:/Documents/Paradox Interactive/Crusader Kings III/mod/Global_modern_map/eu5_export"

# 1. 只有改了 politics 的输入（io_titles、ruler_term 解析、rank 规则…）才需要这一步
"$PY" export_politics.py --force

# 2. 只写头衔历史
"$PY" _patch_title_history.py --mod "$MOD" --export "$EXP"
```

`_patch_title_history.py` 支持 `--dry-run`，先看它打算改什么再落盘。

判断"要不要跑第 1 步"：`io_titles`、`rulers` 提取、`rank` 判定这些都在 `export_politics.py` 里，
改了它们就必须重出 politics.json；只改 `_patch_title_history.py` 自己的逻辑则跳过第 1 步。

## 关键故障：组织抢 key（世系整条消失）

**症状**：某个王国/帝国只剩 1337.4.1 一条，历代世系全没；同一次运行里其他改名 key 的历史都在。

**日志特征**：`_patch_title_history.py` 打印 `old blocks merged away: N`。

**根因**：EU5 的 `15_international_organizations.txt` 里有些是**国际组织**，转换里有一张
`io_titles` 表给它们铸头衔。如果这个组织**同时有对应的 EU5 国家**，两个来源就落到同一个 key 上：

1. 组织那一步先写一个**只有当前领袖 1 条**的块（`wanted[key] = org["leader_character"]`）；
2. 国家的完整世系块在改名预处理里发现"新 key 已有块"，被判为重复，**整块丢弃**。

2026-10-28 的实例：

| 组织 | type | 对应国家 | 被抢的 key | 丢掉的世系 |
|---|---|---|---|---|
| 鞑靼枷锁 | `tatar_yoke` | GLH | `e_golden_horde` | 11 条（1207 术赤起） |
| 天朝 | `middle_kingdom` | CHI | `h_china` | 13 条（1271 忽必烈起） |

**正确口径**：`io_titles` 只留 `hre`、`ilkhanate`——这两个 EU5 里没有对应的国家 tag，
组织的头衔是地图上唯一能承载它的东西。其余有国家的组织一律走国家路径，成员照样答于领袖
（fallback 到 `title_of[leader]`，`liege = h_china` 仍是 122 条，结果不变）。

需要同时改两处：

- `export_politics.py` 的 `io_titles`（用于 `io_of` / `senior_liege`）
- `_patch_title_history.py` 的 `io_titles` **和** 组织 wanted 循环

`_export_title_map.py` 的 `ORG_TITLES`、`_apply_horde_vassal_fix.py` 的 `IO_TITLES` 是诊断表与
一次性旧补丁，不在链路里，可以不动。

## 关键故障：改名预处理删旧块

`_title_overrides.csv` 的 `country / title_key` 让某个国家改挂别的 key（原版同名 key、贝伊国升格）。
`_patch_title_history.py` 会把旧 key 的**整块改名**，以此保住世系（丹麦 31 条、英格兰 29 条）。

隐患：`if new in present: merged += 1`（直接跳过旧块）。它假定"新块更全"，实际往往是
**新块只有一行、旧块有整条世系**。上面「组织抢 key」就是这个逻辑咬到的。

排查时先看 `merged away` 的计数：只要不是 0，就去确认被并掉的是短块还是长块。

## 世系补回（块已被删时）

没有生成器会重建整条世系，只能从备份搬。备份来源按时间就近选：

- `_backup_pipeline_refactor_20261028_162023/zz_eu5_titles.txt`
- `history/titles/zz_eu5_titles.txt.bak_<时间戳>`（`_patch_title_history.py` 每次运行前自动写一份）

做法：按日期把旧块（如 `e_eu5_chi`）的条目**并进**新块（如 `h_china`），

- 已有的日期保留原 body（开局那条带 `government =`，不能覆盖）
- 只补新块缺的日期
- 按 `(年,月,日)` 数值排序，不能按字符串排（否则 1329.10.8 会排到 1329.2.27 前面）
- 行尾统一用文件原有的（CRLF），拼接时先 `replace("\r\n","\n")` 再 `replace("\n", nl)`，
  否则块内会留下裸 LF

## 校验清单（改完必看）

```python
import io, re, collections
t = io.open("history/titles/zz_eu5_titles.txt", encoding="utf-8-sig").read()
keys = re.findall(r"(?m)^([a-z]_[a-z0-9_]+)\s*=\s*\{", t)
decl = set(keys)
lies = re.findall(r"(?m)^\t\tliege = ([a-z0-9_]+)", t)
print("blocks", len(keys), "unique", len(decl))
print("liege 行", len(lies), "悬空", len([x for x in lies if x not in decl]))
print("重复 key", {k: v for k, v in collections.Counter(keys).items() if v > 1})
raw = io.open("history/titles/zz_eu5_titles.txt", "rb").read()
print("BOM", raw.count(b"\xef\xbb\xbf"), "lone LF", raw.count(b"\n") - raw.count(b"\r\n"))
print("braces", t.count("{") - t.count("}"))
```

正常值：blocks 4727 / unique 4723 / liege 2086 行 / 悬空 0 / 裸 LF 0 / 大括号 0 / BOM 1。

`dup` 目前会报 `c_ise`、`c_kazusa`、`c_settsu`、`c_tango` 各 2 个——这是**既有**的重复块
（内容完全相同、相邻 8 行），2026-10-28 之前就在，不是重建引入的。除这 4 个以外出现任何 dup
都是本次操作弄出来的。

另外按国家抽查条数：`k_denmark` 31、`k_england` 29、`h_china` 13、`e_golden_horde` 11。
条数掉到 1 就是世系被删了。

## 硬编码 key 的坑

任何"某国底下所有人都答于它"的地方都不许写死 key。`e_eu5_jap` 这个坑让 61 个县的 liege
和 145 个日本家族的 liege 全悬空过。正确写法：

```python
japan = ckey("e", "JAP")   # 走 _title_overrides，跟着强制 key 走
```

## 禁止事项

- 不要为了修头衔历史去跑 `_fix_politics_output.py`。
- 不要整体重建 `zz_eu5_titles.txt`——补丁层会被冲掉。
- 不要用字符串排序拼日期条目。
- 不要在 `io_titles` 里加有对应国家的组织。
- 不要在没确认备份存在的情况下删块。
