# faith / rite 定义、教义、宗教领袖

## 一、定义分散在四个地方

| 内容 | 文件 | 本 mod 有没有 |
|---|---|---|
| faith 定义（`main_rite`、`faith_details.religion`、`holy_sites`、doctrines） | `common/religion/faith_types/00_faith_types.txt` | **没有**，全继承原版 |
| rite 定义（`faith =` 父信仰、图标、doctrines） | `common/religion/rite_types/*.txt` | **没有**，全继承原版 |
| 信仰史（按日期开 `created`、定 `main_rite`、给教义、指定宗教领袖） | `history/faiths/*.txt` | **有**，16 个文件 |
| 宗教领袖头衔 | `common/landed_titles/zzz_eu5_faith_heads.txt` | **有**，5 个 |

**mod 里 `common/religion/faith_types/` 和 `rite_types/` 根本不存在。** 所以：
- `religion_audit.py` / `religion_set.py` 的 faith/rite 定义表是从**原版**读的（`_common.py` 的 `_pick()` 先找 mod 再回落原版）；
- 你在省份里写 `faith = shangqing_faith`，那个 faith 是原版 CK3 就有的，不是本 mod 铸的；
- 想改某个 faith 的教义/圣地绑定，必须**新建** `common/religion/faith_types/00_faith_types.txt`，见第五节。

## 二、faith 与 rite 的关系

```
religion（伊斯兰教）
  └── faith（逊尼派）        ← 地图上色单位，省份写 faith =
        └── rite（哈乃斐派）  ← 学派/教会细分，省份写 rite =
```

- 每个 faith 有 `main_rite = X`。省只写 `faith` 不写 `rite` 时按 `main_rite` 回落。
- 每个 rite 有 `faith = Y`，即它挂在哪个 faith 下。
- **判 rite 能不能挂到某省看 religion，不看 faith**（详见 `rites.md`）。

## 三、信仰史：`history/faiths/*.txt`

格式由 `_faith_history.info` 定义，顶层 key 是 faith，下面是日期块：

```txt
shaiva_faith = {
    867.1.1 = {
        known = {
            tenet_mendicant_preachers
            tenet_esotericism
            ...
        }
    }
}
```

日期块里能写的（见 `_faith_history.info`）：
- `created = yes` —— 没有角色/省份用到的 faith 默认算「未创立」，要在这里标记；
  但**只要角色或省份用了它，就自动算已创立**，所以 mod 里 55 个 faith 一般不需要手写。
- `main_rite = X` —— 该日期起的主礼。**改主礼必须同时改 faith_types 里的注释**，
  因为 `confucian_faith` / `maitreya_faith` 这两个没有 `main_rite`，完全靠这里按日期定。
- 教义（`known = { ... }` / `permitted = { ... }`）
- 宗教领袖头衔

**注意**：这里写的是**原版 faith 的历史**，改它等于改原版行为。改之前确认这个 faith 在本 mod 确实在用。

## 四、宗教领袖：`zzz_eu5_faith_heads.txt`

本 mod 保留的 5 个头衔，key 全部沿用原版（因为原版 faith 的 `head_of_rite = <key>` 是按 key 找的）：

| key | 对应 |
|---|---|
| `k_papal_state` | 教皇 |
| `k_orthodox` | 君士坦丁堡牧首 |
| `d_coptic_papacy` | 亚历山大牧首 |
| `d_apostolic_church` | 西斯（亚美尼亚）牧首 |
| `d_patriarchate_in_the_east` | 摩苏尔牧首 |

写法要点（文件头注释里有完整说明）：
- `landless = yes` —— 教座只是法理指针，不能占别人的地；
- `capital = c_xxx` —— 指向教座所在的伯爵领；
- 带继承人字段，让职位在继承中不断档；
- **不要**再在 `zz_vanilla_titulars.txt` 里写同名 shim —— titular guard 会在头衔被持有的第一天把 shim 销毁，
  所以真正的声明搬到了这个文件。

## 五、新建一个 faith（只有确实需要时才做）

CK3 里同名块是**整块替换**，不是字段合并。所以在 mod 建 `common/religion/faith_types/00_faith_types.txt` 时：

- 只放**新增**的 faith → 原版 faith 不受影响（这是安全做法）；
- 想改原版某个 faith 的字段 → 必须把那个 faith 的**整块**抄过来再改，抄漏一个字段就是把它冲掉。

最小写法：

```txt
my_new_faith = {
    main_rite = my_new_rite

    faith_details = {
        religion = christianity_religion
        color = { 0.5 0.5 0.5 }
        graphical_faith = catholic_gfx
        # head_of_rite = k_xxx      # 有宗教领袖才写
    }

    holy_sites = { jerusalem rome }   # key 必须存在于 holy_site_types
    doctrines = { ... }
}
```

配套还要有：
1. rite 定义（`common/religion/rite_types/`），写 `faith = my_new_faith`；
2. 本地化 `my_new_faith:` / `my_new_rite:`（见下）；
3. 信仰史（可选，要开 `created` 或按日期换主礼才写）。

## 六、本地化

faith / rite 的显示名就是**同名的本地化 key**，位置：

```
<CK3>/game/localization/simp_chinese/religion/religion_<组>_l_simp_chinese.yml
```

```yml
vaishnava_faith: "毗湿奴派"
quanzhen: "全真派"
```

- 新增 faith/rite 时，**每种语言都要加**，否则游戏里显示原始 key。
- 查不到名字就查原版，**不许编**。`religion_audit.py` 的中文名就是从 mod + 原版 loc 合并来的。

## 七、验证

```bash
$PY $SK/religion_audit.py          # 会报「省份里出现但 faith_types 未定义的 faith/rite」
$PY $SK/religion_chars.py          # 角色层同理
```

这两条报 0，说明省份/角色写的每个 faith/rite 都有定义。
