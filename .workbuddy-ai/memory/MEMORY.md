# 项目长期记忆（EU5_Modern_Borders_noshape）

> 每日细节在 `.workbuddy-ai/memory/YYYY-MM-DD.md`；这里只放长期有效的口径、坑与纪律。

## 一、宗教 / faith / rite
- 地理树 `EU5/game/in_game/map_data/definitions.txt`（tab 缩进）**必须栈解析**：`next(x for x in reversed(stack) if x.endswith(("_region","_area","_province")))`；只认行内列表只能解析到 17032/27418。易错：`andaman_province`→north_sumatra_area、`sumatran_islands_province`→south_sumatra_area、苏拉威西 area=`celebes_area`、米佐丘陵在 bengal_region 下叫 `hill_area`。
- faith 映射表（religion→faith 逐宗教整体落）：`Global_modern_map/eu5_export/eu5_ck3_faith_map_zh.csv`（293 行带中文）；**三表必须同步**：`_build_faith_map.py` CURATED / CSV / `_apply_*_faith.py` REL_RULE——加 CSV 不等于省会变。已映射 195 / 保留 pagan 98。中文名别混：CK3 `satsana_phi`=守护灵教，EU5 同名宗教叫丕教。「门顿教」是 religion 名（`mundhum_religion`）。
- 落盘坑：省只写 `faith` 无 `rite=` 时按 faith 的 main_rite 回落；印度教分化必须**整县染色**（`_apply_hindu_faith_cu.py`）；反复踩的坑是**按县判定、按省落地**（戈尔甘、库法、西沃里尼亚、吉赞/希尔达、多贝亚/锡达莫）；写盘必须**保 CRLF**（rb→decode→split→join→encode，不要 replace \n）；保存点用 `gen_debug/_religion_checkpoint.py`。
- 国家宗教看 `setup/countries/*.txt` 的 `religion_definition`，`religious_school` 只是教法学派；判学派看 `common/religious_schools/*.txt` 的 `enabled_for_country`。什叶国家 22 个（含 maliki 2：BKZ/SKN，已按用户指示改 sunni+maliki）。跨宗教执政全库 201 人。
- 宗教兜底链：pops 人口多数 → location 自己的 religion 标注 → 同省其它 location 多数。`location_templates.txt` 20918 个 location 带 religion。

## 二、CK3 数据结构约定
- 术语红线：CK3 说**伯爵领/男爵领**，EU5 说**省份/地点**。**CK3 只读伯爵领块内第一个 b_ 当首府**，faith/culture/holding/县易主全跟随它。
- dynasty=宗族、house=支系；COA 按 key 自动匹配。统计文化引用必须 `re.finditer(r'(?<![a-z_])culture\s*=\s*(\w+)', line)`。角色块解析先按大括号深度切顶层块。

## 三、文化分类工具链（顺序不能错）
`_classify_cultures.py` → `_annotate_zh_in_classification.py --apply` → `_culture_classification_report.py`。CK3 原版 22 个「0 省份文化」不能当落点（gothic/ancient_egyptian/hebrew/…old_saxon）。

## 四、CU 对照表（用户说「按 csv 分」指这个）
`gen_debug/_cu_vs_ours.csv`：2858 行=2858 个 EU5 province。口径：**先把 cu_rite 挂到整个 EU5 province，再按 location 数取主体**；拿 barony 名直接匹配只命中首府一格。

## 五、生成器纪律
- 用户手改文件绝不覆盖；写前比对内容，无变化不动 mtime，有变化才备份。生成物按 key 排序、带 BOM；脚本默认 dry run。
- **非必要不全量重建**（补丁层会被冲掉），外科手术式只改目标行；**避免无谓干跑和验证仪式**，跑完直接交付。
- **诊断类任务默认只读**，报告结论+改法，等用户说「改」才动手。行号一律用【文件绝对行号】。
- **被否/被取代的错误文件当场删**；新建文件先查路径是否被占用（zz_ 前缀不是无人区）。
- EU5 人名/复合名先查 EU5 自带角色名表，以 EU5 译名为准。游戏安装目录只读，产物一律放工作区。

## 六、EU5 角色名本地化
每个 name 部分是独立 key，合成名按 EU5 部分拼接（中文无分隔符、英文空格）；脚本 `gen_debug/fix_compound_names.py` + `verify_compound_names.py`。

## 七、Git
master=发布分支（EU5 纹章在 eu5-coa 分支），远程 github.com/hathaway682/EU5_1337_to_ck3；用户用 GitHub Desktop 提交，push 前必 fetch。**禁止 git worktree**；跨分支带改动用 plumbing 零检出。staging 前先 `git status` 核对，只能逐个 add。

## 八、存档：已完成分期，勿重做
168 支系→42 宗族（`zz_eu5_merged_houses.txt`）；`dynn_Anjou`=安茹用 `anjou_jerusalem`、`dynn_Robertine`=罗贝尔用 `robertian`、`dynn_Angevin` 是坑；154 个复合君主名 11 语言重译；宗族层对齐原版完成。宗教匹配收尾（用户确认成功）；4361 个原始宗教人物改写 religion；印度教整县染色重跑；BKZ/SKN 7 角色改 maliki。
**待用户定的遗留**：① BKZ/SKN 库西雅 7 省 rite；② 10990 个角色 religion=pagan 但文化主体是基督教/伊斯兰/佛教；③ 244 个印度教省所在县 CU 记耆那教（宗教层级差异）。

