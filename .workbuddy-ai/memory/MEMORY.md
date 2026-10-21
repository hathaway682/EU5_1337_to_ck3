# 项目长期记忆（EU5_Modern_Borders_noshape）

## 一、宗教 / 礼（rite）

### 1.1 地理层级
- **`in_game/map_data/definitions.txt` 是完整地理树**：`subcontinent={region={area={province={loc...}}}}`，tab 缩进，1=region、2=area、3=`*_province`。**必须栈解析**（province 的 loc 列表常跨多行，如 `biak_province`）：压栈后 `next(x for x in reversed(stack) if x.endswith(("_region","_area","_province")))` 推层级，栈顶 `*_province` 时登记该行 token。只认行内列表只能解析到 17032/27418。
- 易错归属：`andaman_province` 挂 **north_sumatra_area**；`sumatran_islands_province` 挂 **south_sumatra_area**；苏拉威西 area 名 **`celebes_area`**。
- `indochina_region`：613 loc / 104 prov，13 area（去 `malay_peninsula` 48 loc = 565 loc / 95 prov）。
- **`bengal_region`**：**米佐丘陵 = `hill_area`**（通用键名，按 mizo_* 猜不到）；阿萨姆 `assam_area`；门隅 `monyul_area`。

### 1.2 已定的 faith 映射
- **东北印度**：米佐丘陵主体 → `sedism`；阿萨姆+门隅主体（含各半的 `chutia_religion`）→ `donyipoloism`。
- **★ 萨尔语群不可整族归并**：`sal_language_family` 下 15 个原始宗教早拆成三拨（`mizo`/`sanamahism`→`sedism`；`koch`/`naga`/`jingpo`+阿萨姆那批→`donyipoloism`）。**凡「某语系整族归一个 faith」，先查该语系里是否早混着多个 faith。**
- **「门顿教」是 religion 名**（`mundhum_religion`），其下 faith：`kiratism` 罽罗多派 / `kiratism_old` / `yumaism` 玉玛派 / `yumaism_old`。省份只能写 `faith`，「归门顿教」一律落 `kiratism`。
- **欧洲 / 彼尔姆组**：高加索 4 个（`khabzeism`/`karachay_balkar_paganism`/`vainakh_paganism`/`lezgin_paganism`）→ `tengri_pagan`，**覆盖 CU**；`erzya_religion`/`moksha_religion` → `finnish_pagan`；`samoyedic_paganism` → `siberian_pagan`；其余按 CU（唯一改动 `mari_paganism` siberian→finnish）。脚本 `_apply_euro_perm_faith.py`。
- **`_apply_faith_map.py` 不能做增量改判**（它假设省份是 EU5 宗教 key）。增量改判用 `_apply_*_faith.py`（按 religion 判定 + ALLOW_OLD）。
- **EU5 本地化行尾常带 `#` 注释**，正则须 `"\s*(?:#.*)?$`。
- **★ 宗教匹配终态（用户确认成功）**：全库 6038 个 pagan 省，CU 覆盖区内只剩 **17 个**，全是 `bantu_religion`。用户明确满意——班图横跨南部非洲、无单一 CK3 faith 可对应，**保持 `pagan` 是有意终态，`_apply_africa_fam_faith.py:61` 不列 bantu 是正确设计，不要再提议拆它。**
- **比达教**：`nyama_religion` → `west_african_bidu_pagan`，**宗教级一对一，不做 culture 细分**（第一版按索宁克人 >50% 筛被否）。脚本 `_apply_soninke_bidu.py`，47 省 + 22 人。
- **梅山教 = `dab_qhuas`（章夸教），不是正一派**：`yao_religion` 27 省落 `dab_qhuas`。
- **中南半岛口径只针对原始宗教**（用户「我只说原始宗教」）：`theravada_faith` 257 省**不动**。印度支那 region（不含马来半岛）11 个原始宗教→`satsana_phi`；缅彝语群+土家语→`bimoism`；泰语→守护灵教；壮语/侗语→麽教。**中文名别混**：CK3 `satsana_phi`=守护灵教，EU5 同名宗教叫丕教。
- **CK3 原版能给东南亚/南岛用的 faith 只有 8 个**：`dayawism`/`kaharingan`/`tolotang`/`aluk`/`bilikuism`/`pulugaism`/`satsana_phi`/`hantuism`。苏门答腊/小巽他/摩鹿加/马来半岛原版无对应，只能 `pagan` 或另建。
- 上述 faith（含 tengri/finnish/siberian/west_african_bidu_pagan）均自带 `main_rite = 同名`，只写 `faith =` 即可。

