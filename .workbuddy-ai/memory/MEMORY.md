# 项目长期记忆（EU5_Modern_Borders_noshape）

> 每日细节在 `.workbuddy-ai/memory/YYYY-MM-DD.md`；这里只放长期有效的口径、坑与纪律。

## 一、层级与数据源
- EU5：location→province→area→region；`definitions.txt`(tab 缩进) 必须栈解析 `next(x for x in reversed(stack) if x.endswith(("_region","_area","_province")))`。
- province 声明一行式，共 4149 province / 27334 location。`06_pops.txt` 的 `size` 是浮点人口，**要人口必须读它**；`eu5_county_peoples.csv` 只是 location 个数多数，不是人口。
- CK3 `b_<name>` 的 `<name>` = EU5 location 名；3725/3819 county 严格对应单一 province。质心缓存 `_ck3_province_centroid.json` 的 **int 键读回必须 `{int(k): v}`**。

## 二、CK3 数据结构约定
- 本地化永远比 key 权威；先 `grep -rn "<key>" localization/simp_chinese/`。
- 首府 = 只读伯爵领块内第一个 b_；省份文件纯 CRLF；文化文件首行带 BOM（00_bantu/nakkavaram/somalian）。
- dynasty=宗族、house=支系；统计文化引用用 `re.finditer(r'(?<![a-z_])culture\s*=\s*(\w+)', line)`；角色块按大括号深度切顶层块。

## 三、文化（改前先看 skill `ck3-culture-pipeline`）
判据优先级：`CULT_RULE > 自动同名 > GROUP_RULE_STRONG > LANG_RULE > GROUP_RULE > 自动`。
- `GROUP_RULE_STRONG` 生效 = 该组排 `eu5_groups` **第一位**（非"只挂这一组"）；但**整体把 GROUP_RULE 提前到 LANG_RULE 是错的**（会改错 17 个）。
- **字典重复 key 会静默覆盖**：改 LANG_RULE/CULT_RULE 后必须用 ast 扫重复 key。
- 图内口径 = 原则上并入 CK3 原版文化；`NEW:` 前缀保留 EU5 key、落地脚本跳过。CU 图内已清零，图外约 610 个 EU5 key 按组收。
- 例外新建 `khoisan`/`malagasy`（CK3 原版没有）：定义手写 `common/culture/cultures/zz_eu5_culture_new.txt`，本地化 `zz_eu5_culture_new_l_simp_chinese.yml`，**不要写进 `zz_eu5_culture_merge.txt`**（被生成器覆盖）。
- 易错落点：arpitan→french（两处都写）；prussian 双义（省+人都要 skip，30 个波罗的普鲁士人勿改萨克森）；EU5 key 错位 azeri→turkish(乌古斯)、adhari/talysh→persian、zaza→kurdish（按 eu5_groups 分流，勿按语言）；草原带 steppe_group→cuman、不带→kipchak，balkar/karachay/kumyk 无 steppe_group→khazar；侗台三分 shan_dialect→tai、kam+kra→bouxcuengh；通古斯含 jurchen_group→jurchen、mongolic+tungusic→shiwei、仅 tungusic→mohe；khakas→uriankhai（勿动）；班图→east_bantu（swahili 显式保）；非洲收尾完整清单见 `_classify_cultures.py` 的 CULT_RULE（约 60 条，2026-10-27）。
- 文化本地化不带「人」，且要同时改 `zz_eu5_culture_merge_l_simp_chinese.yml` 与生成器 LOC 模板。

## 四、宗教（改前先看 skill `ck3-religion-pipeline`）
- 判 rite 能否挂省看 religion 不看 faith；基督教 9 礼绑 `christian_faith`。shangqing_faith=上清派、quanzhen=全真派(rite)。
- 唯一真源 `eu5_ck3_faith_map.csv`（生成器 `_build_faith_map.py` 的 CURATED），三表必须同步。**文件可能被用户回滚，数字要当场 religion_audit.py 核**。

## 五、CU 对照
`_cu_vs_ours.csv`（2858 barony）。CU 范围 = 该表 barony 所属 EU5 province（2448 个）。柏柏尔 butr/baranis 以 CU 为准；**阿拉伯语一律 maghrebi**（algerian/moroccan/tunisian/libyan_arabic）。

## 六、生成器纪律
用户手改文件绝不覆盖；默认 dry run；非必要不全量重建（补丁层被冲）；诊断默认只读、报告结论+改法等用户说「改」；行号一律绝对行号；游戏安装目录只读，产物放工作区。

## 七、其它
- 复合名每部分是独立 key，按 EU5 部分拼接（中文无分隔符、英文空格）。
- Git：master=发布分支，eu5-coa 分支存纹章；禁 git worktree；GitHub Desktop 提交，push 前 fetch。
- 地图可视化一律 `ck3-mapviz`，严禁自己算投影打点。

## 八、工程要点
- 首府链路六步（rank_state→reassign→export→tusi→holstein）；fallback 真多数 = 地数严格大于县内其他单持有者；HRE 同名首府 5 县（c_chrudimsko/c_hanover/c_lippe/c_luneburger_heide/c_neuchatel）跑完 rank_state 须重跑 `fix_holstein_denmark.py`；土司首府规则已回滚勿实施。
- 开局 1337.4.1 三处同步（bookmarks/challenge/groups）；重跑 `_fix_politics_output.py` 丢毛利标记、`_export_title_map.py` 记 58 头衔开局无主。
- regency diarchy 不自动结束，须显式 end_diarchy；1280 个 `eu5_regent_*` 是占位 holder。
- 主头衔 220 条；4 条手工指定只在 `_patch_primary_titles_file.py`，重跑生成器会丢（bds_jalal_al_dawla_iskandar→c_qazvin 等）。
- title_map：帝国/王国/公国→`X_eu5_TAG`；日本→`c_nf_*`；查日本须 grep `zzz_eu5_japan_noble_families.txt`。

## 九、已完成 / 遗留
- 已完成勿重做：168 支系→42 宗族；154 复合君主名重译；4361 宗教人物改写；印度教整县染色；BKZ/SKN 7 角色 maliki。
- 待定：① BKZ/SKN 库西雅 7 省 rite；② 10990 pagan 角色文化主体非 pagan；③ 244 印度教省 CU 记耆那；④ pamiri→afghan（先不动）；⑤ tai_lu/tai_nua 定义去留；⑥ coptic 省份层 0 省阈值；⑦ 涅涅茨→Bjarmian；⑧ 萨尔语群 17 文化（先不管）。
