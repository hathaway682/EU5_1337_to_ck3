# 原始宗教按信徒语系分类

数据源：EU5 `06_pops.txt` 逐条 `define_pop`（culture + religion + size）。
判定链：religion → 信徒的 culture 人口分布 → culture 的 `language` → 语言的 `family`；
EU5 有 18 个语言没写 `family`，改用该文化的 `culture_groups` 兜底。

## 一、非洲原始宗教（`folk_african_group`）

### 班图语系（`bantu_language_family`） —— 4 个宗教，信徒 11808

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `bantu_religion` | 班图拜物教 | 10566 | 95% | rwanda_culture | — |
| `cwezi_religion` | 契韦齐信仰 | 931 | 100% | rutara_culture | — |
| `badimo_religion` | 巴迪莫祖灵信仰 | 296 | 100% | tswana_culture | — |
| `fang_religion` | 梅贝格崇拜 | 15 | 100% | fang_culture | — |

### 南沃尔特语系（`south_volta_language_family`） —— 5 个宗教，信徒 3353

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `isese_religion` | 奥里沙教 | 1774 | 89% | yoruba | 北沃尔特语系 11% |
| `akan_religion` | 阿科姆教 | 782 | 100% | akan | — |
| `abwoi_religion` | 阿布沃伊崇拜 | 320 | 100% | benue | — |
| `odinala_religion` | 奥迪纳拉教 | 245 | 100% | igbo | — |
| `vodun_religion` | 巫毒教 | 231 | 100% | ewe | — |

### 北沃尔特语系（`north_volta_language_family`） —— 11 个宗教，信徒 2482

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `rogo_miki_religion` | 罗戈米基古道 | 711 | 100% | mossi | — |
| `adamawa_religion` | 阿达马瓦信仰 | 613 | 100% | adamawa_culture | — |
| `nyesoa_religion` | 尼亚索阿教 | 293 | 100% | eastern_kru | — |
| `buyli_religion` | 布格利崇拜 | 259 | 100% | dagbani | — |
| `mbori_religion` | 姆博里教 | 204 | 67% | zande_culture | 中苏丹语系 33% |
| `banda_religion` | 班达泛灵论 | 97 | 100% | banda_culture | — |
| `ngbandi_religion` | 恩本迪拜物教 | 95 | 100% | ngbandi_culture | — |
| `naa_wuni_religion` | 纳乌尼信仰 | 72 | 100% | mamprusi | — |
| `eso_religion` | 埃索信仰 | 61 | 100% | kabiye | — |
| `ebore_religion` | 埃博里教 | 50 | 100% | gonja | — |
| `bua_religion` | 布阿泛灵论 | 28 | 100% | gula_iro_culture | — |

### 尼罗特语系（`nilotic_language_family`） —— 6 个宗教，信徒 1835

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `muonyjang_religion` | 坚格信仰 | 616 | 91% | dinka_culture | — |
| `maasai_religion` | 尼亚加崇拜 | 413 | 98% | ongamo_culture | — |
| `nyasaye_religion` | 尼亚萨耶教 | 312 | 100% | luo_culture | — |
| `akuj_religion` | 阿库吉教 | 252 | 100% | turkana_culture | — |
| `asis_religion` | 阿西斯教 | 215 | 100% | tatoga_culture | — |
| `ajok_religion` | 阿约克崇拜 | 28 | 100% | otuho_culture | — |

### 乍得语系（`chadic_language_family`） —— 2 个宗教，信徒 1643

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `bori_religion` | 博里泛灵论 | 1106 | 100% | hausa | — |
| `sao_religion` | 萨奥信仰 | 537 | 66% | sao_culture | 中苏丹语系 33% |

### 大西洋语系（`atlantic_language_family`） —— 5 个宗教，信徒 1145

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `kuru_masaba_religion` | 库鲁·马萨巴信仰 | 482 | 100% | temne | — |
| `geno_religion` | 格诺崇拜 | 274 | 100% | wolof | — |
| `nhaala_religion` | 纳阿拉信仰 | 220 | 100% | balanta | — |
| `a_fat_roog_religion` | 鲁格至大教 | 124 | 100% | serer | — |
| `emit_religion` | 埃米泰信仰 | 45 | 100% | jola | — |

