# 项目长期记忆（EU5_Modern_Borders_noshape）

> 每日细节在 `.workbuddy-ai/memory/YYYY-MM-DD.md`；这里只放长期有效的口径、坑与纪律。

## 一、宗教 / faith / rite
- **地理树** `EU5/game/in_game/map_data/definitions.txt`（tab 缩进）必须栈解析：`next(x for x in reversed(stack) if x.endswith(("_region","_area","_province")))`；只认行内列表只能解析到 17032/27418。易错：`andaman_province`→north_sumatra_area、`sumatran_islands_province`→south_sumatra_area、苏拉威西=`celebes_area`、米佐丘陵在 bengal_region 下叫 `hill_area`。
- **faith 映射表**（religion→faith 逐宗教整体落）：`Global_modern_map/eu5_export/eu5_ck3_faith_map_zh.csv`（293 行带中文）；**三表必须同步**：`_build_faith_map.py` CURATED / CSV / `_apply_*_faith.py` REL_RULE——加 CSV 不等于省会变。已映射 195 / 保留 pagan 98。`satsana_phi`=守护灵教（EU5 同名宗教叫丕教）；「门顿教」是 religion 名（`mundhum_religion`）。
- **落盘坑**：省只写 `faith` 无 `rite=` 时按 faith 的 main_rite 回落；印度教分化必须**整县染色**（`_apply_hindu_faith_branch.py`）；反复踩的坑是**按县判定、按省落地**（戈尔甘、库法、西沃里尼亚、吉赞/希尔达、多贝亚/锡达莫）；写盘必须**保 CRLF**；保存点用 `gen_debug/_religion_checkpoint.py`。
- **东亚系 rite 分配**（`_apply_sect_rite.py`）：按 EU5 `main_menu/setup/start/15_international_organizations.txt` 的 23 个 `type = sect` 实例成员分，**sect 身份 = laws 首个元素**（后两个是共享次级 law）。用户拍板：**DAI/KOR→dhyana、SSG→sukhavati**。**vajrayana_faith 的 main_rite 已改 lamaism**（faith_types 第 358 行），藏传五派+觉囊成员的省自动落 lamaism 不写行；根本说一切有部 10 成员（BUS/INR/JMB/PLB/PNI/SGT/PAH/MUA/MYI/PGS）52 省写 `rite = vinaya`。rite/faith 不符一律走主流兜底。**confucian_faith 无 main_rite**，由 `history/faiths/00_eastern_misc.txt` 按日期定（867=jingxue、1066.9.15=daoxue），1337 开局=daoxue；maitreya_faith 同理。
- **佛教传播三层**（`_apply_buddhist_geo_spread.py`，用户拍板）：① 接壤 BFS；② **近距离隔空/跨海：质心直线 ≤ 300 km**，中间隔海或隔异教省都行，**只做一步不递归**；③ **阿吒力教特批跨 faith 替换 mahayana**——`acharya` 绑 vajrayana_faith，写入时**删 `faith = mahayana_faith` 行、只留 `rite = acharya`**（按「有 rite 就不写 faith」）。源省 = mahayana_faith + 已有具体宗派；acharya 的 8 个省没有 faith 行，必须从 `prov_rite` 单独捞（`ACHARYA_SOURCES`）。待补 = mahayana_faith 无具体宗派 + **owner 非佛教国家**；owner 是佛教国家的省不动 = **保留主流大乘兜底（用户「高昌可不动」）**。父信仰守卫：mahayana 系 7 个 rite 只写 mahayana_faith，vajrayana 系 5 个只写 vajrayana_faith。传播不到不是 bug（孤岛/被异教隔断）。
- **质心缓存 `_ck3_province_centroid.json`**：`_build_province_centroid.py` 从 `map_data/provinces.png`（16384×8192，step=2）算，28569 省。**json 的 int 键读回来会变字符串，必须 `{int(k): v ...}`**。换算：宽 16384 px = 360°，赤道 1 px ≈ 2.446 km，经度按 cos(lat) 收缩（**注意：本 mod 投影并非严格等距圆柱，绝对经纬度不可信，只用相对距离**）。
- **CU（CrusaderUniversalis）取数四层，缺一不可**：mod 在 `E:\SteamLibrary\steamapps\workshop\content\1158310\3811443965`，`history/provinces` 176 文件 / 3071 省块（其中**只有 2540 个真写了 faith/rite**）。① 两张地图**是同一张**（都 16384×8192、definition.csv 都 28574 色/28569 省），**province id 和颜色不同但色块形状相同** → 质心最近邻匹配（`_match_cu_by_shape.py`，**容差 6 px + 按距离升序贪心唯一分配**；2.5 px 会漏掉长江沿岸 12 个有头衔省，因为 CU 把长江画成航道后色块质心偏移 3-5 px，用户 2026-10-22 指出；现 **匹配 99.99%，28567/28569**，只剩 6132、23707）；② **CU 伯爵领首府上色整个伯爵领** → 用 CU 自己的 landed_titles 铺满（4138 伯爵领 / 2514 有值 → 12223 省）；③ **两 mod 伯爵领法理不同，绝不能按 county 名 join** → 必须「CU 伯爵领 → CU 省 → 质心映射 → 本 mod 省」；④ **★★ `history/province_mapping/00_cu_county_mapping.txt`（384 行）必须一起读**（2026-10-22 用户指出文登上清派才发现漏了）——头注释 `# Only current Gall-map county capitals; culture and faith/rite only`，每行 `A = B # c_xxx -> c_yyy` 表示**旧地图伯爵领 c_xxx（首府 A）的 faith/rite 取新地图 c_yyy（首府 B）**。384 行**右边全部有值**，其中 **382 个伯爵领原本被我们判成"无数据"**；**已补（2026-10-22）**：映射补入 382 伯爵领 → 本 mod **13999 省有值（49.0%）**，中日韩目标省 1824 里 **1816 有值（99.6%）**，只剩 8 省走兜底（原 234）。实例：`10495 = 10462`（c_wendeng → c_dengzhou），10462 的 1337 值是 `rite = quanzhen`（全真派），而 **quanzhen 的 faith = shangqing_faith，中文名「上清派」** → 游戏里文登显示上清派，用户说的对。`_cu_vs_ours.csv`（2858 行）**只是同名 barony 抽样（覆盖 20-30%），不要当全量**；用户说「按 csv 分」指的就是它，口径是「先把 cu_rite 挂到整个 EU5 province，再按 location 数取主体」。
- **CU 三教转换**（`_apply_cu_three_teachings.py`）：中国四 kingdom 的三教省 → CU 值属儒/道/佛/明教就用，否则禅宗兜底；朝鲜 mahayana 省按 CU、无数据禅宗兜底；日本 shinto 省按 CU、无数据神道兜底。共改 1824 省。**CU 对中国三教省覆盖率仅 39%（526/1351），825 省靠禅宗兜底，儒教省从 1345 降到 121**。**脚本不幂等**（改完 faith 行没了，重跑查不到目标），要重算必须先还原备份。
- **★★ `history/provinces/00_generated_provinces.txt` 是纯 CRLF**：`newline=""` 读入后每行尾带 `\r`，行级正则必须写 `^(\d+) = \{\r?$`，**插入的新行也必须自带 `\r`**；否则 stat 全空、误报「无变化」、或写出混合行尾。
- **EU5 `religion_definition = mahayana #Azhaliism` 的 `#Azhaliism` 是注释**，宗教值仍是 mahayana（`east_asia.txt` 1392/1400/2168 = YAN/HQG/CDL）；阿吒力教 sect 在 `15_international_organizations.txt:1362`，成员 `CDL YAN HQG`、`laws = { azhaliism_policy vajrayana_policy }`。
- 国家宗教看 `setup/countries/*.txt` 的 `religion_definition`，`religious_school` 只是教法学派；判学派看 `common/religious_schools/*.txt` 的 `enabled_for_country`。什叶国家 22 个（含 maliki 2：BKZ/SKN，已改 sunni+maliki）。跨宗教执政全库 201 人。
- 宗教兜底链：pops 人口多数 → location 自己的 religion 标注 → 同省其它 location 多数。`location_templates.txt` 20918 个 location 带 religion。

