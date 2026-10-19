# EU5 → CK3 全球地图模组 · 交接文档

写给后来的 agent。这份文档放在成品 mod 里，配套三个数据文件一起看：

| 文件 | 内容 |
|---|---|
| `gen_debug/eu5_ck3_title_map.csv` | 全部 6979 条头衔对照表（EU5 tag/tier ↔ CK3 key/tier ↔ 两侧持有者） |
| `gen_debug/eu5_titles_dropped.txt` | 6748 个刻意不建的 CK3 头衔（见 §4.4） |
| `gen_debug/eu5_lieges.json` | 957 个 EU5 tag 在 CK3 里真正该挂的宗主（已跳过没人能持有的头衔） |

最后更新：2026-10-15。这一版补上了「共和执政官角色从来没被写进 mod」的修复（§5.4），
全表重新导出，校验数字见 §8。

---

## 0. 四条路径

| 用途 | 路径 |
|---|---|
| 生成器工作区（脚本、JSON、C# 源码、备份） | `D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map` |
| 成品 mod（**直接改这里**，游戏读的就是它） | `…\mod\EU5_Modern_Borders_noshape` |
| EU5 安装 | `D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game` |
| CK3 安装 | `E:\SteamLibrary\steamapps\common\Crusader Kings III\game` |

dotnet SDK 在 `_tmp_sdk\dotnet.exe`，C# 工程 `_eu5_fork\Ck3MapGen.csproj`。

成品 mod 里真正决定开局政治的文件：

| 文件 | 作用 |
|---|---|
| `history/titles/zz_eu5_titles.txt` | 4692 个头衔块（3819 县 + 657 男爵领 + 130 公国 + 70 王国 + 15 帝国 + h_china） |
| `history/titles/zzz_eu5_japan_noble_families.txt` | 145 个日本世族头衔 `c_nf_*` |
| `common/landed_titles/zz_eu5_titular.txt` | 263 个 EU5 国家头衔声明 + `e_hre`/`e_ilkhanate`/`e_golden_horde`/`h_china`/`k_gen_wilderness` |
| `history/characters/zz_eu5_characters.txt` | EU5 全部人物（9000+，生成器写） |
| `history/characters/zz_eu5_regents.txt` | 1280 个生成摄政（Python 写） |
| `history/characters/zz_eu5_missing_characters.txt` | 导出里出现、mod 其他人物文件没有的角色（含 7 位共和执政官） |
| `history/characters/zz_eu5_government.txt` | 每个统治者一条 `change_government`（写政府，不定义角色） |
| `history/provinces/00_generated_provinces.txt` | 21023 个地点的文化/信仰/rite/地产 |
| `common/on_action/zz_eu5_tributaries.txt` | 118 条朝贡关系（开局第一天生效） |
| `common/on_action/zz_eu5_primary_titles.txt` | 6 条主头衔设置（联统国等） |
| `localization/{english,simp_chinese}/eu5_*_l_*.yml` | 中英文本地化（头衔 7837 条/语言） |

---

## 1. 流水线：三条命令，按顺序跑

```powershell
cd "D:\Documents\Paradox Interactive\Crusader Kings III\mod\Global_modern_map"

# 1) EU5 存档数据 → JSON（5–15 秒；只有在 EU5 侧数据或政治判断改过时才需要 --force）
python eu5_export\export_politics.py --export eu5_export_modern --force

# 2) 把 JSON 的判断落进成品 mod（就地改，不动地图）
python eu5_export\_fix_politics_output.py --mod "..\EU5_Modern_Borders_noshape" --export eu5_export_modern

# 3) 外科补丁：头衔历史的 holder / liege / government / 顺序（幂等，自带 .bak_时间戳）
python eu5_export\_patch_title_history.py --mod "..\EU5_Modern_Borders_noshape" --export eu5_export_modern

# 4) 只导表（不改任何游戏文件）
python eu5_export\_export_title_map.py --mod "..\EU5_Modern_Borders_noshape" --export eu5_export_modern
```

每一步的职责：

| 脚本 | 职责 | 不该做的事 |
|---|---|---|
| `export_politics.py` | 读 EU5 `main_menu/setup/start/*.txt` 与本地化，产出 `eu5_export_modern/eu5_politics.json`：谁持有哪个国家/县/地点、谁是宗主、政体、等级、联统、摄政、组织、外东北人群、日本国府、男爵判定、共和执政官 | 不碰成品 mod |
| `_fix_politics_output.py` | **所有"写进成品"的政治判断**：省历史 culture/faith/rite/holding、角色政体、landed_titles 颜色、头衔声明、日本世族、本地化、朝贡 on_action、主头衔 effect、缺失角色、`gen_debug/*` | 不改 `zz_eu5_titles.txt` 的既有块 |
| `_patch_title_history.py` | 只增改头衔历史：把 `liege` 挪到 1337.1.1、补开局持有者、补 government、按层级重排、删不该存在的块 | 不重写县名、不动别的文件 |
| `_export_title_map.py` | 导 `gen_debug/eu5_ck3_title_map.csv` | 只读 |