### `mande_language`（无 language_family） —— 1 个宗教，信徒 856

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `nyama_religion` | 恩亚马信仰 | 856 | 93% | mandinka | — |

### 东苏丹语系（`eastern_sudanic_language_family`） —— 2 个宗教，信徒 568

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `kalge_religion` | 卡尔格教 | 338 | 80% | daju_culture | 撒哈拉语系 10% |
| `musala_religion` | 穆萨拉教 | 230 | 82% | nuba | — |

### 库施特语系（`cushitic_language_family`） —— 1 个宗教，信徒 501

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `waaqeffanna_religion` | 瓦格教 | 501 | 100% | dahalo_culture | — |

### 巴里托语族（`barito_language_family`） —— 1 个宗教，信徒 484

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `fomba_gasy_religion` | 丰巴加西崇拜 | 484 | 100% | sakalava_culture | — |

### 中苏丹语系（`central_sudanic_language_family`） —— 2 个宗教，信徒 298

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `ori_religion` | 奥里祖灵崇拜 | 181 | 100% | madi_culture | — |
| `lugbara_religion` | 阿德罗教 | 118 | 100% | lugbara_culture | — |

### `ijaw_language`（无 language_family） —— 1 个宗教，信徒 271

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `ijaw_religion` | 埃格贝苏教 | 271 | 100% | ijaw | — |

### `khoe_language`（无 language_family） —— 1 个宗教，信徒 232

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `kaggen_religion` | 卡根神话 | 232 | 51% | kung_culture | kxa_language 32%、tuu_language 16% |

### 闪米特语系（`semitic_language_family`） —— 2 个宗教，信徒 109

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `rebba_religion` | 雷巴教 | 85 | 100% | gumuz_culture | — |
| `anna_religion` | 阿拿教 | 24 | 100% | kunama_culture | — |

### `omotic_language`（无 language_family） —— 1 个宗教，信徒 100

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `omo_religion` | 奥莫信仰 | 100 | 100% | gonga_culture | — |

### 撒哈拉语系（`saharan_language_family`） —— 2 个宗教，信徒 58

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `karama_religion` | 卡拉玛仪俗 | 30 | 100% | zaghawa_culture | — |
| `songhai_religion` | 桑海信仰 | 27 | 100% | songhai | — |

### `tamazight_language`（无 language_family） —— 2 个宗教，信徒 45

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `guanche_religion` | 阿查曼教 | 24 | 100% | guanche | — |
| `godala_religion` | 戈达拉信仰 | 21 | 100% | godala_culture | — |

### `dogon_language`（无 language_family） —— 1 个宗教，信徒 22

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `dogon_religion` | 锡圭教 | 22 | 100% | dogon | — |

## 二、亚洲原始宗教（`folk_asian_group`）

### `mongolian_language`（无 language_family） —— 1 个宗教，信徒 5557

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `tengri` | 腾格里 | 5557 | 62% | mongolian_culture | 突厥语系 35% |

### 通古斯语系（`tungusic_language_family`） —— 1 个宗教，信徒 3728

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `tungusic_shamanism` | 通古斯萨满教 | 3728 | 99% | jurchen_culture | — |

### 南亚语系（`austroasiatic_language_family`） —— 14 个宗教，信徒 2115

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `sarna_religion` | 娑罗教 | 855 | 83% | santal_culture | 达罗毗荼语系 17% |
| `muong_religion` | 芒教 | 333 | 100% | muong_culture | — |
| `ka_niam_khasi_religion` | 卡尼阿姆教 | 205 | 100% | khasi_culture | — |
| `orang_asli_religion` | 阿斯里泛灵论 | 157 | 100% | orang_asli_culture | — |
| `bru_religion` | 布鲁泛灵论 | 138 | 100% | bru_culture | — |
| `palaung_religion` | 崩龙泛灵论 | 130 | 100% | palaung_culture | — |
| `bahnar_religion` | 巴拿泛灵论 | 89 | 100% | bahnar_culture | — |
| `wa_religion` | 木依吉崇拜 | 72 | 100% | wa_culture | — |
| `sora_religion` | 萨瓦拉泛灵论 | 64 | 100% | sora_culture | — |
| `sedang_religion` | 色当泛灵论 | 25 | 100% | sedang_culture | — |
| `kharia_religion` | 卡里亚泛灵论 | 25 | 100% | kharia_culture | — |
| `juang_religion` | 朱昂泛灵论 | 12 | 100% | juang_culture | — |
| `blang_religion` | 布朗泛灵论 | 8 | 100% | blang_culture | — |
| `nicobarese_religion` | 尼科巴泛灵论 | 2 | 100% | nicobarese_culture | — |

