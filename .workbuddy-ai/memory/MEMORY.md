# 项目长期记忆（EU5_Modern_Borders_noshape）

## 宗教 / 礼（rite）关键机制

- **省份只写 `faith = X` 而没有 `rite =` 行时，游戏按该 faith 的 `main_rite` 显示**
  （`common/religion/faith_types/00_faith_types.txt`）：
  `sunni.main_rite = hanafi`、`shia.main_rite = imami`、`orthodox → byzantine_rite`、
  `miaphysitism → armenian_rite`、`coptic → coptic_rite` 等。
  → **凡「某地莫名是 X 礼」，第一件事就是查该省有没有 `rite =` 行；没有就是回落，不是被填错了。**
- 伊斯兰礼的生成是**四段式**：`_eu5_schools.py` → `_apply_rites.py` →
  `_apply_christian_rites.py` → `_apply_islamic_geo_spread.py`。只有后两个会碰 `rite` 行；
  且**任何一段都不得改 `faith`**（改完用 `gen_debug/_snap_faith.py` 校验，必须 0 差异）。
- **反复踩的同一个坑：按「县」判定，按「省」落地。** 县级依据是 EU5 的 `county_religion`
  （人口多数宗教），但 `faith` 是逐省按人口判的，一个县里可能混着 sunni / shia / 异教省。
  已知 5 例：戈尔甘、库法、西沃里尼亚、吉赞/希尔达、多贝亚/锡达莫。
  → 加地区规则时必须问自己：这条规则该按县还是按省？
- 伊斯兰层的落点优先级：县级确定性（owner 的 `sharia_law` > `religious_school`）→
  手动覆盖（imami / 也门 / `REGION_OVERRIDES`，**按省**）→ 逐省 BFS 补漏（只认同父信仰的源）。
- **孤岛传不动**：`_ck3_province_adjacency.json` 只有陆路，没有海路。`adj=[]` 的省
  （拉克沙、马斯克林、nosy_be 等）BFS 一步都走不了，只能靠 `REGION_OVERRIDES` 显式落。
- **印度教分化（faith，不是 rite）的数据上限**：CU 的 `_cu_vs_ours.csv` 只有 2858 行
  （CU 本身只给 2527 个 province 写了 culture/faith 块），其中**印度教 rite 仅 116 行**，
  对应到我们 1242 个印度教省只有 84 个能定派别；剩下 1156 个只能走地区兜底
  （印度→vaishnava_faith、东南亚→shaiva_faith）。**这是 CU 数据本身的覆盖上限，
  不是脚本漏读**——旧 CK3 县色方案只解出 160 县（136 vaishnava + 24 shaiva，无 shakta/smartism），
  所以 CU 方案已经是净改善。脚本 `Global_modern_map/eu5_export/_apply_hindu_faith_cu.py`。

## CK3 数据结构约定（从踩坑中确认）

- **术语红线（用户 2026-10-20 定，汇报/注释/脚本一律遵守）**：
  CK3 侧说 **伯爵领（county）/ 男爵领（barony）**；EU5 侧说 **省份（province）/ 地点（location）**。
  禁止把 CK3 的 county 叫"县"、province 叫"省"。也别说什么"县粒度/省粒度"——
  CK3 的 history/provinces 条目就是男爵领，说"男爵领粒度"。
- **★ CK3 只读伯爵领首府男爵领的 religion/culture**（landed_titles 里该 county 下
  第一个 barony 即首府）。非首府男爵领写了 faith/rite 不影响伯爵领显示。
  判 rite 时逐男爵领判 culture 即覆盖首府；但如果要改"伯爵领显示什么教会"，
  必须动首府男爵领那一条（例如加济安泰普首府 b_ayntab 是 syriac_culture，
  同领的 dluk 是 armenian 也白搭）。

- **dynasty 是宗族，house 是支系**。角色指支系必须写 `dynasty_house = house_xxx`；
  写 `dynasty = house_xxx` 会让游戏去找同名 dynasty，找不到就 fallback 到 `dynn_adam`。
- **COA 按 key 自动匹配**，没有 `coat_of_arms_id` 字段。`common/coat_of_arms/coat_of_arms/` 里
  `house_xxx = <目标>` / `<dynasty_id> = <目标>` 就是挂纹章，别名形如 `house_dreux = 86`。
  别名可以指向别的 COA key 或标题 key（`house_capet = k_france`）。
- 我们的支系 key 若与 vanilla house 同名，vanilla 的 COA 会**自动生效**，不要再写覆盖，
  更不能写 `house_x = house_x` 自引用。
- 文件名 `zz_` 前缀保证在 `00_` 之后加载，覆盖生效。
- `common/dynasty_houses/zz_eu5_merged_houses.txt` 被归并成 house 的条目已注释掉，
  分析脚本要读 culture 必须从备份取。

## 生成器纪律

- 用户手改过的文件绝不覆盖；写前比对内容，无变化就连 mtime 都不动，有变化才备份。
- 生成物按 key 排序、带 BOM（CK3 的 yml 和 common 脚本都要）。
- 生成脚本默认 dry run，显式 `--apply` 才落盘。

## vanilla 数据清单（E:/SteamLibrary/steamapps/common/Crusader Kings III/game）

- `common/coat_of_arms/coat_of_arms/90_dynasties.txt` — 约 3000 个 dynasty/house COA，key 是 dynasty id
- `common/dynasties/` — 10331 个 dynasty，大量没有 COA（运行时随机生成）
- `common/dynasty_houses/` — 596 个 house
- `history/characters/` — 209 个文件 18MB，角色 `name = "Catherine"` 直接是名字
- 注意：本地化里 `japanese_*` 是命名 dynasty，欧洲多用数字 ID；**重名家族常见**
  （Bourbon 329 有 COA / 100146 没有），引用前必须按 name 键二次确认。