**为什么不要重跑全图**：C# 生成器（栅格、地形、头衔历史第一版）一次要很久，而政治/头衔层面的
问题全都能由上面三条 Python 就地修。用户的原话是"不要重跑了"——成品要能马上进游戏检验。
改完 `_fix_politics_output.py` / `_patch_title_history.py` 后立刻重跑它们即可，几秒钟。

---

## 2. 数据来源与 `eu5_politics.json` 字段

顶层键：

| 键 | 内容 |
|---|---|
| `countries` | tag → `{name_en,name_zh,color,culture,religion,rank,government,ruler,regent,consort,capital,holds,rulers[…]}` |
| `characters` | 角色 key → `{name_en,name_zh,first_key,culture,religion,birth,death,dynasty,father,mother,spouses,children,tag}`；生成的摄政叫 `eu5_regent_<tag>`，共和执政官叫 `eu5_rep_<tag>` |
| `dynasties` | 王朝 key → 名称与颜色 |
| `counties` | `c_xxx` → `{capital, owner, ruler}`（owner = 拥有该县首府地点的 EU5 国家；ruler = 那个国家的统治者） |
| `baronies` | `b_xxx` → `{holder, county, tag, location, province, holding, drop_title}` |
| `relations` | `{first, second, type, start, ck3, consul?}`；`ck3` ∈ vassal/tributary/union 才是 CK3 要写的关系，`type` 保留 EU5 原类型（hre/tusi/samanta/tatar_yoke/fiefdom/appanage/dominion/hanseatic_member…） |
| `organizations` | 53 个国际组织；只有 hre / ilkhanate / tatar_yoke / middle_kingdom 会变成头衔 |
| `unions` | 一人兼多国 → `候选人 → [tag…]` |
| `lowered` | 因等级压不住而降级的国家 `{from,to}` |
| `shugo_daimyo` / `shugo_provinces` / `shogunate_seat` | 日本守护大名国府 → 伯爵领（35 / 57 个县 / 145 条） |

`rank` 用 EU5 的字母：`e` 帝国、`k` 王国、`d` 公国、`c` 伯爵领级、`-`（Python 里是 `None`）无等级。
CK3 侧头衔 key 的规则：`{rank}_eu5_{tag小写}`，只给 d/k/e 建；c 级与无等级国家**没有自己的头衔**，
它的地就是它的伯爵领（有地但无县的做男爵领，见 §4.2）。

---

## 3. 头衔与政治规则（当前实现，全部已落在成品里）

### 3.1 县（伯爵领）归属：一县一主

1. 县主 = 该县**首府地点**的持有者。
2. 首府无人持有 → 县内地点最多者。
3. **规则 A**（照顾法兰西小伯爵）：封臣在领主县里有地 → 县给该封臣（多个按县内人口）；
   **领主自己首都所在县永不夺**；**国际组织成员不算封臣**（神罗 313 个成员不参与这条）。
4. 人群国家（EU5 `type = pop`）：只拿**无主**县，按各族 `add_pops_from_locations` 覆盖地点分，多者胜。
5. 外东北（`manchuria_region` − `liaodong_area`）：大元的地若属某人群国家 → 县给该族，族保持**大元封臣**。
6. 无主县 = 荒地，写 `liege = k_gen_wilderness`（成品里 637 条）。

### 3.2 无县有地的小国 → 男爵

**规则 B**：有地、有君主、自己不是别人的领主、非人群国家 → 在**主体县**（地最多、再比人口）
做**男爵**；**每个男爵只留一条首府男爵领**；**公爵/国王也做男爵**（其公国/王国头衔不声明，记在
`drop_title`）。共 657 条，全部属于"一个县都没有"的国家。

### 3.3 等级与外交

