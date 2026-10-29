# 项目长期记忆（EU5_Modern_Borders_noshape）

> 每日细节在 `.workbuddy-ai/memory/YYYY-MM-DD.md`；这里只放长期有效的口径、坑与纪律。

## 一、层级与数据源
- EU5：location→province→area→region；`definitions.txt`(tab 缩进) 必须栈解析 `next(x for x in reversed(stack) if x.endswith(("_region","_area","_province")))`。
- province 声明一行式，共 4149 province / 27334 location。`06_pops.txt` 的 `size` 是浮点人口，**要人口必须读它**；`eu5_county_peoples.csv` 只是 location 个数多数，不是人口。
- CK3 `b_<name>` 的 `<name>` = EU5 location 名；3725/3819 county 严格对应单一 province。质心缓存 `_ck3_province_centroid.json` 的 **int 键读回必须 `{int(k): v}`**。

## 二、CK3 数据结构约定（头衔历史改前先看 skill `ck3-title-history-pipeline`）
- 本地化永远比 key 权威；先 `grep -rn "<key>" localization/simp_chinese/`。
- 首府 = 只读伯爵领块内第一个 b_；省份文件纯 CRLF；文化文件首行带 BOM（00_bantu/nakkavaram/somalian）。
- dynasty=宗族、house=支系；统计文化引用用 `re.finditer(r'(?<![a-z_])culture\s*=\s*(\w+)', line)`；角色块按大括号深度切顶层块。
- **本 mod 实际占用的原版 key 必须从 landless shim 体系里剔除，两处一起改**：`common/landed_titles/zz_vanilla_titulars.txt`（删 shim 块）＋ `common/on_action/00_generated_titular_guard.txt`（删 `title:X = { … destroy_title = prev }` 那行）。只删 shim 不删 guard，真实头衔开局就被销毁；只删 guard 不删 shim，同 key 的 landless 与有地声明冲突。清单真源 = `_title_overrides.csv` 的 `country/title_key`。**有些 key 只在 guard 里、不在 shim 文件里**（k_egypt/k_france/k_maghreb 是原版真实头衔），必须按 guard 全量比对。这两个文件是外部 Ck3MapGen v0.96 产物，重跑会写回。先例见 `zzz_eu5_faith_heads.txt` 头部注释。
- **`io_titles` 只能放"EU5 里没有对应国家的组织"**（hre、ilkhanate）。`tatar_yoke`/`middle_kingdom` 有对应国家（GLH/CHI），一旦也给它们铸头衔，组织会先写一个只有当前领袖 1 条的块，国家的完整世系块在改名预处理里被判重复删掉（2026-10-28 中华/金帐世系全丢就是这个）。去掉后成员仍走 `title_of[leader]` 兜底，liege 结果不变。**改名预处理"新 key 已有块就删旧块"是危险动作**：它假定新块更全，实际往往是新块只有一行、旧块有整条世系。
- **无地头衔（d/k/e）全丢，不留空壳**（2026-10-29 马恩岛 + 8 个空壳公国）：`export_politics.py` 有一条"统治者已持有伯爵领的，不能降为别人县里的男爵"（`rulers_with_county`），这类国家不进 `baronies`、不产生 `drop_title`，于是保留原 rank 铸出空壳头衔。判据在 `_fix_politics_output.py` 的 `declined` 段：**rank in (d,k,e)、0 个自己的县、不在 lords、且 ruler 已持有别国县 → 头衔丢弃**。全表命中 9 个：MNN（k）+ BRZ/INO/JAW/KLN/LIM/NMS/RCB/SIZ（d）；PAP 有罗马、HRE/ILK 的 rank=None，不误伤。用户明确"空壳公国也丢掉"，所以 d 级不再豁免。**地不跟着动**：MNN 的地在 `c_inner_hebrides`（苏格兰的县，8 个男爵领之一），8 个公国的地也各自留在原县。删头衔时要连带清三处：`eu5_titles_dropped.txt`、`zz_eu5_titular.txt` 声明、11 个语言的本地化行；`zz_eu5_primary_titles.txt` 里 `set_primary_title_to = title:d_eu5_*` 也要删（生成器已用 `title_key not in dropped` 过滤，下次重跑不会写）。同类排查口径：`rank in (d,k,e) and not own_counties`。

