# 项目长期记忆（EU5_Modern_Borders_noshape）

> 每日细节在 `.workbuddy-ai/memory/YYYY-MM-DD.md`；这里只放长期有效的口径、坑与纪律。

## 一、层级与数据源
- EU5：location（≈CK3 男爵领）→ province（≈CK3 伯爵领）→ area → region。
- `EU5/game/in_game/map_data/definitions.txt`（tab 缩进）**必须栈解析**：`next(x for x in reversed(stack) if x.endswith(("_region","_area","_province")))`；只认行内列表只能解析到 17032/27418。易错：andaman→north_sumatra_area、苏拉威西=celebes_area、米佐丘陵在 bengal_region 下叫 hill_area。
- province 声明一行式 `xxx_province = { loc1 loc2 ... }`，正则 `(?m)^\s*([a-z0-9_]+)_province\s*=\s*\{([^}]*)\}`，共 **4149 province / 27334 location**。
- `main_menu/setup/start/06_pops.txt`：`locname = { define_pop = { size = 18.9 culture = X religion = Y } }`，**50255 pop / 20794 location**，`size` 是浮点人口。
- CK3 `b_<name>` 的 `<name>` 就是 EU5 location 名；**3725/3819 county 严格对应单一 EU5 province，0 个跨省**，94 个查不到（岛屿/无主地/火星名）。
- **`eu5_county_peoples.csv` 是 location 个数多数，不是人口**；要人口必须自己读 `06_pops.txt`。
- 质心缓存 `_ck3_province_centroid.json`（provinces.png 16384×8192，28569 省；**int 键读回来必须 `{int(k): v}`**）。

## 二、CK3 数据结构约定
- **本地化永远比 key 权威**（实例 `acharya`=阿吒力教）；先 `grep -rn "<key>" localization/simp_chinese/`，没有就问用户，不许编。
- **EU5 语系定义**在 `in_game/common/languages/*.txt` 的 `family = xxx_language_family`，查语系一次 grep 即可，别翻目录。
- **CK3 只读伯爵领块内第一个 b_ 当首府**，faith/culture/holding/易主全跟随它。
- dynasty=宗族、house=支系；统计文化引用必须 `re.finditer(r'(?<![a-z_])culture\s*=\s*(\w+)', line)`；角色块按大括号深度切顶层块。
- 省份文件 `history/provinces/00_generated_provinces.txt` **纯 CRLF**：行级正则 `^(\d+) = \{\r?$`，插入的新行自带 `\r`。
- **CK3 文化文件首行带 BOM**（`00_bantu.txt`/`00_nakkavaram.txt`/`00_somalian.txt`），`^[a-z_]+ = \{` 匹配不到第一个文化，统计会漏。

## 三、文化
- 工具链：`_classify_cultures.py` → `_annotate_zh_in_classification.py --apply` → `_culture_classification_report.py`。CK3 原版 22 个「0 省份文化」不能当落点。
- **判据优先级**：`CULT_RULE > 自动同名 > GROUP_RULE_STRONG > LANG_RULE > GROUP_RULE > 自动（语言唯一/传承唯一）`。
  要压住 LANG_RULE 就写 CULT_RULE；想让某个「文化组」整体决断，写 `GROUP_RULE_STRONG`（现有 tungusic→mohe、nilosahelian→daju、bantu→east_bantu、khoisan→khoisan、malagasy→malagasy、papuan→papuan）。
  **`GROUP_RULE_STRONG` 生效条件 = 该组排在 `eu5_groups` 第一位**（不是「只挂这一个组」）：班图 95 个里 58 个是 `bantu_group;xxx_group`，只认单组会漏一半；而 `jurchen_group;tungusic_group` 的 jurchen 在首位，女真不会被抢走。
  **整体把 GROUP_RULE 提到 LANG_RULE 之前是错的**：GROUP_RULE 155 条里绝大多数是 `r(10,"")`/`r(11,"")` 占位，实测让 17 个文化改错（9 个犹太人压成 radhanite、4 个 swahili 退化 NEW:、khas/tharu→bodpa、maden→NEW:halmaheran、nivkh→mohe）。
  **★ 光加 GROUP_RULE 无效**：`GROUP_RULE` 里根本没有 cushitic/nilotic/west_african/central_african 这些条目，接管它们的是 `LANG_RULE` 的 `r(9,...)` 需建分离文化条目 —— 必须写 CULT_RULE。