| 规则 | 说明 |
|---|---|
| 等级 | 来自 EU5 `country_rank`；无等级按县级算 |
| 联统 | 两国同一君主 → 不写附庸关系，写 `ck3: "union"`；其地跟着**那个人本身**的宗主走。51 组、127 个 tag |
| 附庸的附庸同级 | 顺链上推；整链压不住 → 朝贡 |
| 附庸降级 | 领主压不住时降附庸（王国→公国、公国→伯国），下限"比自己的真下属都高"（男爵下属不算）；降不下去就上推或朝贡。当前降 31 家 |
| 县级国家有真封臣 | 升公国（日本系除外） |
| 组织的成员 | 神罗 273 / 天朝 126（tusi）/ 鞑靼枷锁 22 / 伊尔汗 22 → 挂到 `e_hre`/`h_china`/`e_golden_horde`/`e_ilkhanate`（成品里 206 条 `liege = e_hre`） |
| 朝贡 | 118 条，写在 `zz_eu5_tributaries.txt`，开局第一天建立 |
| 主头衔 | `zz_eu5_primary_titles.txt` 6 条：联统国开局后用 effect 指定主头衔，不靠字母序 |

关系总数：**949 附庸 + 118 朝贡 + 27 联统**。

### 3.4 刻意不建的 CK3 头衔（6748 条，`gen_debug/eu5_titles_dropped.txt`）

四类原因，写在一起给补丁和宗主解析共同使用：

1. **等级不符**：c 级/无等级国家的 `d_/k_/e_` 头衔从不声明（如 `d_eu5_aac`）。
2. **降级后不再符合**：`lowered` 的国家保留原等级的头衔全部丢（`d_eu5_cdl`）。
3. **只落一个县/只能做男爵**：一个县且从属他人的公国 → 头衔丢掉、县直接挂给领主（`d_eu5_ath`、
   `d_eu5_brz` 等；`drop_title` 的 21 条走同一逻辑）。
4. **EU5 没有王座**：rank ≥ d 但 `ruler` 为空的国家（汉萨同盟这种"有成员没君主"的）→ 头衔丢掉，
   其附庸改挂领主的领主（吕贝克→皇帝）。52 个这样的头衔在成品里是"已声明但开局无人持有"，
   **且没有任何头衔挂给它们**（已校验为 0），所以不会造成静默失效。

### 3.5 日本

- **守护大名**：拿 EU5 `kokufu`（国府，源 `main_menu/setup/start/07_cities_and_buildings.txt`）
  所在的伯爵领，共 57 个县；座郡冲突按**伯爵领名字**定夺（`c_kazusa`→高、`c_settsu`→赤松、
  `c_tango`→上杉、`c_ise`→北畠）。这些县 `liege = e_eu5_jap`。
- **世族头衔**：守护大名 + 其余成员共 **145 家** `c_nf_*`，伯国级、`landless`、`capital` 必须指向
  一个真实存在的伯爵领（**不能自指**，否则没有位置会闪退）。全部 `liege = e_eu5_jap`，
  `succession_laws = { noble_family_succession_law }`。
- **守护大名手上的伯爵领**看国府，不看 EU5 的 ownership。
- 只有守护大名 + 其他大名 + 两位天皇（律令制）：北朝 `NTC` 用 `inherit_ruler_terms = YMT` 继承皇室序列 → 光明天皇。

### 3.6 摄政

- EU5 明写摄政且日期覆盖 1337 的 28 国：有**本国幼主**的 → 头衔给幼主（CK3 自己安排摄政）；
  否则给摄政本人（丹麦、罗斯托夫、科曼日等 9 国）。
- 其余 1280 国（EU5 没有君主）→ 生成角色 `eu5_regent_<tag>` 持有。
- 生成摄政写在 `zz_eu5_regents.txt`，并且**同一 key 在 `zz_eu5_government.txt` 里另有一段 effect**
  （CK3 会把两份历史合并，这是刻意的模式，不是重复定义）。

### 3.7 共和执政官（封建君主兼任共和国）★

一个君主同时是某**共和国**的元首时（例：伊万一世持有莫斯科与诺夫哥罗德；罗贝托持有那不勒斯、
蒙多维、普拉托），共和国必须由**自己人**当封臣管理，否则城市会被君主的封建领地吞掉。
实现：`export_politics.py` 造 `eu5_rep_<tag>` 执政官角色，让共和国头衔落到他名下并做君主的封臣。
当前 7 家：

| 执政官 | 持有的共和国头衔 | 宗主 |
|---|---|---|
| `eu5_rep_nov` | `d_eu5_nov` + 29 个诺夫哥罗德伯爵领 | `k_eu5_mos` |
| `eu5_rep_mnd` | `c_mondovi` | `k_eu5_nap` |
| `eu5_rep_luc` | `c_lucca` | `d_eu5_ver` |
| `eu5_rep_pad` | `c_padua` | `d_eu5_ver` |
| `eu5_rep_par` | `c_parma` | `d_eu5_ver` |
| `eu5_rep_pes` | `b_pesaro`（在 `c_urbino` 内） | 逐级归 `c_urbino` |
| `eu5_rep_pra` | `b_prato`（在 `c_florence` 内） | 逐级归 `c_florence` |

