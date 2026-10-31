# 宗族（dynasty）对齐原版 —— 规则 v2

> 2026-10-31 定。起因：用户发现 `rurikovich`（留里克）没被对齐，追查后确认是**规则盲区**，不是手滑漏列。

## 一、旧规则的两个盲区（为什么 rurikovich 会漏）

1. **候选集错**：旧规则只取 `dynasty_merge_map.json` 里的 **42 个"归并父宗族"**。
   `rurikovich` 在 mod 里只出现 1 次（仅定义、没有任何 `house` 子支系引用），
   它是个**独立 dynasty**，从不进入 BFS 归并，于是被整个流程跳过。
   mod 实际有 **1111 个 dynasty 块**，归并只覆盖 210 个（42 父 + 168 子），
   其余 ~900 个独立 dynasty 从未被对齐检查扫过。

2. **匹配键错**：旧规则靠 `name` 字段/人工判断。
   但 `name` 是**本地化键**，可能是错译——`rurikovich` 的 name 是 `name_roderick`（"罗德里克"），
   而 vanilla 正确键是 `dynn_Rurikid`（"留里克"）。拿 name 匹配必然漏。
   （"罗德里克"在 vanilla 其实是另一个键 `dynn_Rotreik`。）

3. **culture 未归一化**：mod dynasty 的 culture 仍是 EU5 key（如 `muscovite`），
   CK3 没有 `muscovite` 文化（对应 `russian`）。直接拿 culture 硬比会漏。

## 二、v2 规则

- **候选集**：mod 全部 `*_dynasty` 顶层块（`common/dynasties/zz_eu5_dynasties.txt`，1111 个）。
- **匹配键**：dynasty KEY 去掉 `_dynasty` 后缀（EU5 原始家族名，如 `rurikovich`），**不用 name**。
- **文化匹配**：mod culture 先经 `gen_debug/_culture_classification.csv` 的 `target` 列
  归一化到 CK3 文化（`muscovite -> russian`），再与 vanilla dynasty 的 culture 比对。
  无 culture 的 dynasty 不算文化匹配（只能靠名字）。
- **名字评分**：`difflib.SequenceMatcher` ratio + 受控词根加分
  （公共前缀 ≥5 且长度差 ≤4 时提升到最多 0.95，避免短名前缀造成假满分）。
- **vanilla 数据源**：`E:\SteamLibrary\...\game\common\dynasties\*.txt`（只读，10078 个 dynasty）。

### 置信分层

| tier | 条件 | 处理 |
|---|---|---|
| A | 名字 ≥0.99 + 文化匹配 | 最安全，可自动 |
| B | 名字 0.85~0.99 + 文化匹配 | 较安全（rurikovich 在此层） |
| C | 名字 0.62~0.85 + 文化匹配 | **有误配，必须人工复核** |
| D | 名字 ≥0.85 但文化不匹配/无 culture | 名字精确的多数对；跨文化同名可疑 |
| E | 名字 0.62~0.85 + 文化不匹配 | 复核 |
| N | 无候选 | 保持 mod 自定义 |

## 三、当前结果（2026-10-31，dry-run）

- mod dynasty 1111 = 已对齐 28 + 待处理 1083
- A=112 B=58 C=145 D=221 E=453 N=94
- `rurikovich` 诊断：`core=rurikovich, norm_culture=russian -> 705 dynn_Rurikid, score=0.850`（B 层，规则本可捕获）

**已知误配样例（C 层，证明不能自动）**：
`hanau→dynn_Hainaut`、`hohnstein→dynn_Holstein`、`tamura→dynn_Tomura`、`chiavelli→dynn_Crivelli`、`neville→dynn_Mandeville`。

**D 层跨文化同名可疑样例**：`bali→bedouindyn014 dynn_Bali`（巴厘岛 vs 贝都因，同名巧合）。

## 四、用法

```bash
python gen_debug/_align_dynasty_v2.py           # dry-run，输出 dynasty_alignment_candidates.csv
python gen_debug/_align_dynasty_v2.py --apply   # 落地（当前版本只出清单，写回+COA 追加待实现）
```

候选清单：`gen_debug/dynasty_alignment_candidates.csv`
（列：tier, mod_key, mod_name, mod_culture, culture_norm, van_key, van_name, van_culture, name_score, culture_match, mod_line）

## 五、落地注意

1. 只建议自动落地 **A+B**（名字精确/高相似 + 文化匹配）。
2. C/E 必须人工逐条过；D 里名字 1.000 的多数可信，但跨文化同名要剔。
3. 改 name 时用 vanilla `dynn_*` 键**原样照搬**（含 `dynn_KudO_`/`dynn_SU_pplingenburg` 这类怪字符）。
4. 挂 COA 别名前必须确认 vanilla 该 dynasty 真的有 COA 条目（查 `90_dynasties.txt`），没有的只改名不挂。
