# 项目长期记忆（EU5_Modern_Borders_noshape）

> 每日细节在 `.workbuddy-ai/memory/YYYY-MM-DD.md`；这里只放长期有效的口径、坑与纪律。
> **改头衔/法理 → 先读本文件二、六、八；改文化、宗教、生成器链路 → 必须先读同目录 `PIPELINES.md`。**

## 一、数据源与层级
- EU5：location→province→area→region。`definitions.txt` 是 tab 缩进，必须栈解析 `next(x for x in reversed(stack) if x.endswith(("_region","_area","_province")))`。4149 province / 27334 location。
- 要人口必须读 `06_pops.txt` 的 `size`（浮点）；`eu5_county_peoples.csv` 只是 location 个数多数。
- CK3 `b_<name>` 的 `<name>` = EU5 location 名；3725/3819 county 严格对应单一 province。质心缓存 `_ck3_province_centroid.json` 读回必须 `{int(k): v}`。
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
- title_map：帝国/王国/公国→`X_eu5_TAG`；日本→`c_nf_*`，查日本 grep `zzz_eu5_japan_noble_families.txt`。主头衔 220 条；4 条手工指定只在 `_patch_primary_titles_file.py`，重跑生成器会丢。
- **按 title_map 批量补内容前，必须先过 `_title_overrides.csv`**：清单/CSV 里的 `title_key` 常是**改名前的旧键**（SIC 记 `k_sicily` 实为 `k_trinacria`；DLH 记 `k_delhi` 实为 `e_hindustan`）。给旧键补内容 = 同一世系在新旧键各写一遍（2026-10-30 补类1 踩到，已删旧键块回退）。判据：`override[tag] != csv_key` 就跳过。

## 三、生成器纪律
用户手改文件绝不覆盖；默认 dry run；非必要不全量重建；诊断默认只读、报告结论+改法等用户说「改」；行号一律绝对行号；游戏安装目录只读，产物放工作区。
- **只改 politics.json 的输入时，链路只需 `export_politics.py` → `_patch_title_history.py`，绝不要跑 `_fix_politics_output.py`**：它是总装脚本，一次写 20 多个产物——province history 的 21046 条 culture/faith/holding、characters 的 government/regent、`zz_eu5_titular.txt` 颜色、tributaries、primary titles、两种语言本地化。2026-10-28、2026-10-29 各犯一次（第二次冲掉省份历史与本地化，靠备份还原）。跑之前先问：这一步真的需要动这个文件吗。
- **`zz_eu5_titles.txt` 绝不可整体重建**：`_patch_title_history.py` 按 politics 重写 holder/government/liege，会冲掉后续补丁层。该脚本**只补不改**。补丁层清单见 `PIPELINES.md` 三。

## 四、其它
- 复合名每部分是独立 key，按 EU5 部分拼接（中文无分隔符、英文空格）。
- Git：master=发布分支，eu5-coa 分支存纹章；禁 git worktree；GitHub Desktop 提交，push 前 fetch。
- 地图可视化一律 `ck3-mapviz`，严禁自己算投影打点。
- **备份归档**：所有 `*.bak*` 放 `F:/EU5_Modern_Borders_bak/`，**按原目录结构分层保留**，项目目录内不得残留 bak。
- **编码**：mod 的 `.txt`/`.yml` 是 UTF-8-BOM + CRLF。追加内容一律写 `\r\n`（用 `\n` 会写出裸 LF）。`json.dumps` 用 `newline="\n"`。删整行正则必须带 `[^\r\n]*\r?$`，否则只删前缀把值留成孤立行；CRLF 里 `[^\r\n]*$` 匹配不到（`$` 前卡着 `\r`），要写 `\r?$` 或用 `.*$`。

## 五、已完成 / 遗留
- 已完成勿重做：168 支系→42 宗族；154 复合君主名重译；4361 宗教人物改写；印度教整县染色；BKZ/SKN 7 角色 maliki；CU 法理树重建（2026-10-29）；ALB/MLL 恢复王国并清 stale liege；LIT 升王国 + 8 公国（2026-10-29）；**类1「有头衔没历史」补世系 244 标题（15 建块 + 229 插入，1532 人），类1 missing 1327→0（2026-10-30，脚本 `_fill_lost_lineages.py`，报告 `_filled_lineages_report.csv`）**。
- 待定：① BKZ/SKN 库西雅 7 省 rite；② 10990 pagan 角色文化主体非 pagan；③ 244 印度教省 CU 记耆那；④ pamiri→afghan（先不动）；⑤ tai_lu/tai_nua 定义去留；⑥ coptic 省份层 0 省阈值；⑦ 涅涅茨→Bjarmian；⑧ 萨尔语群 17 文化（先不管）；⑨ `00_generated_titular_guard.txt` 缺失是否补；⑩ 2026-10-29 16:27 总装脚本另改的 11 个无备份文件未逐个核；⑪ **类2「没头衔挂不了」28 国 98 人未处理**（清单 `_lost_lineages_split.csv` 类别 2；其中 LUX 卢森堡的 `title_key` 列其实是人物 id，需先定怎么处理）；⑫ `k_mediterranean_sea` 显示名是否覆盖成「马略卡」；⑬ 遗留断引用 `c_armagnac` 的 `holder = amg_mascarose_ii_lomagne` 在 characters 里不存在（2026-10-30 前就有，未动）。