## 二、CK3 数据结构约定
- **★ 本地化永远比 key 值权威**（用户三次强调）：判断 rite/faith/头衔是什么，**先看本地化**，绝不按 key 字面意思脑补。`acharya` 从 key 看像「阿阇梨」，本地化实际是**阿吒力教**。原话："不要根据key值擅自下定论，本地化永远比key值权威，你没记住吗"。
- **★★ 本地化必须从原版找**（2026-10-22 用户纠正）：rite / faith / 中国头衔的中文名**基本都在 CK3 原版**，本 mod 的 `localization/` 里搜不到是正常的——**不要据此断言"这个词不存在"或"只存在于 EU5"**（踩过：查"上清派"在 mod 里 0 命中就误判成 EU5 专属，实际原版就有）。
  - 原版路径：`E:\SteamLibrary\steamapps\common\Crusader Kings III\game\localization\simp_chinese\`（**注意有 `game\` 一层**），宗教名在 `religion/religion_*_l_simp_chinese.yml`。
  - 查找顺序：**mod localization → 原版 localization → 问用户**，不许自己编名字。
  - 原版 rite 中文名速查（实测）：`dhyana`=禅宗、`vinaya`=律宗、`pundarika`=法华宗、`sukhavati`=净土宗、`yogacara`=唯识宗、`avatamsaka`=华严宗、`acharya`=阿吒力教、`shangqing`=上清派、`quanzhen`=全真派、`zhengyi`=正一派、`mingism`=明教。
  - **rite 是原版机制**，不是本 mod 自创：原版决议有 `GetRiteByKey('shangqing')`，原版 `history/provinces/h_china.txt` 就写 `rite = pundarika`。另注：原版 `h_china.txt:5542` 的 **8839 = 濮阳**，与本 mod 的 8839（文登）撞号，但 descriptor 有 `replace_path="history/provinces"`，原版不加载、不冲突。
- 术语红线：CK3 说**伯爵领/男爵领**，EU5 说**省份/地点**。**CK3 只读伯爵领块内第一个 b_ 当首府**，faith/culture/holding/县易主全跟随它。
- dynasty=宗族、house=支系；COA 按 key 自动匹配。统计文化引用必须 `re.finditer(r'(?<![a-z_])culture\s*=\s*(\w+)', line)`。角色块解析先按大括号深度切顶层块。

## 三、文化分类工具链（顺序不能错）
`_classify_cultures.py` → `_annotate_zh_in_classification.py --apply` → `_culture_classification_report.py`。CK3 原版 22 个「0 省份文化」不能当落点（gothic/ancient_egyptian/hebrew/…old_saxon）。
- **★ 检验「某文化有没有历史人物」要查源 key，不是目标 key**：拉丁（EU5 `roman_culture`）→ `roman`，查 `culture = roman` 得 0 个是错的；实际角色带源 key `roman_culture`，**62 个全是 `byz_*` 罗马皇帝**（卡利古拉…阿纳斯塔修斯，拜占庭头衔历史从公元 37 年排到 1337）。查「谁在用这个文化」必须查源 key，`history/titles/*.txt` 头衔持有者列表最直接（拜占庭 = `e_eu5_byz`）。
- **文化落地在分支 `culture_conversation`（提交 `2d0c041 欧洲`），master/pop 上没有**；那边省份/角色/宗族全是 EU5 原始 key，游戏里看罗马皇帝会显示「拉丁」而不是「罗马」。

## 四、生成器纪律
- 用户手改文件绝不覆盖；写前比对内容，无变化不动 mtime，有变化才备份。生成物按 key 排序、带 BOM；脚本默认 dry run。
- **非必要不全量重建**（补丁层会被冲掉），外科手术式只改目标行；**避免无谓干跑和验证仪式**，跑完直接交付。
- **诊断类任务默认只读**，报告结论+改法，等用户说「改」才动手。行号一律用【文件绝对行号】。
- **被否/被取代的错误文件当场删**；新建文件先查路径是否被占用（zz_ 前缀不是无人区）。
- EU5 人名/复合名先查 EU5 自带角色名表，以 EU5 译名为准。游戏安装目录只读，产物一律放工作区。

## 五、EU5 角色名本地化
每个 name 部分是独立 key，合成名按 EU5 部分拼接（中文无分隔符、英文空格）；脚本 `gen_debug/fix_compound_names.py` + `verify_compound_names.py`。

## 六、Git
master=发布分支（EU5 纹章在 eu5-coa 分支），远程 github.com/hathaway682/EU5_1337_to_ck3；用户用 GitHub Desktop 提交，push 前必 fetch。**禁止 git worktree**；跨分支带改动用 plumbing 零检出。staging 前先 `git status` 核对，只能逐个 add。

## 七、存档：已完成分期，勿重做
168 支系→42 宗族（`zz_eu5_merged_houses.txt`）；`dynn_Anjou`=安茹用 `anjou_jerusalem`、`dynn_Robertine`=罗贝尔用 `robertian`、`dynn_Angevin` 是坑；154 个复合君主名 11 语言重译；宗族层对齐原版完成。宗教匹配收尾；4361 个原始宗教人物改写 religion；印度教整县染色重跑；BKZ/SKN 7 角色改 maliki。
**待用户定的遗留**：① BKZ/SKN 库西雅 7 省 rite；② 10990 个角色 religion=pagan 但文化主体是基督教/伊斯兰/佛教；③ 244 个印度教省所在县 CU 记耆那教。

## 八、伯爵领首府规则（BaronyOrder rank_state）
- 生成器 `Global_modern_map/eu5_export/_capital_correct.py`（`--barony-order`：id / rank_pop / rank_state）。**CK3 只读伯爵领块内第一个男爵领当首府**。
- rank_state：definitions 首府领主是 minor（全地在一省 + rank≤county + 非瑞士联邦含 ZUR）而县里有大势力时移首府；过半守卫→附庸守卫（只查直属封君）→名称命中（`name_match_pick`，只看大势力的同名镇）→seated→占地最多者的最大镇；主教区/骑士团飞地单独一支；`seat_names_county`（县名=首府镇名，读 EU5 本地化）永不搬。
- **链路六步**：① `_capital_correct.py --barony-order rank_state` → ② `_apply_rank_state_seats.py --old-picks <旧json>`（只动 old∪new picks 的县，**其余县原样不动**——手改首府因此能活）→ ③ `export_politics.py` → ④ `_reassign_counties.py --mod <mod> --export .`（先 dry-run）→ ⑤ `_apply_tusi_governments.py --apply`（④ 会把土司县写成 feudal）→ ⑥ `fix_holstein_denmark.py`（④/② 会冲掉 HRE 5 县）。
- **★ fallback 真多数规则**（用户拍板"试试"后实施）：major 要从 minor 处拿走伯爵领，地数须**严格大于县内任何其他单个持有者**（含在座 minor，**不要求过半**）。实现位置 `_capital_correct.py` fallback 分支：`big, ground` 出来后统计全县 `every` 各持有者地数，`len(ground) <= max(其他)` 则 continue。效果：fallback pick 67→36（31 个县留原首府领主）；重跑 `fix_holstein_denmark.py` 后 RANK_STATE=41。回归探针 `_probe_majority.py`（只读）。
- **`_reassign_counties.py` 排除名单** `<mod>/gen_debug/eu5_reassign_keep.json`（BOM+CRLF）：列名 title 一律不碰。现 12 项：c_holstein/b_kiel + c_chrudimsko/c_hanover/c_lippe/c_luneburger_heide/c_neuchatel 及其新首府 b_chrudim/b_hanover/b_paderborn/b_luneburg/b_basel。
- **★★ 土司首府两条规则：2026-10-22 已全回滚，作废勿再实施**（"土司相关全回滚，你的改动很失败"）。`_capital_correct.py` 无土司代码、RANK_STATE=67 picks、mod 树两文件与 HEAD 逐字节一致。**嘉绒问题回到起点**（c_gyelrong 首府=打箭炉/明正 CKL）。
- **★ HRE 同名首府规则**（`gen_debug/fix_holstein_denmark.py` 第 3 节，与丹麦摄政同一脚本）：HRE 境内（县内每个 location 持有者都是 HRE 成员）首府强制划给同名男爵领（EU5 中文本地化：镇名=县名或县名一片，单字不算）。5 县：c_chrudimsko caslav→chrudim、c_hanover hildesheim→hanover（HDH→BRU）、c_lippe soest→paderborn（KOL→PDB）、c_luneburger_heide dannenberg→luneburg、c_neuchatel delemont→**basel**（用户拍板"巴塞尔给巴塞尔"）。HDH 不消灭（还持 c_harz）。**脆弱点：将来跑 `_capital_correct.py rank_state` 会重算冲掉这 5 个县，跑完链路必须重跑本脚本。**
- **fix_holstein_denmark.py 只写特殊伯爵领，不碰摄政**：丹麦摄政在 `history/characters/zz_eu5_diarchy_regencies.txt`（dan_valdemar_atterdag 1332.8.2 起 Gerhard 为 diarch、set_diarchy_swing=100），角色本体在 zz_eu5_characters.txt——再往 zz_eu5_regents.txt 插块就是重复定义。
- **既定约定（勿当 bug）**：export_politics「仍有县者不降男爵领」——还拥有别的县的国家，其在别县残余地不建 b_ 块。

## 九、地图可视化（ck3-mapviz skill）
「把 XX 画到世界地图上」一律先用 skill `ck3-mapviz`（scan/dump/diff/render/init，render 约 20-25s）。spec 里 `groups`+`color.mode="direct"`，`titles` 给头衔 id（county 默认 expand 整棵子树），`provs` 直接给省 id，产物 `_full.png`。**严禁自己算投影/质心打点**，按 province 色块涂色。统计出图前先看 `00_landed_titles.txt` mtime。CU 覆盖类图脚本：`_make_cu_world_spec.py`（三档：直写/伯爵领继承/无数据）、`_make_cu_target_spec.py`（中日韩目标省）。
