# 项目长期记忆（EU5_Modern_Borders_noshape）

> 每日细节在 `.workbuddy-ai/memory/YYYY-MM-DD.md`；这里只放长期有效的口径、坑与纪律。
> **改头衔/法理 → 先读本文件二、六、八；改文化、宗教、生成器链路 → 必须先读同目录 `PIPELINES.md`。**

## 一、数据源与层级
- EU5：location→province→area→region。`definitions.txt` 是 tab 缩进，必须栈解析 `next(x for x in reversed(stack) if x.endswith(("_region","_area","_province")))`。4149 province / 27334 location。
- 要人口必须读 `06_pops.txt` 的 `size`（浮点）；`eu5_county_peoples.csv` 只是 location 个数多数。
- CK3 `b_<name>` 的 `<name>` = EU5 location 名；3725/3819 county 严格对应单一 province。质心缓存 `_ck3_province_centroid.json` 读回必须 `{int(k): v}`。
- **头衔 `capital` 对齐**：`countries[tag]["capital"]` 是 **location 名**，CK3 侧取 `b_<location>` 的父 `c_`；`capital` 一律写 `c_`（三个声明文件里 2482 个全是 `c_`，无 `b_` 写法）。工具 `gen_debug/_fix_title_capital.py`（幂等，`--dry-run`），只处理 title_map 里原生 d/k/e/h 键、跳过目标县 owner 不是该国的（MEN 的 `milas` 无 `b_milas`、落在 AYD 的 `c_aydin`）。**`00_landed_titles.txt` 的 capital 是 CU 产物，重跑会覆盖**。
- 本地化永远比 key 权威，先 `grep -rn "<key>" localization/simp_chinese/`。

