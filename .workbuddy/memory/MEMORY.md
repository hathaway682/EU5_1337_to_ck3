# 项目长期记忆 — EU5_Modern_Borders_noshape

## 路径
- 成品 mod（就地改，已 git init，忽略 `/gfx`）：`…\Crusader Kings III\mod\EU5_Modern_Borders_noshape`
- 生成器（无 git，`_backup_*` 不可恢复）：`…\mod\Global_modern_map`；C# `newest/ck3procedural-main/`，Python `eu5_export/*.py`
- 并行产物 `F:\EU5_Modern_Borders_rank_state_ei2`（ei2，3819 县）。**游戏安装目录只读。**

## 开局日期（★2026-10-18 定稿）
- **EU5 开局 = `1337.4.1`**（原版 `loading_screen/common/defines/00_defines.txt`：`START_DATE = "1337.4.1"`）
- mod 曾全线写死 `1337.1.1`：3 处书签声明 + 4 个历史文件共 **7801** 条日期戳
- 另有 4 条真实日期落在 1337.1.2–1337.4.1，当前**晚于**书签 → 变"未来历史"，开局后才触发
- 生成端写死点（改日期须全同步，否则正则失配）：`Config/MapConfig.cs:361`（`StartDate => $"{StartYear}.1.1"`）、
  `export_politics.py:393`、`_export_title_map.py:33`、`_apply_horde_vassal_fix.py:32`、`_apply_sea_governments.py:154/163/168`