### 1.3 落盘机制与坑
- **★ 三表必须同步**：`_build_faith_map.py` 的 CURATED（生成器）、`eu5_ck3_faith_map.csv`（审计表）、`_apply_*_faith.py` 的 `REL_RULE`（执行表）。往 CSV / CURATED 加映射**不代表省份会变**。已两次复现（安达曼/尼科巴 4 男爵领；`karen`/`jingpo`/`kirat_mundhum` 23 省）。→ **凡「某地还是 pagan」而 CSV 明明有映射，第一件事 grep 落盘脚本的 REL_RULE。**
- **`_apply_asian_faith_geo.py` 是伯爵领粒度（county_religion），对东南亚大面积空转**。**凡 CSV 有映射而省份 0 实例，先怀疑粒度**，改用 location 粒度（`_apply_asia_folk_faith.py`）。
- **省份只写 `faith = X` 无 `rite =` 行时按该 faith 的 `main_rite` 显示**（sunni→hanafi、shia→imami、orthodox→byzantine_rite、miaphysitism→armenian_rite、coptic→coptic_rite）。**凡「莫名是 X 礼」，先查有没有 `rite =` 行；没有就是回落。**
- 伊斯兰礼生成**四段式**：`_eu5_schools.py` → `_apply_rites.py` → `_apply_christian_rites.py` → `_apply_islamic_geo_spread.py`。只有后两个碰 `rite` 行，**任何一段不得改 `faith`**。
- **反复踩的坑：按「县」判定，按「省」落地。** 已知 5 例：戈尔甘、库法、西沃里尼亚、吉赞/希尔达、多贝亚/锡达莫。加地区规则先问：按县还是按省？
- 伊斯兰层落点优先级：县级确定性（owner 的 `sharia_law` > `religious_school`）→ 手动覆盖（imami/也门/`REGION_OVERRIDES`，**按省**）→ 逐省 BFS 补漏（只认同父信仰源）。
- **孤岛传不动**：`_ck3_province_adjacency.json` 只有陆路无海路。`adj=[]` 的省（拉克沙、马斯克林、nosy_be）BFS 走不了，只能 `REGION_OVERRIDES` 显式落。
- **改判要放行旧值**：`ALLOW_OLD` 全局白名单（`{"pagan"}`）；改判用 `ALLOW_OLD_BY_REL` **按宗教放行**（`yao_religion:{zhengyi}`、`pelebegu_religion:{hantuism}`、`naga_religion`/`jingpo_religion:{satsana_phi}`、`mari_paganism:{siberian_pagan}`），不许放宽全局。
- **印度教分化**：`_apply_hindu_faith_cu.py`（人物侧另一条线 `_apply_hindu_faith_chars.py`）。**分化结果会被后续全量重建冲掉，需要重跑。**
  **★ 必须「整县染色」，不能逐男爵领查 CU**：CU 只给伯爵领首府男爵领写 rite，默认用首府上色**整个伯爵领**。做法 = 按 `_cu_vs_ours.csv` 的 `our_county` 聚合「县 → 多数 cu_rite」再铺到全县。逐男爵领只有 **72 省**能定派，整县染色 **495 省**（差 7 倍）；同县多 rite 冲突 50 个取多数。
  现状：`vaishnava_faith` 815 / `shaiva_faith` 279 / `shakta_faith` 55 / `smartism` 18（共 1167 印度教省），其余 672 省走地区兜底。
  **未处理**：244 个印度教省所在县 CU 记的是耆那教（digambara 135 + svetambara 82 + yapaniya 27），另 vajrayana 157 / mahayana 100 / theravada 70 / lamaism 21 记佛教——宗教层级差异，不属 faith 分化范畴。另 `smartism` 颜色 `{1.0 0.3 0.3}` 与 `shaiva_faith` `{0.9 0.2 0.3}` 几乎同色，视觉无法分辨。