## 二、头衔与法理（硬规则）
- **法理树 = Crusader Universalis 1337.4.1 开局态**（h 7 / e 56 / k 225 / d 657 / c 3819 / b 21046）。mod 原有 77 个区域王国（k_iberia / k_russian / k_indonesia …）全部废弃。重建细节见 `PIPELINES.md` 一。
- **解析 key 的正则必须写 `[A-Za-z0-9_-]`**（`k_kabisay-an`、`k_galicia-volhynia` 会被截成 `an`/`volhynia`，父链直接断）；日期块 key 还要加 `.`，否则 `867.1.1 = {` 被拆成 `1 = {`。
- **法理只存在于 `00_landed_titles.txt` 的嵌套里**（h_ > e_ > k_ > d_ > c_ > b_）。**绝不要为了改持有人/颜色在别的文件顶层重复声明同一 key**——后加载的同名块**替换整块、不合并**，头衔立刻失去父头衔（2026-10-29：281 个法理公国被 `zz_eu5_titular.txt` 顶层重写）。改持有人只动 `history/titles/`；`common/landed_titles/` 只放本 mod 新铸的头衔。两文件现已零重名，**要一直保持**。
- **占用原版 key 必须两处一起剔除**：`zz_vanilla_titulars.txt` 删 shim 块 ＋ `common/on_action/00_generated_titular_guard.txt` 删 `title:X = { … destroy_title = prev }`。只删 shim → 真实头衔开局被销毁；只删 guard → landless 与有地声明冲突。清单真源 = `_title_overrides.csv` 的 `country/title_key`；**有些 key 只在 guard 里、不在 shim 里**（k_egypt/k_france/k_maghreb 是原版真实头衔）。两文件是外部 Ck3MapGen v0.96 产物，重跑会写回。**guard 文件目前不存在**，保险只剩 `can_create = { always = no }`。
- **原版 CK3 有的键 ≠ 本 mod 有**：本 mod 的 `00_landed_titles.txt` 是 CU 1337 树、整个替换原版，所以原版法理头衔在这里往往不存在（例：`k_lithuania` 原版有、CU 里没有，立陶宛的公国挂在 `k_baltic` 下）。改 `title_key` 前必须在本 mod 三个声明文件（`00_landed_titles.txt` / `zz_eu5_titular.txt` / `zz_vanilla_titulars.txt`）里确认目标键真的存在，**「删 shim」与「补声明」必须成对做**。收尾一律校验一遍：history 里所有 `liege` 目标都要能在声明里找到。
- **stale-liege 清扫的「改名产物就留着」兜底不能按 `lieges[-1] in rename.values()` 判**：`k_naples`/`k_aragon` 都是改名目标，任何 liege 恰好指它们的块都会被放过（2026-10-29 ALB/MLL 8 块）。判据必须是「这一块里的 liege 真的被 rename 重写过」——改名前先 `findall` 存 `renamed_liege`。日志打 `stale liege taken out: <key> was under <X>`。
- **无地头衔（d/k/e）全丢，不留空壳**：判据在 `_fix_politics_output.py` 的 declined 段——**rank in (d,k,e)、0 个自己的县、不在 lords、ruler 已持有别国县 → 丢弃**。命中 9 个：MNN ＋ BRZ/INO/JAW/KLN/LIM/NMS/RCB/SIZ；PAP、HRE/ILK 不误伤。**地不跟着动**。删头衔连带清四处：`eu5_titles_dropped.txt`、`zz_eu5_titular.txt` 声明、11 语言本地化、`zz_eu5_primary_titles.txt` 的 `set_primary_title_to`。排查口径 `rank in (d,k,e) and not own_counties`。
- **`io_titles` 只能放「EU5 里没有对应国家的组织」**（hre、ilkhanate）。`tatar_yoke`/`middle_kingdom` 有对应国家（GLH/CHI），给了头衔就会先写一个只有当前领袖 1 条的块，国家的完整世系块在改名预处理里被判重复删掉（2026-10-28 中华/金帐世系全丢）。**改名预处理「新 key 已有块就删旧块」是危险动作**：新块常只有一行、旧块有整条世系。
- 首府 = 只读伯爵领块内第一个 `b_`。dynasty=宗族、house=支系。角色块按大括号深度切顶层块；文化引用用 `re.finditer(r'(?<![a-z_])culture\s*=\s*(\w+)', line)`。
- **宗族对齐规则 v2（2026-10-31）**：候选集必须是 mod **全部 `*_dynasty`**（`zz_eu5_dynasties.txt` 共 1111 个），**绝不能用 `dynasty_merge_map.json` 的 42 归并父宗族当全集**——独立 dynasty（无 house 子支系）不在归并 map 里，会整批漏掉（`rurikovich` 就这么漏的）。匹配用 **dynasty KEY 主体**（`xxx_dynasty` 去后缀 = EU5 原始家族名），**不用 name 字段**（name 是本地化键，可能错译：rurikovich 的 `name_roderick`=罗德里克，vanilla 正确是 `dynn_Rurikid`=留里克，罗德里克在 vanilla 是另一个键 `dynn_Rotreik`）。culture 必须先经 `gen_debug/_culture_classification.csv` 的 target 归一化（muscovite→russian，CK3 无 muscovite）再比。工具 `gen_debug/_align_dynasty_v2.py`，文档 `gen_debug/dynasty_alignment_rule.md`，清单 `gen_debug/dynasty_alignment_candidates.csv`。2026-10-31 已落地 A+B 层 170 个（75 挂 COA / 95 只改名，校验 170/170）；C 层有误配（hanau→Hainaut、hohnstein→Holstein、tamura→Tomura）待复核。
- **v2 批量对齐已整体回滚（2026-10-31 用户拍板）**：`_apply_align_v2.py` 落地的 A+B 170 个**全部撤回**（回滚脚本 `gen_debug/_rollback_align_v2.py`，备份 `.bak_rollback_20261031_210035`）。原因：tier B 的模糊名相似（score≈0.85）+ 文化匹配产生大量跨家族误配——`shimazu→japanese_shimada`(岛津→岛田)、`aki→dynn_Maki`、`alpin→dynn_Ailpin`、`apokaukos→dynn_Apokapis`、`amorian→dynn_Amorios`。**教训：名字相似度+同文化不能作为自动落地依据**，日文/希腊文罗马字转写差异小、不同家族名只差一两个字母，阈值 0.85 太松；宁可只做 score=1.000 精确同名，其余一律人工核。手工对齐的 28 个（含 rurikovich）与藤原系并入均未受影响。
- **日本宗族归并（2026-10-31 用户拍板）**：臣籍降下的源/平/大和系（murakami_genji/saga_genji/seiwa_genji/taira/takashina/uda_genji）**不并入大和**，保持独立 dynasty；**藤原的子系要并入藤原**。已把 hatano/kondou/kudou/nakamura/oyama/saitou/sanjou/utsunomiya 降级为 house_xxx（dynasty=fujiwara_dynasty），26 子 house 改挂 fujiwara，88 角色 dynasty=fujiwara+dynasty_house=house_xxx。脚本 `gen_debug/_merge_fujiwara_subclans.py`。
- title_map：帝国/王国/公国→`X_eu5_TAG`；日本→`c_nf_*`，查日本 grep `zzz_eu5_japan_noble_families.txt`。主头衔 220 条；4 条手工指定只在 `_patch_primary_titles_file.py`，重跑生成器会丢。
- **按 title_map 批量补内容前，必须先过 `_title_overrides.csv`**：清单/CSV 里的 `title_key` 常是**改名前的旧键**（SIC 记 `k_sicily` 实为 `k_trinacria`；DLH 记 `k_delhi` 实为 `e_hindustan`）。给旧键补内容 = 同一世系在新旧键各写一遍（2026-10-30 补类1 踩到，已删旧键块回退）。判据：`override[tag] != csv_key` 就跳过。