## 数据口径
- **政治 setup 只读「原版」EU5** `game\main_menu\setup\start\`（05 characters / 06 pops /
  07 cities / 10 countries / 12 diplomacy / 15 organizations）。workshop mod 只给
  `in_game/map_data` + 本地化，**内容不同，别混用**
- 伯爵领名 ← `eu5_titles_l_simp_chinese.yml` 的 `c_*`；县内 location ← `mapping.json` `locations[]`；
  首府 ← `eu5_politics.json` `counties[c].capital`
- 人口 ← `06_pops.txt` 的 `size=` 之和；海陆 ← `definition.csv` 第 5 列 `prov_*`/`sea_*`
- ★ CK3 province id（`b_x = { province = N }`，1-21046）≠ mapping.json 里 b_x 的 province（EU5 location id）
- ★ province 邻接 `_ck3_province_adjacency.json`（50913 对）；provinces.png 像素 = definition.csv 的
  RGB，**不是** R+G*256+B*65536；链路 = 像素 RGB →(definition 第0列)→ province id
- location 持有者 ← `export_politics.py` L574-582：`holds` 按 `OWN_ORDER` 取 (rank,tag) 最小；
  `control*` 只定归属不计大小
- HRE 成员 ← `relations[type=='hre'].second`（`first` 恒为皇帝 UBV）
- **11 个 location 名带大写国家后缀**（`targoviste_BUL`/`map_ASK`…）：正则用 `[A-Za-z0-9_]+`

## 县首府 & c 级国家（★血泪）
- **县首府 = 该县下第一个 barony**（不是 definition.csv / province id）
- **`c` 级国家没有自己的头衔**，靠持有那个伯爵领存在 → 换县主会让它消失。
  要留自由市（WRM/BSC/ULM/NUR）→ **改伯爵领首府**，让它在原县保留自己的城市男爵领
- 改县主 = `history/titles` 换 holder（整条链）+ `landed_titles` 换首府 barony

## 头衔历史铁律
- 县块历史链 = **该县持有者的统治者序列**；**领地改派 → 整条链换成新县主 X 的 `rulers`**
  （`ruler.start = { holder = ruler.character }`，**日期升序**；末尾 `1337.4.1`；X 无 rulers → 只留一条）
- 降级为男爵的原县主 O：男爵块 holder 取 `gen_debug/eu5_ck3_title_map.csv` 的 `ck3_holder`
- 正则带 `re.S`；替换整块**补回闭括号 `}`**；规划脚本读**备份原件**
- 自校验：花括号平衡、块数、单个 BOM、holder 已定义、日期升序
- `zz_eu5_titles.txt` = **UTF-8 BOM + CRLF**，正则用 `\r?\n`

## rank_state 判据
- 「不重要势力」= ①location 全在同一县 ②**等级是伯国，或 setup 没写 `country_rank`**
  ③**非瑞士联邦成员**（BRN LCU SYZ URI OBW）+ **ZUR 苏黎世**。四条全满足才算
- **`country_rank` 缺失 = 伯国**（**1632** 个没写）。写死 `=="county"` 会漏
- 首府被它占着 + 同县有重要势力有地 + 它不是这些势力的封臣 → 改派
- ★ **首府名 = 县名（或为其子串）的县永不改派**（用户加）：`.lower()`、单向，pick 后**最后**过滤，压过其余
- ★ **ZUR 为什么进豁免**（2026-10-18）：苏黎世 1337 未入瑞士联邦，只持有 `zurich` 一处 → 被判 minor，
  `c_thurgau` 首府被推到 `frauenfeld`（HAB 的城）→ 整县变奥地利。加进豁免后首府回 `zurich`、县主 ZUR
- ★ **本地领主严格过半 → 不让位**（用户为锡金加的）：`2 * 本县持有数 > len(lst)` 即撤掉改派。
  分母是**县内全部地点**（含有主/无主），代码位置在 vassal 检查之后、`cand` 之前。
  实测挡下 **33** 个县，含 `c_sikkim`（SKK 4/5 被 TIB 1/5 夺）、`c_garhwal`（7/9 被 1 夺）、`c_torino`、`c_oberwallis`
- ★ **飞地神权国让位**（用户为条顿加）：首府领主 `government == theocracy`、**在本县只占 1 地**、
  主教座（`countries[tag].capital`）**不在本县**、县内最大势力占 ≥2 → 让给该势力人口最大的城。
  `theoc` 从 `eu5_politics.json` 读（government 模板已由 export_politics 展开；capital 来自 setup，不回环）。
  实测 **6** 县：`c_tauberfranken`→UFF(crailsheim)、`c_ober_dem_wienerwald`→HAB(amstetten)、
  `c_vosges`→LOR(darney)、`c_flaming`→SWB(schweinitz)、`c_lower_carinthia`→HAB(klagenfurt)、
  `c_upper_carinthia`→GOR(lienz)
- ★ **不要用 `eu5_politics.json` 的 `counties.capital` 当「原首府」做诊断**：那是上一轮产物，
  已被规则改过（锡金/利珀/下施蒂里亚就是这样被误判成飞地）。原首府只认 `definitions.txt` 的第一个 location
- ★ **候选顺序 = ①首府在本县的主要势力 ②否则占多数的势力**（2026-10-18 第四轮，用户：
  "先看首都在这里的主要势力……再看占多数的"）：
  ①`countries[t].capital` 所在县 == 本县且该城由 t 持有 → 它的首府城当首府（并列按 本县持有数 → 首府人口）；
  ②否则县内非 minor 势力里持有地最多者（并列比人口和），取**它的最大城** ——
  不再是"所有主要势力里人口最大的城"（那会把县交给只占 1 城的飞地采邑主教）。
  起因：特里尔 TRI 的座堂城 `trier` 在 `c_hunsruck`，首府却被推到 `merzig`(LOR)，大主教无县可坐。
- ★ **`leads_here` 已删除**（同轮，用户："你没必要特意保采列和利珀……不如给了奥地利"）。
  连带：`c_lower_styria`→**HAB 奥地利**(slovenj_gradec)、`c_lippe`→KOL(soest)、`c_harz`→HDH(alfeld)、
  `c_middle_weser`→MUN(vechta)。**别再自作主张加回"保护某个小领主"的判据**。
- ★ **不要用 `eu5_politics.json` 的 `counties.capital` 当「原首府」做诊断**：那是上一轮产物，
  已被规则改过（锡金/利珀/下施蒂里亚就是这样被误判成飞地）。原首府只认 `definitions.txt` 的第一个 location
- 实测（ei2）：不重要势力 897，改派县 139 → 78 → 68 → 64 → **68**
- **已落地**（2026-10-18，四轮）：备份 `RANK_STATE.json.bak_139` / `.bak_78` / `.bak_68` / `.bak_64`；
  末轮 `still moved 68`，两份产物 `_apply_rank_state_seats.py --old-picks .bak_64` 各 `moved 20`，
  全 3819 县首府 == export capital、县主 == export ruler，0 不符；树 1853184 B / `{51248}`；
  history D 1402187 B `{29391}`、F 1403322 B `{29371}`
- ★ **男爵领 = 自己的首都**（2026-10-18 定）：`export_politics.py` 给「无县小国」派男爵领时，
  **先看 `countries[tag].capital`**，首都在哪个有地的县就坐哪个县、就坐首都本身；首都是别人的县首府
  或不在其有地的县 → 才退回人口最大。改前是纯人口最大（698 块里 94 块没落在首都，采列拿
  `b_lasko` 而不是首都 celje、利珀拿 `b_detmold` 而不是 lippstadt）；改后 690/698 落在首都。
  县主的座不走这张表（持 `c_` 头衔 → 首府 `b_` 隐式归他）。
- 工具链：`_capital_correct.py --barony-order rank_state` → `export_politics.py` →
  `_apply_rank_state_seats.py --old-picks <旧.json>` → `_reassign_counties.py` →
  **`_sync_baron_holdings.py`（男爵领搬了，province history 的 holding 跟着搬）** →
  **末了必跑 `_apply_sea_governments.py`**
- ★ **sync 必须在 sea 之前**：sea 按 EU5 改革 `mandala_system` 判 mandala（比 export 的
  "monarchy+非伊斯兰"窄），会把不符的落点改回 `tribal_holding`；反过来跑会盖掉 sea 的结果
- ★ `_capital_correct.py` 对「不再改派」的县不还原顺序
- ★ `export_politics.py` 的 stamp `files` 须含 `RANK_STATE.json`

## 法理首都（★CK3 口径）
- **county 没有 `capital` 字段**：首府 = 块里第一个男爵领。**只有 duchy 及以上有
  `capital = c_xxx`**，那就是法理首都（不是"第一个子头衔递归"出来的）
- 我们的 EU5 国家头衔（无地 titular）在 `common/landed_titles/zz_eu5_titular.txt`
- 口径（用户拍板）：**`cap` = EU5 setup 的国家首都 → mapping.json 的 location→county，
  直接写那个县**。不看"首都归谁持有"、不挑人口最大的县
- ★ 坑：早先只建「县首府 → 县」映射，首都若不是它所在县的首府就查不到（德里
  `sargadwari` ∈ `c_central_doab`，首府是 etawah）→ 62 个头衔空着。已改 `_fix_politics_output.py`
  （吃 mapping 全映射 + 已声明块补写），产物侧用 `_fix_dejure_capital.py`（幂等）
- 未补（有意）：`k_gen_wilderness` / `e_ilkhanate` / `e_golden_horde` / `d_ryuukyuu_sea`
- 遗留未处理：`zz_vanilla_titulars.txt` 1562 条 `capital = c_gen_buamu_4`（该县不存在）

## 主头衔（primary title）
- `common/on_action/zz_eu5_primary_titles.txt`：`set_primary_title_to`，CK3 在同 tier 多title时自己乱挑
- 口径：**同 tier 多个 → 取他自己的 EU5 首都所在伯国/头衔**；d/k/e 走 `title_key[tag]`，
  伯爵级走 `c_<首都所在县>`（c 级国家没有自己的头衔键）
- 生成端 `_fix_politics_output.py` primaries 段；产物侧 `_fix_primary_counties.py`（幂等，合并原条目）
- ★ 解析现有条目的正则必须用 `.*?` + `re.S`（`\{[^}]*?` 跨不过嵌套的 `if = {`，会把已有条目全丢）
- 判定"他有更高头衔"要看 `gen_debug/eu5_titles_dropped.txt`：头衔被删 = 戴不上，仍算伯爵级
- 实测：伯爵级多县 **345** 人，能按首都定 **208/207**（D/F），其余 138 是 `eu5_regent_*`
  无 capital 或首都城在别人县里 → 未设，等用户定兜底口径

## 东南亚政体
- 判据 = EU5 改革 `mandala_system`：有 → `mandala_government` + `temple_citadel_holding`；
  其余 → `wanua_government` + `tribal_holding`
- **`reforms` 大半由 `include = "模板"` 带入，必须递归展开**（字面量 2 个 → 展开后 **61** 个 tag）
- 区域 = `south_east_asia` + `melanesia_region`（在 oceania 下）= 2148 地点 / 236 县
- **`government = meritocratic` 一律豁免**（只 DAI 大越、KOR 高丽）
- ★ 须覆盖 `wanua_government`：`common/governments/zz_gen_wanua_government.txt`，8 组 heritage
- ★ 县没有 1337 条目 = 开局无主，**不能写政府**；`holder_at_1337()` 只认 1337 条目
- **`VTN` = 万象（老挝），越南 = `DAI`**。★ 别按 tag 猜国家

## 附庸与朝贡（三层，分开）
- `relations[].ck3` ∈ {vassal,union,tributary}；C# `Eu5PoliticsWriter` 与 `_fix_politics_output.py`
  只读此字段 → 改 `export_politics.py` 一处即全链路
- `tributary_by_nature(v,l)` = 曼陀罗地区(SEA_TAGS) + `l=="GRM"` → **用于推断头衔等级**
- `tribute_candidate(v,l)` = 上式 **or `is_horde(l)`**；方向只有「游牧领主→自己的下属」
- `is_free(tag)`：无 liege / 与 liege 同统治者 / 与 liege 按朝贡写且 liege 自由；HRE 与伊儿汗国成员 → 不自由
- `written_as_tribute(v,l)` = `tribute_candidate` **and `is_free(l)`**
- **朝贡靠 `common/on_action/zz_eu5_tributaries.txt` 开局 effect，limit 要双方 `is_independent_ruler = yes`**
  → 朝贡端头衔历史里**不能有 `liege =`**
- `lowered`：与宗主同级封臣降一级；改等级须**整键改名**（`_rename_title.py`）
- **stamp**：`files` 的 size+mtime 进 sha256，命中 `SystemExit(0)`。★ **脚本自身须在 `files` 里**
- `gen_debug/eu5_lieges.json`：tag → liege 头衔键，`_patch_title_history.py` 据此写 `liege =`
- 实测：vassal 899 / tributary 168 / union 27（总数 1094）

## rite 判定
- **按国家分**：人物 id 前缀 = tag 小写
- 基督教 `liturgical_language`：church_slavonic→slavic、koine→byzantine(主礼不写)、geez→ethiopian、
  armenian→armenian；格鲁吉亚四国 GEO/IME/SME/AAI → georgian_rite
- 伊斯兰 ★ **优先 `sharia_law`**，其次 `religious_school`
- ★ **父信仰匹配铁律**：国家学派须与县/人物 religion 父信仰一致才采用
- 被异教徒统治找不到 rite → **province 级接壤 BFS 传播**
- **BOS → 独立信仰 `bosnian_church`**；`shia.main_rite` 已改为 `imami`
- CK3 faith 只有 sunni/shia/kharijite，**其余全是 rite**

## 导出树就地重排的坑
- `_capital_correct.py` **就地重写** 00_eu5_landed_titles.txt，且把"我算出来就是这个顺序"当
  "文件已经对了" → 非目标县被排乱**永不被发现**。查法：逐县比 barony 顺序 vs mapping.json
  location id 顺序，排除 `RANK_STATE.json` 里的县
- 修单县顺序 `_restore_id_order.py --file <lt> --county <name>`：★ 重排须**保留县块头与第一个
  barony 之间的行**（县自己的 `color = {..}`）
- 产物完整性：看 `gfx/ gui/ localization/ events/` 四个目录

## 配准 / 经纬度（★2026-10-18 用户纠正，pagan 匹配翻车根因）
- **CK3 侧 province 图必须用 Miller 投影 mod 的图**：`E:\SteamLibrary\steamapps\workshop\content\1158310\2320354406\map_data\provinces.png`
  ＝ `F:\新建文件夹\ArcGIS_Miller_Gall_Georeference\miller_provinces.png`（3,875,348 B，同一份）。
  **绝不能用原版 `game\map_data\provinces.png`**——那个投影是 P 社乱拼接的（旋转/斜切）。
- **EU5 侧 = Gall 立体投影**：`F:\新建文件夹\ArcGIS_Miller_Gall_Georeference\gall_provinces.png`（8,737,202 B）
  ＝ `Global_modern_map\eu5_export\provinces.png`。
- **正确变换 = `eu5_export\_georef.py` 的真反算**（Miller `miller_px_to_lonlat` / Gall `eu5_px_to_lonlat`）；
  参考实现 `_geo_bridge.py`（CK3 Miller 质心 → lonlat → Gall 像素 → EU5 location）。
- ★ **禁止用线性拟合 `v_ll`/`m_ll` 代替真投影**（`_apply_ck3_pagan_match.py` 就错在这）：
  vanilla 拟合 lon 混 `-11.686*y`、lat 混 `-9.390*x` 正是拼接图斜切的指纹；mod 侧 `lon≈359.6*x` 才正常。

## CK3 非洲 religion/culture 来源（★2026-10-18 用户：province_mapping）
- CK3 非洲的宗教/文化**不是**逐省写在 `history/provinces`，而是靠
  `history/province_mapping/00_{guinea,egypt,arabia,persia,sapmi,sri_lanka}.txt`：
  格式 `目标省 = 代表省`（如 `6992 = 6733`），被映射省**继承代表省的 culture/rite**，自己块里不写。
  实证：`6733 = { culture = malinke; rite = west_african_pagan }`（在 `k_mali.txt`），而 `6992` 在
  `history/provinces` 里**无块**。
- 覆盖不全/有脏：`00_arabia` 20 条中 9 条注释掉（不可通行）；`00_guinea` 344 条但有 **4 个源省映射到
  不同代表省**（如 `8141` 同时 `=6722` / `=8222`）；`xx = xx` = 恒等/未填。
  → **不能把 CK3 非洲当"每省都有具体原始宗教"的可靠源**。
- ★ 旧 `_apply_ck3_pagan_match.py` 直接读 `history/provinces` → 漏掉全部被映射省（如 6992），叠加投影
  错误，故全歪。注意 vanilla 用 `rite =`（如 `rite = west_african_pagan`），不是 `faith =`。
- ★ **覆盖率实测（2026-10-18）**：非洲 1466 省（32 个 k_* 王国历史 ∪ 00_guinea/00_egypt 映射）=
  有信仰 941（604 自带 + 337 映射）、冲突 5、**无人荒地 519（holding=none/空块）**、**真正缺信仰仅 1（685）**、pagan 616。
  撒哈拉以南（guinea/ghana/mali/jenne/takrur/songhay/gur/gurma/hausaland/igbo-benue/yorubaland/akan/kanem/
  borgu/sao/kong/darfur）**100% 自带、0 缺口**；"none" 全在北非/东非（maghreb/egypt/nubia/abyssinia/adal…）
  且几乎都是荒地。→ **CK3 非洲人口省数据其实是齐的，"没填"是无人省**。

## 工作方式约定（用户）
- 先讲判断再动手；一次做完，不留半吊子中间态。改成品 → 再回改脚本
- **诊断默认只读**，先报告 + 给改法，等说"改"才动手
- 报告给数字和文件名；重大操作前备份（有 git 就别无限膨胀）
- 全量生成**别一遍遍重复**，第一遍有问题直接汇报
- 别按 tag 猜国家；别顺手扩大任务范围