## 三、文化（改前先看 skill `ck3-culture-pipeline`）
判据优先级：`CULT_RULE > 自动同名 > GROUP_RULE_STRONG > LANG_RULE > GROUP_RULE > 自动`。
- `GROUP_RULE_STRONG` 生效 = 该组排 `eu5_groups` **第一位**（非"只挂这一组"）；但**整体把 GROUP_RULE 提前到 LANG_RULE 是错的**（会改错 17 个）。
- **字典重复 key 会静默覆盖**：改 LANG_RULE/CULT_RULE 后必须用 ast 扫重复 key。
- 图内口径 = 原则上并入 CK3 原版文化；`NEW:` 前缀保留 EU5 key、落地脚本跳过。CU 图内已清零，图外约 610 个 EU5 key 按组收。
- 例外新建 `khoisan`/`malagasy`（CK3 原版没有）：定义手写 `common/culture/cultures/zz_eu5_culture_new.txt`，本地化 `zz_eu5_culture_new_l_simp_chinese.yml`，**不要写进 `zz_eu5_culture_merge.txt`**（被生成器覆盖）。
- 易错落点：arpitan→french（两处都写）；prussian 双义（省+人都要 skip，30 个波罗的普鲁士人勿改萨克森）；EU5 key 错位 azeri→turkish(乌古斯)、adhari/talysh→persian、zaza→kurdish（按 eu5_groups 分流，勿按语言）；草原带 steppe_group→cuman、不带→kipchak，balkar/karachay/kumyk 无 steppe_group→khazar；侗台三分 shan_dialect→tai、kam+kra→bouxcuengh；通古斯含 jurchen_group→jurchen、mongolic+tungusic→shiwei、仅 tungusic→mohe；khakas→uriankhai（勿动）；班图→east_bantu（swahili 显式保）；非洲收尾完整清单见 `_classify_cultures.py` 的 CULT_RULE（约 60 条，2026-10-27）。
- 文化本地化不带「人」，且要同时改 `zz_eu5_culture_merge_l_simp_chinese.yml` 与生成器 LOC 模板。
- **人物/王朝层的 culture 是外部 Ck3MapGen 按旧映射表写死的**：文件里存的是 `turkish`/`occitan`，根本不存在 `adhari_culture`/`arpitan`，所以 `_apply_people_culture.py` 扫不到、CSV 改了也回溯不了。核对口径 = 读 EU5 `main_menu/setup/start/05_characters.txt` 的 `culture =`，按角色 ID 逐块比对 mod 侧（2026-10-28 查出 SRV 三君主 turkish 应为 persian、115 个 arpitan 角色全是 occitan）。占位摄政 `eu5_regent_*`：ID = `eu5_regent_`+tag 小写，触发条件 = EU5 该国无具名统治者（852 个里 801 个 `ruler = random`）。**判定口径 = EU5 国家的 `culture_definition` / `religion_definition`**（在 `in_game/setup/countries/<region>.txt`，2337 个 tag 全覆盖；**不要用首都省份人口主体**，两者常不同，如 SKI 主流文化是 adhari、首都 shaki 人口主体却是 lezgin）。按此重算 852 个里只有 18 个错（2026-10-28 已修 36 行，两文件各 18）。每个 ID 在 `zz_eu5_characters.txt` 与 `zz_eu5_regents.txt` 各一份块。religion 层 73 种国教全部有对应 CK3 faith，无跨宗教错配，未动。

## 四、宗教（改前先看 skill `ck3-religion-pipeline`）
- 判 rite 能否挂省看 religion 不看 faith；基督教 9 礼绑 `christian_faith`。shangqing_faith=上清派、quanzhen=全真派(rite)。
- 唯一真源 `eu5_ck3_faith_map.csv`（生成器 `_build_faith_map.py` 的 CURATED），三表必须同步。**文件可能被用户回滚，数字要当场 religion_audit.py 核**。

## 五、CU 对照
`_cu_vs_ours.csv`（2858 barony）。CU 范围 = 该表 barony 所属 EU5 province（2448 个）。柏柏尔 butr/baranis 以 CU 为准；**阿拉伯语一律 maghrebi**（algerian/moroccan/tunisian/libyan_arabic）。

## 六、生成器纪律
用户手改文件绝不覆盖；默认 dry run；非必要不全量重建（补丁层被冲）；诊断默认只读、报告结论+改法等用户说「改」；行号一律绝对行号；游戏安装目录只读，产物放工作区。
- **只改 politics.json 的输入时（例如 `io_titles`），链路只需 `export_politics.py` → `_patch_title_history.py`，绝不要跑 `_fix_politics_output.py`**：它是总装脚本，一次写 20 多个产物——province history 的 21046 条 culture/faith/holding、characters 的 government/regent、`zz_eu5_titular.txt` 颜色、tributaries、primary titles、两种语言的本地化。为修两个头衔的历史跑它，会把地块的文化宗教连同这些补丁层一起冲掉（2026-10-28 事故，用户已回滚地块）。跑之前先问：这一步真的需要动这个文件吗。

