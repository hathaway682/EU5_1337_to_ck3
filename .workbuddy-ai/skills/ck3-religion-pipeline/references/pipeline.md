# 宗教数据链路全景

## 一、两层结构：faith 与 rite

CK3 的宗教地图是**两层**：

| 层 | 字段 | 作用 | 数量 |
|---|---|---|---|
| faith（信仰） | `faith =` | 地图上色的单位、教义、宗教领袖 | mod 定义 103 个，省份用到 55 种 |
| rite（礼/宗派） | `rite =` | 同一个 faith 内的教会/学派细分，决定显示哪个教派名 | mod 定义 152 个，省份用到 28 种 |

**关键机制**（`common/religion/`）：

- `faith_types/*.txt` 的每个 faith 有 `main_rite = X`。省份**只写 faith 不写 rite 时，按 main_rite 回落**，所以大部分省根本不需要写 rite 行（当前 21034 个有 faith 的省里只有 4066 个写了 rite）。
- `rite_types/*.txt` 的每个 rite 有 `faith = Y`，即它挂在哪个 faith 下。
- **判「一个 rite 能不能挂到某个省」看的是 religion，不是 faith**。vanilla 的 9 个基督教礼全绑在伞形 faith `christian_faith`（迦克墩派）上，而省份写的是 `orthodox` / `catholic` / `miaphysitism` —— 这是正常设计。跨 religion 才是错（例：`rite = quanzhen` 属于 `taoism_religion`，挂到 `faith = confucian_faith` 上就是错的）。
- `faith` 没有 `main_rite` 时（如 `confucian_faith`、`maitreya_faith`），由 `history/faiths/*.txt` 的日期块决定，1337 开局落到 `daoxue` / `maitreya`。

## 二、唯一真源

**EU5 religion → CK3 faith 的映射只有一份真源**：`Global_modern_map/eu5_export/eu5_ck3_faith_map.csv`（人读版 `_zh.csv` 多几列中文）。

- 生成器：`_build_faith_map.py`，判定顺序 = ① 同名 key → ② 同名显示名（去掉 `_religion`/`_pagan`/`_faith`/`_group` 后缀比）→ ③ 手写 `CURATED` 表 → ④ 兜底 `pagan`。
- `CURATED` 表在 `_build_faith_map.py` 里，**每条都带用户拍板日期和理由**，改映射要改这里而不是改 CSV。
- **三处必须同步**：`_build_faith_map.py` 的 `CURATED` / `eu5_ck3_faith_map.csv` / 各 `_apply_*` 脚本里的硬编码规则表（如 `REL_RULE`）。

## 三、执行顺序（分层补丁，后面的盖前面的）

从下往上，每一层都是幂等的、只改目标行。**重跑某一层之前先想清楚它会不会盖掉上层的成果。**

| # | 层 | 脚本 | 输入 → 输出 |
|---|---|---|---|
| 0 | 主生成 | `eu5_to_ck3.py` | EU5 数据 → 省份史（此时 faith 里是 **EU5 的 religion key**） |
| 1 | 映射表 | `_build_faith_map.py` | `06_pops.txt` + CK3 原版 loc → `eu5_ck3_faith_map.csv` |
| 2 | 批量替换 | `_apply_faith_map.py` | 省份/角色的 EU5 key → CK3 faith；`gen_faith_*` 一律 `pagan` |
| 3 | 原始宗教修正 | `_apply_african_faith_geo.py`、`_apply_asian_faith_geo.py`、`_apply_asia_folk_faith.py`、`_apply_siberian_faith.py`、`_apply_siberia_shaman.py`、`_apply_ck3_pagan_match.py`、`_apply_folk_samename.py`、`_apply_euro_perm_faith.py`、`_apply_africa_fam_faith.py`、`_apply_soninke_bidu.py`、`_apply_heresy_pops.py`、`_fix_wrongpagan.py` | 都是「当前 faith 是 pagan → 改回具体原始宗教」，靠 `province → county → eu5_peoples.json` 反查 EU5 宗教 |
| 4 | faith 分化 | `_apply_hindu_faith_branch.py`（**最新口径 2026-10-22**，按 EU5 `hindu_branch` 国际组织成员）；`_apply_hindu_faith_geo.py` 是旧口径 | 印度教 4 派 → 4 个 faith |
| 5 | rite 层 · 伊斯兰 | `_apply_rites.py`（按 EU5 `religious_school` 写学派）+ `_apply_islamic_geo_spread.py`（地理传播补学派） | sunni/shia/ibadi → hanafi/maliki/… |
| 6 | rite 层 · 基督教 | `_apply_christian_rites.py` | orthodox/miaphysite → slavic_rite/byzantine_rite/ethiopian_rite/… |
| 7 | rite 层 · 东亚 | `_apply_sect_rite.py` | EU5 sect 国际组织（**sect 身份 = `laws` 首个元素**）→ 禅宗/净土/华严/律宗… |
| 8 | rite 层 · 佛教传播 | `_apply_buddhist_geo_spread.py` | 给 mahayana_faith 省补具体宗派（三层传播，见下） |
| 9 | 中日朝 | `_apply_cu_three_teachings.py` | 按 CU 数据把中国三教省/朝鲜大乘/日本神道转成具体 rite |
| 10 | 角色层 | `_apply_char_religion.py`、`_apply_hindu_faith_chars.py`、`_apply_christian_rites_chars.py` | `history/characters/*.txt` 的 `religion =` |