- **★ 宗教地图保存点 / 一键还原**：`gen_debug/_religion_checkpoint.py`
  - `save [标签]` → `gen_debug/religion_checkpoints/faith_<时间戳>[_标签].json`；`list`；`restore latest`（干跑）/ `--apply` / `--faith-only`
  - **含 faith + rite 两样**（format 2：`{"format":2,"faith":{},"rite":{}}`）。用户明确要「包括 rite」。
  - 还原语义：`faith` 只改不一致的省；`rite` 快照有值就改（块里没有就紧跟 faith 行补一行），快照没有 rite 的省若多出 `rite =` 行就删掉。其它行一字节不动；无变化不写盘；写盘前备份。
  - **已用「faith 改值 + rite 改值 + rite 删行 + rite 凭空加行」四种损坏测过，还原后 md5 与原文件完全一致**。
  - 当前保存点：`faith_20261022_013157.json`（21046 省 / faith 55 种 / rite 3808 行 24 种）。
- **老快照 format 1（扁平 `{ID: faith}`）只还原 faith，不碰 rite**（「老快照没有 rite 字段」≠「当时没有 rite 行」）。
- **`gen_debug/_snap_faith.py` 已删除**（用 `io.open(..., newline="")` + 块首正则 `^(\d+) = \{$`，`$` 匹配不到 `\r` 前末尾 → restore 恒为 0 改动）。**要校验/还原 faith+rite 一律用 `_religion_checkpoint.py`。**
- **★ 「读全文→逐行改→整体写回」的脚本，写盘必须保住 CRLF**：`io.open(...).read()` 的 universal newlines 已把 `\r\n` 归一成 `\n`，用默认或 `newline="\n"` 写回会把整个文件翻成裸 LF（`_apply_hindu_faith_cu.py` 踩过，翻掉 109066 个 CRLF）。最稳是**按字节读写**：`io.open(p,"rb").read()` → decode → `split(sep)` → `sep.join()` → `(BOM+text).encode()` 直接写 bytes。**不要用 `data.replace(b"\n", b"\r\n")` 补行尾**（会变 `\r\r\n`）。

### 1.4 国家宗教 vs 教法学派（★ 别搞混）
- **国家宗教看 `religion_definition`**（`EU5/in_game/setup/countries/*.txt`）。**`religious_school` 只是教法学派**（`main_menu/setup/start/10_countries.txt`）。两者可不一致，且不一致是 EU5 有意为之。
- 什叶国家共 **22 个**：zaidi 7、ismaili 6、jafari 3、safavid 1、imamiya 1、alevism 1、**maliki 2（BKZ、SKN）**——全库只有这两个「什叶国家挂逊尼马立克学派」（`maliki_school` 只在 `muslim.txt` 的 sunni 块里）。
- **★ `safavid_school` 不是什叶学派，是苏菲教团学派**（`common/religious_schools/sufi.txt:117`，`enabled_for_country` 同时允许 sunni 和 shia；`muslim.txt` 的 shia 块 84 行与 sunni 块 147 行都列了它）。全库只有 2 个国家挂它：**KKL 哈勒哈里**（sunni，伊朗西北）和 **ABL 阿尔达比勒＝萨法维教团本体**（shia，`persia.txt:437`，开局无地）。所以「逊尼国家挂萨法维学派」**不是异常**，别再当反向特例。
- **KKL = 哈勒哈里**（`crescent.txt:136`，`adhari_culture`，`sunni`；开局 4 地点 ardabil/hashatjin/khalkhal/nir，首都 khalkhal，君主 `ruler = random`）。在我们 mod 落成 `c_ardabil`（首府 b_ardabil=6513，faith sunni / rite hanafi）+ `c_miyaneh`，持有者生成摄政 `eu5_regent_kkl`。
- **BKZ / SKN 就是库西雅（`c_qusiyya`）/ 萨瓦金（`c_suakin`）两家**，`religion_definition = shia`。因既无 `sharia_law`、`religious_school` 又是逊尼 maliki（与 shia 父信仰不匹配被拒）→ 给不出什叶学派 → 库西雅 7 省被 `REGION_OVERRIDES` 的「埃及什叶 → ismaili」兜走。**这 7 省 rite 待用户定。**
- **★ 麦加（MEC）在 EU5 是 `zaidi_school` 宰德派，这是对的，不是数据错误**——麦加谢里夫家族（Qatadid）本身就信宰德派。**不要再把它当 bug 提。**
- 跨宗教执政（角色 religion ≠ tag 的 `religion_definition`）：全库 **201 人 / 7740（2.6%）**，明细 `gen_debug/_cross_religion_rulers.csv`，脚本 `_probe_cross_religion.py`。BYZ 48（hellenism 41 是罗马皇帝彩蛋）、CHG 20、MGE 17、CIL 10、OGE 9。