- **★ 字典重复 key 会静默覆盖**：`LANG_RULE` 里 shan_dialect / kam_language / kra_language 各写过两次，后写吃掉侗台三分口径。已删。**改这几个表后必须用 ast 扫重复 key**（现全部 0 重复）。
- **★ 图内口径 = 原则上并入 CK3 原版文化**；`NEW:` 前缀保留 EU5 key，落地脚本跳过。**CU 地图范围内已清零**；图外仍有约 610 个 EU5 key（美洲/大洋洲正在按组收）。
- **例外：用户指定新建的 `khoisan` / `malagasy`**（CK3 原版没有）。定义手写在 **`common/culture/cultures/zz_eu5_culture_new.txt`**（BOM+CRLF），本地化在 **`localization/simp_chinese/zz_eu5_culture_new_l_simp_chinese.yml`**。**不要写进 `zz_eu5_culture_merge.txt`**——那个文件由 `_apply_eu_culture_merge.py` 重跑覆盖。支柱复用 `khoisan_group`/`eu5_heritage_khoisan_group`、`malagasy_group`/`eu5_heritage_malagasy_group`（`00_generated_pillars.txt` 已有）。name_list 与 ethnicities 只能复用同组资源。
  **tradition 坑**：在 CK3 目录有定义但 mod 里 0 次使用的疑为 DLC，选 tradition 前先 grep `00_generated_cultures.txt` 确认已在用（如 `tradition_tgp_rice_cultivators`/`tradition_fp3_irrigation_experts`/`tradition_stratified_society`）。
- 落点速查（易错项）：anglo_irish→english、norse_gael→gaelic、walloon→french、(western/eastern_)pomeranian→saxon、EU5 prussian(德意志)→saxon、kazani/mishar→bolghar、gyalrong→qiang、sudanese_arab→bedouin。
  **`arpitan`（阿尔卑坦）→ french**：EU5 把它放在 `french_group;swiss_group`、`arpitan_dialect`，是法语支不是奥克-罗曼；2026-10-27 用户纠正，CULT_RULE 与 LANG_RULE 两条都要写 french。奥克只留 auvergnat/gascon/languedocien/limousin/provencal/vivaro_alpine。