三处细节：

- 座城必须是 `city_holding`（省历史按**县主国家的政体**写地产，共和→城市）。
- PES/PRA 的唯一地点落在别人的县里，CK3 的男爵领只能听县主，所以这两位挂不到那不勒斯头上；
  要挂就得给他们各自的伯爵领（动地图）。
- 2026-10-15 之前这 7 个角色**只有政府文件里的一段 effect、没有被定义成角色**，
  CK3 拿到 `holder = eu5_rep_mnd` 会直接丢掉整行 → 共和国退回封建君主。修法见 §5.4。

### 3.8 地区政体

- 东南亚（EU5 `sub_continent:south_east_asia`，= `indochina_region` + `indonesia_region`，1586 地点 /
  190 县）**加美拉尼西亚**（`oceania/pacific_islands/melanesia_region`，562 地点 / 46 县 —— 新几内亚、
  所罗门、瓦努阿图、新喀里多尼亚、斐济，合计 **2148 地点 / 236 县**）：
  **由 EU5 的 `mandala_system` 政府改革决定**（★ 2026-10-18 起，取代旧的"单县无附庸判村社"）：
  - 开局 `reforms` 里带 `mandala_system` 的 tag → `mandala_government`，县首府 `temple_citadel_holding`；
  - 其余一律 → `wanua_government`，县首府 `tribal_holding`（与 EU5 政体无关，clan/herder/feudal 也照改）。
  - `reforms` 写在 tag 的 `government = { ... }` 里，很多 tag 靠 `include = "indonesia_monarchy"` 等模板带进来，
    必须展开 include 才算（展开后 61 个 tag，只在 tag 块里直接数只有 BTU/MYI 两个）。
  - 该区所有附庸改成朝贡，等级不变。
  - **例外：EU5 `government = meritocratic` 的国家一律不动**（全图仅 2 个：越南 `DAI` 大越、高丽 `KOR`）。
    越南 13 县 + `k_eu5_dai` 保持 `meritocratic_government`、首府 `castle_holding`；它没有 `mandala_system`，
    按"其余→村社"会被错改成 wanua。高丽不在区内，但同一条豁免一起写死。
  - ⚠️ **不要按 tag 缩写猜国家**：`VTN` 是**万象 Vientiane**（老挝），不是越南；越南是 `DAI`。认国家一律读
    `eu5_politics.json` 的 `name_en` / `name_zh`（或 EU5 本地化），不要看三字母码联想。
  - 美拉尼西亚 46 县里只有 1 个县有国家：`c_doberai` 的**马登 Maden（`MAD`，EU5 `herder`）**，本次改为
    `wanua_government` + 首府 `tribal_holding`（province 20994）；其余 45 县是 `gen_wilderness_holder` 荒野。
  - `common/governments/zz_gen_wanua_government.txt` 的 `primary_heritages` 因此从 5 组扩到 8 组：
    austronesian / shan / thai / tibeto_burman / austroasiatic + **papuan / micronesian / polynesian**
    （马登的 `abun_culture` 是 `papuan_group`，不加会让 wanua 对该统治者 invalid）。
  - 落点 `Global_modern_map/eu5_export/_apply_sea_governments.py`（幂等）。
- **土司（EU5 relation `type: tusi`，126 条）另有一道覆盖，跑在上面这条之后**（★ 2026-10-19）：
  `Global_modern_map/eu5_export/_apply_tusi_governments.py`（幂等，默认 dry-run，`--apply` 落盘）。
  把 126 个土司属国的统治者一律改成 `tribal_government`：头衔历史 `government` 行（ck3_holder 是土司统治者的
  150 个头衔）+ `zz_eu5_government.txt` 的 `change_government`（126 条）+ 首府地产 `tribal_holding`
  （110 处，只改已建成的 castle/temple_citadel/tribal/herder 地面；city/church 不动，同 SEA 规则）。
  ⚠️ 顺序必须是"先 SEA 后土司"：西南边缘（车里 CHH、勐汀 MTG）在 EU5 的 `south_east_asia` 里，
  会被 SEA 脚本错改成 `wanua_government`（村社），土司覆盖再把它按回来部落制。跑反了等于没修。
- 格尔米扬 `GRM` 的 3 个附庸同样改成朝贡（模拟历史势力范围瓦解）。

### 3.9 EU5 政体 → CK3 政体/地产

