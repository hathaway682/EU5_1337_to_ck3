# CU（CrusaderUniversalis）取数

CU 是另一个 CK3 mod，也是**唯一**给中日朝提供了具体三教宗派的外部数据源。
取数必须走四层，少一层就会漏。

CU 路径：`E:\SteamLibrary\steamapps\workshop\content\1158310\3811443965`

## 第 ① 层：CU 自己的省份史

`history/provinces/*.txt`，每个省块形如

```
10462 = { # b_penglai, c_dengzhou
    culture = han
    rite = pundarika
    1000.1.1 = { rite = jingxue }
    1066.1.1 = { rite = daoxue }
    1178.1.1 = { rite = quanzhen }
}
```

- **只写 `rite =` 和 `faith =` 两种字段**，`religion =` 一次都没出现；被注释掉的省块 0 个。
- **顶层值 + 日期块**两段式，取 **≤1337 的最后一次**（本 mod 唯一书签 `bm_generated` 是 `start_date = 1337.1.1`）。1340 之后的变更要排除。
- 覆盖率天生很低：CU 的 `landed_titles` 有 21046 个省，但 `history/provinces` 只写了约 3071 个省块，其中**只有约 2540 个真写了 faith/rite**。其余靠 CK3 默认 faith（`descriptor.mod` 有 `replace_path="history/provinces"`，不继承 vanilla）。
  **这就是覆盖率的天花板，不是我们漏读。**

## 第 ② 层：伯爵领首府铺满

CU 的规则是「**伯爵领首府上色整个伯爵领**」。所以：

```
CU 伯爵领 c_xxx 的各省 → 取有值那省的多数值 → 铺到 c_xxx 的全部省
```

用 CU 自己的 `common/landed_titles/*.txt` 栈解析出 `county → [province]`。
这一步把 2540 个有值省放大到约 12000 个。

**绝不能按 county 名 join 到本 mod**——两 mod 的伯爵领法理完全不同。

## 第 ③ 层：`history/province_mapping/`（最容易漏的一层）

CU 有个 `history/province_mapping/00_cu_county_mapping.txt`，头一行写着：

```
# Only current Gall-map county capitals; culture and faith/rite only.
```

约 384 行，格式 `A = B # c_old -> c_new`，意思是**旧地图伯爵领 c_old（首府 A）的 faith/rite 去新地图 c_new（首府 B）取**。

漏读这一层的后果：382 个伯爵领被误判「无数据」。实例：

```
10495 = 10462   # c_wendeng -> c_dengzhou
```

`10462` 的 1337 值是 `rite = quanzhen`（全真派），所以文登在 CU 里是全真派 —— 而 CU 的 `history/provinces` 里根本没有 10495 这个省块。

## 第 ④ 层：质心匹配到本 mod

两个 mod 的 `provinces.png` **是同一张图**（都 16384×8192，`definition.csv` 都 28574 色 / 28569 省），
**province id 和 RGB 都不同，但色块形状相同**。所以按像素质心最近邻匹配：

```bash
# 1) 两边各算一次质心（step=2 降采样）
python _build_province_centroid.py --map-dir <mod>/map_data --out _ck3_province_centroid.json
python _build_province_centroid.py --map-dir <CU>/map_data  --out _cu_province_centroid.json

# 2) 匹配（容差 6 px，按距离升序贪心唯一分配）
python _match_cu_by_shape.py --tol 6.0
```

**容差为什么是 6 px 不是 2.5 px**：CU 加了长江航道，沿岸色块被水道切开，质心沿江偏移 3–5 px。
2.5 px 时 13 个省匹配不上，6 px 时只剩 2 个（6132、23707）。

## 完整链路

```bash
cd <MOD_ROOT>/Global_modern_map/eu5_export

python _build_cu_rite_full.py      # ①②③ → _cu_rite_full.json（CU 省 -> 值）
python _apply_cu_three_teachings.py --apply   # ④ + 写盘（默认 dry run）
python _make_cu_world_spec.py      # 出全球覆盖率图 spec
python _make_cu_target_spec.py     # 出中日韩覆盖率图 spec
```

**幂等性坑**：`_apply_cu_three_teachings.py` 会把 `faith = X` 行换成 `rite = Y`，
重跑时读不到原来的 faith，所以**必须先从备份还原再重跑**：

```bash
cp <备份>/history/provinces/00_generated_provinces.txt <MOD>/history/provinces/
```

## 三教转换规则（`_apply_cu_three_teachings.py`）

| 范围 | 接受的值 | 无效值兜底 |
|---|---|---|
| 中国四 kingdom，faith ∈ {`confucian_faith`,`shangqing_faith`,`zhengyi`,`mahayana_faith`,`manichaean_faith`} | `daoxue`/`jingxue`/`confucian_faith`、`shangqing`/`quanzhen`/`zhengyi`、佛教 14 个 rite、`mingism` | `dhyana` 禅宗 |
| 朝鲜，`faith = mahayana_faith` | CU 的 rite 或 faith | `dhyana` 禅宗 |
| 日本，`faith = shinto_faith` | CU 的 rite 或 faith | `shinto` 神道教 |

**只动这三个范围**，非三教省（`bimoism`/`moism`/`dab_qhuas`/`satsana_phi`/`tengri_pagan`/…）
是之前按 EU5 religion→CK3 faith 映射表投好的，**不许被 CU 覆盖**。

## 已知的分布偏差（CU 数据本身的问题，不是投射错）

- **全真教只有祖庭级点位**：CU 全库 `rite = quanzhen` 只有 2 处，铺满伯爵领后放大成十几省，全在山东。1337 年全真早已是华北第一大派，CU 没做这个扩散。
- **上清派点位散**：CU 只有约 10 个省块，江南反而少。
- **日本只有神道省被转换**，镰仓佛教（净土宗、禅宗）在 CU 里没有数据。
- **CU 的默认 faith 是 vanilla `pagan`**：那 18000 多个没写 history 的省在 CU 里就是 pagan，拿它当数据等于拿默认值当依据。
