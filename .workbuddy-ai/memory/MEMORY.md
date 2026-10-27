# 项目长期记忆（EU5_Modern_Borders_noshape）

> 每日细节在 `.workbuddy-ai/memory/YYYY-MM-DD.md`；这里只放长期有效的口径、坑与纪律。

## 一、宗教 / faith / rite
- 地理树 `EU5/game/in_game/map_data/definitions.txt`（tab 缩进）**必须栈解析**：`next(x for x in reversed(stack) if x.endswith(("_region","_area","_province")))`；只认行内列表只能解析到 17032/27418。易错：andaman→north_sumatra_area、sumatran_islands→south_sumatra_area、苏拉威西=celebes_area、米佐丘陵在 bengal_region 下叫 hill_area。
- faith 映射 `Global_modern_map/eu5_export/eu5_ck3_faith_map_zh.csv`；**三表必须同步**：`_build_faith_map.py` CURATED / CSV / `_apply_*_faith.py` REL_RULE——加 CSV 不等于省会变。已映射 195 / 保留 pagan 98。CK3 `satsana_phi`=守护灵教（EU5 同名宗教叫丕教）；「门顿教」是 religion 名（mundhum_religion）。
- 落盘坑：省只写 faith 无 rite= 时按 main_rite 回落；印度教分化必须**整县染色**（`_apply_hindu_faith_branch.py`，CU 分法已删）；**按县判定、按省落地**是反复踩的坑；写盘**保 CRLF**（rb→decode→split→join→encode，勿 replace \n）。
- 东亚 rite（`_apply_sect_rite.py`）：**sect 身份 = laws 首个元素**（藏传 `laws = { sakya_policy mulasarvastivada_policy vajrayana_policy }` 首个才是宗派）。用户拍板 DAI/KOR→dhyana、SSG→sukhavati。vajrayana_faith 的 main_rite 已改 lamaism（faith_types 358 行），藏传五派+觉囊自动落不写行。根本说一切有部 10 成员 52 省写 vinaya。confucian_faith 无 main_rite，由 `history/faiths/00_eastern_misc.txt` 按日期定（1337=daoxue）；maitreya_faith 同理。
- 佛教传播（`_apply_buddhist_geo_spread.py`）：只有 mahayana 需要补（theravada/vajrayana 回落即对）。源=mahayana+已有具体宗派；待补=mahayana 无宗派+owner 非佛教国；owner 佛教国不动（保留主流兜底）。三层（用户拍板）：① 接壤 BFS；② 质心直线 ≤300 km 隔空、只做一步不递归；③ 阿吒力特批跨 faith 替换 mahayana（acharya 绑 vajrayana_faith，写时删 faith 行只留 rite，8 省须从 prov_rite 单独捞）。父信仰守卫：mahayana 系 7 rite 只写 mahayana_faith，vajrayana 系 5 个只写 vajrayana_faith。
- 质心缓存 `_ck3_province_centroid.json`（provinces.png 16384×8192，28569 省；**int 键读回来必须 `{int(k): v}`**）。
- `history/provinces/00_generated_provinces.txt` 纯 CRLF：行级正则 `^(\d+) = \{\r?$`，插入的新行自带 `\r`。
- EU5 `religion_definition = mahayana #Azhaliism` 的 `#Azhaliism` 是注释，宗教值仍 mahayana。国家宗教看 `setup/countries/*.txt`；什叶 22 国（BKZ/SKN 已改 sunni+maliki）。宗教兜底链：pops 多数→location 标注→同省其它 location 多数。

## 二、CK3 数据结构约定
- **本地化永远比 key 权威**（实例 `acharya`=阿吒力教）；判断先 `grep -rn "<key>" localization/simp_chinese/`，没有问用户，不许编。
- CK3 说伯爵领/男爵领，EU5 说省份/地点；**CK3 只读伯爵领块内第一个 b_ 当首府**，faith/culture/holding/易主全跟随它。
- dynasty=宗族、house=支系；统计文化引用必须 `re.finditer(r'(?<![a-z_])culture\s*=\s*(\w+)', line)`；角色块按大括号深度切顶层块。