### 萨尔语族（`sal_language_family`） —— 14 个宗教，信徒 2100

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `koch_religion` | 库奇泛灵论 | 403 | 100% | koch_culture | — |
| `mizo_religion` | 米佐泛灵论 | 399 | 100% | zo_culture | — |
| `bathou_religion` | 巴图教 | 226 | 100% | bodo_culture | — |
| `donyi_polo_religion` | 冬尼波罗教 | 214 | 100% | tani_culture | — |
| `songsarek_religion` | 松萨雷泛灵论 | 162 | 100% | garo_culture | — |
| `dimasa_religion` | 戴科泛灵论 | 138 | 100% | dimasa_culture | — |
| `naga_religion` | 那加泛灵论 | 123 | 100% | naga_culture | — |
| `tiwa_religion` | 蒂瓦泛灵论 | 114 | 100% | tiwa_culture | — |
| `karbi_religion` | 米基尔泛灵论 | 108 | 100% | karbi_culture | — |
| `chutia_religion` | 久蒂亚泛灵论 | 83 | 100% | chutia_culture | — |
| `rabha_religion` | 拉巴泛灵论 | 50 | 100% | rabha_culture | — |
| `kundism_religion` | 昆迪泛灵论 | 47 | 100% | deori_culture | — |
| `mishmi_religion` | 米什米泛灵论 | 22 | 100% | mishmi_culture | — |
| `jingpo_religion` | 载瓦泛灵论 | 10 | 100% | jingpo_culture | — |

### `hmong_language`（无 language_family） —— 2 个宗教，信徒 1511

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `yao_religion` | 梅山教 | 961 | 100% | yao_china_culture | — |
| `hmongism` | 章夸教 | 550 | 100% | hmong_culture | — |

### 缅语族（`burmic_language_family`） —— 9 个宗教，信徒 1297

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `bimoism` | 毕摩教 | 703 | 100% | yi_culture | — |
| `karen_religion` | 克伦泛灵论 | 402 | 100% | karen_culture | — |
| `lisu_religion` | 傈僳泛灵论 | 44 | 100% | lisu_culture | — |
| `ngacang_religion` | 阿昌泛灵论 | 40 | 100% | ngacang_culture | — |
| `hani_religion` | 哈尼泛灵论 | 32 | 100% | hani_culture | — |
| `lahu_religion` | 厄莎信仰 | 30 | 100% | lahu_culture | — |
| `dongba_religion` | 东巴教 | 24 | 100% | nashi_culture | — |
| `jino_religion` | 基诺泛灵论 | 19 | 100% | jino_culture | — |
| `nu_religion` | 怒族泛灵论 | 2 | 100% | nu_culture | — |

### 达罗毗荼语系（`dravidian_language_family`） —— 3 个宗教，信徒 1191

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `koyapunem_religion` | 拘耶补念教 | 1073 | 100% | gond | — |
| `khond_religion` | 孔德泛灵论 | 68 | 100% | khond_culture | — |
| `gosain_religion` | 戈赛因派 | 51 | 100% | malto_culture | — |

### 壮侗语系（`tai_language_family`） —— 1 个宗教，信徒 1176

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `moism` | 麽教 | 1176 | 100% | zhuang_culture | — |

### `tujia_language`（无 language_family） —— 1 个宗教，信徒 671

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `nuo_religion` | 傩教 | 671 | 100% | tujia_culture | — |

