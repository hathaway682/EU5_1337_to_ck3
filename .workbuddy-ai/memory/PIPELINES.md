# 链路与领域细则（EU5_Modern_Borders_noshape）

> `MEMORY.md` 的配套长文。硬规则在 `MEMORY.md`，这里是「怎么做」的细节。

## 一、CU 法理树重建（2026-10-29）
- 必须先把 `history/titles` 的 `de_jure_liege` ＋ `effect` 里的 `set_de_jure_liege_title` 按 **<=1337.4.1**（CU 的 `zz_1337_bookmark.txt`，与 mod 开局同日）取每个头衔最后一个生效值，共 **68 条生效**（50 d + 18 k），否则拿到的是静态初始态。
- 脚本 `_probe_cu_dejure.py` / `_rebuild_dejure_cu.py` / `_prune_landless_shims.py`；源副本 `gen_debug/_dejure_src_20261029.txt`（脚本读它，不读产物自身）；映射 `gen_debug/_dejure_cu_map.csv`。
- d_ 按 CU 覆盖内 province 最大比例归 CU 王国，覆盖外 239 个保持原王国；废弃 36 个 key（6 e + 30 k），全部在 history 里没有块。
- 重建后必须同时 prune `zz_eu5_titular.txt` 与 `zz_vanilla_titulars.txt` 里同 key 的无地声明，否则后加载覆盖回无地。
- 首府按 CU 的县对应（用户指定，不用投影）：① CU 的 capital 县在 mod 有同名 → 直接用；② 用 `_cu_vs_ours.csv` 的 `cu_county→our_county` 映射；③ 用 CU 该县首府男爵领名查 csv 的 `barony` 列；④ 都不行才回退子块首府。结果 288 个 h/e/k 里 249 个位置正确。

## 二、文化（改前先看 skill `ck3-culture-pipeline`）
判据优先级：`CULT_RULE > 自动同名 > GROUP_RULE_STRONG > LANG_RULE > GROUP_RULE > 自动`。
- `GROUP_RULE_STRONG` 生效 = 该组排 `eu5_groups` **第一位**（非「只挂这一组」）；但**整体把 GROUP_RULE 提前到 LANG_RULE 是错的**（会改错 17 个）。
- **字典重复 key 会静默覆盖**：改 LANG_RULE/CULT_RULE 后必须用 ast 扫重复 key。
- 图内口径 = 并入 CK3 原版文化；`NEW:` 前缀保留 EU5 key、落地脚本跳过。图外约 610 个 EU5 key 按组收。
- 例外新建 `khoisan`/`malagasy`（原版没有）：定义 `common/culture/cultures/zz_eu5_culture_new.txt`，本地化 `zz_eu5_culture_new_l_simp_chinese.yml`，**不要写进 `zz_eu5_culture_merge.txt`**（被生成器覆盖）。
- 易错落点：arpitan→french（两处都写）；prussian 双义（省+人都 skip，30 个波罗的普鲁士人勿改萨克森）；azeri→turkish(乌古斯)、adhari/talysh→persian、zaza→kurdish（按 eu5_groups 分流，勿按语言）；草原带 steppe_group→cuman、不带→kipchak，balkar/karachay/kumyk 无 steppe_group→khazar；侗台 shan_dialect→tai、kam+kra→bouxcuengh；通古斯含 jurchen_group→jurchen、mongolic+tungusic→shiwei、仅 tungusic→mohe；khakas→uriankhai（勿动）；班图→east_bantu（swahili 显式保）；非洲收尾清单见 `_classify_cultures.py` 的 CULT_RULE（约 60 条）。
- 文化本地化不带「人」，且要同时改 `zz_eu5_culture_merge_l_simp_chinese.yml` 与生成器 LOC 模板。
- **人物/王朝层的 culture 是外部 Ck3MapGen 按旧映射表写死的**：存的是 `turkish`/`occitan`，不存在 `adhari_culture`/`arpitan`，所以 `_apply_people_culture.py` 扫不到、CSV 改了也回溯不了。核对口径 = 读 EU5 `main_menu/setup/start/05_characters.txt` 的 `culture =`，按角色 ID 逐块比对。
- 占位摄政 `eu5_regent_*`：ID = `eu5_regent_`+tag 小写，触发条件 = EU5 该国无具名统治者（852 个里 801 个 `ruler = random`）。**判定口径 = EU5 国家的 `culture_definition`/`religion_definition`**（`in_game/setup/countries/<region>.txt`，2337 tag 全覆盖），**不要用首都省份人口主体**（SKI 主流文化 adhari、首都 shaki 主体 lezgin）。按此 852 个里只有 18 个错。每个 ID 在 `zz_eu5_characters.txt` 与 `zz_eu5_regents.txt` 各一块。73 种国教全部有对应 faith。

## 三、宗教（改前先看 skill `ck3-religion-pipeline`）
- 判 rite 能否挂省看 religion 不看 faith；基督教 9 礼绑 `christian_faith`。shangqing_faith=上清派、quanzhen=全真派(rite)。
- 唯一真源 `eu5_ck3_faith_map.csv`（`_build_faith_map.py` 的 CURATED），三表必须同步。**文件可能被用户回滚，数字要当场 `religion_audit.py` 核**。

## 四、CU 对照
`_cu_vs_ours.csv`（2858 barony）。CU 范围 = 该表 barony 所属 EU5 province（2448 个）。柏柏尔 butr/baranis 以 CU 为准；**阿拉伯语一律 maghrebi**（algerian/moroccan/tunisian/libyan_arabic）。