### 1.5 语系
- **语系中文名以 EU5 简中为准**：`atlantic_language_family`=**塞内语族**（不是「大西洋」）、`chadic`=乍得语族、`cushitic`=库希特语族、`bantu`=班图语支。
- **按语系整族归 faith**：语系 = 该 religion 信徒人口最多的语系（`06_pops.txt`→culture→`language`→`family`，dialect 继承父语言）；只处理 `folk_*`；脚本 `_apply_africa_fam_faith.py`。

## 二、CK3 数据结构约定
- **术语红线**：CK3 侧说**伯爵领（county）/男爵领（barony）**；EU5 侧说**省份（province）/地点（location）**。禁止把 CK3 county 叫"县"、province 叫"省"；CK3 的 history/provinces 条目就是男爵领，说"男爵领粒度"。
- **★ CK3 只读伯爵领首府男爵领的 religion/culture**（landed_titles 里该 county 下第一个 barony）。非首府男爵领写了不影响显示；要改"伯爵领显示什么教会"必须动首府那一条。
- **`DEFAULT_MAX_TRADITIONS = 5`**。
- **`roman` 有定义无人物**（0 角色 0 省份）；**`romani` 连定义都没有**（正则只误撞 `muroma`）。
- **新文化抢显示名时原版文化必须改名**：`pommeranian`（实为卡舒比人）→卡舒比；`prussian`→古普鲁士；新文化 `pomeranian`/`prussian_german` 取波美拉尼亚/普鲁士。
- **dynasty 是宗族，house 是支系**。指支系必须 `dynasty_house = house_xxx`；写 `dynasty = house_xxx` 会 fallback 到 `dynn_adam`。
- **COA 按 key 自动匹配**，无 `coat_of_arms_id` 字段。`common/coat_of_arms/coat_of_arms/` 里 `house_xxx = <目标>` 即挂纹章，别名可指向别的 COA key 或标题 key（`house_capet = k_france`）。我们的支系 key 若与 vanilla house 同名，vanilla COA **自动生效**，不要写覆盖，更不能 `house_x = house_x` 自引用。
- `zz_` 前缀保证在 `00_` 之后加载。`zz_eu5_merged_houses.txt` 里被归并成 house 的条目已注释掉，分析脚本读 culture 要从备份取。

## 三、文化分类工具链（三段式，顺序不能错）
- `gen_debug/_classify_cultures.py`（出 15 列）→ `_annotate_zh_in_classification.py --apply`（补 name_zh/target_zh/target_zh_src）→ `_culture_classification_report.py`（出 md）。**跳过中间那步，中文三列会被分类器整个冲掉。**
- **CK3 原版 22 个「0 省份文化」**（有定义但 0 引用，不能当落点）：gothic ancient_egyptian hebrew hunnic trojan macedonian carthaginian ilmenian severian volhynian frankish suebi ashkenazi sephardi kochinim bavlim roman langobard serer tujia kazak old_saxon。
  **★ 统计必须用 `re.finditer(r'(?<![a-z_])culture\s*=\s*(\w+)', line)`**，不能只匹配行首——大量文化写在日期块里（`960.1.1 = {	culture = norman }`），行首匹配会把 norman(7) andalusian(51) galician(10) asturleonese(10) aragonese(6) songhai(21) german(1) 误判成 0。
