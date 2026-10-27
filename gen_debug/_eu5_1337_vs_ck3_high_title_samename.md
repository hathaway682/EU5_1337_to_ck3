# EU5（1337 开局有地国家） × CK3 原版公国及以上头衔 同名对照

## 口径

- **EU5 侧**：`main_menu/setup/start/10_countries.txt` 中 1337.4.1 开局**至少持有一块领地**（`own_*` / `control_*` 列表非空）的国家 tag。
  - 文件里共 1206 个 tag，其中有地 **634 个**；另 572 个无地 tag 被排除（含只有 `our_cores_conquered_by_others` 的法理国家，如 GUY 吉耶纳、GLC 加利西亚、LON 莱昂、CRI 克里米亚）。
  - 中文名取 `main_menu/localization/simp_chinese/*.yml` 里的 `TAG:` 条目（634 个里 633 个有中文名，KEE 缺）。
- **CK3 侧**：`common/landed_titles/*.txt` 中的 `e_` / `k_` / `d_` 头衔，共 1662 个 key，其中 1620 个有简中名。
- **判定**：中文字符串完全相等（已解析 `$var$` 引用与 `#格式` 标记）。

## 结果

**127 条命中**，去重后 **104 个名字**。

- 帝国级 e_：3 个名字
- 王国级 k_：43 个名字
- 公国级 d_：58 个名字

## 帝国级 e_（3）

| 名字 | EU5 tag | 领地数 | CK3 头衔 |
| --- | --- | --- | --- |
| 埃及 | MAM | 143 | e_aegyptus、k_egypt |
| 日本 | JAP | 339 | e_japan |
| 马里 | MAL | 21 | d_moray、e_mali、k_mali |

## 王国级 k_（43）

| 名字 | EU5 tag | 领地数 | CK3 头衔 |
| --- | --- | --- | --- |
| 丹麦 | DAN | 40 | k_denmark |
| 伊庇鲁斯 | EPI | 10 | d_epirus、k_epirus |
| 保加利亚 | BUL | 63 | k_bulgaria |
| 克罗地亚 | CRO | 11 | d_croatia、k_croatia |
| 加奈姆 | KBO | 32 | d_kanem、k_kanem |
| 加纳 | GHA | 16 | k_ghana |
| 勃艮第 | BUR | 14 | d_burgundy、k_burgundy |
| 博尔古 | BOR | 9 | d_borgu、k_borgu |
| 卡布 | KAB | 16 | d_kaabu、k_kaabu |
| 卡拉曼 | KAR | 33 | k_karaman |
| 卡斯蒂利亚 | CAS | 244 | d_castilla、k_castille |
| 埃雷特纳 | ERE | 42 | k_eretnid |
| 塔克鲁尔 | TKR | 16 | d_takrur、k_takrur |
| 塞尔维亚 | SER | 63 | k_serbia |
| 塞浦路斯 | CYP | 7 | d_cyprus、k_cyprus |
| 威尼斯 | VEN | 22 | d_venice、k_venice |
| 布列塔尼 | BRI | 27 | d_brittany、k_brittany |
| 弗拉基米尔 | VLR | 8 | k_opolye |
| 彼尔姆 | PRM | 64 | d_perm、k_permia |
| 德里 | DLH | 397 | k_delhi |
| 挪威 | NOR | 119 | k_norway |
| 撒哈拉 | SHR | 2 | k_sahara |
| 桑海 | SON | 12 | k_songhay |
| 比萨 | PIS | 4 | d_et_pisa、d_pisa、k_pisa |
| 法兰西 | FRA | 250 | k_france |
| 波斯尼亚 | BOS | 21 | k_bosnia |
| 泰凯 | TEK | 7 | k_tekke |
| 特拉比松 | TRE | 8 | k_trebizond |
| 瑞典 | SWE | 131 | k_sweden |
| 瑞士 | SWI | 8 | d_swiss、k_switzerland |
| 盖尔米扬 | GRM | 17 | k_germiyan |
| 纳瓦拉 | NAV | 11 | d_navarra、k_navarra |
| 艾登 | AYD | 9 | k_aydin |
| 萨鲁汗 | SRU | 6 | k_saruhan |
| 葡萄牙 | POR | 67 | k_portugal |
| 西西里 | SIC | 22 | d_sicily、k_sicily |
| 达莫特 | DAM | 8 | d_damot、k_damot |
| 那不勒斯 | NAP | 65 | k_naples |
| 门泰谢 | MEN | 8 | k_mentese |
| 阿基坦 | AQN | 20 | d_aquitaine、k_aquitaine |
| 阿尔巴尼亚 | ALB | 3 | k_albania |
| 阿拉贡 | ARA | 85 | d_aragon、k_aragon |
| 阿朱兰 | AJU | 35 | k_ajuraan |