> 第 9 层依赖 CU 数据，链路见 `cu-source.md`。

## 四、几个关键传播算法

### 佛教（`_apply_buddhist_geo_spread.py`）

只有 `mahayana_faith` 需要补（`theravada_faith` 的 main_rite 就是 `theravada`、`vajrayana_faith` 的 main_rite 已改成 `lamaism`，自动正确）。三层：

1. **接壤 BFS**：从已有具体宗派的省沿 CK3 province 接壤扩散。
2. **≤300 km 隔空**：质心直线距离（等距圆柱投影，赤道 1px≈2.446 km，经度按 cos(lat) 收缩），**只做一步不递归**。
3. **阿吒力教特批**：`acharya` 绑 `vajrayana_faith`，允许跨 faith 替换 `mahayana_faith`；写盘时**删掉 faith 行只留 `rite = acharya`**。原 acharya 省没有 faith 行，必须从 `prov_rite` 单独捞才能当源。

**父信仰守卫**：mahayana 系 7 个 rite 只写 `mahayana_faith`，vajrayana 系 5 个只写 `vajrayana_faith`。

**「owner 是佛教国家 → 不参与传播」**：高昌（QCH）等佛教国家的省保留主流大乘，这是用户明确要求的。

### 伊斯兰（`_apply_islamic_geo_spread.py`）

什叶/伊巴德/逊尼省如果 owner 的教法学派帮不上（owner 是异派国家、或没写学派），按 CK3 province 接壤从「父信仰相同」的已确定省传播最近学派。**sunni 只从 sunni 源、shia 只从 shia、ibadi 只从 ibadi。**

### 印度教（`_apply_hindu_faith_branch.py`）

**教随国定**：EU5 tag → `hindu_branch` 国际组织成员 → 支派 → CK3 faith。
县无 owner 或 owner 不在任何支派成员表里 → 地理兜底（印度次大陆 → `vaishnava_faith`，东南亚 → `shaiva_faith`）。
**整县染色**：按县判定、按县落地，不要按省单独判。

## 五、角色层

`history/characters/*.txt` 的 `religion = pagan` 是生成器的占位值，本身不带 EU5 宗教信息。`_apply_char_religion.py` 用 `culture` 反推：取该文化在 `06_pops.txt` 里人口最多的宗教，只有属于 `folk_*` 组才处理。映射结果仍是 `pagan` 的（如 `bantu_religion`）**保持不动**，这是用户认可的终态。

## 六、保存点

`gen_debug/_religion_checkpoint.py` 管 faith + rite 两层，是改宗教前必打的保险：

```bash
cd <MOD>/gen_debug
python _religion_checkpoint.py save 标签       # 存到 religion_checkpoints/faith_<ts>_<标签>.json
python _religion_checkpoint.py list
python _religion_checkpoint.py restore latest            # 干跑
python _religion_checkpoint.py restore latest --apply    # 真写
python _religion_checkpoint.py restore latest --apply --faith-only
```

还原是外科手术式的：只改与快照不一致的行，culture/holding/注释一个字节不动；快照里没 rite 的省，文件里多出的 `rite =` 行会被删掉。