| EU5 | CK3 政体 | 首府地产 |
|---|---|---|
| monarchy | feudal_government | castle_holding |
| republic | republic_government | city_holding |
| theocracy | theocracy_government | church_holding |
| tribe | tribal_government | tribal_holding |
| steppe_horde | nomad_government | nomad_holding |
| clan（只有伊斯兰封建改氏族） | clan_government | castle_holding |
| administrative（拜占庭、德里） | administrative_government | castle_holding |
| celestial（中国） | celestial_government | castle_holding |
| meritocratic（越南、高丽） | meritocratic_government | castle_holding |
| japan_feudal | japan_feudal_government | castle_holding |
| japan_ritsuryo | japan_administrative_government | castle_holding |
| mandala | mandala_government | temple_citadel_holding |
| wanua | wanua_government | tribal_holding |
| herder（人群国家） | herder_government | herder_holding |

### 3.10 荒野

无主县写 `gen_wilderness_holder`，挂 `k_gen_wilderness`，本地化在 `zz_eu5_politics_l_*.yml`；
荒野也有自己的政体和地产类型 `wilderness_holding`。

---

## 4. 文件层铁律（每条都是事故换来的）

1. **一条记录必须多行**：`日期 = {` / 换行 / 字段 / 换行 / `}`。写成
   `1318.2.22 = { holder = X liege = Y }` 会被 CK3 当成一个坏字段，**整个文件的所有头衔都会没有持有者**
   （日志不报错）。
2. **`liege =` 单独写成 1337.1.1 那一条**。写在持有者登基那天，CK3 会因为宗主头衔当天还没被封出
   而丢掉整行（波希米亚挂不上神罗就是这个原因）。
3. **只有一个 BOM**。双 BOM 会让整个 landed_titles 文件判废（`zz_vanilla_titulars.txt` 出过这个事故，
   日志刷 14104 条 `Invalid landed title name`）。
4. **头衔按层级从高到低排**（h/e → k → d → c → b），同一天的条目合并成一条。
5. **不要写 `landless = yes`** 给有地头衔；日本世族头衔例外（它们是刻意 landless）。
6. **角色必须先定义再被引用**：任何 `holder = X` 的 X 必须能在 `history/characters/*.txt` 里找到定义
   （政府文件不算，见 §5.4）。

---

## 5. 故障史（踩过的坑与根因）

### 5.1 双 BOM → 整个文件判废
`zz_vanilla_titulars.txt` 被写了两遍 BOM，CK3 解析后面所有块为垃圾。修法：读文件 `lstrip("\ufeff")`，
写完检查头 3 字节。

### 5.2 单行多字段 → 全部头衔无主
见 §4.1 第 1 条。

### 5.3 `liege` 写在登基日 → 整行被丢
见 §4.2 第 2 条。`_patch_title_history.py` 专门把 `liege` 搬到 1337.1.1。

### 5.4 ★ `holder` 指向不存在的角色 → 共和国被封建君主吞掉
**症状**：封建君主兼任的共和国一直是坏的（那不勒斯/威尼斯系、诺夫哥罗德）。
**根因**：`_fix_politics_output.py` 统计"角色是否已定义"时把 `zz_eu5_government.txt` 也当成角色文件读了，
而那个文件里每个统治者都有一段 `X = { 1337.1.1 = { effect = … } }`，于是 7 位执政官被判为"已存在"，
从没被写进任何角色文件。CK3 拿到 `holder = eu5_rep_mnd`（不存在的人）→ 丢掉整行 → 县退回给
上一次的持有者（封建君主），并且带着 `government = republic_government`，看起来就是"君主变成了共和"。
**修法**：扫描已定义角色时跳过 `zz_eu5_government.txt`（脚本里带注释）；重跑第 2、3 条命令后
7 位执政官写进 `zz_eu5_missing_characters.txt`。
**同类清理**：那次重跑还清掉了 `zz_eu5_missing_characters.txt` 里 448 条与 `zz_eu5_regents.txt`
重复的旧摄政块（1280 条摄政一条没少）。
**自查**：任何时候都要能回答"全文件 `holder =` 引用的角色是否都有定义"，脚本见 §6。

### 5.5 EU5 自己的数据拼法不一致
`amg_mascarose_ii_lomagne`：EU5 `05_characters.txt` 定义成 `mascorose`，`10_countries.txt` 引用成
`mascarose`。标题历史照抄了引用 → 悬空引用。已把 `c_armagnac`、`c_rouergue` 两处对齐到有定义的拼法。
（这类要按 EU5 数据的拼写去核对，别想当然。）