## 公国级 d_（58）

| 名字 | EU5 tag | 领地数 | CK3 头衔 |
| --- | --- | --- | --- |
| 亚滕加 | YAT | 5 | d_yatenga |
| 伊费 | IFE | 1 | d_ife |
| 冰岛 | ICE | 21 | d_iceland |
| 凯法洛尼亚 | CEP | 5 | d_cephalonia |
| 切尔尼戈夫 | CHR | 14 | d_chernigov |
| 加贝斯 | GBS | 12 | d_gabes |
| 努佩 | NUP | 8 | d_nupe |
| 卡拉切夫 | KCH | 15 | d_karachev |
| 卡诺 | KAN | 4 | d_kano |
| 卡齐纳 | KTS | 4 | d_katsina |
| 卢森堡 | LUX | 10 | d_luxembourg |
| 图瓦特 | TAT | 9 | d_touat |
| 塔菲拉勒特 | TFL | 21 | d_tafilalt |
| 奇里乞亚 | CIL | 12 | d_cilicia |
| 奥弗涅 | AUV | 1 | d_auvergne |
| 奥约 | OYO | 11 | d_oyo |
| 姆扎卜 | MZB | 4 | d_mzab |
| 安科纳 | ANC | 1 | d_ancona |
| 安茹 | ANJ | 7 | d_anjou |
| 巴尔 | BAR | 13 | d_bar |
| 巴格林 | BQL | 5 | d_baqlin |
| 巴津 | BZN | 5 | d_bazin |
| 巴莱 | BLE | 5 | d_bali |
| 布拉班特 | BRB | 11 | d_brabant |
| 帕泰 | PTE | 1 | d_pate |
| 戈比尔 | GOB | 6 | d_gobir |
| 扎卜 | ZAB | 11 | d_zab |
| 拉古萨 | RAG | 2 | d_et_ragusa |
| 普罗旺斯 | PRO | 19 | d_provence |
| 普龙斯克 | PRK | 8 | d_pronsk |
| 杰里德 | DJE | 2 | d_jerid |
| 格拉纳达 | GRA | 18 | d_granada |
| 梁赞 | RYA | 11 | d_ryazan |
| 比亚尔米亚 | BJA | 91 | d_biarmia |
| 波旁 | BOU | 10 | d_bourbon |
| 瓦加杜古 | OUA | 16 | d_wagadugu |
| 皮埃蒙特 | PIE | 3 | d_piedmonte |
| 纳博讷 | NRB | 1 | d_et_narbonne |
| 纳吉斯 | NQS | 2 | d_naqis |
| 维罗纳 | VER | 24 | d_verona |
| 罗马 | PAP | 21 | d_et_roma |
| 耽罗 | TMN | 2 | d_tamna |
| 荷兰 | HOL | 8 | d_holland |
| 萨伏依 | SAV | 10 | d_savoie |
| 诺曼底 | NRM | 21 | d_normandy |
| 诺沃西利 | NSL | 12 | d_novosil |
| 贝宁 | BEN | 10 | d_benin |
| 费赞 | FZA | 14 | d_fezzan |
| 贾富努 | DFN | 15 | d_diafunu |
| 达瓦罗 | DAW | 4 | d_dawaro |
| 达赫拉克 | DHK | 49 | d_dahlaks |
| 邦布 | BBK | 11 | d_bambuk |
| 阿奎莱亚 | AQU | 14 | d_et_aquileia |
| 阿洛迪亚 | ALO | 26 | d_sennar |
| 阿马尼亚克 | AMG | 11 | d_armagnac |
| 雅典 | ATH | 18 | d_athens |
| 马库里亚 | MAK | 21 | d_makuria |
| 马略卡 | MLL | 21 | d_mallorca |