## 九、伯爵领首府规则（BaronyOrder rank_state）
- 生成器 `Global_modern_map/eu5_export/_capital_correct.py`（`--barony-order`：id / rank_pop / rank_state）。**CK3 只读伯爵领块内第一个男爵领当首府**。
- rank_state：definitions 首府领主是 minor（全地在一省 + rank≤county + 非瑞士联邦含 ZUR）而县里有大势力时移首府；过半守卫→附庸守卫（只查直属封君）→名称命中（`name_match_pick`，只看大势力的同名镇）→seated→占地最多者的最大镇；主教区/骑士团飞地单独一支；`seat_names_county`（县名=首府镇名，读 EU5 本地化）永不搬。
- **链路四步**：① `_capital_correct.py --barony-order rank_state` → ② `_apply_rank_state_seats.py --old-picks <旧json>`（只动 old∪new picks 的县，**其余县原样不动**——手改首府因此能活）→ ③ `export_politics.py` → ④ `_reassign_counties.py --mod <mod> --export .`（先 dry-run）。**第⑤步**：④ 会把土司县写成 feudal，必须重跑 `_apply_tusi_governments.py --apply`。**第⑥步**：④/② 会冲掉 HRE 5 县，必须重跑 `fix_holstein_denmark.py`（2026-10-22 起链路是六步）。
- **★ fallback 真多数规则（2026-10-22 用户拍板"试试"后实施）**：major 要从 minor 处拿走伯爵领，地数须**严格大于县内任何其他单个持有者**（含在座 minor，**不要求过半**）。实现位置 `_capital_correct.py` fallback 分支：`big, ground` 出来后统计全县 `every` 各持有者地数，`len(ground) <= max(其他)` 则 continue。效果：fallback pick 67→36（31 个县留原首府领主，如 c_lower_styria 全县留 CLI/首府 celje）；重跑 `fix_holstein_denmark.py` 后 RANK_STATE=41。回归探针 `Global_modern_map/eu5_export/_probe_majority.py`（只读，复刻 rank_state 全逻辑）。
- **`_reassign_counties.py` 排除名单** `<mod>/gen_debug/eu5_reassign_keep.json`（BOM+CRLF）：列名 title 一律不碰。现 12 项：c_holstein/b_kiel（丹麦摄政安排）+ c_chrudimsko/c_hanover/c_lippe/c_luneburger_heide/c_neuchatel 及其新首府 b_chrudim/b_hanover/b_paderborn/b_luneburg/b_basel。
- **★★ 土司首府两条规则：2026-10-22 已全回滚，作废勿再实施**（"土司相关全回滚，你的改动很失败"）。`_capital_correct.py` 无土司代码、RANK_STATE=67 picks、mod 树两文件与 HEAD 逐字节一致。**嘉绒问题回到起点**（c_gyelrong 首府=打箭炉/明正 CKL）。
- **★ HRE 同名首府规则（2026-10-22，`gen_debug/fix_holstein_denmark.py` 第 3 节，与丹麦摄政同一个脚本）**：HRE 境内（县内每个 location 持有者都是 HRE 成员，members 读 eu5_politics.json `organizations type=hre`）首府强制划给同名男爵领（EU5 中文本地化：镇名=县名或县名一片，单字不算）。5 个县：c_chrudimsko caslav→chrudim、c_hanover hildesheim→hanover（HDH→BRU）、c_lippe soest→paderborn（KOL→PDB，覆盖原 rank_state pick）、c_luneburger_heide dannenberg→luneburg、c_neuchatel delemont→**basel**（县显示名是"巴塞尔"，用户拍板"巴塞尔给巴塞尔"）。HDH 不消灭（还持 c_harz）。**脆弱点：将来跑 `_capital_correct.py rank_state` 会重算 RANK_STATE 冲掉这 5 个县，跑完链路必须重跑本脚本**（docstring 已写）。
- **fix_holstein_denmark.py 只写特殊伯爵领，不碰摄政**（用户："这里本来就不该负责添加摄政"）：丹麦摄政在 `history/characters/zz_eu5_diarchy_regencies.txt`（dan_valdemar_atterdag 1332.8.2 起 Gerhard 为 diarch、set_diarchy_swing=100），角色本体在 zz_eu5_characters.txt——再往 zz_eu5_regents.txt 插块就是重复定义。
- **既定约定（勿当 bug）**：export_politics「仍有县者不降男爵领」——还拥有别的县的国家，其在别县残余地不建 b_ 块。

## 十、地图可视化（ck3-mapviz skill）
「把 XX 画到世界地图上」一律先用 skill `ck3-mapviz`（scan/dump/diff/render/init，render 约 20s）。spec 里 `groups`+`color.mode="direct"`，`titles` 给头衔 id（county 默认 expand 整棵子树），产物 `_full.png`。**严禁自己算投影/质心打点**，按 province 色块涂色。统计出图前先看 `00_landed_titles.txt` mtime。