## 三、文化
- 工具链顺序不能错：`_classify_cultures.py` → `_annotate_zh_in_classification.py --apply` → `_culture_classification_report.py`。CK3 原版 22 个「0 省份文化」不能当落点。
- 定稿：图内全部并入已有文化、不建新文化（cat1-cat9 共 649 条映射；cat10/cat11 target=`NEW:` 保持 EU5 key）。CK3 新版官方要加 norse_gael/arpitan，自建同名撞车 → 原 5 个新文化与 17 个 cat8 融合全部取消。
- 落点速查：anglo_irish→english、norse_gael→gaelic、walloon→french、gallo→breton、(western/eastern_)pomeranian→saxon、EU5 prussian(德意志)→saxon、kazani/mishar→bolghar、crimean/astrakhani/nogai→cuman、turkish_culture→turkmen、azeri→turkish、gyalrong→qiang、algerian/moroccan/tunisian→maghrebi、sudanese_arab→bedouin。
- **`prussian` 双义（省份层+人物层都要 skip）**：省份层 EU5 德意志普鲁士→saxon 已改完；现省里 30 个 prussian 是波罗的普鲁士人，**再跑会误改成萨克森**，脚本 `KEEP_IN_PROV`+`KEEP_IN_PEOPLE` 双重排除。
- 判文化名一律先查本地化：CK3 `turkish`=乌古斯、`kazak`=喀扎克、`kirghiz`=黠戛斯、`uriankhai`=兀良孩、`kimek`=基马克。
- 草原东西支：带 EU5 steppe_group→cuman（astrakhani/crimean/nogai）；不带→kipchak（uzbek/kumyk/balkar/…）。能独立的保留：bashkir/bolghar/chuvash/uyghur/kirghiz/cuman。
- 亚洲按语族并入 37 个/306 省全落地：uriankhai→收 6 个南西伯利亚突厥（CK3 注释点名 Khakas/Tuvans）；lhomon→meitei 6 个（注释点名 Monpa/Lhoba/Kho-Bwa/Mishmi）；通古斯拆两支——鄂温克+鄂伦春→jurchen，其余 11 个西西伯利亚小族→mohe；高加索 circassian/abkhazian/abazin+lezgin/nakh/avar/dargin/lak→alan，laz/svan/mingrelian→georgian；`avar_culture` 是高加索阿瓦尔、与 CK3 `avar` 同名异族，落 alan；tai_long→tai。
- 已知历史遗留（未动）：`00_bookmarks.txt` 引 languedocien、`00_generated_challenge.txt` 引 highland（两 key 无定义）。
- 落地脚本 `gen_debug/_apply_eu_culture_v2.py`（默认 dry run，读 CSV cat1-cat9）。

## 四、CU 对照表（「按 csv 分」指这个）
`gen_debug/_cu_vs_ours.csv`（2858 行=2858 个 EU5 province）：先把 cu_rite 挂到整个 province，再按 location 数取主体；拿 barony 名直接匹配只命中首府一格。

## 五、生成器纪律
用户手改文件绝不覆盖；写前比对内容，无变化不动 mtime，有变化才备份；生成物按 key 排序、带 BOM；脚本默认 dry run。**非必要不全量重建**（补丁层会被冲掉），外科手术式只改目标行；避免无谓干跑和验证仪式。**诊断类任务默认只读**，报告结论+改法，等用户说「改」才动手；行号一律【文件绝对行号】。被否/被取代的错误文件当场删；新建文件先查路径占用。EU5 人名先查 EU5 自带角色名表；游戏安装目录只读，产物一律放工作区。