## 五、生成链路（两段）
`_fix_politics_output.py` → `_patch_title_history.py`，规则全在里面，不再需要 `_apply_*.py` 补丁层。
- **降级判据**：rank=d 且 **liege 头衔也是 d 级** 才降级。实测只降 SWB → d_eu5_mag；18 个单伯爵领公国自动保住，**不要给它们写 override**。
- **人工决定表** `gen_debug/_title_overrides.csv`（加载器 `eu5_export/_title_overrides.py`）：scope=country/title/county/barony，field=rank/title_key/liege/holder/government，没有 declare。要改「谁持有/liege 是谁/什么政体/挂哪个 key」只改这张表，别写补丁脚本。播种脚本 `_seed_title_overrides.py` 只跑过一次，之后归手工维护（重跑会覆盖）。
- **点名升格** `RAISED = {"LIT": "k"}`（`export_politics.py`，放在 `lowered = collections.Counter()` **之前**）：改 `countries[tag]["rank"]`，让附庸公国不再被 `lowered` 降级。key 走 `_title_overrides.csv` 的 `country/<tag>/title_key`。**附庸的 liege 必须是 k/e 级**，写 `d_` 会得到「公国挂公国」的非法 liege（2026-10-29 立陶宛 8 条 `d_lithuania` → `k_lithuania`）。
- **地图上的有地公国** `_grant_landed_duchies.compute(mod, export, lieges=None)` 返回五元组 `grants, why, blocked, under_duke, countries`（改签名必须同步三处调用点）。三条规则：同名且 tag 是 d → 改名换公国；同名但 tag 是 k/e → 只加公国；控制 ≥50% 且公国内无别的公爵首府 → 给他。**否决：获授者当前 `liege` 是 `d_` 头衔就不给**（伯爵升公爵后同级不能互为封臣；只看 liege 前缀、不判 rank）。被否掉的公国要 `dropped` 删块 + 撤 `zz_eu5_titular.txt` 声明。**`seated`（别的公爵首府在这里）只算至少持有 1 个伯爵领的 rank=d 国家**：187 个 rank=d 里 51 个一个县都没有，拿它们挡人就是拿幽灵挡真人（2026-10-29 阿拉贡 5/6 被 ANR+CAT 挡在 d_catalonia 外）。地图上**没有 `d_barcelona`**，`c_barcelona` 属 `d_catalonia`。两个脚本都调它，**`duchy_rename` 必须在 `ckey` 之前初始化**、`title_key` 算完要重映射、`dropped[old] = new` 用赋值；声明循环要跳过 `00_landed_titles.txt` 已有的 key（`declared` 只认 `zz_eu5_titular.txt`）。
- **区域政体** `_gov_rules.py`（曼陀罗/村社/穆斯林 clan + 土司 tribal）、**牧群** `_herders.py`（448 个 herder 国家整批剔掉，17 县还 CHI、586 县荒野）。都在生成器里调。
- **改过 key 的国家必须连块一起改名**：`_fix_politics_output.py` 用 `dropped[old]=new` 删旧声明，`_patch_title_history.py` 用改名预处理把旧块换 key（保世系）。漏了就出现 `k_eu5_dan` 与 `k_denmark` 并存、或 liege 指向不存在的 key。**任何「某国底下所有头衔的 liege 都指向它」的地方都不许写死旧 key**（`e_eu5_jap` 的坑让 61 个县 + 145 个日本家族全悬空过）。
- **`zz_eu5_titles.txt` 的补丁层**（整体重建会全冲掉）：土司 tribal 119 处、海洋 wanua 66 处、中华 liege 17 县、c_hanover/c_holstein/c_lippe 同名首府修正、c_mugla 的 k_mentese、b_kiel/b_brixen holder。
- regency diarchy 不自动结束，须显式 end_diarchy；1280 个 `eu5_regent_*` 是占位 holder。

## 六、首府与开局
- 首府链路六步（rank_state→reassign→export→tusi→holstein）；fallback 真多数 = 地数严格大于县内其他单持有者；HRE 同名首府 5 县（c_chrudimsko/c_hanover/c_lippe/c_luneburger_heide/c_neuchatel）跑完 rank_state 须重跑 `fix_holstein_denmark.py`；土司首府规则已回滚勿实施。
- 开局 1337.4.1 三处同步（bookmarks/challenge/groups）；重跑 `_fix_politics_output.py` 丢毛利标记、`_export_title_map.py` 记 58 头衔开局无主。

## 七、颜色口径
- 头衔颜色 = 该头衔自己那份色，**不做任何派生/替换**。`_fix_politics_output.py` 的 `usable()`
  以前会把近白（`max-min <= 24 且 max >= 190`）换成 key 哈希色，2026-10-29 已删——近白也是色
  （原版 `k_trinacria` 就是 `{ 249 232 247 }`）。
- **原版键头衔的颜色用原版那份**，权威表 `eu5_export/_vanilla_title_colors.json`（1440 条，
  从原版 `common/landed_titles/` 抄出，含 hsv 写法）。换 `title_key` 时不要沿用被替换掉的旧键颜色：
  `k_delhi` 220 150 75 与 `e_hindustan` 0 76 76 是两个头衔各自的色。
- `*_eu5_*` 头衔的颜色 = 该 tag 在 politics 里的 `color` 原值。
- **原版键头衔不止在 `zz_eu5_titular.txt` 里**：五个信首（`k_papal_state`/`k_orthodox`/
  `d_coptic_papacy`/`d_apostolic_church`/`d_patriarchate_in_the_east`）声明在
  `common/landed_titles/zzz_eu5_faith_heads.txt`，颜色写死在 `_faith_heads.py` 的 `COLORS` 表。
  总装脚本的「原版色」那一段只扫 `zz_eu5_titular.txt`，**改颜色时这两个地方都要看**。
