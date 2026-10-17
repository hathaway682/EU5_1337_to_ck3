# 项目长期记忆 — EU5_Modern_Borders_noshape

## 项目性质
CK3 全面转换 mod：把 EU5（Europa Universalis V）的 1337 年开局政治 + 全球地图移植到 CK3。
- 成品 mod（游戏直读、就地改）：`D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape`
- 生成器工作区（脚本/JSON/备份）：`…\mod\Global_modern_map`
- 交接文档：成品 mod 里的 `AGENT_HANDOVER.md`（§1 流水线、§3 规则、§4 铁律、§5 故障史）
- 游戏安装目录（EU5/CK3 的 `game\`）**一律只读**

## 版本管理（2026-10-16 起）
- **成品 mod 目录已 `git init`**（1 个 init 提交，`.gitignore` 只忽略 `/gfx`）。
- 生成器工作区 `Global_modern_map` **没有 git**。
- 因此：成品文件的改动可由 git 还原；生成器工作区的 `_backup_*` 删了不可恢复。
- 手工备份不再需要无限膨胀。

## 数据口径速记（复用）
- **政治 setup 一律读「原版」EU5**，不用 workshop 模组的 setup：
  `D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game\main_menu\setup\start\`
  （`06_pops.txt` / `07_cities_and_buildings.txt` / `10_countries.txt` / `15_international_organizations.txt` …）。
  workshop 那个 mod（`…\workshop\content\3450310\3609767543`）**只提供 `in_game/map_data` 和本地化**。
  用户 2026-10-16 明确："不要管 workshop，我们用的是原版数据"。
  ⚠️ 两份文件**内容不同**（原版文件更大：pops 5084334 vs 5051984 字节；单地点国家数 595 vs 563）。
  `export_modern_borders.py` 的 `fingerprint` 现在把原版 setup 也纳入，改数据会自动触发重跑。
- 伯爵领显示名 ← `localization/simp_chinese/eu5_titles_l_simp_chinese.yml` 的 `c_*`
- 县内 location ← `Global_modern_map/eu5_export_modern/mapping.json` 的 `locations[]`（`kind=='land'`，`county` 字段）
- 首府 ← `eu5_politics.json` 的 `counties[c].capital`（= CK3 `00_landed_titles.txt` 里该县**第一个**男爵领）
- 人口 ← 原版 `main_menu/setup/start/06_pops.txt` 每个 location 内 `size =` 之和
- 海陆 ← `map_data/definition.csv` 第 5 列前缀：`prov_*` 陆地 / `sea_*` 水域
- **CK3 province id** 在 `common/landed_titles/00_landed_titles.txt` 的 `b_x = { province = N }`（1-21046，共 21046 个；
  有 barony 的陆地 province）。≠ mapping.json 里 b_x 的 province（那是 EU5 location id）。
- **province 邻接**：`Global_modern_map/eu5_export/_ck3_province_adjacency.json`（`_build_ck3_adjacency.py` 从
  mod `map_data/provinces.png` 推，50913 对/20613 节点）。★ provinces.png 像素颜色 = `definition.csv` 的 RGB，
  **不是** R+G*256+B*65536 编码；正确链路 = 像素 RGB →(查 definition.csv 第0列)→ CK3 province id。
- location 持有者 ← 复刻 `export_politics.py` L574-582：遍历各国 `holds` 全部类别，按 `OWN_ORDER` 取 (rank,tag) 最小者
  （`OWN_ORDER` = own_control_core / own_core / own_control_integrated / own_integrated / own_control_conquered /
  own_conquered / control_core / control / own_control_colony / own_colony；`control*` 只用来定归属，不计国家大小）
- HRE 成员 ← `eu5_politics.json` 的 `relations` 里 `type=='hre'` 的 **`second`**（`first` 恒为皇帝 UBV）
- **11 个 location 名字带大写国家后缀**（`targoviste_BUL`/`constantine_ALG`/`tata_MOR`/`map_ASK`…）：
  任何 `[a-z0-9_]+` 的正则都会把它们切两半，必须用 `[A-Za-z0-9_]+`。

## 县首府排序规则 `--barony-order`（2026-10-16，可选，对比用）
- 落点 `eu5_export/_capital_correct.py`（决定 `00_eu5_landed_titles.txt` 里每县 barony 顺序 = 首府）。
  上游 `export_modern_borders.py --barony-order` → `run_modern_borders.ps1 -BaronyOrder`（**只有带 `-Export` 才生效**）。
  规则记进 `eu5_export_modern/EXPORT_STAMP.json`；`export_politics.py` 读这个 stamp 决定县主口径。
- `id`（默认，行为不变）= definitions 顺序。
- `rank_pop` = **城市 → 集镇 → 首都乡村 → 非首都乡村**：
  1) EU5 rank（`07_cities_and_buildings.txt` 的 `rank =`，`city`/`megalopolis` > `town` > 未列出=rural）；
  2) 同档内「多 location 国家的首都」（`10_countries.txt` 里该国 `capital = <loc>` 且它 own_* 并集 >1 个 location）永远靠前；
  3) 再按人口降序；4) 最后按 id。
  例外：city/town 的持有者是**单 location 国家** → 按 rural 排（防自由市被抬成县首府）。
- **`rank_pop` 下县主跟着首府走**：`export_politics.py` 取 export 树**第一个 barony** 的 location 作 capital，
  县归它的持有者；首府无人持有则退回 definitions 首 location（防止县掉进荒野）。
- 实测（原版数据，3831 县）：首府变 1989 个（同领主 1630 / 换领主 264，其中 95 个从单地点国家挪走）；
  县主实际改变 **349** 个；首府档位 city 200→238、town 374→600、首都乡村 538、非首都乡村 2455；
  坐在自由市上的县 116→58；super-title capital 变 217/760。
- ⚠️ C# `Capitals.SeatCounties()` 自己按地形/chief burg 打分设 `county.Seat`，写出时 `SeatFirst()` 提到第一位 ——
  实测只覆盖 ~31/3816 个县（99.2% 仍是 export 树顺序决定），所以 export 顺序仍是主要决定因素。

## 头衔历史铁律（★ 2026-10-16 血泪）
- **县块里的历史链 = 该县持有者的统治者序列**：`c_ayutthaya` 的 1082→1337 十条 = ADH 阿踰陀的
  `countries[].rulers` 逐条吻合；`c_millieu` 的 22 条 = FCB 的 rulers。
- **领地改派时整条链换成新县主 X 的 `rulers`，不是只改 1337**（用户原话："领地变化跟着整个头衔历史"）：
  - 每条 = `日期( = ruler.start) = { holder = ruler.character }`，**按日期数值升序**
    （`982.1.1` 必须最前；字符串排序会把它排到最后）。
  - 末尾写 `1337.1.1 = { holder = X 的 1337 持有者; government; liege }`（liege 单独写这条，§4.2）。
  - X 无 `rulers` 的 → 只留 1337 一条（24 个里 13 个如此）。
- **降级为男爵的原县主 O，男爵块 holder = O 在 1337 生效的持有者** =
  `gen_debug/eu5_ck3_title_map.csv` 里 O 的 `ck3_holder`（与"原县块 1337 时刻实际生效的 holder"一致）。
  ⚠️ 别用原县块里正则命中的第一个 holder —— 那是历史链最早那条（`c_ayutthaya` 会错取 1082 的
  `adh_narai`，正确是 1337 的 `adh_boromracha`）。
- 正则必须带 `re.S`；替换整块时**别忘补回块的闭括号 `}`**（漏了会块合并、花括号失衡）。
- **规划脚本读块内容时必须读备份原件**，不能读已被改过的成品文件（会读到改后的值）。
- 每次改完自校验：花括号平衡、`c_` 块数、`b_` 块数、单个 BOM、holder 是否都已定义、日期是否升序。

## 县首府 & c 级国家（★ 2026-10-16）
- **县首府 = `common/landed_titles/00_landed_titles.txt` 里该县下第一个 barony**（不是 definition.csv / province id）。
  要改首府就调 barony 顺序，把新县主的城市 `b_<X.capital>` 提到第一位。
- **`c` 级国家在 mod 里没有自己的头衔**（title map note：`country-below-county-rank: its land is its counties`），
  "作为国家存在"完全靠持有那个伯爵领 —— 所以把县换主会让它消失。
  要让自由市（WRM/BSC/ULM/NUR 等）留下来，就**改伯爵领首府**，让它在原县里保留自己的城市男爵领。
- 改县主 = 两件事一起做：`history/titles` 换 holder（整条链）+ `landed_titles` 换首府 barony。

## 东南亚政体（★ 2026-10-18 定稿，取代"单县无附庸判村社"）
- 判据 = EU5 政府改革 `mandala_system`（`in_game/common/government_reforms/country_specific.txt`，
  `major = yes`，potential = 首都 `sub_continent:south_east_asia` + dharmic/theravada/mahayana/satsana_phi）。
  - 有 → CK3 `mandala_government` + 县首府 `temple_citadel_holding`
  - 其余一律 → `wanua_government` + 县首府 `tribal_holding`
- **`reforms` 写在 tag 的 `government = { ... }` 里，且大半由 `include = "模板"` 带入**
  （`main_menu/setup/templates/*.txt`）。**必须递归展开 include**：只 grep tag 块字面量只有 BTU/MYI 两个，
  展开后 **61 个 tag**。tag 自己写 `reforms` 覆盖模板。`indonesia_monarchy` 带 mandala，
  `indonesia_limited_monarchy` 不带。
- 区域 = `definitions.txt` 的 `south_east_asia` 子块（= indochina_region + indonesia_region，
  1586 location / 190 县 / 1038 barony province）。
- 覆盖 c_ 县持有者 + 只持 b_ 的男爵持有者；`gen_wilderness_holder` 跳过。
- 落点 `eu5_export/_apply_sea_governments.py`（幂等，排在 `_fix_politics_output.py` 之后）。
  实测 120 领主（60 mandala / 60 wanua）、188 头衔。地产只改已建的（none/wilderness 不动），
  等价于生成器 `Governments.CapitalHolding`。

## 东南亚政体判定（★ 2026-10-18）
- 判据 = EU5 政府改革 `mandala_system`（`government_reforms/country_specific.txt`，61 个 tag，靠
  `include = "模板"` 展开才数得全）。有 → `mandala_government` + `temple_citadel_holding`；
  其余 → `wanua_government` + `tribal_holding`。脚本 `eu5_export/_apply_sea_governments.py`。
- **区域 = `south_east_asia` + `melanesia_region`**（后者在 `oceania/pacific_islands` 下，不是 asia 的
  sub_continent）：1586 + 562 地点 = **2148 地点 / 236 县**。美拉尼西亚 46 县里只有 `c_doberai`
  有国家（马登 Maden / `MAD`），其余是荒野。
- `common/governments/zz_gen_wanua_government.txt` 的 `primary_heritages` = **8 组**：
  austronesian / shan / thai / tibeto_burman / austroasiatic / papuan / micronesian / polynesian。
- **`VTN` 是万象 Vientiane（老挝），不是越南；越南 tag = `DAI`**（大越）。
- **`government = meritocratic` 的国家一律豁免**：全图只有 DAI（越南）和 KOR（高丽），
  保持 `meritocratic_government` + `castle_holding`。越南没有 `mandala_system`，
  不豁免就会被"其余→村社"吞掉。高丽不在 SEA 区，但同一豁免写死。
- ★ **不要按 tag 缩写猜国家**，认国家读 `eu5_politics.json` 的 `name_en` / `name_zh`。
- ★ 县没有 `1337.1.1` 条目（领主死在中途、没写继承人）时 = 开局无主，**不能给它写政府**；
  `holder_at_1337()` 必须只认 1337 条目，不能取"最后一个日期的 holder"（曾因此在 `c_bomberai` 崩）。

## 工作方式约定（用户）
- 先讲判断再动手；一次做完，不要半吊子中间态。
- 改成品 → 再回改脚本，使重跑结果一致。
- 报告要给数字和文件名。
- 备份：重大操作前备份；但既然有 git，不要无限膨胀。

## rite 判定方法论（★ 2026-10-16 定稿，替代旧「按文化分」）
- **按国家分**：人物 id 前缀 = 国家 tag 小写（`bul_chaka`→BUL；`eu5_regent_<tag>`/`eu5_rep_<tag>` 也认，tag 在第 3 段）。
- **国家按礼仪语言/教法学派分**：
  - 基督教 `liturgical_language`（EU5 `10_countries.txt`）：church_slavonic→slavic_rite、
    koine→byzantine_rite(主礼不写)、geez→ethiopian_rite、armenian→armenian_rite。
  - 伊斯兰 `religious_school`：什叶 jafari/imamiya→imami、ismaili→ismaili、zaidi→zayidi、nizari/mustali/alevism/alawi；
    逊尼 hanafi/hanbali/maliki/shafii；ibadi→ibadi(父信仰 kharijite)。
  - ★ **伊斯兰法理判定优先用 `sharia_law`**（`laws = { sharia_law = <X>_policy }`，纯法理学派、无教团干扰，
    用户 2026-10-17 指出）。优先级：`sharia_law` > `religious_school`（后者混了神学派 maturidi/ashari 和苏菲
    教团 qadiri/chishti/mevlevi，不能直接定 madhhab）。唯一冲突：TUR(maturidi→hanafi_policy)、
    TDE(qadiri→shafii_policy)，恰好是历史事实（奥斯曼=哈乃斐、索马里=沙斐仪）。
  - 格鲁吉亚四国 GEO/IME/SME/AAI 没写礼仪语言 → georgian_rite（"看好格鲁吉亚礼就行"）。
- **波斯尼亚 BOS → 独立信仰 `bosnian_church`**（不是东正教 rite；EU5 里 BOS 的 religion 就是 bosnian_church）。
- **被异教徒统治找不到 rite 的县 → 相连信仰块地理传播**（province 级接壤 BFS，找最近同 religion 且已确定 rite 的县）。
  覆盖东正教（被逊尼/天主教/异教统治）+ 什叶派/伊巴德派（被逊尼统治，这是用户强调的重点）。
- ★ **父信仰匹配铁律**：owner/国家的学派（sharia_law 或 religious_school）必须与「县/人物 的 religion」父信仰
  一致才采用。逊尼县只认逊尼学派，什叶县只认什叶学派。否则「什叶国家统治的逊尼县」会被错定成什叶 rite
  （曾把麦加麦地那错定成 zayidi，修好后正确落到 hanbali）。
- **天主教伦巴第/爱尔兰/anglo_irish/AMA/toledo 特殊规则保持现状，不按国家礼仪语言**（ambrosian/insular/roman/mozarabic）。
- **主礼不写**：byzantine_rite（orthodox 的 main_rite）不冗余写；一性论内部差异（埃塞/科普特/安条克/亚美尼亚）
  是地域性，**不靠地理传播**，按文化+黎凡特地理兜底。
- 脚本：县层 `_apply_christian_rites.py`（东正/一性论/波斯尼亚）+ `_apply_islamic_geo_spread.py`（什叶/伊巴德地理传播）；
  人物层 `_apply_christian_rites_chars.py`（按 id 前缀→国家，含伊斯兰人物 rite）。三个脚本都幂等 + 无变化不写。
- ★ 地理传播的固有限制：只能找「最近的同宗教确定县」，无法保证历史分支正确（如呼罗珊被传播到里海沿岸的
  zayidi 而非历史上的 imami）。这类历史归属偏差要单独向用户披露。
- ★ 只用 `envs/gis` venv 跑邻接/栅格脚本（numpy+PIL）；管线脚本用裸 python（无 numpy）。
- ★ **CK3 的 faith/rite 两级结构**：`faith` 只有 **sunni / shia / kharijite**（定义在 `common/religion/faith_types/00_faith_types.txt`，
  每块首行 `main_rite = <key>`）；四大教法学派与什叶各派都是 **rite**（定义在 `common/religion/rite_types/00_rite_types.txt`，
  每项 `faith = <parent>`）。vanilla：`sunni→hanafi`、`shia→ismaili`、`kharijite→ibadi`。
  **本项目已把 `shia.main_rite` 改为 `imami`**（2026-10-17，理由：1337 年十二伊玛目派已是什叶主流）；
  该文件是 mod 里 vanilla 的全量拷贝，改它即覆盖 vanilla。sunni/kharijite 未动。

## 附庸关系与朝贡（`export_politics.py`）
- `relations[].ck3` 只有三种：`vassal` / `union` / `tributary`。C# `Emit/History/Eu5PoliticsWriter`
  和 `_fix_politics_output.py` **只读 json 的这个字段**，不自己重算 → 改 `export_politics.py` 一处即全链路。
- `tributary` 在 CK3 里靠 `common/on_action/zz_eu5_tributaries.txt` 开局 effect
  （`break_subject_contract_and_establish_tributary_effect`）建立，**双方必须都是独立统治者**
  （limit `is_independent_ruler = yes`），所以 tributary 国家在头衔历史里不能有 `liege =`。
- ★ **两个判定必须分开（2026-10-18 血泪）**：
  - `tributary_by_nature(vassal, lord)` = 曼陀罗地区（SEA_TAGS）+ GRM，**这是 `raised`/`lowered`/
    `own_vassals` 推断头衔等级的依据**；
  - `written_as_tribute(vassal, lord)` = 上面这个 **or `is_horde(vassal)` or `is_horde(lord)`**，
    只在写最终 `ck3` 字段时用。
  把 horde 直接加进前者会连带改等级（实测 CRS d→None、QCH d→k）。用户要求"游牧底下改朝贡，
  **头衔等级不变**"，所以拆开。36 个 `steppe_horde`，60 条 vassal→tributary，rank 零变化。

## 东南亚村社制（2026-10-18）
- CK3「村社制」= `wanua_government`（vanilla TGP）。判定脚本 `eu5_export/_apply_sea_wanua.py`，
  挂在 `run_ei2_variant.ps1` **最后**（`_fix_politics_output.py` 之后，因为后者会重写
  `zz_eu5_government.txt`）。规则：SEA 地区（EU5 `indochina_region`/`indonesia_region`）内，CK3 只持
  1 个 `c_` 或 1 个 `b_`、且该人对应 EU5 tag 不在 relations 的 `first`（无 vassal/朝贡）→ 政府 wanua、
  地产 tribal。实测 83 人（44 单县 + 39 单男爵）。
- ★ **必须覆盖 `wanua_government`**：vanilla 的 `primary_heritages = { heritage_austronesian }` 与 mod
  生成文化的 `austronesian_group` 一套 heritage key 对不上，不覆盖则 wanua 对全图 invalid。
  覆盖文件 `common/governments/zz_gen_wanua_government.txt`（五个组：austronesian/shan/thai/
  tibeto_burman/austroasiatic），做法同 `zz_gen_japan_government_types.txt` 去掉 heritage_japonic。
- `required_county_holdings` 只约束建造、不是政府合法性；39 个男爵都不是县首府，所以改他们不动县主的
  mandala `primary_holding`。

