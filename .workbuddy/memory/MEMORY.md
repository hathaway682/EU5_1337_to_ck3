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
- **CK3 province id** 只在 `history/titles/zz_eu5_titles.txt` 的 `b_x = { province = N }`（≠ mapping 里 b_x 的 province，那是 EU5 location id）
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

## 工作方式约定（用户）
- 先讲判断再动手；一次做完，不要半吊子中间态。
- 改成品 → 再回改脚本，使重跑结果一致。
- 报告要给数字和文件名。
- 备份：重大操作前备份；但既然有 git，不要无限膨胀。
