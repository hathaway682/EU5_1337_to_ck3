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

## 八、强制锁定首府标准流程（2026-11-10 用户拍板，原 MEMORY 六）
用户说「把 X 强制设为其所在伯爵领的首府」= **默认全套一起改**，不必逐项确认；原话「伯爵领归属，挂的头衔也一并修改，这是标准流程，记下来」。统一写进 `gen_debug/fix_holstein_denmark.py` 的对应小节（幂等、保留 BOM/CRLF、docstring 记依据）。
1. **两处法理树**：`common/landed_titles/00_landed_titles.txt` ＋ EXPORT `landed_titles/00_eu5_landed_titles.txt`，把 `b_X` 提为 `c_<county>` 的第一个 barony（CK3 首府 = 第一个 `b_`）。
2. **`history/titles/zz_eu5_titles.txt`**：该 `c_` 的 `1337.4.1` holder 改成 X 国 ruler，`government` 同步换成 X 国的（republic→`republic_government`）；历史日期段不动。
3. **`gen_debug/eu5_ck3_title_map.csv` 只改 country 行**：X 国 `b_X → c_<county>`（tier c、名换 county 名、government、note 改 `its land is its counties`）；`county` 行 / `barony` 行一律不动。country 行 note 常是带引号且内含逗号的字段，解析必须 `csv.reader`，**不能 `split(",")`**。
4. **原持有者不是一律降级为男爵领**：只有「EU5 里除了这个 county 没有别的地」才像 RIM→`b_rimini` 那样，把它的 country 行从 `c_` 改挂 `b_<原首府>` 并在 `zz_eu5_titles.txt` 新建该 `b_` 块承接 holder。**公国 / 多地的原持有者什么都不动**——用户原话「吕讷堡又不是只拿了一块地，你纠结他干什么」：LUN rank d、11 个 location、country 行挂 `d_eu5_lun`，失去 `c_elbmarch` 后仍有地，`country,LUN` 与 `b_harburg` 都不动。
5. **`gen_debug/eu5_reassign_keep.json`**：加 `c_<county>`、`b_X`，以及（有降级时）`b_<原首府>`，防 `--barony-order rank_state` 重跑把座位抢回去。
6. 完整重跑 `_export_title_map.py` 会按 `seat` / `barony_of` 把 country 行写回旧绑定，**导出后必须重跑 `fix_holstein_denmark.py`**。
已落地：c_holstein/kiel、HRE 同名首府 5 县、c_oriel、c_flaming/c_palatinate、c_romagna（RAV/RIM）、c_elbmarch（HAM/LUN）、c_wesermarch（BRM/OLD）、**首都 5 县（2026-11-14）**：c_gamrun/b_hormuz、c_malmohus/b_lund、c_kosovo/b_prizren、c_main_franconia/b_wurzburg、c_neckar/b_stuttgart。
- **首都 5 县是「已持有、只校正首府」型**：五个国家 rank 都是 d/k/c，country 行挂 `d_`/`k_`/`c_` 高阶头衔而非 `b_<首都>`，原持有者（霍恩贝格 HHB）另有 `c_swabian_alb`，所以**不改 title_map 任何行、不新建降级男爵领**；只有 holder 不是本国 ruler 的三个县（c_malmohus 教会人物、c_kosovo 地方领主、c_neckar HHB ruler）改了 1337.4.1 holder，`c_malmohus` 顺带 `ecclesiastical_government → feudal_government`。判据见「六」第 4 条（LUN 裁定）。
- **重跑补丁脚本时第 6 节可能把 RAV/RIM 的 country 行再绑一次**：`_export_title_map.py` 会按 seat/barony_of 写回旧绑定，脚本按既定规则自动修回，不是 bug；看到 "2 rows rebound" 说明期间有人重跑过导出。
- 坑：`fix_holstein_denmark.py` 第 2 节原先在已打补丁的数据上会崩（`c_holstein` 的 `1337.1.1` liege 已被手改成 `k_denmark`、holder 移进单独 `1337.4.1` 块）；已加幂等分支，命中已落地状态就整段不写，绝不覆盖手改行。

## 九、宗教 skill（原 MEMORY 七，`.workbuddy-ai/skills/ck3-religion-pipeline/`，2026-11-14 建）
宗教改动一律走这个 skill，不要临时写脚本。四个工具：`religion_audit.py`（省份只读体检）、`religion_set.py`（改省份 faith/rite）、`religion_chars.py`（改角色 religion/rite + 跨宗教执政统计）、`religion_snapshot.py`（faith+rite 保存点/还原，原 `gen_debug/_religion_checkpoint.py` 已移入并删除）。参考：`pipeline.md`（10 层执行顺序）、`rites.md`（多 rite 全表）、`pitfalls.md`、`cu-source.md`、`holy-sites.md`、`faith-defs.md`。
- **★ 切省份块必须按大括号深度，不能取「第一个 `}`」**。省份块里有 `1337.4.1 = { ... }` 日期子块，其闭括号缩进 `\t\t\t`；按第一个 `}` 切会把子块尾巴当顶层、写回时闭括号变无缩进 `}`。2026-11-14 实测改 1 个省掉 2 万字节缩进，**BOM/CRLF/括号全平衡、体检不报错**，只有跟备份 diff 才看得出。旧 `_religion_checkpoint.py` 也带这个 bug。改完必须比字节数和 md5。
- mod **没有** `common/religion/faith_types/` 和 `rite_types/`，faith/rite 定义全继承原版（103 faith / 152 rite）。要改教义得整块抄原版，CK3 同名块是替换不是合并。
- 12 个省只有 `rite = acharya` 没有 `faith` 行，是既定写法（有 rite 就不写 faith），不是漏数据。
- 角色块会重复出现：`zz_eu5_characters.txt` 是完整定义，`zz_eu5_government.txt` 是纯 effect 补丁块，后者不能塞 `religion =`。
- 跨宗教统计必须先用 `eu5_ck3_faith_map.csv` 把 EU5 `religion_definition` 翻成 CK3 faith 再比，否则 `theravada` vs `theravada_faith` 全是假阳性；同 religion 的兄弟 faith（miaphysitism vs armenian_apostolic）不算错。当前真跨宗教 153 人（BYZ 42 / CHG 20 / MGE 17）。
- 圣地 270 个，已确认 198 / 未确认 72；`common/religion/holy_site_types/00_holy_site_types.txt` 只改 `county`/`barony`，不动 modifiers。mod 无 faith_types 所以「被引用」= 出现在原版 faith 的 `holy_sites` 列表里，不被引用的就是孤儿，用 `gen_debug/_drop_orphan_holy_sites.py` 清。