- **`prussian` 双义（省份层+人物层都要 skip）**：省里现存的 30 个 prussian 是波罗的普鲁士人，**再跑会误改成萨克森**，脚本 `KEEP_IN_PROV`+`KEEP_IN_PEOPLE` 双重排除。
- 判文化名一律先查本地化：CK3 `turkish`=乌古斯、`kazak`=喀扎克、`kirghiz`=黠戛斯、`uriankhai`=兀良孩、`kimek`=基马克、`bouxcuengh`=布僮、`shiwei`=室韦、`tai`=傣、`hlai`=黎；`samoyed` 显示「Bjarmian」、`maluku` 显示「文老古」、`nakkavaram` 显示「那旺」。
- **EU5 key 与中文名错位**：`azeri_culture`=**阿塞拜疆**（turkic_group）→ **turkish（乌古斯）**；`adhari_culture`=阿扎里（iranian_group）→ persian；`talysh_culture`→persian；`zaza_culture`=扎扎（实为库尔德语支）→ **kurdish**。依据 `EU5/game/main_menu/localization/simp_chinese/cultural_and_languages_l_simp_chinese.yml`。EU5 把 adhari/talysh/zaza 都塞进 `adharic_language`，按语言并入会全变突厥——必须按 eu5_groups 分流。
- 草原东西支：带 `steppe_group`→cuman（astrakhani/crimean/nogai）；不带→kipchak（uzbek/telengit/teleut/yerle_qaliq）。**例外：balkar/karachay/kumyk 只 turkic_group、无 steppe_group，2026-10-27 用户定 → `khazar`（可萨）**（语言是 kipchak_language，必须 CULT_RULE 覆盖；原先一度定 alan，已改口）。能独立保留：bashkir/bolghar/chuvash/uyghur/kirghiz/cuman。
- **侗台三分（不建新文化）**：台语支 `shan_dialect`→**tai**；侗水 `kam_language` + 仡央 `kra_language`→**bouxcuengh**（`00_tai.txt:47`）。`tai_lu`/`tai_nua` 的 `NEW:shan` 已作废。
- **通古斯三分（组判定优先于语言判定）**：① 含 `jurchen_group`→**jurchen**；② 同时含 `mongolian_group`+`tungusic_group`→**shiwei**（`00_mongolic.txt:225`）；③ 只有 `tungusic_group`→**mohe**（`GROUP_RULE_STRONG`，16 个鄂温克诸部自动命中）。
- 亚洲按语族并入：uriankhai→收南西伯利亚突厥（sakha/soyot/khakas）；lhomon→meitei 6 个；高加索 circassian/abkhazian/abazin+lezgin/nakh/avar/dargin/lak→alan，laz/svan/mingrelian→georgian；`avar_culture` 是高加索阿瓦尔、与 CK3 `avar` 同名异族，落 alan；tai_long→tai。
- **`khakas_culture`→uriankhai**（CK3 原版注释 "specifically the Khakas and the Tuvans"）。2026-10-27 一度改 kirghiz 又改回，**勿再动**。
- **西伯利亚东北部收尾**：`lamut_language`→**mohe**、`yukaghir_language`→**nivkh**、`chukotko_kamchatkan_language`→**nivkh**、`nicobarese_language`→**nakkavaram**（尼科巴与安达曼同处理）。落值：nivkh 307、mohe 387、uriankhai 70、kirghiz 33。
- **尼罗-撒哈拉 → daju**：`GROUP_RULE_STRONG["nilosahelian_group"]`（成员 berta/fur/gumuz/kadu/katla/kunama/moru/nuba/nyimang/surma 另在 CULT_RULE 逐个补）；`tunjur`/`funj` 的 eu5_groups 为空，按 cat7 显式落 daju。**EU5 把 tunjur/funj/fur/gumuz/kunama 误标 `egyptian_dialect`** —— 这就是撒南出现埃及文化的原因。
- **撒哈拉语族 → zaghawa（用户 2026-10-27）**：`saharan_language` 7 成员（bilala/kanembu/maba_africa/masalit/runga/toubou/zaghawa），`LANG_RULE` 由 kanuri 改 **zaghawa**；**必须显式写两条 CULT_RULE**：`kanembu→kanuri`（唯一例外）、`toubou→zaghawa`（挂 nilosahelian_group，强组层在 LANG_RULE 之前，不写会被截成 daju）。
- **非洲收尾（非洲 NEW 已清零）**：库希特→somali、尼罗特→welayta、中非/双组→sao、纯中非→daju、dogon→**marka**、senufo→**bobo**（按 CU）、ijaw→igbo、bantoid/benue→east_bantu、ket→mohe、andamanese→**nakkavaram**。**完整成员清单以 `_classify_cultures.py` 的 CULT_RULE 为准**（约 60 条），见 2026-10-27 日志。
  **这些刻意不写组级**：cushitic 17、nilotic 11、west_african;central_african 13，组级会冲掉 afar/beja/welayta/ethiopian 等已落对的。
  **CK3 安达曼群岛 = `nakkavaram`（那旺）**：`00_nakkavaram.txt:1`。
- **班图语族 → `east_bantu`（除斯瓦希里）**：`00_bantu.txt:1`（带 BOM），本地化已覆盖成「班图」。`swahili_culture` 在 CULT_RULE 显式保 `swahili`。
- **科普特 → `ancient_egyptian`**（`00_dead.txt:36`）。**但 coptic 从不是任何 EU5 province 的人口第一**，省份层仍是 0 省。
- **大洋洲/台湾**：`formosan_culture`→**amis**（`00_malayic.txt:396`）。**`GROUP_RULE_STRONG["papuan_group"]`=papuan**（2026-10-27 用户定），覆盖 139 个成员。bife/buruwai/iwur/kamoro/kimaama/marind/moi/wamesa 那 8 条 CULT_RULE 与组规则一致、保留无害；**alor/makasae/bunak/fataluku→maluku 那 4 条已删**（CULT_RULE 优先级更高，不删会挡住组规则）。
- **文化本地化一律不带「人」**：`_collective_noun` 等直接写族名。改的是 `localization/simp_chinese/zz_eu5_culture_merge_l_simp_chinese.yml` **和生成器** `gen_debug/_apply_eu_culture_merge.py` 的 LOC 模板（模板不改，重跑会把「人」写回来）。CK3 原版只有 `yeren`（野人）带「人」，是文化本名，不动。
- 已知历史遗留（未动）：`00_bookmarks.txt` 引 languedocien、`00_generated_challenge.txt` 引 highland（两 key 无定义）。
- **省份层落地口径 = 按 EU5 province 人口多数、同省统一**（`gen_debug/_apply_province_pop_culture.py`，支持 `--classif`、默认 dry run）：pops `size` 按 culture 累加 → province 多数 → 该 province 下所有男爵领写同一值；无 pop 的 110 县 fallback「同县当前多数」。**同目录 `_apply_county_majority_culture.py` 是错误第一版（location 个数投票），已废弃**。
- CSV 改法必须保 BOM+CRLF：`csv.reader(io.StringIO(io.open(P,"rb").read().decode("utf-8-sig")))` → `csv.writer(out, lineterminator="\r\n")` → `write(out.getvalue().encode("utf-8-sig"))`。Excel 独占锁会 WinError 32，先写 `.tmp_new` 用 `--classif` 指过去。

