# 项目长期记忆（EU5_Modern_Borders_noshape）

> 每日细节在 `.workbuddy-ai/memory/YYYY-MM-DD.md`；流程细节在 `PIPELINES.md`。这里只放长期硬规则。
> **改头衔/法理 → 本文件一、二；改文化/宗教/生成链路 → 先读 `PIPELINES.md`。**

## 一、数据源与层级
- EU5：location→province→area→region。`definitions.txt` tab 缩进，栈解析 `next(x for x in reversed(stack) if x.endswith(("_region","_area","_province")))`。4149 province / 27334 location。
- 人口读 `06_pops.txt` 的 `size`；`eu5_county_peoples.csv` 只是 location 个数多数。
- CK3 `b_<name>` 的 `<name>` = EU5 location 名；质心缓存 `_ck3_province_centroid.json` 读回必须 `{int(k): v}`。
- 头衔 `capital`：`countries[tag]["capital"]` 是 location 名，CK3 侧取 `b_<location>` 的父 `c_`，一律写 `c_`；工具 `_fix_title_capital.py`。`00_landed_titles.txt` 的 capital 是 CU 产物，重跑会覆盖。
- 本地化比 key 权威，先 grep `localization/simp_chinese/`。

## 二、头衔与法理（硬规则）
- 法理树 = CU 1337.4.1 开局态。**2026-11-18 起除 `h_china` 外的大洲霸权全删**（h_america/oceania/africa/asia/atlantic_ocean_continent/europe），其下 13 个帝国升为顶层；`_rebuild_dejure_cu.py` 用 `KEEP_HEGEMONIES` 控制，清理脚本 `_drop_continent_hegemonies.py`。`zz_vanilla_titulars.txt` 里的 h_roman_empire / h_india 等是原版空壳，不是生成器产物。
- 解析 key 正则必须 `[A-Za-z0-9_-]`（`k_kabisay-an` 会被截断）；日期块 key 还要加 `.`。
- **法理只存在于 `00_landed_titles.txt` 的嵌套里**。绝不在别的文件顶层重复声明同一 key——后加载的同名块替换整块、不合并，头衔立刻失去父头衔。改持有人只动 `history/titles/`，两文件保持零重名。
- 占用原版 key 必须成对剔除：`zz_vanilla_titulars.txt` 删 shim ＋ `00_generated_titular_guard.txt` 删 `destroy_title`（该 guard 文件目前不存在，保险只剩 `can_create = { always = no }`）。真源 `_title_overrides.csv`。
- 原版有的键 ≠ 本 mod 有：改 `title_key` 前在三个声明文件里确认目标键存在，「删 shim」与「补声明」成对做；收尾校验 history 里所有 `liege` 目标都能找到。
- stale-liege 清扫的兜底不能按 `liege in rename.values()` 判，要看该块的 liege 是否真被重写过。
- 无地 d/k/e 全丢不留空壳（判据 `rank in (d,k,e) and not own_counties`）；删头衔连带清四处：`eu5_titles_dropped.txt`、`zz_eu5_titular.txt`、11 语言本地化、`zz_eu5_primary_titles.txt`。
- `io_titles` 只放 EU5 里没有对应国家的组织（hre、ilkhanate）；`tatar_yoke`/`middle_kingdom` 有国家（GLH/CHI），给头衔会丢掉整条世系。
- 首府 = 伯爵领块内第一个 `b_`；dynasty=宗族、house=支系；文化引用 `re.finditer(r'(?<![a-z_])culture\s*=\s*(\w+)', line)`。
- 宗族对齐：候选集 = 全部 `*_dynasty`（`zz_eu5_dynasties.txt` 1111 个），不用 `dynasty_merge_map.json` 的 42 个；匹配用 dynasty KEY 主体不用 name；culture 先经 `_culture_classification.csv` 归一化。**模糊名+同文化不能自动落地（0.85 阈值误配一片），只做 score=1.000 精确同名，其余人工核**；v2 批量 170 个已整体回滚。
- 日本宗族：源/平/大和系保持独立 dynasty，藤原子系并入 `fujiwara_dynasty`（`_merge_fujiwara_subclans.py`）。
- title_map：帝国/王国/公国→`X_eu5_TAG`；日本→`c_nf_*`。主头衔 220 条，4 条手工指定只在 `_patch_primary_titles_file.py`。
- **按 title_map 补内容前先过 `_title_overrides.csv`**：CSV 的 title_key 常是改名前的旧键（SIC 记 k_sicily 实为 k_trinacria；DLH 记 k_delhi 实为 e_hindustan）。判据 `override[tag] != csv_key` 就跳过。

