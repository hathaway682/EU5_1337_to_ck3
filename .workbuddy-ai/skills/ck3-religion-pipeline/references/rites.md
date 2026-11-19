# rite / faith 速查

## 一、先记住三条

1. **判「这个 rite 能不能挂到这个省」看 religion，不看 faith。**
   省 `faith = orthodox` + `rite = slavic_rite`（绑 `christian_faith`）是对的，两者都在 `christianity_religion`。
   省 `faith = confucian_faith` + `rite = quanzhen`（绑 `shangqing_faith`，属 `taoism_religion`）是错的。
2. **只有 21 个 faith 有多个 rite**，其余 82 个 faith 都是「一个 faith 一个同名 rite」，**根本不用写 rite 行**（靠 `main_rite` 回落）。
3. **中文名一律查原版本地化**：`E:\SteamLibrary\steamapps\common\Crusader Kings III\game\localization\simp_chinese\`
   （注意有 `game\` 这一层）。mod 自己的 `localization/simp_chinese/` 只覆盖了少部分 key。
   `grep -rn "^shangqing:" <原版loc>` 就是最快的查法。

## 二、多 rite 的 faith 全表（★ = 该 faith 的 main_rite，不写就落这个）

### 佛教
| faith | 中文 | rites |
|---|---|---|
| `mahayana_faith` | 大乘佛教 | `mahayana`★、`dhyana`禅宗、`sukhavati`净土宗、`pundarika`法华宗、`avatamsaka`华严宗、`yogacara`唯识宗、`vinaya`律宗 |
| `vajrayana_faith` | 金刚乘佛教 | `lamaism`★藏传佛教、`acharya`阿吒力教、`mantrayana`真言宗、`vajrayana`金刚乘佛教、`ari`阿利僧派 |
| `theravada_faith` | 上座部佛教 | `theravada`★（只有一个） |
| `maitreya_faith` | 弥勒教 | `maitreya`（**faith 本身没有 main_rite**，靠 `history/faiths/00_eastern_misc.txt` 按日期定） |

### 中国三教 / 日本 / 朝鲜
| faith | 中文 | rites |
|---|---|---|
| `confucian_faith` | 儒家 | `daoxue`道学、`jingxue`经学（**没有 main_rite**，`history/faiths/00_eastern_misc.txt` 1337 = `daoxue`） |
| `shangqing_faith` | **上清派** | `shangqing`★上清派、`quanzhen`全真派 |
| `shinto_faith` | 神道教 | `shinto`★神道教、`shugendo`修验道 |
| `manichaean_faith` | 摩尼教 | `manichean`★摩尼教、`mingism`明教 |
| `bon_faith` | 苯教 | `bon`★居苯派、`old_bon`恰苯派 |

> **上清派 = `shangqing_faith`（faith 名），全真派 = `quanzhen`（rite 名）**。所以一个省 `faith = shangqing_faith` 时游戏显示「上清派」；要显示「全真派」得写 `rite = quanzhen`。

### 伊斯兰
| faith | 中文 | rites |
|---|---|---|
| `sunni` | 逊尼派 | `hanafi`★哈乃斐、`maliki`马立克、`shafii`沙斐仪、`hanbali`罕百里、`sahabah`直传派、`tabiun`再传派 |
| `shia` | 什叶派 | `imami`★十二伊玛目、`ismaili`伊斯玛仪、`zayidi`栽德、`nizari`尼扎里耶、`hafizi`哈菲兹、`alawite`阿拉维、`alevi`阿列维、`ghulat`伊赫提拉夫 |
| `kharijite` | 哈瓦利吉派 | `ibadi`★出走派、`azariqa`、`najdat`、`sufri` |

### 基督教
| faith | 中文 | rites |
|---|---|---|
| `christian_faith` | 迦克墩基督教 | `roman_rite`★罗马礼、`byzantine_rite`希腊礼、`slavic_rite`斯拉夫礼、`georgian_rite`格鲁吉亚礼、`insular_celtic`海岛礼、`mozarabic_church`穆扎赖卜礼、`ambrosian_rite`安布罗斯礼、`beneventan_rite`贝内文托礼、`carolingian_christianity`加洛林礼 |
| `miaphysitism` | 科普特正教 | `coptic_rite`★科普特礼、`ethiopian_rite`吉兹礼、`antiochian_rite`安条克礼 |
| `armenian_apostolic` | 亚美尼亚宗徒教会 | `armenian_rite`★ |

> **基督教是特例**：9 个礼全绑在伞形 faith `christian_faith` 上，而省份写 `orthodox` / `catholic`。所以「rite 父 faith ≠ 省 faith」在这里是**正常**的，不要当 bug 改。

### 印度教 / 其他
| faith | 中文 | rites |
|---|---|---|
| `vaishnava_faith` | 毗湿奴派 | `vaishnavism`★、`krishnaism`奎师那派 |
| `shaiva_faith` | 湿婆派 | `shaivism`★、`advaitism`不二论吠檀多派 |
| `shakta_faith` | 性力派 | `srikula_shaktism`★、`kalikula_shaktism` |
| `jain_faith` | 耆那教 | `digambara`★天衣派、`svetambara`白衣派、`yapaniya`耶波尼耶派 |
| `gnostic_faith` | 诺斯替派 | `valentinianism`★、`cainitism`、`priscillianism` |
| `yazidi_faith` | 雅兹迪教 | `yazidi`★、`meshefaresism`、`kitebacilweism` |
| `mandaean_faith` | 曼达派 | `mandeaism`★、`sabianism` |
| `rabbinic_faith` | 拉比派 | `rabbinism`★、`merkabah` |

## 三、一 faith 一 rite、但名字不同的（写 rite 行才有意义）

`armenian_apostolic`→`armenian_rite`、`theravada_faith`→`theravada`、`maitreya_faith`→`maitreya`、
`sadr_al_islam`→`nabi`、`cathar`→`cathar_rite`、`waldensian`→`waldensian_rite`、
`lollard`→`lollard_rite`、`hussite`→`hussite_rite`、`joachimite`→`joachimite_rite`、
`iconoclast`→`iconoclast_rite`、`bogomilist`→`bogomilist_rite`、`paulician`→`paulician_rite`、
`messalian`→`messalian_rite`、`adoptionist`→`adoptionist_rite`

其余 67 个 faith 的 rite 与 faith 同名（`bimoism`/`moism`/`tengri_pagan`/`kaharingan`/…），
**不写 rite 行，靠 main_rite 自动落**。

## 四、各地区既定口径

| 区域 | 口径 | 依据 |
|---|---|---|
| 东亚佛教 | EU5 sect 国际组织，**sect 身份 = `laws` 首个元素**；DAI/KOR→`dhyana`、SSG→`sukhavati`（用户 2026-10-22 指定，覆盖多 sect 身份） | `_apply_sect_rite.py` |
| 藏传 | 五派（萨迦/噶当/噶举/宁玛/觉囊）全部自动落 `lamaism`（`vajrayana_faith` 的 main_rite 已改成 lamaism） | 同上 |
| 根本说一切有部 | 10 个成员 52 省写 `vinaya` | 同上 |
| 中国三教省 | 按 CU，只接受 `daoxue/jingxue/confucian_faith`、`shangqing/quanzhen/zhengyi`、佛教 14 个、`mingism`；否则禅宗兜底 | `_apply_cu_three_teachings.py` |
| 朝鲜 | 大乘佛教省按 CU；无效值 → `dhyana` 兜底 | 同上 |
| 日本 | 神道教省按 CU；无效值 → `shinto` 兜底 | 同上 |
| 伊斯兰 | 按 EU5 国家 `religious_school`；owner 帮不上时按接壤传播 | `_apply_rites.py` + `_apply_islamic_geo_spread.py` |
| 东正教 | 按 owner 国家 `liturgical_language`（教会斯拉夫→`slavic_rite`、希腊→`byzantine_rite`、格鲁吉亚四国→`georgian_rite`） | `_apply_christian_rites.py` |
| 一性论 | 按 owner 礼仪语言（geez→`ethiopian_rite`、armenian→`armenian_rite`），找不到再按男爵领自己的 culture | 同上 |
| 波斯尼亚 BOS | 直接写 `faith = bosnian_church`（独立 faith，不是 rite） | 同上 |
| 印度教 | **教随国定**：EU5 tag → `hindu_branch` 成员 → 支派 → faith | `_apply_hindu_faith_branch.py` |
| 大理 / 阿吒力 | `rite = acharya` 且**删掉 faith 行**（`acharya` 绑 `vajrayana_faith`） | `_apply_buddhist_geo_spread.py` |

## 五、查名字

```bash
# 原版（最权威）
grep -rn "^shangqing:" "E:/SteamLibrary/steamapps/common/Crusader Kings III/game/localization/simp_chinese/"

# mod 自己的覆盖（少）
grep -rn "shangqing" <MOD>/localization/simp_chinese/

# 用 skill 脚本一次查全（原版 + mod，mod 优先）
python .workbuddy-ai/skills/ck3-religion-pipeline/scripts/religion_audit.py --rite quanzhen
```