## 四、宗教 / faith / rite
- faith 映射 `Global_modern_map/eu5_export/eu5_ck3_faith_map_zh.csv`；**三表必须同步**：`_build_faith_map.py` CURATED / CSV / `_apply_*_faith.py` REL_RULE。已映射 195 / 保留 pagan 98。CK3 `satsana_phi`=守护灵教（EU5 同名宗教叫丕教）；「门顿教」是 religion 名（mundhum_religion）。
- 落盘坑：省只写 faith 无 rite= 时按 main_rite 回落；印度教分化必须**整县染色**（`_apply_hindu_faith_branch.py`）；**按县判定、按省落地**是反复踩的坑；写盘**保 CRLF**。
- 东亚 rite（`_apply_sect_rite.py`）：**sect 身份 = laws 首个元素**。DAI/KOR→dhyana、SSG→sukhavati。vajrayana_faith 的 main_rite 已改 lamaism，藏传五派+觉囊自动落不写行。根本说一切有部 10 成员 52 省写 vinaya。confucian_faith / maitreya_faith 无 main_rite，由 `history/faiths/00_eastern_misc.txt` 按日期定（1337=daoxue）。
- 佛教传播（`_apply_buddhist_geo_spread.py`）：只有 mahayana 需要补。三层：① 接壤 BFS；② 质心直线 ≤300 km 隔空、只做一步不递归；③ 阿吒力特批跨 faith 替换 mahayana（acharya 绑 vajrayana_faith，写时删 faith 行只留 rite，8 省须从 prov_rite 单独捞）。父信仰守卫：mahayana 系 7 rite 只写 mahayana_faith，vajrayana 系 5 个只写 vajrayana_faith。
- EU5 `religion_definition = mahayana #Azhaliism` 的 `#Azhaliism` 是注释。国家宗教看 `setup/countries/*.txt`；什叶 22 国（BKZ/SKN 已改 sunni+maliki）。兜底链：pops 多数→location 标注→同省其它 location 多数。

## 五、CU 对照表（「按 csv 分」指这个）
`gen_debug/_cu_vs_ours.csv`（2858 行 = 2858 barony，列 `barony, our_province, our_county, our_culture, our_faith, cu_culture, cu_rite, cu_county, cu_province`）：先把 cu_rite 挂到整个 province，再按 location 数取主体；拿 barony 名直接匹配只命中首府一格。
- **CU 地图范围 = 该表 barony 所属的 EU5 province（2448 个）**。用户 2026-10-27 明确「只看 CU 地图范围内，外面的就别管」。
- **柏柏尔 butr/baranis 以 CU 为准；但该口径只适用于柏柏尔文化**：→ **baranis**：kabyle、chaoui、masmuda、sanhaja；→ **butr**：zenati、mozabite、tuareg、eastern_amazigh、lamtuna、messufa、godala、toubou。→ **阿拉伯语一律 maghrebi**：algerian、moroccan、tunisian、libyan_arabic（CU 虽以 baranis 最多，用户明确否决）。

## 六、生成器纪律
用户手改文件绝不覆盖；写前比对内容，无变化不动 mtime，有变化才备份；生成物按 key 排序、带 BOM；脚本默认 dry run。**非必要不全量重建**（补丁层会被冲掉），外科手术式只改目标行；避免无谓干跑和验证仪式。**诊断类任务默认只读**，报告结论+改法，等用户说「改」才动手；行号一律【文件绝对行号】。被否/被取代的错误文件当场删；新建文件先查路径占用。EU5 人名先查 EU5 自带角色名表；**游戏安装目录只读**，产物一律放工作区。