### 藏语系（`tibetic_language_family`） —— 3 个宗教，信徒 355

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `shamanism` | 萨满教 | 143 | 92% | magar_culture | — |
| `kirat_mundhum_religion` | 门顿教 | 127 | 100% | kirati_culture | — |
| `monpa_religion` | 门巴泛灵论 | 85 | 100% | monpa_culture | — |

### `kam_language`（无 language_family） —— 4 个宗教，信徒 305

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `kam_religion` | 萨岁崇拜 | 254 | 100% | kam_culture | — |
| `sui_religion` | 水书信仰 | 42 | 100% | sui_culture | — |
| `mulam_religion` | 仫佬民俗信仰 | 5 | 100% | mulam_culture | — |
| `maonan_religion` | 毛南民俗信仰 | 4 | 100% | maonan_culture | — |

### 汉语系（`chinese_language_family`） —— 1 个宗教，信徒 183

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `wu_religion` | 巫觋教 | 183 | 100% | she_culture | — |

### `formosan_language`（无 language_family） —— 1 个宗教，信徒 169

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `formosan_religion` | 汉图泛灵论 | 169 | 100% | formosan_culture | — |

### 日本语系（`japonic_language_family`） —— 1 个宗教，信徒 144

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `utaki_religion` | 御岳崇拜 | 144 | 100% | ryukyu_culture | — |

### `qiangic_language`（无 language_family） —— 1 个宗教，信徒 64

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `rmaism` | 白石崇拜 | 64 | 100% | rma_culture | — |

### `ainu_language`（无 language_family） —— 1 个宗教，信徒 39

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `ainu_religion` | 神威信仰 | 39 | 100% | ainu_culture | — |

### `yukaghir_language`（无 language_family） —— 1 个宗教，信徒 36

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `yukaghir_shamanism` | 尤卡吉尔萨满教 | 36 | 100% | yandyr_culture | — |

### 印度-雅利安语系（`indic_language_family`） —— 1 个宗教，信徒 27

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `vedda_religion` | 维达泛灵论 | 27 | 100% | vedda | — |

### `chukotko_kamchatkan_language`（无 language_family） —— 1 个宗教，信徒 14

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `chukchi_shamanism` | 楚科奇萨满教 | 14 | 100% | chukchi_culture | — |

### 爱斯基摩-阿留申语系（`eskaleut_language_family`） —— 1 个宗教，信徒 12

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `yupik_shamanism` | 尤皮克萨满教 | 12 | 97% | kaniag_culture | — |

### `andamanese_language`（无 language_family） —— 1 个宗教，信徒 6

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `andamanese_religion` | 安达曼泛灵论 | 6 | 100% | andamanese_culture | — |

## 三、东南亚原始宗教（`folk_se_asian_group`）

### 壮侗语系（`tai_language_family`） —— 1 个宗教，信徒 1947

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `satsana_phi` | 丕教 | 1947 | 51% | tai_nua_culture | hlai_language 23%、南亚语系 22% |

### 婆罗洲语族（`bornean_language_family`） —— 12 个宗教，信徒 663

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `degar_religion` | 德加泛灵论 | 222 | 100% | degar_culture | — |
| `piil_pesenggiri_religion` | 帕松吉里哲学 | 117 | 100% | lampung_culture | — |
| `orang_rimba_religion` | 库布泛灵论 | 68 | 100% | orang_rimba_culture | — |
| `minangkabau_religion` | 米南加保泛灵论 | 54 | 100% | minangkabau_culture | — |
| `kan_khwan_religion` | 坎宽神话 | 51 | 100% | kayan_culture | — |
| `pengarap_asal_religion` | 阿萨尔信仰 | 36 | 100% | iban_culture | — |
| `nyang_serai_religion` | 娘‑瑟莱泛灵论 | 34 | 100% | rejang_culture | — |
| `adat_puun_religion` | 阿达普恩教 | 25 | 100% | kenyah_culture | — |
| `momolianism_religion` | 摩摩利安教 | 24 | 100% | dusun_culture | — |
| `ipok_religion` | 伊波克信仰 | 18 | 100% | melanau_culture | — |
| `besavik_religion` | 贝沙威信仰 | 8 | 100% | punan_culture | — |
| `orang_laut_religion` | 罗越泛灵论 | 7 | 100% | orang_laut_culture | — |

