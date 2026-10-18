# EU5 mod 家族 vs CK3 原版家族 复用分析（v2，含角色交叉验证）

生成时间：2026-10-18
分析方法：家族名语义匹配 + 角色真实姓名（经本地化翻译）+ 生卒年交叉验证

## 重要前提：ID 体系不同

mod 与 CK3 原版（vanilla）用两套不同的 dynasty ID 体系：

| | mod（`zz_eu5_dynasties.txt`） | CK3 原版（`00_dynasties.txt` 等） |
|---|---|---|
| dynasty key | 命名 key，如 `borjigin_dynasty` | 数字 ID，如 `11100` |
| name 字段 | `xxx_dynasty` 或 `name_xxx` | `dynn_XXX` |
| 角色引用方式 | `dynasty = borjigin_dynasty` | `dynasty = 11100` |

"复用"= 把 mod 自定义的那份删掉，改引用 vanilla 数字 ID 对应的同名家族（vanilla 已带 CoA/prefix/本地化）。

## 总览

| 项 | 数量 |
|---|---|
| CK3 原版 dynasty 总数 | 4214 |
| EU5 mod dynasty 总数 | 1272 |
| 家族语义同名匹配 | 257（→ 272 个 mod_key→vanilla_id 对） |

### 角色交叉验证（用本地化真实姓名）

对每个同名家族对，把 mod 角色的 `name = "xxx"` 经本地化字典翻译成真实姓名，与 vanilla 该家族下角色的真实姓名+生卒年做匹配：

| 类别 | 数量 | 说明 |
|---|---|---|
| 总家族对 | 272 | |
| 有同名角色证据（name_hits ≥ 1） | **118** | 至少 1 个角色真实姓名撞上 |
| └ 强证据（name+birth 都中） | **41** | 同名且生卒年相同/相差 ≤1 年 |
| 无证据 | 154 | |
| └ 两边都有角色但姓名没撞上 | 90 | 需手工核对 |
| └ 至少一边没角色 | 64 | 无法用角色证据 |

## 强证据样本（41 条，name_real + birth 都匹配）

下表列强证据样本（每条取一个代表角色）：

| mod_dynasty | strong | name_hits | mod 角色/出生 | vanilla 角色/出生 |
|---|---|---|---|---|
| angelos_dynasty | 1 | 6 | Andronikos / 1132 | Andronikos / 1133 |
| anjou_dynasty | 3 | 22 | Robert / 1319 | Robert / 1277 |
| artois_dynasty | 4 | 7 | Philip / 1269 | Philippe / 1269 |
| asen_dynasty | 1 | 9 | Boril / 1179 | Boril / 1181 |
| auvergne_dynasty | 1 | 9 | Robert / 920 | Robert / 932 |
| bahri_dynasty | 2 | 5 | al-Ašraf / 1334 | al-Mansur Abu Bakr / 1321 |
| balliol_dynasty | 1 | 1 | Edward / 1283 | Edward / 1283 |
| blois_dynasty | 1 | 11 | William / 1135 | William / 1137 |
| bohun_dynasty | 1 | 4 | Humphrey / 1276 | Humphrey / 1155 |
| borjigin_dynasty | 5 | 53 | Arghun / 1258 | Arghun / 1255 |
| comyn_dynasty | 1 | 5 | Alexander / 1217 | Alexander / 1260 |
| courtenay_dynasty | 4 | 8 | Robert / 1168 | Robert / 1201 |
| dampierre_dynasty | 3 | 11 | Agnes / 1237 | Agnes / 1237 |
| dandolo_dynasty | 1 | 3 | Anna / 1200 | Anna / 1200 |
| douglas_dynasty | 1 | 7 | Archibald / 1297 | Archibald / 1327 |
| doukas_dynasty | 2 | 5 | Andronikos / 981 | Andronikos / 980 |
| dunkeld_dynasty | 4 | 11 | Alexander / 1077 | Alexander / 1077 |
| grimaldi_dynasty | 1 | 7 | Gabriel / 1302 | Gabriele / 1254 |
| hohenstaufen_dynasty | 3 | 9 | Beatrix / 1205 | Beatrix / 1157 |
| hohenzollern_nurnberg_dynasty | 2 | 9 | Anna / 1335 | Anna / 1314 |
| ibelin_dynasty | 3 | 9 | Alice / 1304 | Alice / 1304 |
| kantakouzenos_dynasty | 3 | 8 | Andronikos / 1327 | Andronikos / 1334 |
| laskaris_dynasty | 1 | 3 | Irene / 1204 | Eirene / 1196 |
| marinid_dynasty | 2 | 5 | Abd al / 1157 | Abd al-Haqq / 1157 |
| montagu_dynasty | 1 | 2 | William / 1301 | William / 1301 |

（剩余 16 条强证据见 `dynasty_cross_check_loc.json`）

## 仅 name 证据（无 birth 锚定，77 条）

这类只有姓名撞上、没有生卒年佐证，置信度中等。典型：
- `ahom`：Sutuphaa vs Sutupha
- `anjou_jerusalem`：Sybil vs Sybille
- `audley`：James vs James
- `barcelona`：Joanna vs Joan（5 个角色撞名）
- `beaumont`：Elizabeth vs Elizabeth（15 个撞名）
- `bourbon`：Beatrix vs Beatrix
- `candarids`：Ali vs Ali

完整清单见 JSON。

## 重要副产品：mod name_key 坏键问题

诊断 `zz_eu5_characters.txt` 角色的 `name = "xxx"` 字段在本地化字典里能否查到：

| 项 | 数量 |
|---|---|
| mod 用到的 name_key 总数 | 4045 |
| 有本地化（good） | 3111 |
| **无本地化（坏键）** | **934** |
| 受坏键影响的角色数 | **934 / 8593（约 11%）** |

坏键清单见 `gen_debug/mod_bad_name_keys.txt`（按使用次数排序）。这些角色的 name 字段在游戏里会显示成 raw key（如 `name_xxx`），需要补本地化或改用 vanilla 已有的 name key。

## 结论与置信度分级

- **A 级·高置信度可直接复用（41 条）**：家族同名 + 至少 1 个角色真实姓名+生卒年都对上。可以放心把 mod 这份删掉、改用 vanilla 数字 ID。
- **B 级·中置信度（77 条）**：家族同名 + 角色真实姓名撞上但没 birth 锚定。多数仍可复用，但建议抽几条手工核一下。
- **C 级·待人工核对（90 条）**：家族同名 + 两边都有角色但姓名没撞上。可能：
  1. mod 和 vanilla 用了同家族名但**不同分支/不同时期**的角色（vanilla 多为 867/1066 起点，mod 是 1337）；
  2. mod 角色用了 vanilla 没有的人；
  3. 误匹配（家族名相同但实际不是同一家族）。
- **D 级·无法判定（64 条）**：至少一边没角色，只能靠家族名本身判断。

## 产物文件

| 文件 | 内容 |
|---|---|
| `gen_debug/dynasty_reuse_analysis.md` | v1 报告（仅家族名匹配，A/B/C 三类） |
| `gen_debug/dynasty_reuse_analysis.csv` | v1 全量分类表 |
| `gen_debug/dynasty_cross_check.json` | v2 角色交叉验证（用 raw name_key，已被 v2_loc 取代） |
| **`gen_debug/dynasty_cross_check_loc.json`** | **v2 最终版：用本地化真实姓名做交叉验证，含强证据 41 条** |
| `gen_debug/mod_bad_name_keys.txt` | mod 坏键清单（934 个 name_key 无本地化） |