### 5.6 导出县名与地图县名不一致
`_fix_politics_output.py` 全量重建头衔文件那次，凭空造了 28 个地图上不存在的县、丢了 3 个，
两套县名全部无主。**所以头衔历史只由 `_patch_title_history.py` 就地补，绝不重建。**
当前对照表里有 18 行是"导出有、地图没有"的名字（`c_acre`、`c_fiji`、`c_ifoghas`…），
这些是已知差异，`c_ifoghas`/`c_fiji` 还让 `TMK`/`TOV` 两个小国没有落脚点。

### 5.7 主头衔与联统
不能按字母序定主头衔；联统国（同一个人）开局后用 `zz_eu5_primary_titles.txt` 的 effect 指定主头衔。
附属头衔的生效日期要**比主头衔晚一天**，否则开局那一刻主头衔还没定。
荒野要有 `k_wildness` 级别的名字，否则显示的是伯爵领名。

---

## 6. 校验清单（每次改完必跑）

```powershell
# 全量对照表 + 基础统计（只读）
python eu5_export\_export_title_map.py --mod "..\EU5_Modern_Borders_noshape" --export eu5_export_modern
```

期望（2026-10-15 实测）：

| 检查 | 期望 |
|---|---|
| `holder =` 引用了没有定义的角色 | **0** |
| 有主伯爵领在 1337.1.1 的持有者与 JSON 不符 | **0**（3182 个县逐条比对） |
| 国家头衔的 `liege` 与 `gen_debug/eu5_lieges.json` 不符 | **0**（957 条） |
| 头衔块层级顺序倒挂 | **0** |
| 引用了"开局无人持有时"的头衔（52 个） | **0** |
| BOM | 文件头恰好一个，文件内部无第二个 |
| 花括号 | 平衡（当前 28547 / 28547） |
| 7 位执政官 | 角色已定义 + 政府文件里有 `change_government = republic_government` |
| 145 个世族头衔 | 都有 holder + `liege = e_eu5_japan` + 合法 capital（是伯爵领、不自指、地图上存在） |

已知可接受的例外：

- 守护大名座郡的 `liege` 写 `e_eu5_jap`（即使县主另有其人）；
- 荒野写 `k_gen_wilderness`；
- 52 个 d/k/e 国家头衔"已声明但开局无人持有"（EU5 本来就没给王座，且没有任何头衔挂给它们）；
- 18 行"导出有、地图没有"的县名（§5.6）。

---

## 7. 长期规则：备份与回滚