### 菲律宾语族（`philippine_language_family`） —— 5 个宗教，信徒 471

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `anitism_religion` | 阿尼托泛灵论 | 409 | 93% | tagalog_culture | — |
| `malesung_religion` | 马莱宗信仰 | 34 | 100% | mongondow_culture | — |
| `gorontalo_religion` | 哥伦打洛泛灵论 | 23 | 72% | gorontalo_culture | celebic_language 28% |
| `adat_musi_religion` | 穆希教 | 3 | 100% | talaud_culture | — |
| `sangirese_religion` | 马萨德派 | 2 | 100% | sangirese_culture | — |

### `buginese_language`（无 language_family） —— 2 个宗教，信徒 380

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `tolotang_religion` | 托洛唐教 | 302 | 75% | buginese_culture | 摩鹿加语族 24% |
| `aluk_religion` | 阿鲁克古道 | 78 | 100% | torajan_culture | — |

### `batak_language`（无 language_family） —— 3 个宗教，信徒 238

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `pelebegu_religion` | 帕玛林教 | 223 | 100% | batak_culture | — |
| `arat_sabulungan_religion` | 萨布伦甘教 | 14 | 100% | mentawai_culture | — |
| `enggano_religion` | 恩加诺泛灵论 | 1 | 100% | enggano_culture | — |

### 萨尔语族（`sal_language_family`） —— 1 个宗教，信徒 176

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `sanamahism` | 萨那玛依教 | 176 | 100% | meitei_culture | — |

### 摩鹿加语族（`moluccan_language_family`） —— 8 个宗教，信徒 171

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `wetarese_religion` | 韦塔雷斯信仰 | 45 | 95% | wetarese_culture | — |
| `lamatuan_religion` | 拉马图安教 | 34 | 100% | atoni_culture | — |
| `marapu_religion` | 玛拉甫信仰 | 25 | 100% | sumba_culture | — |
| `kirin_koda_religion` | 拘陀吉灵教 | 24 | 57% | lamaholot_culture | 跨新几内亚语系 43% |
| `dua_nggae_religion` | 杜阿·恩加埃教 | 24 | 100% | lio_culture | — |
| `naurus_religion` | 诺茹派 | 8 | 100% | seramese_culture | — |
| `mitu_religion` | 米图泛灵论 | 6 | 100% | aru_culture | — |
| `sula_religion` | 苏拉泛灵论 | 6 | 100% | buru_culture | — |

### 巴里托语族（`barito_language_family`） —— 1 个宗教，信徒 92

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `kaharingan_religion` | 卡哈林干信仰 | 92 | 66% | ngaju_culture | 婆罗洲语族 34% |

### `celebic_language`（无 language_family） —— 5 个宗教，信徒 42

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `tolaki_religion` | 托拉基泛灵论 | 14 | 100% | tolaki_culture | — |
| `tomanuru_religion` | 托玛努鲁教 | 9 | 100% | kaili_culture | — |
| `buton_religion` | 布敦泛灵论 | 9 | 100% | buton_culture | — |
| `lamoa_religion` | 拉莫阿教 | 5 | 100% | pamona_culture | — |
| `banunut_religion` | 巴奴努信仰 | 5 | 100% | saluan_culture | — |

### `ternate_language`（无 language_family） —— 2 个宗教，信徒 34

| 宗教 key | 中文名 | 信徒 | 本组占比 | 主要文化 | 其它语系/语言（>10%） |
|---|---|---:|---:|---|---|
| `kolano_religion` | 科拉诺长老信仰 | 18 | 76% | tidore_culture | 哈马黑拉-几内亚语系 15% |
| `goma_religion` | 戈马泛灵论 | 16 | 100% | tobelo_culture | — |

## 汇总

| 组 | 宗教数 | 信徒合计 | 分组数 |
|---|---:|---:|---:|
| 一、非洲原始宗教 | 50 | 25810 | 18 |
| 二、亚洲原始宗教 | 63 | 20700 | 21 |
| 三、东南亚原始宗教 | 40 | 4214 | 10 |
