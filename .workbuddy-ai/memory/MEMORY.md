# 项目长期记忆（EU5_Modern_Borders_noshape）

> 每日细节在 `.workbuddy-ai/memory/YYYY-MM-DD.md`；这里只放长期有效的口径、坑与纪律。

## 一、宗教 / faith / rite

### 1.1 地理树解析
- `EU5/game/in_game/map_data/definitions.txt` 是完整地理树 `subcontinent={region={area={province={loc...}}}}`，tab 缩进（1=region、2=area、3=`*_province`）。**必须栈解析**：`next(x for x in reversed(stack) if x.endswith(("_region","_area","_province")))` 推层级；只认行内列表只能解析到 17032/27418。
- 易错归属：`andaman_province`→`north_sumatra_area`；`sumatran_islands_province`→`south_sumatra_area`；苏拉威西 area 名 `celebes_area`；米佐丘陵在 bengal_region 下叫 `hill_area`。
- `indochina_region` = 613 loc / 104 prov（去 `malay_peninsula_area` 48 loc 后 565 loc / 95 prov）。

### 1.2 已定的 faith 映射（ religion → faith 一张表，逐宗教整体落 ）
- 东北印度：米佐丘陵→`sedism`；阿萨姆+门隅→`donyipoloism`。
- **萨尔语群不可整族归并**：先查该语系里是否已混多个 faith。
- **「门顿教」是 religion 名**（`mundhum_religion`），faith 有 kiratism/kiratism_old/yumaism/yumaism_old；省份落 `kiratism`。
- 欧洲/彼尔姆：高加索 4 个→`tengri_pagan`（覆盖 CU）；erzya/moksha→`finnish_pagan`；samoyedic→`siberian_pagan`（`_apply_euro_perm_faith.py`）。
- 中南半岛（用户「我只说原始宗教」，`theravada_faith` 257 省不动）：indochina 区域 11 个原始宗教→`satsana_phi`；缅彝语群+土家语→`bimoism`；泰语→守护灵教；壮侗语→麽教。
- 非洲：`nyama_religion`→`west_african_bidu_pagan`（宗教级 1 对 1）；语系映射只处理 `folk_*`。
- **中文名别混**：CK3 `satsana_phi`=守护灵教；EU5 同名宗教叫丕教。
- **班图终态**：CU 覆盖区内剩 17 个 `bantu_religion` 保持 `pagan` 是有意终态，用户已确认满意，**不要再提议拆**。
- CK3 原版东南亚/南岛可用 faith 仅 8 个：dayawism/kaharingan/tolotang/aluk/bilikuism/pulugaism/satsana_phi/hantuism。
- 上述 faith 均自带 `main_rite = 同名`，只写 `faith =` 即可。
- **★ 带中文的信仰映射表**：`Global_modern_map/eu5_export/eu5_ck3_faith_map_zh.csv`（BOM+CRLF，293 行）。
  生成脚本 `_add_zh_to_faith_map.py`（dry-run 默认，`--apply` 落盘）。
  在源表 8 列（`eu5_religion,group,eu5_name,locations,ck3_faith,ck3_rite,match,note`）之后补 7 列：
  `eu5_religion_zh`、`eu5_group_zh`、`ck3_faith_zh`、`ck3_religion_zh`、`ck3_rite_zh`、
  `our_faith_provinces`、`our_faith_rites`。293 行中文 0 缺失。
  - 中文源：EU5 宗教/分组 → `EU5/main_menu/localization/simp_chinese/religion_l_simp_chinese.yml`；
    CK3 信仰/宗教/礼 → `CK3/localization/simp_chinese/**`（os.walk 全量 230176 条）。
    `hussite_rite` 等值是 `$hussite$` 引用，须二次解析。
  - faith→religion 归属：`CK3/common/religion/faith_types/00_faith_types.txt` 的
    `faith_details = { religion = xxx }`，**块级解析，勿行内正则**。
  - **★ `our_faith_provinces`/`our_faith_rites` 是 faith 级，多行重复、不可跨行求和**
    （tolotang 20 行每行都是 263）。列名带 `faith_` 就是防这个坑。
  - 统计：已映射 195 / 保留 pagan 98；CK3 faith 62 种（有省份 52 种）；
    match 分布 set 162 / pagan 98 / name 11 / key-suffix 11 / key 11。