- **"安茹"有两把别名的陷阱**：`dynn_Anjou`(723)=安茹 Anjou（安茹系王室/金雀花/耶路撒冷王室，
  查 `history/titles/k_jerusalem.txt` 那些国王 dynasty 全是 723）= `anjou_jerusalem` 用它；
  `dynn_Robertine`(743)=罗贝尔 = `robertian` 用它。**`dynn_Angevin` 是坑**：中文也译"安茹"、
  英文 Angevin，但只在文化命名池(`common/culture/name_lists/00_frankish.txt`)出现，
  **没有任何 dynasty/house 引用、无对应 COA**——别拿它当 dynasty name，会变成无纹章的捏造名。

## EU5 角色名本地化——人名翻译的真相之源（重要约定）

- **改/补 mod 人名（含复合君主名）必须先查 EU5 自带角色名表，不要手工音译：**
  `D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game/main_menu/localization/<lang>/`
  - `character_names_dynamic_l_<lang>.yml`（~50592 条 key，11 语言齐全，含简体中文）
  - `character_names_l_<lang>.yml`（补充）
- 每个 name 部分是独立 key（`name_togha: "脱花"`、`name_timur: "帖木儿"`）；
  部分完整合成名也直接本地化（`name_ang.name_chey: "昂杰"`、`name_indra.name_bhupesvaracuda: "因陀罗普佩斯瓦拉朱达"`）。
- 中文合成规则：按 EU5 部分直接**无分隔符拼接**（脱花+帖木儿=脱花帖木儿）；英文按空格。
- EU5 偶有自己的怪译（tekuder=贴古迭儿/EN=Togoldor，john=约翰/EN=Johan，henry=亨里克/EN=Henrik），
  但既然 mod 是 EU5 转 CK3，**以 EU5 为准**。
- 修复合名脚本：`gen_debug/fix_compound_names.py`（EU5 优先）+ `gen_debug/verify_compound_names.py`。

## 已完成的分期工作

1. 168 个支系归到 42 个宗族下（`zz_eu5_merged_houses.txt`）
2. 修两处致命 bug：house 文件首行 `l_english:/n`、1781 处 `dynasty = house_` → `dynasty_house`
3. 人名本地化补齐：1382 个 `name_eu5_*` key，中英两份 yml
4. 挂 vanilla COA：29 条写入 + 6 条自动生效，共 36 个支系拿到真实纹章
5. 154 个复合君主名按 EU5 本地化重译（脱花帖木儿 等），11 语言文件全部修正
6. **宗族（dynasty）层对齐原版（B 路）全部完成**：27 个可锚定宗族全部对齐原版（3 个先前 + 24 个批量，清单见 `gen_debug/dynasty_alignment_plan.md`）。做法=保留 42 宗族归并，仅把每个父宗族 `name` 改 vanilla 本地化键、在 `common/coat_of_arms/coat_of_arms/95_zz_eu5_dynasty_aliases.txt`（手写"接线"，95_ 晚于 vanilla 90_ 加载）追加纹章别名（有原版 COA 的 21 个挂别名；无原版 COA 的 6 个仅改名）。15 个无原版对应（ivree/nakamura/utsunomiya/kawano/sanjou/shimazu/al_fadl/asturleonesa/chuujou/deste/montfort_feldkirch/seljukids/sratsimir/vatatzes/zovneski）保持 mod 自定义。批量脚本 `gen_debug/align_dynasties.py`（CRLF+BOM 安全、带备份、逐键自检）。

## EU5 素材版权隔离架构（2026-10-18 定）

- master = 发布分支，**不含任何 EU5 纹章素材**（贴图/定义/调色板/别名全在 eu5-coa 分支）；用户：「不敢上创意工坊而已，GitHub 我怕啥」。
- 远程：github.com/hathaway682/EU5_1337_to_ck3（公开库），分支 master / eu5-coa / pop。
- 用户日常用 GitHub Desktop 提交推送，会和我的 git 操作并发——push 前必 fetch。

## Git 分支操作铁律（2026-10-19 用事故换的）

- **禁止 `git worktree`**：worktree = 整库完整检出。本仓库 1GB+，D 盘常期紧张
  （2026-10-19 一度 0 可用），一个 worktree 就能把盘撑爆。跨分支带改动的正确做法：
  只把目标分支的**单个文件** `git show <branch>:<path>` dump 到 C 盘临时文件，改完用
  plumbing 提交（`GIT_INDEX_FILE` 临时索引 → `git read-tree <branch>` →
  `update-index --cacheinfo` → `write-tree` → `commit-tree` → `update-ref`），
  基点一致的其他文件直接 `cacheinfo` 引用源分支提交里的 blob。全程零检出。
- **staging 前先 `git status` 核对每个文件的改动归属**：工作区常同时存在别的会话/
  用户本人的未提交改动。只能逐个 `git add <明确文件>`；`git add 整文件` 前必须确认
  该文件的 diff 全是本次自己的（用备份/基线 diff 验证行数与内容）。
- 生成器升级导致的重导产物（如对照表 CSV 换 schema 的整表 churn）不属于单个修复提交，
  按「只补不改」只改目标行列。
- sandbox 代理可能连不上 GitHub（502），push 失败时如实报告，不要反复重试轰炸。
