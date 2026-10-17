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
  ③**非瑞士联邦成员**（BRN LCU SYZ URI OBW）。三条全满足才算
- **`country_rank` 缺失 = 伯国**（**1632** 个没写）。写死 `=="county"` 会漏
- 首府被它占着 + 同县有重要势力有地 + 它不是这些势力的封臣 → 改派
- ★ **首府名 = 县名（或为其子串）的县永不改派**（用户加）：`.lower()`、单向，pick 后**最后**过滤，压过其余
- 实测（ei2）：不重要势力 897，改派县 139 → **78**（61 县被上一条挡下，含 lubeck/saluzzo/lucca/namur）
- **已落地**（2026-10-18）：旧 139 条存 `RANK_STATE.json.bak_139` 当 `--old-picks`；
  导出树 + 两份产物树各 `reverted 61`；`export_politics.py` 重算后 `c_lubeck`=LUB、`c_saluzzo`=SAL；
  `_reassign_counties.py` 落地（D 56 县 / F 65 县，其中 6 个是释放县、50 个是上轮游牧修复的尾巴）；
  全 3819 县首府 == export capital、县主 == export ruler，0 不符
- 工具链：`_capital_correct.py --barony-order rank_state` → `export_politics.py` →
  `_apply_rank_state_seats.py --old-picks <旧.json>` → `_reassign_counties.py` →
  **末了必跑 `_apply_sea_governments.py`**
- ★ `_capital_correct.py` 对「不再改派」的县不还原顺序
- ★ `export_politics.py` 的 stamp `files` 须含 `RANK_STATE.json`

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

## 工作方式约定（用户）
- 先讲判断再动手；一次做完，不留半吊子中间态。改成品 → 再回改脚本
- **诊断默认只读**，先报告 + 给改法，等说"改"才动手
- 报告给数字和文件名；重大操作前备份（有 git 就别无限膨胀）
- 全量生成**别一遍遍重复**，第一遍有问题直接汇报
- 别按 tag 猜国家；别顺手扩大任务范围
