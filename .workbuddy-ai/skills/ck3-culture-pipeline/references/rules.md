# 判据层级与四张规则表

## 唯一真源

`gen_debug/_classify_cultures.py` 里的四张表是**唯一真源**，`gen_debug/_culture_classification.csv`
是它的产物。改落点永远先改表，再重新生成 / 同步 CSV。

| 表 | 条数（2026-10） | 作用域 |
|---|---:|---|
| `CULT_RULE` | 272 | 单个 EU5 文化 → CK3 文化 |
| `GROUP_RULE_STRONG` | 6 | 整组强制决断，在 `LANG_RULE` **之前**查 |
| `LANG_RULE` | 309 | 按 EU5 语言（一个语言下所有文化） |
| `GROUP_RULE` | 155 | 按文化组，在 `LANG_RULE` **之后**查 |

## 判定优先级（从高到低）

```
CULT_RULE  >  自动同名  >  GROUP_RULE_STRONG  >  LANG_RULE  >  GROUP_RULE  >  自动（语言唯一/传承唯一）
```

- **`CULT_RULE` 优先级最高**：写了文化级规则，组级和语言级都管不到它。所以想压住
  `LANG_RULE` 就写 `CULT_RULE`。
- **`GROUP_RULE_STRONG` 的生效条件**：该组必须排在 `eu5_groups` 的**第一位**（不是「只挂这一个组」）。
  例：班图 95 个里 58 个是 `bantu_group;xxx_group`，只认单组会漏一半；而
  `jurchen_group;tungusic_group` 的 jurchen 在首位，女真不会被 `tungusic_group` 抢走。
- **`GROUP_RULE` 不能整体提到 `LANG_RULE` 之前**：155 条里绝大多数是 `r(10,"")`/`r(11,"")` 占位，
  提上来实测让 17 个文化改错（犹太人压成 radhanite、swahili 退化 NEW:、khas/tharu→bodpa、
  maden→NEW:halmaheran、nivkh→mohe）。
- **光加 `GROUP_RULE` 常常无效**：`GROUP_RULE` 里根本没有 cushitic / nilotic / west_african /
  central_african 这些条目，接管它们的是 `LANG_RULE` 的 `r(9,...)`「需建分离文化」占位。
  这种要写 `CULT_RULE` 才管用。

## 规则行写法

```python
r(category, "target", "说明")
```

- `category` 决定 CSV 的 `category` 列：1-9 = **CU 地图范围内**（会被
  `_apply_province_pop_culture.py` 默认落地），10-11 = **图外自创 / 图外可参考**（默认不碰）。
- `"target"` 填 CK3 文化 key；`""` 表示保留占位不决断；`"NEW:xxx"` 表示保留 EU5 key（落地脚本跳过）。

## 怎么加一条

1. 在 `CULT_RULE` 里找到同类区块（欧洲/非洲/亚洲/美洲…），按字母序插入一行。
2. 如果这个文化还会被 `LANG_RULE` 收走，**两条都改**保持一致（只有 `CULT_RULE` 生效，
   但两条一致能防止以后误读）。
3. 改完必须用 `ast` 扫重复 key（见 `references/pitfalls.md`）。
4. 然后按 `references/pipeline.md` 的流程同步 CSV + 省份 + 人物层。

## 常见误判

- **本地化永远比 key 权威**：`turkish`=乌古斯、`kazani`≠哈萨克、`samoyed` 显示「Bjarmian」、
  `maluku` 显示「文老古」、`nakkavaram` 显示「那旺」、`khazar` 显示「可萨」。
- **EU5 key 与中文名错位**：`azeri_culture`=**阿塞拜疆**（turkic）不是阿扎里；
  `adhari_culture` / `talysh_culture` 是伊朗语支；`zaza_culture` 实为库尔德语支。
  EU5 把 adhari/talysh/zaza 都塞进 `adharic_language`，按语言并入会全变突厥。
- **同组不同族**：`avar_culture` 是高加索阿瓦尔，与 CK3 潘诺尼亚 `avar` 同名异族。
- **双义 key**：`prussian` 在省份层是 EU5 德意志普鲁士（→saxon），在人物层是波罗的普鲁士人（不动）。
- **语言归属要查 EU5 原始数据**：`arpitan` 看着像奥克-罗曼，EU5 实际放在
  `french_group;swiss_group` / `arpitan_dialect`，属法语支。