## 七、其它约定
- EU5 复合名：每个 name 部分是独立 key，按 EU5 部分拼接（中文无分隔符、英文空格）；脚本 `gen_debug/fix_compound_names.py` + `verify_compound_names.py`。
- Git：master=发布分支（EU5 纹章在 eu5-coa 分支），远程 github.com/hathaway682/EU5_1337_to_ck3；GitHub Desktop 提交，push 前必 fetch；**禁止 git worktree**；staging 前先 `git status`，只能逐个 add。
- 地图可视化一律先用 skill `ck3-mapviz`（render 约 20s），**严禁自己算投影/质心打点**。

## 八、伯爵领首府 / 开局日期 / 摄政（工程要点，细节见日志）
- **首府链路六步**：`_capital_correct.py --barony-order rank_state` → `_apply_rank_state_seats.py --old-picks <旧json>` → `export_politics.py` → `_reassign_counties.py`（先 dry-run）→ `_apply_tusi_governments.py --apply` → `fix_holstein_denmark.py`。
- **★ fallback 真多数**：major 要从 minor 拿走伯爵领，地数须**严格大于县内任何其他单个持有者**（不要求过半）。探针 `_probe_majority.py`。排除名单 `gen_debug/eu5_reassign_keep.json`。
- **HRE 同名首府**（`fix_holstein_denmark.py` 第 3 节）5 县：c_chrudimsko、c_hanover、c_lippe、c_luneburger_heide、c_neuchatel。**跑 rank_state 会冲掉，跑完链路必须重跑**。**土司首府两条规则已全回滚，勿再实施**。
- **开局日期 1337.4.1**：三处同步 `default_start_date`（`bookmarks/00_bookmarks.txt:8`、`challenge_characters/00_generated_challenge.txt:8`、`groups/00_bookmark_groups.txt:8`）。EU5 原始 1337.1.1 保留 112 条占位，其余改 4.1 共 12430。**重跑风险**：`_fix_politics_output.py` 会丢毛利来源标记；`_export_title_map.py` 会把 58 个头衔记为开局无主。
- **查日本头衔必须 grep `history/titles/zzz_eu5_japan_noble_families.txt`**（145 个 `c_nf_*`），只 grep `zz_eu5_titles.txt` 会漏。
- **CK3 liege 来源**：`setup/start/12_diplomacy.txt` 的 `dependency`（652 条，仅 28 带 start_date）+ HRE 成员身份（`export_politics.py` 1018–1024）；**关系本身没有日期**。
- **regency diarchy 不会自动结束**，必须显式 `end_diarchy`；`zz_eu5_diarchy_regencies.txt` 21 块已按 EU5 日期对齐，DAN end=1400.1.1 等于永不结束。1280 个 `eu5_regent_*` 是占位 holder。
- **主头衔** `common/on_action/zz_eu5_primary_titles.txt` 共 220 条；**4 条手工指定的只在 `_patch_primary_titles_file.py` 里，重跑生成器会丢**（bds_jalal_al_dawla_iskandar→c_qazvin、gel_reinoud_ii_van_gelre→c_gelderland、rig_friedrich_von_pernstein→c_inner_livonia、utr_jan_van_diest→c_overijssel）。
- **title_map**：帝国/王国/公国→`X_eu5_TAG`；日本→`c_nf_*`（JAP/NTC/STC 记帝国）；**dynasty 反查有假阳性**（`c_nf_yamato`/STC、`c_nf_hei`/BQA）；联统 junior 伯国以下留空不记（41 个）。

## 十一、已完成，勿重做
168 支系→42 宗族（`zz_eu5_merged_houses.txt`）；`dynn_Anjou`=安茹用 `anjou_jerusalem`、`dynn_Robertine`=罗贝尔用 `robertian`、`dynn_Angevin` 是坑；154 个复合君主名 11 语言重译；4361 个原始宗教人物改写 religion；印度教整县染色；BKZ/SKN 7 角色改 maliki。

**待用户定的遗留**：① BKZ/SKN 库西雅 7 省 rite；② 10990 个角色 religion=pagan 但文化主体是基督教/伊斯兰/佛教；③ 244 个印度教省所在县 CU 记耆那教；④ `pamiri_culture`→afghan（用户说"先不动"）；⑤ `tai_lu`/`tai_nua` 文化定义与本地化是否删；⑥ `coptic`→ancient_egyptian 省份层 0 省，是否加少数派阈值规则；⑦ 涅涅茨→samoyed 显示名 Bjarmian；⑧ 萨尔语群 17 个文化（用户说"先不管"）。
