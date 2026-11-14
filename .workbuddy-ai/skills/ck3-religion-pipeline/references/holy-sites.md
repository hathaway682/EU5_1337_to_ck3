# 圣地（holy sites）

## 一、三层结构

CK3 的圣地是三层，**改错层等于白改**：

| 层 | 在哪 | 决定什么 | 本 mod 状态 |
|---|---|---|---|
| ① 圣地块定义 | `common/religion/holy_site_types/*.txt`（mod 有） | 这个圣地叫什么、落在哪个县/男爵领、给什么加成 | mod 自己维护，265 个 + 动态圣地 |
| ② faith → 圣地绑定 | `common/religion/faith_types/*.txt` 里每个 faith 的 `holy_sites = { ... }` | 哪个信仰把这里当圣地 | **mod 没有这个目录，全部继承原版** |
| ③ 显示名 | `localization/*/religion_*.yml` | 圣地中文名 | 原版已有，mod 一般不动 |

关键后果：**mod 没有 `faith_types/`，所以圣地与信仰的绑定关系完全由原版决定。**
你能改的只有「这个圣地在我们的地图上落在哪个男爵领」。

## 二、圣地块定义长什么样

```txt
jerusalem = {
	county = c_filastin
	barony = b_jerusalem

	parameters = {
		jerusalem_conversion_bonus
	}

	county_holder_character_modifier = {
		monthly_piety_gain_mult = 0.05
		different_faith_opinion = 5
	}

	county_modifier_scaled = {
		scale = holy_site_total_artifact_rarity
		prosperity_growth_factor = 0.01
	}
	faith_character_modifier = { character_travel_safety_mult = 0.1 }
}
```

- `county` / `barony` 是**唯二需要跟本 mod 地图对齐的字段**，其余加成从原版照搬。
- `county` 必须真的包含 `barony`，否则游戏里不生效（改完用 `_holy_site_status.py` 或 `holy_sites_table.csv` 复核）。
- `01_dynamic_holy_site_types.txt` 里是 `is_dynamic = yes` 的动态圣地，没有固定 county/barony，不用管落点。

## 三、孤儿圣地：位置改得再对也不会生效

**判据（2026-11-14 用户拍板）**：mod 没有 `faith_types/`，所以「被引用」= 该 key 出现在**原版** `faith_types` 的某个 `holy_sites` 列表里。
原版 faith 也不引用的，就是死数据，应当删掉。

```bash
cd <MOD>/gen_debug
python _drop_orphan_holy_sites.py            # 干跑，列出要删的
python _drop_orphan_holy_sites.py --apply
```

不删的两类：
- 被原版 faith 引用的（如 `bumiayu`、`preah_vihear`）；
- 动态圣地（`is_dynamic = yes`）。

## 四、工具链（都在 `gen_debug/`，全部默认 dry-run）

| 脚本 | 作用 |
|---|---|
| `_holy_sites_to_csv.py` | 把 mod 全部圣地导出成 `holy_sites_table.csv`，并标注「已确认 / 未确认」和判定依据 |
| `_holy_site_status.py` | 只读进度盘点：已对 / 已修 / 剩余，剩余再分「有同名候选」和「没候选」 |
| `_fix_holy_site_by_same_name.py` | 按「半径 300 km 内同名男爵领」修 `county`/`barony`（用户 2026-10-23 定的 300 km） |
| `_apply_holy_site_knowledge_map.py` | 按人工知识映射（异名同地，如「迦太基=突尼斯」「汴梁=开封」）修落点，MAP 在脚本里 |
| `_apply_cu_holy_sites.py` | 把落点换成 CrusaderUniversalis 的数据（CU 用自己的命名，需换算到本 mod） |
| `_drop_orphan_holy_sites.py` | 删没有被任何原版 faith 引用的圣地 |
| `_eu5_holy_site_compare.py` | 拿 EU5 官方 `common/holy_sites/*.txt` 与 CK3 落点对照（EU5 的 `location` = 本 mod 的 `b_<name>`） |

### 标准流程：修一批圣地的落点

```bash
cd <MOD>/gen_debug
python _holy_site_status.py                       # 1) 看还剩多少
python _fix_holy_site_by_same_name.py             # 2) 干跑同名规则
python _fix_holy_site_by_same_name.py --apply
python _apply_holy_site_knowledge_map.py --apply  # 3) 异名同地
python _holy_sites_to_csv.py                      # 4) 重新导出盘点表
```

### 改单个圣地

直接编辑 `common/religion/holy_site_types/00_holy_site_types.txt` 里那一块的
`county =` / `barony =` 两行即可，**不要动 modifiers**（那是从原版抄来的加成）。

## 五、现状（2026-11-14）

- 圣地块 **270 个**（`holy_sites_table.csv`），其中 **已确认 198 / 未确认 72**。
- 「已确认」的依据分布：`barony key 同` 41、`barony 中文名同名` 9、`barony 名互为前缀` 5、`县名同名` 4、人工知识映射若干。
- 未确认的 72 个多为「本 mod 地图上找不到同名地块」，需要人工判断或从 EU5 圣地数据反查。

## 六、纪律

- **只改 `county` / `barony`，不动本地化文本、不动 modifiers。**
- 文件是 UTF-8 BOM + CRLF，改完必须校验（`religion_audit.py` 不查这个文件，用 `_holy_site_status.py` 或直接查字节）。
- 想改「哪个信仰把这里当圣地」= 要建 `common/religion/faith_types/00_faith_types.txt`，
  但 CK3 里同名 faith 块是**整块替换**不是合并，抄漏一个字段就会把原版教义冲掉。
  真要改，整份抄原版再改，别只写一个片段。