- **陷阱**：`novgorodian`/`ruthenian`/`belarusian`/`red_ruthenian` 只在 `creation_names/00_names.txt` 里，**无 culture 定义**，写进 province 是无效 key。原版东斯拉夫全用 `russian`。
- CK3 官方中文怪译：`kazakh_name = "乌兹别克"`（应作哈萨克），已在 annotate 的 ZH_OVERRIDE 覆盖。

## 四、生成器纪律
- **★ 「分组映射」= 宗教 → faith，不是按省份逐省判（骂过一次）。** 用户给地理分组口径，用来决定**每个宗教归哪个 faith**；落地时一个宗教整体一个 faith。判断标准：产物里还能不能反查出「religion → faith」这张表。
- **★ 分组必须收敛：一个宗教只归一个组，按多数。** 跨两地区时归省份最多的组，少数派只在备注记数量，**不许分组表出现两行**。
- 用户手改过的文件绝不覆盖；写前比对内容，无变化连 mtime 都不动，有变化才备份。
- 生成物按 key 排序、带 BOM；生成脚本默认 dry run，显式 `--apply` 才落盘。
- **改 CSV 保留行尾 `\r`**：`raw.split("\n")` 后每行末尾还挂 `\r`，`",".join([...])` 会吃掉它变裸 LF。重建后按原行是否以 `\r` 结尾补回，改完核对 `CRLF == LF`。
- **★ 被否决/被取代的错误文件当场删掉，不留后患**。三类：① 做法被否的脚本；② 它的 plan/中间 CSV；③ 口径做错、已被取代的分析脚本。删前 grep 确认无引用，删完同步改记忆。**正确的脚本/数据一律不删。** 实例：`_apply_se_asia_region_faith.py`、`_se_asia_region_faith_plan.csv`、`_analyze_cu_se_asia.py`。
- **★ 角色块解析必须先按大括号深度切顶层块**：`culture` 常写在 `religion` **之后**，逐行扫到 religion 时 culture 还没读到 → 只识别 190 人（正确 4361）。先切块，再整块找 religion + culture。
- **CK3 角色支持 `rite =` 字段**（`zz_eu5_characters.txt` 已有 `rite = hanafi` 等）。

## 五、EU5 逐 location 数据源
基址 `EU5 = D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game`（**只读**）。
- **`location_templates.txt`** — 每 location 一行，location 级属性权威标注。20918 个 location 带 `religion =`；走廊类（trail/river）常整行不带。
- **`definitions.txt`** — province→location，4149 province / 27418 location。
- **`06_pops.txt`**（`define_pop`）— 真实人口，可混宗教，适合取多数；存在 `anadyr_trail = { }` 空块。
- **`common/languages/*.txt`** — **有些语言没有 `family =` 行**，按语系聚合时算「未标注语系」，不是漏读。`kam_language`（侗语，`00_indochina.txt:153`）无 family，故侗语不在 `tai_language_family`；**壮侗语系按 EU5 只有 2 门：`tai_language`、`zhuang_language`**。`satsana_phi` 是混合桶：泰语 51.2%/黎语 22.7%/戈都语 12.4%/克木语 9.6%。脚本 `_analyze_tai_language_split.py`。
- **兜底链（宗教）**：① `06_pops.txt` 人口多数 → ② 该 location 自己的 `location_templates.txt` `religion` 标注 → ③ 同 EU5 province 内其它有标注 location 的多数。**不要拿 CK3 的 county/barony 结构反推 location 级属性**。