## 六、其它约定
- EU5 复合名：每个 name 部分是独立 key，按 EU5 部分拼接（中文无分隔符、英文空格）；脚本 `gen_debug/fix_compound_names.py` + `verify_compound_names.py`。
- Git：master=发布分支（EU5 纹章在 eu5-coa 分支），远程 github.com/hathaway682/EU5_1337_to_ck3；GitHub Desktop 提交，push 前必 fetch；**禁止 git worktree**；staging 前先 `git status` 核对，只能逐个 add。
- 地图可视化一律先用 skill `ck3-mapviz`（render 约 20s），**严禁自己算投影/质心打点**。

## 七、伯爵领首府（BaronyOrder rank_state）
- 生成器 `Global_modern_map/eu5_export/_capital_correct.py --barony-order rank_state`；CK3 只读伯爵领块内第一个男爵领当首府。
- rank_state 判定链：definitions 首府领主是 minor 而县里有大势力时移首府；过半守卫→附庸守卫（只查直属封君）→名称命中→seated→占地最多者的最大镇；主教区/骑士团飞地单独一支；`seat_names_county`（县名=首府镇名，读 EU5 本地化）永不搬。
- **链路六步**：① `_capital_correct.py --barony-order rank_state` → ② `_apply_rank_state_seats.py --old-picks <旧json>`（只动 old∪new picks 的县，**其余县原样不动**）→ ③ `export_politics.py` → ④ `_reassign_counties.py --mod <mod> --export .`（先 dry-run）→ ⑤ `_apply_tusi_governments.py --apply` → ⑥ `fix_holstein_denmark.py`。
- **★ fallback 真多数规则（用户拍板）**：major 要从 minor 处拿走伯爵领，地数须**严格大于县内任何其他单个持有者**（含在座 minor，不要求过半）。fallback pick 67→36；回归探针 `_probe_majority.py`（只读）。
- `_reassign_counties.py` 排除名单 `<mod>/gen_debug/eu5_reassign_keep.json`（BOM+CRLF）12 项。
- **★★ 土司首府两条规则 2026-10-22 已全回滚，作废勿再实施**（"土司相关全回滚，你的改动很失败"）；嘉绒问题回到起点（c_gyelrong 首府=打箭炉/明正 CKL）。
- **HRE 同名首府**（`fix_holstein_denmark.py` 第 3 节）：HRE 境内首府强制划给同名男爵领（EU5 中文本地化镇名=县名或县名一片，单字不算）。5 县：c_chrudimsko、c_hanover（HDH→BRU）、c_lippe（KOL→PDB）、c_luneburger_heide、c_neuchatel→basel。**跑 rank_state 会重算冲掉这 5 县，跑完链路必须重跑本脚本**。
- 丹麦摄政在 `zz_eu5_diarchy_regencies.txt`，`fix_holstein_denmark.py` 不碰摄政；export_politics「仍有县者不降男爵领」是既定约定，勿当 bug。

## 八、开局日期 = 1337.4.1（2026-10-23 定稿）
- 三处必须同步：`common/bookmarks/bookmarks/00_bookmarks.txt:8`、`challenge_characters/00_generated_challenge.txt:8`、`groups/00_bookmark_groups.txt:8` 的 `default_start_date`。
- **EU5 原始记录字面是 1337.1.1 的保留**（"只知年份取年初"占位）；**我们钉的「开局触发」基线写 1337.4.1**。EU5 setup 里 `1337.4.1` 一次不出现（引擎起点常量），setup 语义=4.1 快照。已拆分：改 4.1 共 12430、保留 112（脚本 `gen_debug/_split_start_date_1337.py`）。
- **查日本头衔必须 grep 三个 z 的 `history/titles/zzz_eu5_japan_noble_families.txt`**（145 个 `c_nf_*`），只 grep `zz_eu5_titles.txt` 会漏、进而误判"某国无头衔"。
- **重跑风险**：15 个脚本的日期字面量已统一为 4.1，它们按 4.1 找开局块会跳过保留的 112 条 1.1；`_fix_politics_output.py` 重跑会重写 regents/bookmark 并丢毛利来源标记；`_export_title_map.py` 会把 58 个头衔记为开局无人持有。
- **拆分脚本的粒度坑（2026-10-27 已修）**：`_split_start_date_1337.py` 的 `process_titles` 只改日期行文本，块内其余行（尤其 `liege`）跟着 holder 的 EU5 `ruler_term start_date` 整块走。6 个头衔因此把 liege 留在 1.1，而 liege 指向的头衔 holder 钉在 4.1 → CK3 建封臣关系时领主头衔无人持有，开局无上级领主（格拉摩根、热那亚）。已用 `gen_debug/_fix_liege_date.py`（幂等）把 liege 摘到独立 4.1 块。
- **CK3 liege 的来源**：① `EU5/main_menu/setup/start/12_diplomacy.txt` 的 `dependency`（652 条，仅 28 条带 start_date）；② HRE 成员身份（`export_politics.py` 1018–1024，`_org["type"]=="hre"` 的 members 即使无 dependency 也算皇帝臣属）。**关系本身没有日期**，写进哪个日期块只由生成器/拆分脚本决定。热那亚挂 `e_hre` 是 HRE 成员，不是 vassal dependency。