### 1.3 落盘机制与坑
- **三表必须同步**：`_build_faith_map.py` CURATED / `eu5_ck3_faith_map.csv` / `_apply_*_faith.py` REL_RULE。加 CSV 不等于省会变——「某地还是 pagan 而 CSV 有映射」先 grep 落盘脚本 REL_RULE。
- `_apply_asian_faith_geo.py` 是伯爵领粒度，东南亚大面积空转；CSV 有映射而省份 0 实例先怀疑粒度，改 location 粒度（`_apply_asia_folk_faith.py`）。
- 省只写 `faith` 无 `rite =` 行时按 faith 的 `main_rite` 回落显示；「莫名是 X 礼」先查有没有 rite 行。
- 伊斯兰礼四段式：`_eu5_schools.py`→`_apply_rites.py`→`_apply_christian_rites.py`→`_apply_islamic_geo_spread.py`；任何一段不得改 faith。落点优先级：县级 sharia_law>religious_school → 手动覆盖（按省）→ 逐省 BFS（只认同父信仰源）。`_ck3_province_adjacency.json` 无海路，孤岛只能 REGION_OVERRIDES 显式落。
- 增量改判用 `ALLOW_OLD`/`ALLOW_OLD_BY_REL` 放行旧值，不放宽全局。
- 印度教分化 `_apply_hindu_faith_cu.py`：**必须整县染色**（按 `_cu_vs_ours.csv` 的 our_county 聚合多数 cu_rite 铺到全县），逐男爵领只有 72 省能定、整县 495 省。结果会被后续全量重建冲掉需重跑。现状 vaishnava 815 / shaiva 279 / shakta 55 / smartism 18。
- 反复踩的坑：**按县判定、按省落地**。已知 5 例：戈尔甘、库法、西沃里尼亚、吉赞/希尔达、多贝亚/锡达莫。
- **★ 保存点/还原**：`gen_debug/_religion_checkpoint.py`（`save/list/restore latest [--apply] [--faith-only]`，format 2 含 faith+rite，四种损坏测过 md5 一致）。`_snap_faith.py` 已删除（块首正则匹配不到 CRLF，restore 恒 0）。
- **★ 写盘必须保 CRLF**：按字节读写（rb→decode→split(sep)→join→(BOM+text).encode()），不要 `data.replace(b"\n", b"\r\n")`。

### 1.4 国家宗教 vs 教法学派
- 国家宗教看 `EU5/in_game/setup/countries/*.txt` 的 `religion_definition`；`religious_school`（`main_menu/setup/start/10_countries.txt`）只是教法学派。
- 判学派属哪个宗教必须看 `common/religious_schools/*.txt` 的 `enabled_for_country`。`safavid_school` 是苏菲教团学派（sunni/shia 都允许），只有 KKL（哈勒哈里，sunni）和 ABL（萨法维本体，shia）挂它，**不是异常**。
- 什叶国家 22 个：zaidi 7 / ismaili 6 / jafari 3 / safavid 1 / imamiya 1 / alevism 1 / **maliki 2（BKZ 库西雅、SKN 萨瓦金）**——这俩什叶国家却挂逊尼马立克学派，库西雅 7 省 rite 被「埃及什叶→ismaili」兜走，**待用户定**。两家的 7 个角色已按用户指示改 sunni+maliki（`_set_bkz_skn_maliki.py`）。
- MEC 麦加 `zaidi_school` 是对的（谢里夫家族本就信宰德派），**不是 bug**。
- 跨宗教执政全库 201 人（2.6%），`gen_debug/_cross_religion_rulers.csv`。
- 国家宗教看 religion_definition，不是 religious_school；BKZ/SKN 的 religion_definition=shia，不是跨宗教执政。

### 1.5 EU5 逐 location 数据源（只读）
- `location_templates.txt`：20918 个 location 带 `religion=`；`06_pops.txt`：真实人口可混宗教；`common/languages/*.txt`：**有的语言没有 family 行**（侗语 `kam_language` 无 family，故侗语不算 tai 语系；壮侗语系 EU5 只有 tai/zhuang 两门）。
- 宗教兜底链：pops 人口多数 → location 自己的 religion 标注 → 同省其它 location 多数。不要拿 CK3 county/barony 结构反推 location 属性。

## 二、CK3 数据结构约定
- 术语红线：CK3 说**伯爵领/男爵领**，EU5 说**省份/地点**。
- **CK3 只读伯爵领首府男爵领（块内第一个 b_）的 religion/culture**；改显示必须动首府。
- `DEFAULT_MAX_TRADITIONS = 5`；`roman` 有定义无人物；`romani` 无定义。
- 新文化抢显示名时原版文化必须改名（pommeranian→卡舒比、prussian→古普鲁士）。
- dynasty=宗族、house=支系；指支系必须 `dynasty_house =`。COA 按 key 自动匹配，`common/coat_of_arms/coat_of_arms/` 里 `house_xxx = <目标>` 即挂纹章；与原版同名则 vanilla COA 自动生效，不要写覆盖、不能自引用。
- 统计文化引用必须用 `re.finditer(r'(?<![a-z_])culture\s*=\s*(\w+)', line)`（文化常写在日期块里）。`novgorodian`/`ruthenian`/`belarusian`/`red_ruthenian` 无 culture 定义，无效 key。
- 角色块解析先按大括号深度切顶层块再找 religion+culture（逐行扫只识别 190/4361）。

## 三、文化分类工具链（顺序不能错）
`_classify_cultures.py` → `_annotate_zh_in_classification.py --apply` → `_culture_classification_report.py`。跳过中间步中文三列会被冲掉。
CK3 原版 22 个「0 省份文化」不能当落点：gothic ancient_egyptian hebrew hunnic trojan macedonian carthaginian ilmenian severian volhynian frankish suebi ashkenazi sephardi kochinim bavlim roman langobard serer tujia kazak old_saxon。

