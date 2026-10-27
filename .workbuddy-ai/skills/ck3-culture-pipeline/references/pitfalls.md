# 踩坑清单（每一条都真踩过）

## 数据解析

- **`definitions.txt` 必须栈解析**。它是 tab 缩进的嵌套结构，只认行内列表只能解析到
  17032 / 27418 个 location。正确写法：
  `next(x for x in reversed(stack) if x.endswith(("_region","_area","_province")))`。
  易错归属：andaman→north_sumatra_area、sumatran_islands→south_sumatra_area、
  苏拉威西=celebes_area、米佐丘陵在 bengal_region 下叫 hill_area。
- **`eu5_county_peoples.csv` 是 location 个数多数，不是人口**。要人口必须自己读
  `main_menu/setup/start/06_pops.txt`（`size` 是浮点）。
- **CK3 文化文件首行带 BOM**（`00_bantu.txt` / `00_nakkavaram.txt` / `00_somalian.txt`），
  用 `^[a-z_]+ = \{` 匹配会漏掉第一个文化。读文件一律 `encoding="utf-8-sig"`。
- **统计文化引用必须用 `(?<![a-z_])culture\s*=\s*(\w+)`**，否则会命中 `sub_culture` 之类的子串。
- **质心缓存 JSON 的 int 键**：`{int(k): v}`，否则全部查不到。

## 规则表

- **Python 字典重复 key 会静默覆盖**。`LANG_RULE` 里 shan_dialect / kam_language / kra_language
  各写过两次，后写吃掉侗台三分口径。**每次改完必须扫重复**：

  ```python
  import ast, collections, io
  tree = ast.parse(io.open('gen_debug/_classify_cultures.py', encoding='utf-8').read())
  for n in tree.body:
      if isinstance(n, ast.Assign) and isinstance(n.value, ast.Dict):
          keys = [k.value for k in n.value.keys if isinstance(k, ast.Constant)]
          dup = [k for k, v in collections.Counter(keys).items() if v > 1]
          if dup: print(n.targets[0].id, dup)
  ```

- **`CULT_RULE` 优先级高于 `GROUP_RULE_STRONG`**。如果先给某个文化写了 CULT_RULE 指向 A，
  之后又想让整组走 B，**必须把那几条 CULT_RULE 删掉**，否则它们会挡住组规则。
  （实例：alor/makasae/bunak/fataluku → maluku 那 4 条删掉后，`papuan_group` 才接管得住。）
- **`GROUP_RULE_STRONG` 只认 `eu5_groups` 的第一位**。写之前先看目标组的成员在组合里排第几。

## 省份层

- **`prussian` 双义**：省份层现存的 30 个 prussian 是波罗的普鲁士人（pruthenian/sudovian/
  curonian 改过来的），再按 CSV 扫一遍会误改成萨克森。脚本必须有 `KEEP_IN_PROV` / `KEEP_IN_PEOPLE`。
- **按县判定、按省落地**是反复踩的坑。判定用 EU5 province 的人口多数，落地写该 province 下
  所有男爵领，保证同一个 CK3 伯爵领内不会五花八门。
- **不属于任何 county 的省会被漏掉**。`_apply_province_pop_culture.py` 只走 county，
  改完记得用「member → 目标」映射把残留省补一遍（查法见 `culture_audit.py` 的 [3] 项）。
- **`--only-selected` 一定要加**。不加会把 `cmap.get(eu5, eu5)` 的兜底值（裸 EU5 key）写进旧世界。
  干跑时如果看到 `greek_culture` / `farsi_culture` 这类裸 key 冒进 top 列表，就是漏了这个开关。

## 文件格式

- **CRLF 丢失**：`io.open(p, encoding='utf-8-sig')` 读进来是 `\n`，写回就变成裸 LF。
  必须按字节读 → `split('\n')` → `'\r\n'.join()` → 加 BOM 写字节。
- **CSV 写坏**：Excel 独占锁会 `WinError 32`，先写 `.tmp_new` 再用 `--classif` 指过去。
- **写完必须复核**：BOM 在不在、`raw.count(b'\r\n')` 是否等于行数、裸 LF 是否为 0。

## 本地化

- **文化本地化一律不带「人」**：`_collective_noun` 等直接写族名。
- 改本地化要同时改**生成器模板**（`gen_debug/_apply_eu_culture_merge.py` 的 LOC 模板），
  否则重跑会把「人」写回来。
- **CK3 原版只有 `yeren`（野人）带「人」**，那是文化本名，不动。

## 新文化定义

- 定义写在**独立文件** `zz_eu5_culture_new.txt` / `zz_eu5_culture_group.txt`，
  **不要写进 `zz_eu5_culture_merge.txt`** —— 那个文件由 `_apply_eu_culture_merge.py` 重跑覆盖。
- `tradition` 要先 grep `00_generated_cultures.txt` 确认**已经在用**。在 CK3 目录有定义但 mod 里
  0 次使用的疑为 DLC（如 `tradition_tgp_rice_cultivators` / `tradition_fp3_irrigation_experts` /
  `tradition_stratified_society`）。
- `name_list` 与 `ethnicities` 只能复用同组资源；支柱用 `<group>_group` /
  `eu5_heritage_<group>_group`（`00_generated_pillars.txt` 里成对存在）。
- 新建后要校验引用完整性：heritage / language / tradition / name_list / ethnicity / ethos /
  martial_custom 全部能解析到。
- **颜色去重**：克隆代表文化会导致撞色，129 个组文化里出现过 4 组同色（147 92 94），需要微调。

## 不要做的事

- 不要按文件夹名 / 文件名脑补数据用途（mod 名带 modern 不代表里面的数据才是要用的）。
- 不要擅自换已经跑通的方法，也不要自己拍数值阈值 / 半径。
- 不要因为「顺手」去改用户没提的相邻系统。
- 不要在诊断任务里顺手改代码 —— 用户可能正在跑游戏实测。