## 九、摄政周期（2026-10-23 修）
- **CK3 的 regency diarchy 不会自动结束**（`CK3/game/common/diarchies/diarchy_types/00_regencies.txt`：`start = { always = yes }` / `end = { always = no }`），只写 `try_start_diarchy` 会挂到游戏结束，必须显式 `end_diarchy`。
- `zz_eu5_diarchy_regencies.txt` 21 块已按 EU5 start/end_regency_date 对齐（CHZ 1336.1.1、MGM 1329.1.1、OKI 1327.1.1 等），全部补结束块；DAN end=1400.1.1 等于永不结束。
- MAC/PMB/CET/ULS/PLK 无块是文件头写明的有意排除（摄政是有地统治者）；1280 个 `eu5_regent_*` 是占位 holder 不是摄政。

## 十、主头衔（2026-10-23 修）
- 主头衔不在 title history，是 `_fix_politics_output.py` 生成 `common/on_action/zz_eu5_primary_titles.txt`（`on_game_start` → `set_primary_title_to`）。伯国层：持 ≥2 伯国且不持 d/k/e 的 ruler，按 own tag 优先取 capital 所在县，仅当在持有集才写；capital 在别人县的不猜。
- **守护大名例外**（`for...else`，用户批准）：他们的县 owner 全是 JAP，循环永远找不到 seat；own tag ∈ `shugo_daimyo` 时先试国府县 `shugo_daimyo[tag]`，不在持有集再试本国 capital 县。**else 分支精确只增 13 个守护大名**（old 197→new 210），零副作用。HSK 的国府县 c_settsu 被 AKM 占有，按 capital awa→c_awa。
- **文件已与生成器逐条一致（2026-10-23 两轮外科手术补丁）**：`gen_debug/_patch_primary_titles_file.py`（可重复跑，同值条目自动跳过）。216 条 = 210 县级 + 6 个 d/k/e 层级；含 13 个守护大名 + 3 个漏写（bru_otto→c_brunswick、hhb_rudolf_iii→c_swabian_alb、uls_elizabeth→c_antrim）；已删 2 条过期（eu5_regent_mci→c_yazhou、hhb_margaretha→c_swabian_alb）与 12 条单县冗余。审计探针 `gen_debug/_audit_primary_titles.py`（只读）。
- **四个「EU5 capital 在他人县」的人 = 用户手工指定（2026-10-23，通用处理不抢地，title history 未动）**：bds_jalal_al_dawla_iskandar→c_qazvin（capital kojur 在 mzn_hasan 的 c_rustamdar，加兹温属 BDS own_control_integrated）、gel_reinoud_ii_van_gelre→c_gelderland（capital geldern 在 BRG 的 c_niederrhein）、rig_friedrich_von_pernstein→c_inner_livonia（capital limbazi 在 c_south_livonia，里加市维持自治）、utr_jan_van_diest→c_overijssel（capital verden 在 LUN 的 c_aller）。共 220 条。**这 4 条生成器推不出来，只在补丁脚本里，重跑生成器会丢、需重跑脚本补回**。
- 设计上不猜的剩余缺口：121 个 `eu5_regent_*` 占位 holder。