## 四、CU 对照表（用户说「按 csv 分」指这个）
- `gen_debug/_cu_vs_ours.csv`：2858 行 = 2858 个 EU5 province；`barony` 列是省首府 location 名；`cu_rite` 列是 CU 给整省的信仰，覆盖 2448 EU5 province = 13186 CK3 省份。
- **口径：先把 cu_rite 挂到整个 EU5 province，再按 location 数取主体**。拿 barony 名直接匹配只命中首府一格（苏拉威西第一版这么错的）。

## 五、生成器纪律
- 分组映射 = religion→faith，一个宗教只归一个组按多数；不许分组表出现两行。
- 用户手改文件绝不覆盖；写前比对内容，无变化不动 mtime，有变化才备份。
- 生成物按 key 排序、带 BOM；脚本默认 dry run，`--apply` 才落盘。
- **★ 非必要不全量重建**（补丁层会被冲掉）；外科手术式只改目标行。**避免无谓干跑和验证仪式**，跑完直接交付。
- **★ 诊断类任务默认只读**，报告结论+改法，等用户说「改」才动手。
- 改 CSV 保留行尾 `\r`，重建后核对 `CRLF == LF`。
- **★ 被否/被取代的错误文件当场删**（脚本、plan/中间 CSV、口径做错的分析脚本），删前 grep 无引用。正确脚本不删。
- **新建文件先查路径是否被占用**（zz_ 前缀不是无人区）。
- EU5 人名/复合名必须先查 EU5 自带角色名表 `main_menu/localization/<lang>/character_names*_l_<lang>.yml`，不手工音译；以 EU5 译名为准。
- 游戏安装目录只读，产物一律放工作区。

## 六、EU5 角色名本地化
每个 name 部分是独立 key，合成名按 EU5 部分拼接（中文无分隔符、英文空格）；EU5 怪译以 EU5 为准（tekuder=贴古迭儿、john=约翰）。脚本 `gen_debug/fix_compound_names.py` + `verify_compound_names.py`。

## 七、Git
- master=发布分支（不含 EU5 纹章，全在 eu5-coa 分支），远程 github.com/hathaway682/EU5_1337_to_ck3；用户用 GitHub Desktop 提交，**push 前必 fetch**。
- **禁止 git worktree**；跨分支带改动用 plumbing（GIT_INDEX_FILE→read-tree→update-index→write-tree→commit-tree→update-ref）零检出。
- staging 前先 `git status` 核对归属，只能逐个 add 明确文件。sandbox 连不上 GitHub 就如实报告，不重试轰炸。

## 八、存档：已完成分期，勿重做
168 支系→42 宗族（`zz_eu5_merged_houses.txt`）；`dynn_Anjou`=安茹（金雀花）用 `anjou_jerusalem`、`dynn_Robertine`=罗贝尔用 `robertian`、`dynn_Angevin` 是坑（无 dynasty/house 引用）；154 个复合君主名 11 语言重译；宗族层对齐原版完成（`gen_debug/dynasty_alignment_plan.md`）。
- 宗教匹配收尾（用户确认成功）；4361 个原始宗教人物改写 religion；比达教 47 省+22 人；印度教整县染色重跑；BKZ/SKN 7 角色改 maliki。
- **待用户定的遗留**：① BKZ/SKN 库西雅 7 省 rite；② 10990 个角色 religion=pagan 但文化主体是基督教/伊斯兰/佛教（00:56 提出）；③ 244 个印度教省所在县 CU 记耆那教（宗教层级差异，不属 faith 范畴）。

## 九、伯爵领首府规则（BaronyOrder rank_state，2026-10-22 改）
- 生成器 `Global_modern_map/eu5_export/_capital_correct.py`（`--barony-order`：id 默认 / rank_pop / rank_state）。**CK3 只读伯爵领块内第一个男爵领当首府**，faith/culture/holding/县易主全跟随它。
- rank_state：definitions 首府的领主是 minor power（全地在一省 + rank≤county + 非瑞士联邦含 ZUR）而县里有大势力时移首府；过半守卫→附庸守卫→**名称命中（`name_match_pick`，大势力的 location 本地化名与县名相同/部分相同，不看人口，单字符不算）**→seated（大势力首都本县）→占地最多者的最大镇。主教区/骑士团飞地单独一支。县名=首府镇名（`seat_names_county`，读 EU5 本地化，key 兜底）永不搬。
- **改规则后四步链路**：① `_capital_correct.py --barony-order rank_state`（重写 RANK_STATE.json+导出树）→ ② `_apply_rank_state_seats.py --old-picks <旧json>` 作用于每棵树（把不再 pick 的县还原 definitions 序）→ ③ `export_politics.py`（stamp 含 RANK_STATE.json，自动重建）→ ④ `_reassign_counties.py --mod <mod> --export .`（同步 history/titles/zz_eu5_titles.txt 持有者，先 dry-run）。
- 注意：`history/characters/zz_eu5_titles.txt` 是 10-18 陈旧副本，管线不维护；导出树 LF 无 BOM，mod 树 BOM+CRLF（`_apply_rank_state_seats.py` 保encoding）。