## 三、生成器纪律
- **★ 绝不对真实文件做「写入测试」**（`open(p,'wb')` 一打开就截断；2026-11-18 第二次犯）。只读检查用 `os.stat` / `'r+b'` 打开即关。产物一律「临时文件 + `os.replace`」。
- 用户手改文件绝不覆盖；默认 dry run；非必要不全量重建；诊断默认只读、报告结论+改法等用户说「改」；行号一律绝对行号；游戏安装目录只读。
- **只改 politics.json 的输入时链路只需 `export_politics.py` → `_patch_title_history.py`，绝不跑 `_fix_politics_output.py`**（总装脚本一次写 20+ 产物，2026-10-28/29 各犯一次）。
- **`zz_eu5_titles.txt` 绝不可整体重建**；`_patch_title_history.py` 只补不改。补丁层清单见 `PIPELINES.md` 三。

## 四、其它
- EU5 新版目录：`main_menu/setup/1337/10_countries.txt`（旧 `setup/start` 已拆，硬编码会静默失效）。
- 东南亚曼陀罗口径：以 `_gov_rules._sea` 的 `reforms = { mandala_system }` 为准；`export_politics.py` 的「东南亚 monarchy + 非穆斯林 → mandala」是过宽旁路。例外 CHA 写进 `MANDALA_EXCEPTIONS`。
- 复合名每部分是独立 key（中文无分隔符、英文空格）。
- Git：master=发布分支，eu5-coa 存纹章；禁 worktree；GitHub Desktop 提交，push 前 fetch。
- 地图可视化一律 `ck3-mapviz`。
- CU 会开局重算 development（`cu_neighbor_reassigned_initialization.txt` 已注释，重跑或更新 CU 后必查）。
- 备份：`*.bak*` 放 `F:/EU5_Modern_Borders_bak/`，按原目录结构；项目目录内不留 bak。
- 编码：`.txt`/`.yml` 多为 UTF-8-BOM + CRLF，但 **`00_landed_titles.txt` 是 UTF-8 无 BOM + LF**，`history/titles/zz_eu5_titles.txt`、`history/characters/zz_eu5_government.txt` 也是纯 LF。改前先数 `b'\r\n'`/`b'\n'`。删整行正则带 `[^\r\n]*\r?$`。

## 五、已完成 / 遗留
- 已完成勿重做：168 支系→42 宗族；154 复合君主名重译；4361 宗教人物改写；印度教整县染色；CU 法理树重建；ALB/MLL 恢复王国清 stale liege；LIT 升王国 + 8 公国；类1 补世系 244 标题（`_fill_lost_lineages.py`）；**删 6 个大洲霸权、13 帝国升顶层（2026-11-18）**。
- 待定：① BKZ/SKN 库西雅 7 省 rite ② 10990 pagan 角色文化 ③ 244 印度教省 CU 记耆那 ④ pamiri→afghan ⑤ tai_lu/tai_nua ⑥ coptic 0 省阈值 ⑦ 涅涅茨→Bjarmian ⑧ 萨尔语群 17 文化 ⑨ guard 文件是否补 ⑩ 10-29 总装另改的 11 个无备份文件未核 ⑪ 类2「没头衔挂不了」28 国 98 人（`_lost_lineages_split.csv`）⑫ `k_mediterranean_sea` 显示名 ⑬ `c_armagnac` 断引用 holder。

## 六、首府 / 宗教
- 强制锁定首府标准流程（两处法理树、`zz_eu5_titles.txt` holder、title_map 只改 country 行、降级判据、`eu5_reassign_keep.json`、导出后重跑 `fix_holstein_denmark.py`）→ **`PIPELINES.md` 八**。
- 宗教改动一律走 skill `.workbuddy-ai/skills/ck3-religion-pipeline/`（四工具；切省份块必须按大括号深度；mod 无 faith_types/rite_types）→ **`PIPELINES.md` 八 末段**。