## 三、生成器纪律
用户手改文件绝不覆盖；默认 dry run；非必要不全量重建；诊断默认只读、报告结论+改法等用户说「改」；行号一律绝对行号；游戏安装目录只读，产物放工作区。- **只改 politics.json 的输入时，链路只需 `export_politics.py` → `_patch_title_history.py`，绝不要跑 `_fix_politics_output.py`**：它是总装脚本，一次写 20 多个产物——province history 的 21046 条 culture/faith/holding、characters 的 government/regent、`zz_eu5_titular.txt` 颜色、tributaries、primary titles、两种语言本地化。2026-10-28、2026-10-29 各犯一次（第二次冲掉省份历史与本地化，靠备份还原）。跑之前先问：这一步真的需要动这个文件吗。
- **`zz_eu5_titles.txt` 绝不可整体重建**：`_patch_title_history.py` 按 politics 重写 holder/government/liege，会冲掉后续补丁层。该脚本**只补不改**。补丁层清单见 `PIPELINES.md` 三。

## 四、其它
- 复合名每部分是独立 key，按 EU5 部分拼接（中文无分隔符、英文空格）。
- Git：master=发布分支，eu5-coa 分支存纹章；禁 git worktree；GitHub Desktop 提交，push 前 fetch。
- 地图可视化一律 `ck3-mapviz`，严禁自己算投影打点。
- **CU 会在开局重算 development**：`common/on_action/cu_neighbor_reassigned_initialization.txt` 里的 `cu_neighbor_reassigned_development_initialize` 会按邻接重新初始化各地发展度，把 `history/titles/` 里写的 `change_development_level` 全部冲掉。现已整段注释；**重跑生成器或更新 CU 后必须检查是否被写回**。判断"发展度没生效"先看这里，别怀疑写法。
- **备份归档**：所有 `*.bak*` 放 `F:/EU5_Modern_Borders_bak/`，**按原目录结构分层保留**，项目目录内不得残留 bak。
- **编码**：mod 的 `.txt`/`.yml` 是 UTF-8-BOM + CRLF。追加内容一律写 `\r\n`（用 `\n` 会写出裸 LF）。`json.dumps` 用 `newline="\n"`。删整行正则必须带 `[^\r\n]*\r?$`，否则只删前缀把值留成孤立行；CRLF 里 `[^\r\n]*$` 匹配不到（`$` 前卡着 `\r`），要写 `\r?$` 或用 `.*$`。