## 六、「按 CSV 分」= CU 对照表 `gen_debug/_cu_vs_ours.csv`
- 用户说「按 csv 分」指的**不是**自建 `eu5_ck3_faith_map.csv`，而是 **CU 对照表**。原话：「我说的当然是CU里的数据」。自建表里那些宗教常还是 `pagan`，查它等于查空气。
- **CU 表粒度**：2858 行 = 2858 个 EU5 province，一行一省；`barony` 列 = 该省**首府 location 名**（不是 CK3 的 barony）；`cu_rite` 列 = CU 给整省的信仰（0 行 pagan/空值），覆盖 2448 个 EU5 province = 13186 个 CK3 省份。
- **★ 口径**：**先把 `cu_rite` 挂到整个 EU5 province，再按 location 数（或省数）取该宗教主体**。直接拿 `barony` 名匹配只命中首府一格，会把整片区域误判「CU 无覆盖」（苏拉威西第一版这么错的）。
- 现成只读脚本：`Global_modern_map/eu5_export/_analyze_celebes_cu.py`。

## 七、EU5 角色名本地化
- **改/补 mod 人名（含复合君主名）必须先查 EU5 自带角色名表，不要手工音译**：`EU5/game/main_menu/localization/<lang>/` 的 `character_names_dynamic_l_<lang>.yml`（~50592 条 key，11 语言含简中）与 `character_names_l_<lang>.yml`。
- 每个 name 部分是独立 key（`name_togha: "脱花"`）；部分完整合成名也直接本地化（`name_ang.name_chey: "昂杰"`）。中文合成按 EU5 部分**无分隔符拼接**；英文按空格。
- EU5 偶有怪译（tekuder=贴古迭儿/EN=Togoldor、john=约翰/EN=Johan、henry=亨里克/EN=Henrik），但 mod 是 EU5 转 CK3，**以 EU5 为准**。脚本：`gen_debug/fix_compound_names.py` + `verify_compound_names.py`。

## 八、Git 与分支
- master = 发布分支，**不含任何 EU5 纹章素材**（全在 eu5-coa 分支）。远程 github.com/hathaway682/EU5_1337_to_ck3（公开库），分支 master / eu5-coa / pop。用户日常用 GitHub Desktop 提交推送，会和我的 git 操作并发——push 前必 fetch。
- **禁止 `git worktree`**：整库完整检出，仓库 1GB+，D 盘常期紧张。跨分支带改动的做法：`git show <branch>:<path>` dump 到 C 盘临时文件，改完用 plumbing 提交（`GIT_INDEX_FILE` → `read-tree` → `update-index --cacheinfo` → `write-tree` → `commit-tree` → `update-ref`），全程零检出。
- **staging 前先 `git status` 核对改动归属**：工作区常同时存在别的会话/用户本人的未提交改动。只能逐个 `git add <明确文件>`；整文件 add 前必须确认 diff 全是本次自己的。
- 生成器升级导致的重导产物（CSV 换 schema 的整表 churn）不属于单个修复提交，按「只补不改」只改目标行列。
- sandbox 代理可能连不上 GitHub（502），push 失败如实报告，不要反复重试轰炸。

## 九、已完成的分期工作（存档，勿重做）
168 支系→42 宗族（`zz_eu5_merged_houses.txt`）；修 house 首行 `l_english:/n` + 1781 处 `dynasty=`→`dynasty_house`；补 1382 个 `name_eu5_*` key；挂 vanilla COA（29 写入 + 6 自动生效）；154 个复合君主名 11 语言重译；**宗族层对齐原版（B 路）完成**（27 个可锚定宗族，清单 `gen_debug/dynasty_alignment_plan.md`，脚本 `gen_debug/align_dynasties.py`）。
- **"安茹"两把别名的陷阱**：`dynn_Anjou`(723)=安茹（金雀花/耶路撒冷王室）→ 用 `anjou_jerusalem`；`dynn_Robertine`(743)=罗贝尔 → 用 `robertian`。**`dynn_Angevin` 是坑**：中文也译安茹，但只在 `name_lists/00_frankish.txt` 出现，**无 dynasty/house 引用、无 COA**。
