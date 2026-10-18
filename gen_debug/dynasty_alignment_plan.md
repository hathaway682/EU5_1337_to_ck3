# 宗族（dynasty）层对齐原版 — 完整清单

> 方法：B 路。保留 42 宗族归并，只把每个父宗族的 `name` 改为 vanilla 本地化键，
> 并在 `common/coat_of_arms/coat_of_arms/95_zz_eu5_dynasty_aliases.txt`（95_ 前缀，晚于 vanilla 90_ 加载）追加纹章别名。
> 角色对父宗族的 `dynasty = xxx` 引用不变（key 没动），故支系关系完整保留。
> 批量脚本：`gen_debug/align_dynasties.py`（CRLF+BOM 安全、带备份、逐键自检）。

## 已对齐 27 个（3 先前 + 24 批量）

### 先前 3 个
| mod 宗族 | name 键 | COA 目标 | 备注 |
|---|---|---|---|
| seiwa_genji_dynasty | dynn_Minamoto | japanese_minamoto_seiwa | 源氏 / 蓝底龙胆纹 |
| robertian_dynasty | dynn_Robertine | 743 | 罗贝尔 / 蓝黄棋盘纹 |
| anjou_jerusalem_dynasty | dynn_Anjou | 723 | 安茹 / c_anjou；独立主家，不并入 robertian |

### 批量 24 个（含纹章 18 + 仅改名 6）
| mod 宗族 | name 键 | COA 目标 | 类别 |
|---|---|---|---|
| kudou_dynasty | dynn_KudO_ | japanese_kudo | 单一明确+有纹章 |
| uda_genji_dynasty | dynn_Minamoto | japanese_minamoto_uda | 单一明确+有纹章 |
| saga_genji_dynasty | dynn_Minamoto | japanese_minamoto_saga | 单一明确+有纹章 |
| murakami_genji_dynasty | dynn_Minamoto | japanese_minamoto_murakami | 单一明确+有纹章 |
| ooe_dynasty | dynn_O_e | japanese_oe | 单一明确+有纹章 |
| saitou_dynasty | dynn_SaitO_ | japanese_saito | 单一明确+有纹章 |
| takashina_dynasty | dynn_Takashina | japanese_takashina | 单一明确+有纹章 |
| hatano_dynasty | dynn_Hatano | japanese_hatano | 单一明确+有纹章 |
| yamato_dynasty | dynn_Yamato | japanese_yamato | 单一明确+有纹章 |
| aleramici_dynasty | dynn_Aleramicci | 206 | 单一明确+有纹章 |
| angelos_dynasty | dynn_Angelos | 195 | 单一明确+有纹章 |
| blois_dynasty | dynn_Blois | 721 | 单一明确+有纹章 |
| hohenzollern_dynasty | dynn_Hohenzollern | 12476 | 单一明确+有纹章 |
| de_brienne_dynasty | dynn_Brienne | 80 | 单一明确+有纹章 |
| taira_dynasty | dynn_Taira | japanese_taira_kanmu | 多候选取主分支 |
| fujiwara_dynasty | dynn_Fujiwara | japanese_fujiwara | 多候选取主分支 |
| orsini_dynasty | dynn_Orsini | 2 | 多候选取主分支 |
| barcelona_dynasty | dynn_Barcelona | 100204 | 多候选取主分支 |
| kondou_dynasty | dynn_KondO_ | —（无 vanilla COA） | 单一明确+无纹章，仅改名 |
| tatara_dynasty | dynn_Tatara | —（无 vanilla COA） | 单一明确+无纹章，仅改名 |
| oyama_dynasty | dynn_Oyama | —（无 vanilla COA） | 单一明确+无纹章，仅改名 |
| antelminelli_dynasty | dynn_Antelminelli | —（无 vanilla COA） | 单一明确+无纹章，仅改名 |
| lomagne_dynasty | dynn_Lomagne | —（无 vanilla COA） | 单一明确+无纹章，仅改名 |
| subic_dynasty | dynn_S_ubiC_ | —（无 vanilla COA） | 单一明确+无纹章，仅改名 |

> name 键里 `dynn_KudO_` / `dynn_SaitO_` / `dynn_KondO_` / `dynn_O_e` / `dynn_S_ubiC_` 是 vanilla 原样大写怪字符，必须照搬，否则中文不显示。

## 保持 mod 自定义 15 个（无原版对应）
ivree、nakamura、utsunomiya、kawano、sanjou、shimazu、al_fadl、asturleonesa、chuujou、deste、montfort_feldkirch、seljukids、sratsimir、vatatzes、zovneski

## 产物/备份
- 改动文件：`common/dynasties/zz_eu5_dynasties.txt`（24 处 name）、`common/coat_of_arms/coat_of_arms/95_zz_eu5_dynasty_aliases.txt`（+18 行）
- 备份：`common/dynasties/zz_eu5_dynasties.txt.20261018_210407.bak`
- 脚本：`gen_debug/align_dynasties.py`

## 可选收尾
- 24 个宗族原 mod 本地化键（如 `kudou_dynasty` / `fujiwara_dynasty` …）变孤儿键，无害；是否清理待定。