## 十一、已完成分期，勿重做
168 支系→42 宗族（`zz_eu5_merged_houses.txt`）；`dynn_Anjou`=安茹用 `anjou_jerusalem`、`dynn_Robertine`=罗贝尔用 `robertian`、`dynn_Angevin` 是坑；154 个复合君主名 11 语言重译；宗教匹配收尾（用户确认成功）；4361 个原始宗教人物改写 religion；印度教整县染色；BKZ/SKN 7 角色改 maliki。
**待用户定的遗留**：① BKZ/SKN 库西雅 7 省 rite；② 10990 个角色 religion=pagan 但文化主体是基督教/伊斯兰/佛教；③ 244 个印度教省所在县 CU 记耆那教。

## 十二、eu5_ck3_title_map.csv（2026-10-23 重订口径）
- 生成器 `Global_modern_map/eu5_export/_export_title_map.py --mod <mod> --export <export>`，产物 `<mod>/gen_debug/eu5_ck3_title_map.csv`（BOM+CRLF）。**用户拍板的记录口径**：
  - **帝国/王国/公国** → 生成头衔 `X_eu5_TAG`（联统 junior 的公国及以上也记，有生成头衔）；rank 被 drop 的走原 seat/barony fallback。
  - **日本** → 一律记统治者所在氏族的 `c_nf_*` 世族头衔（**守护大名也不记伯爵领**）；例外三个：JAP→e_eu5_jap（幕府）、NTC→e_eu5_ntc、STC→e_eu5_stc（两朝廷，用户拍板）。取法：ruler 直接持该 c_nf_*，否则按 dynasty 唯一反查。**注意 dynasty 反查有假阳性**（`c_nf_yamato`/STC、`c_nf_hei`/BQA 是多国共用 dynasty family 的前缀相撞）；SUW 曾靠反查落 c_nf_suwa，2026-10-23 已把世族文件第 1384 行 holder 改成 jap_suwa_yoritsugu（摄政期头衔给 heir 的规则），现为直查匹配。
  - **联统 junior 的伯国及以下** → **留空不记**（note `union-junior: seat not recorded yet`，共 41 个：20 rank c + 21 rank None），等联统专题再处理。senior 判定：`unions` 列表里排除 senior 自己的 tag（nav_philip_iii_evreux 的 NAV 不在自己列表里，ANG/EVR 都算 junior）。
  - **其它伯国** → 主头衔文件 `zz_eu5_primary_titles.txt` 里 ruler 的县级主头衔（生成的或手工指定的），**仅当该县 owner==本国 tag**（否则会记成联统 senior 的县）；没有则走 seat 扫描（capital 匹配县 → 字典序首个自有县 → 男爵领）。
- **PAP 特例**：记 `k_papal_state`（原版头衔），不是 `k_eu5_pap`（幽灵，无 landed_titles 声明/无持有人/无中文名）。与 `_fix_politics_output.py` 的 `tk` 规则一致。
- **导出数据比旧 CSV 新**（json 10-22 22:24 > CSV 10-22 22:11）：57 个县 owner 变（c_julich AAC→JUL 等）、QCH rank d→k、16 个县和 153 个男爵领消失——**消失的是现代边界 mod 数据里的幽灵行，原版/EU5 数据没有，属正确消失**（用户确认）。旧 CSV 备份 `.bak_titlemap_20261023`。
- 重跑即刷新；CSV 被编辑器占用时会 PermissionError，写临时路径验证后再落盘。

# 项目长期记忆（EU5_Modern_Borders_noshape）

## CK3 数据结构约定（从踩坑中确认）

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