## 七、其它
- 复合名每部分是独立 key，按 EU5 部分拼接（中文无分隔符、英文空格）。
- Git：master=发布分支，eu5-coa 分支存纹章；禁 git worktree；GitHub Desktop 提交，push 前 fetch。
- 地图可视化一律 `ck3-mapviz`，严禁自己算投影打点。
- **备份归档位置（长期约定）**：所有 `*.bak*` 备份统一放 `F:/EU5_Modern_Borders_bak/`，**按原目录结构分层保留**（common/history/gen_debug/localization 等），项目目录内不得残留 bak 文件。2026-10-28 已把 317 个历史 bak 全量迁出。需要临时备份时也放这里，别留在项目里。

## 八、工程要点
- 首府链路六步（rank_state→reassign→export→tusi→holstein）；fallback 真多数 = 地数严格大于县内其他单持有者；HRE 同名首府 5 县（c_chrudimsko/c_hanover/c_lippe/c_luneburger_heide/c_neuchatel）跑完 rank_state 须重跑 `fix_holstein_denmark.py`；土司首府规则已回滚勿实施。
- 开局 1337.4.1 三处同步（bookmarks/challenge/groups）；重跑 `_fix_politics_output.py` 丢毛利标记、`_export_title_map.py` 记 58 头衔开局无主。
- **链路已重构（2026-10-28 16:50 之后）**，`zz_eu5_titles.txt` 可以整链重跑了。现在的链路只有两段：
  `_fix_politics_output.py` → `_patch_title_history.py`，规则全在里面，不再需要任何 `_apply_*.py` 补丁层。
  - **降级判据**：rank=d 且 **liege 头衔也是 d 级** 才降级（原来还要求"只有 1 个伯爵领"，已删）。
    实测只降 SWB → d_eu5_mag；18 个单伯爵领公国自动保住，**不要给它们写 override**。
  - **人工决定表** `gen_debug/_title_overrides.csv`（加载器 `eu5_export/_title_overrides.py`）：
    scope=country/title/county/barony，field=rank/title_key/liege/holder/government，没有 declare。
    要改"谁持有/答于谁/什么政体/挂哪个 key"，只改这张表，别写补丁脚本。播种脚本 `_seed_title_overrides.py`
    只跑过一次，之后表归手工维护（重跑会按脚本内容覆盖）。
  - **区域政体** `_gov_rules.py`（曼陀罗/村社/穆斯林 clan + 土司 tribal），**牧群** `_herders.py`
    （448 个 herder 国家整批剔掉，17 县还 CHI、586 县荒野）。这两个都在生成器里调，不在链路外。
  - **改过 key 的国家必须连块一起改名**：`_fix_politics_output.py` 用 `dropped[old]=new` 删旧声明，
    `_patch_title_history.py` 用改名预处理把旧块换 key（保世系）。漏了就会出现 `k_eu5_dan` 和
    `k_denmark` 并存、或者 liege 指向不存在的 key。**任何"某国底下全答于它"的地方都不许写死旧 key**
    （`e_eu5_jap` 这个坑让 61 个县 + 145 个日本家族全悬空过）。
- **`zz_eu5_titles.txt` 绝不可整体重建**（2026-10-28 实测）：`_patch_title_history.py` 按 politics 重写 holder/government/liege，会冲掉后面所有 `_apply_*.py` 补丁层——土司 tribal 119 处、海洋 wanua 66 处、中华 liege 17 县、c_hanover/c_holstein/c_lippe 同名首府修正、c_mugla 的 k_mentese、b_kiel/b_brixen holder。另外 politics 还留着 448 个 herder 国家（rank=None）和 4 个已升王国的贝伊（AYD/ERE/MEN/TUR rank=d），直接重建会写出 603 个无主县并复活 d_eu5_ayd 等 4 块。
  （注：上面这段是重构**之前**的记录；重构后前两类已被 `_gov_rules.py`/`_herders.py` 接管，
  但"不要整体重建"这条仍然有效——`_patch_title_history.py` 只补不改。）
- regency diarchy 不自动结束，须显式 end_diarchy；1280 个 `eu5_regent_*` 是占位 holder。
- 主头衔 220 条；4 条手工指定只在 `_patch_primary_titles_file.py`，重跑生成器会丢（bds_jalal_al_dawla_iskandar→c_qazvin 等）。
- title_map：帝国/王国/公国→`X_eu5_TAG`；日本→`c_nf_*`；查日本须 grep `zzz_eu5_japan_noble_families.txt`。

## 九、已完成 / 遗留
- 已完成勿重做：168 支系→42 宗族；154 复合君主名重译；4361 宗教人物改写；印度教整县染色；BKZ/SKN 7 角色 maliki。
- 待定：① BKZ/SKN 库西雅 7 省 rite；② 10990 pagan 角色文化主体非 pagan；③ 244 印度教省 CU 记耆那；④ pamiri→afghan（先不动）；⑤ tai_lu/tai_nua 定义去留；⑥ coptic 省份层 0 省阈值；⑦ 涅涅茨→Bjarmian；⑧ 萨尔语群 17 文化（先不管）。