## 五、已完成 / 遗留
- 已完成勿重做：168 支系→42 宗族；154 复合君主名重译；4361 宗教人物改写；印度教整县染色；BKZ/SKN 7 角色 maliki；CU 法理树重建（2026-10-29）；ALB/MLL 恢复王国并清 stale liege；LIT 升王国 + 8 公国（2026-10-29）；**类1「有头衔没历史」补世系 244 标题（15 建块 + 229 插入，1532 人），类1 missing 1327→0（2026-10-30，脚本 `_fill_lost_lineages.py`，报告 `_filled_lineages_report.csv`）**。
- 待定：① BKZ/SKN 库西雅 7 省 rite；② 10990 pagan 角色文化主体非 pagan；③ 244 印度教省 CU 记耆那；④ pamiri→afghan（先不动）；⑤ tai_lu/tai_nua 定义去留；⑥ coptic 省份层 0 省阈值；⑦ 涅涅茨→Bjarmian；⑧ 萨尔语群 17 文化（先不管）；⑨ `00_generated_titular_guard.txt` 缺失是否补；⑩ 2026-10-29 16:27 总装脚本另改的 11 个无备份文件未逐个核；⑪ **类2「没头衔挂不了」28 国 98 人未处理**（清单 `_lost_lineages_split.csv` 类别 2；其中 LUX 卢森堡的 `title_key` 列其实是人物 id，需先定怎么处理）；⑫ `k_mediterranean_sea` 显示名是否覆盖成「马略卡」；⑬ 遗留断引用 `c_armagnac` 的 `holder = amg_mascarose_ii_lomagne` 在 characters 里不存在（2026-10-30 前就有，未动）。

## 六、强制锁定首府标准流程（2026-11-10 用户拍板）
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

## 七、宗教 skill（`.workbuddy-ai/skills/ck3-religion-pipeline/`，2026-11-14 建）
宗教改动一律走这个 skill，不要临时写脚本。四个工具：`religion_audit.py`（省份只读体检）、`religion_set.py`（改省份 faith/rite）、`religion_chars.py`（改角色 religion/rite + 跨宗教执政统计）、`religion_snapshot.py`（faith+rite 保存点/还原，原 `gen_debug/_religion_checkpoint.py` 已移入并删除）。参考：`pipeline.md`（10 层执行顺序）、`rites.md`（多 rite 全表）、`pitfalls.md`、`cu-source.md`、`holy-sites.md`、`faith-defs.md`。
- **★ 切省份块必须按大括号深度，不能取「第一个 `}`」**。省份块里有 `1337.4.1 = { ... }` 日期子块，其闭括号缩进 `\t\t\t`；按第一个 `}` 切会把子块尾巴当顶层、写回时闭括号变无缩进 `}`。2026-11-14 实测改 1 个省掉 2 万字节缩进，**BOM/CRLF/括号全平衡、体检不报错**，只有跟备份 diff 才看得出。旧 `_religion_checkpoint.py` 也带这个 bug。改完必须比字节数和 md5。
- mod **没有** `common/religion/faith_types/` 和 `rite_types/`，faith/rite 定义全继承原版（103 faith / 152 rite）。要改教义得整块抄原版，CK3 同名块是替换不是合并。
- 12 个省只有 `rite = acharya` 没有 `faith` 行，是既定写法（有 rite 就不写 faith），不是漏数据。
- 角色块会重复出现：`zz_eu5_characters.txt` 是完整定义，`zz_eu5_government.txt` 是纯 effect 补丁块，后者不能塞 `religion =`。
- 跨宗教统计必须先用 `eu5_ck3_faith_map.csv` 把 EU5 `religion_definition` 翻成 CK3 faith 再比，否则 `theravada` vs `theravada_faith` 全是假阳性；同 religion 的兄弟 faith（miaphysitism vs armenian_apostolic）不算错。当前真跨宗教 153 人（BYZ 42 / CHG 20 / MGE 17）。
- 圣地 270 个，已确认 198 / 未确认 72；`common/religion/holy_site_types/00_holy_site_types.txt` 只改 `county`/`barony`，不动 modifiers。mod 无 faith_types 所以「被引用」= 出现在原版 faith 的 `holy_sites` 列表里，不被引用的就是孤儿，用 `gen_debug/_drop_orphan_holy_sites.py` 清。