- **重大/破坏性操作前必须备份**（回滚、批量重写、覆盖成品、改脚本源码、改名/删除）：
  先复制到带时间戳目录 `_backup_YYYYMMDD_HHMM_<说明>\`，**动手之前**把备份路径告诉用户。
  备份范围要含：将被覆盖的源码、成品文本、重跑所需的 JSON/CSV。
- **"回滚"默认指成品 mod**（用户要马上进游戏检验），不是生成器源码。用户说回滚就复制备份覆盖回去，
  **不要用"重跑脚本"冒充回滚**；要动源码必须用户明说。
- 用户暴躁、要一次做完：不要把"下一步"当交付；先讲判断再动手，别一声不响干活；报告要给数字和文件名。
- `_patch_title_history.py` 每次运行会在 `history/titles/` 留一个 `zz_eu5_titles.txt.bak_*`，
  这是它自带的安全网，别顺手删掉最近的那个。

---

## 8. 当前统计（2026-10-15）

**EU5 侧**

- 国家 2337（e 19 / k 97 / d 188 / c 438 / 无等级 1595）
- 政体分布：monarchy 932、herder 448、tribe 253、clan 171、japan_feudal 148、republic 135、
  mandala 115、theocracy 75、steppe_horde 36、无 17、administrative 2、meritocratic 2、japan_ritsuryo 2、celestial 1
- 角色 9027、王朝 1279
- 县 3832（有主 3185、无主 647）、男爵领 657（全部属于没有县的国家）
- 关系：949 附庸、118 朝贡、27 联统（EU5 原始类型里有 hre 273、tusi 126 等）
- 组织 53、联统 51 组（127 个 tag）、降级 31 家、丢弃头衔 6748
- 生成摄政 1280、EU5 指名摄政 28（其中 9 国由摄政本人持位）
- 共和执政官 7

**CK3 成品侧**

- 头衔历史 4692 块（c 3819 / b 657 / d 130 / k 70 / e 15 / h 1）+ 145 个世族头衔
- landed_titles 声明 263 个 EU5 头衔 + 5 个非 EU5（`e_hre`、`e_ilkhanate`、`e_golden_horde`、`h_china`、`k_gen_wilderness`）
- 省历史 21023 个地点的 culture/faith、21046 个 holding
- 本地化 7837 条/语言（英文、简中）
- 对照表 6979 行（country 2337 / county 3835 / barony 657 / japan_house 145 / organization 4 / other 1）

---

## 9. 全部头衔对照表 `gen_debug/eu5_ck3_title_map.csv`

列定义：

| 列 | 含义 |
|---|---|
| `kind` | country / county / barony / organization / japan_house / other |
| `eu5_tag` | 该头衔对应的 EU5 tag；县/男爵领填拥有它的国家 tag |
| `eu5_tier` | EU5 自己的等级 e/k/d/c/- |
| `ck3_key` | mod 里的 landed title key（c 级/无等级国家填它的座县或男爵领；头衔被丢弃时也是座县，原因写在 note） |
| `ck3_tier` | key 的层级 e/k/d/c/b |
| `eu5_holder` | EU5 侧坐在这个位置上的角色 key |
| `ck3_holder` | 成品 1337.1.1 实际持有者（空 = 开局无人持有） |
| `ck3_liege` / `ck3_government` | 成品里该头衔的宗主与政体 |
| `ck3_declared` | 该 key 是否有 landed_titles 声明 |
| `note` | 说明性标记：union / consul / regent / lowered / tributary / vassal / shugo-daimyo / rank-title-dropped / only-on-the-map / unowned-in-eu5 … |

抽样（完整表见 CSV）：

| kind | eu5_tag | eu5_tier | ck3_key | ck3_tier | eu5_holder | ck3_holder | ck3_liege | note |
|---|---|---|---|---|---|---|---|---|
| country | MOS | k | k_eu5_mos | k | mos_ivan_i_danilovich_kalita_rurikovich | 同左 | — | union,tributary |
| country | NOV | d | d_eu5_nov | d | eu5_rep_nov | eu5_rep_nov | k_eu5_mos | consul,vassal,consul-holds |
| country | MND | c | c_mondovi | c | eu5_rep_mnd | eu5_rep_mnd | k_eu5_nap | consul（c 级国家没有自己的头衔） |
| country | DAN | k | k_eu5_dan | k | shl_gerhard_iii_holstein_rendsburg | 同左 | — | union,regent-holds |
| country | ATH | d | c_attica | c | ath_william | ath_william | k_eu5_sic | rank-title-dropped (d_eu5_ath) |
| country | BSC | c | c_millieu | c | eu5_regent_bsc | eu5_regent_bsc | e_hre | vassal,generated-regent（帝国自由市，皇帝直属） |
| country | JAP | e | e_eu5_jap | e | jap_ashikaga_takauji | jap_ashikaga_takauji | — | — |
| county | MND | - | c_mondovi | c | eu5_rep_mnd | eu5_rep_mnd | k_eu5_nap | seat-of MND (Mondovi) |
| barony | PES | - | b_pesaro | b | eu5_rep_pes | eu5_rep_pes | — | in c_urbino,lord PES (Pesaro) |
| japan_house | KOU | d | c_nf_kou | c | jap_kou_no_moronao | jap_kou_no_moronao | e_eu5_jap | daimyo house |
| organization | UBV | - | e_hre | e | ubv_ludwig_iv_wittelsbach | 同左 | — | hre led by … |

重新生成：`python eu5_export\_export_title_map.py --mod "..\EU5_Modern_Borders_noshape" --export eu5_export_modern`

---

## 10. 未决 / 待用户确认

### 10.1 ★ 首府属自由市（或小国）的县，县该给谁

现行规则是"县给首府地点的持有者"（§3.1 第 1 条）。这条规则在"首府是一座自由市、县里其余土地
是某个封建大国"时会反过来：整座县变成城市共和国，真正的公爵反而成了城里的男爵。
实测（用 `mapping.json` 的 location→county 和各国 `holds` 列表逐县比对）：

- **280 个县**的首府持有者，在县内占的地**少于**另一国；
- 其中 **18 个**首府持有者是共和国；
- 其中 **12 个**是"自由市 vs 封建/神权大国"，最明显的一批：

| 县 | 首府持有者（县内地点数） | 县内占多数者（地点数） |
|---|---|---|
| `c_millieu` | BSC 贝桑松自由市（1） | FCB 弗朗什孔泰（2） |
| `c_lower_alsace` | SFC 斯特拉斯堡自由市（1） | ALS 阿尔萨斯（2） |
| `c_upper_alsace` | CFC 科尔马自由市（1） | FRT（2） |
| `c_thuringer_becken` | ERF 埃尔福特（1） | THU 图林根（3） |
| `c_ries` | NUR 纽伦堡（1） | ANS 安斯巴赫（3） |
| `c_south_livonia` | RIG 里加（1） | ARR（3） |
| `c_zvenigorod` | NOV 诺夫哥罗德（1） | MOS 莫斯科（3） |
| `c_thurgau` | ZUR 苏黎世（1） | HAB 哈布斯堡（2） |
| `c_swabian_alb` | ULM 乌尔姆（1） | WUR 符腾堡（2） |
| `c_western_upper_swabia` | RVA（1） | HAB（2） |
| `c_eastern_upper_swabia` | AGC 奥格斯堡（1） | HAB（2） |
| `c_totma` | NOV 诺夫哥罗德（3） | RSO（4） |

用户原话："米约大市应该是弗朗什孔泰的封臣吗？以及封建兼任共和共和要变成封臣的啊"、
"我说应该建立共和制封臣角色管理他的共和头衔，之前就是这么干的"。
两种可能的处理，**改法只差一行，但影响几百个县，动手前要跟用户确认**：

1. **维持现状**：县给首府持有者（自由市拿县，封建大国在县里做男爵）。
2. **按县内土地多数拐弯**：县给县内占多数的一方，首府那座自由市退成**城市男爵领 + 共和执政官角色**
   （即 §3.7 的机制用在自由市身上）——这更贴近"米约大市应该是弗朗什孔泰的封臣"。
   实现在 `export_politics.py` 定 `counties[x]["owner"]` 的地方（现在只看首府持有者）。

### 10.2 导出有、地图没有的县名

18 个县名只存在于 EU5 导出侧（`c_acre`、`c_al_watah`、`c_assaba`、`c_chagos`、`c_christmas_island`、
`c_jurua`、`c_kyzylkum`、`c_loreto`、`c_fiji`、`c_ifoghas` …，完整清单见 CSV 里 `ck3_declared=no` 的行）。
其中 `c_ifoghas`、`c_fiji` 是 `TMK`（Tadmekka）和 `TOV`（Tovata）唯一的落脚点，所以这两个小国
在成品里没有任何地。要修得先核对 EU5 的县名与地图县名的对应表。

### 10.3 挂在县主之外的共和城市

`PES`（佩萨罗）与 `PRA`（普拉托）的唯一地点落在 `c_urbino` / `c_florence` 里，CK3 的男爵领只能听
县主，所以这两位执政官挂不到那不勒斯头上（`PRA` 在 EU5 里是那不勒斯的附庸）。要挂就得给它们
各自的伯爵领（动地图）。

### 10.4 已声明但开局无人持有的国家头衔

52 个（EU5 本来就不给王座的国家，如 `e_eu5_era`、`e_eu5_yua`、`k_eu5_cdn`、`d_eu5_cat`…）。
已校验：没有任何头衔的 `liege` 指向它们，所以不会造成静默失效。

### 10.5 首府落在别人县里的国家（只统计，未改）

由 `_audit_capitals_outside_county.py` 生成 `gen_debug/eu5_capitals_outside_county.csv`：
**447 家**国家的首府地点是别人名下县里的一条男爵领（其中 10 条的男爵领已经写给了别人）。
分两类：

- **A 类 77 家**：自己有伯爵领，但**没有一个是自己首府所在的县**。美因茨（`MAI`，首府 `mainz`
  在沃尔姆斯自由市的 `c_untermain` 里）、特里尔（`TRI`）、符腾堡（`WUR`，首府斯图加特在
  `c_neckar`，县主 HHB）、乌得勒支（`UTR`）、沃里尼亚（`VOL`，首府利沃夫在 `c_lviv`，
  县主 HAL）、弗朗什孔泰（`FCB`）、欧庞（`OPV`）、格尔德恩（`GEL`）、日内瓦（`GNV`）、
  班贝格/弗赖辛/拿骚-锡根/布雷根茨/霍恩贝格/兰茨贝格/安斯巴赫（神罗小邦）、阿朱兰（`AJU`）、
  霍伊萨拉（`HSL`）、马巴尔（`MAB`）、乔罗斯（`CRS`）、哈奇温（`HCN`）、普雷佩查（`TAR`）等。
  按等级：k 5、d 8、c 11、无等级 53；按政体：monarchy 31、herder 16、tribe 10、clan 7、
  theocracy 6、mandala 4、steppe_horde 3。
- **B 类 370 家**：一个县都没有、又不是 §3.2 的男爵（175 家 EU5 根本没给统治者，其余是他人的领主
  或没有任何县内土地）。

用户 2026-10-16 的决定：**只统计，不改**。理由是"跨伯爵领持有男爵领没用"——给这些国家在
别人县里补一条首府男爵领，只会让它们变成那个县县主的封臣，既不是自己的地，也改变不了
首府不在自己手里的现实。要做只有一条路：按县内土地多数决定县主（§10.1 的方案 2）。
