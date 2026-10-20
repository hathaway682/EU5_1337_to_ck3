# EU5 → CK3 文化分类汇总

口径：2088 个文化 / 21046 个男爵领。分类依据为各文化的传承（heritage）、语言（language）与 EU5 原始语言字段（eu5_language）。逐文化明细见 `_culture_classification.csv`。

## 一、按类别

| 类别 | 名称 | 文化数 | 男爵领 | 占比 |
|---:|---|---:|---:|---:|
| 1 | 同名同地 | 129 | 4918 | 23.4% |
| 2 | 异名同族 | 30 | 842 | 4.0% |
| 3 | 同名错位 | 2 | 167 | 0.8% |
| 4 | 按语言并入 | 320 | 4401 | 20.9% |
| 5 | 按方言并入 | 43 | 1294 | 6.1% |
| 6 | 按文化组并入 | 17 | 406 | 1.9% |
| 7 | 按地理并入 | 150 | 1318 | 6.3% |
| 8 | 需建融合文化 | 17 | 363 | 1.7% |
| 9 | 需建分离文化 | 74 | 461 | 2.2% |
| 10 | 图外可参考 | 351 | 1560 | 7.4% |
| 11 | 图外自创 | 955 | 5316 | 25.3% |
| | **合计** | **2088** | **21046** | **100%** |

## 二、按大洲 / 大区 × 类别（文化数）

**大洲 × 类别**

| 大洲 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 合计 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 亚洲 | 56 | 12 | 2 | 210 | 14 | 4 | 132 | 3 | 39 | 29 | 18 | 519 |
| 欧洲 | 50 | 13 | 0 | 46 | 29 | 2 | 17 | 11 | 2 | 0 | 0 | 170 |
| 非洲 | 23 | 5 | 0 | 64 | 0 | 11 | 0 | 3 | 33 | 122 | 19 | 280 |
| 北美洲 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 462 | 462 |
| 南美洲 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 268 | 268 |
| 大洋洲 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 200 | 187 | 388 |
| 无地块 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |

**大区 × 类别**

| 大区 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 合计 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 北美 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 462 | 462 |
| 大洋洲 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 200 | 187 | 388 |
| 南美 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 268 | 268 |
| 非洲 | 18 | 5 | 0 | 56 | 0 | 11 | 0 | 3 | 21 | 122 | 19 | 255 |
| 东南亚 | 13 | 2 | 0 | 35 | 0 | 0 | 96 | 0 | 2 | 5 | 1 | 154 |
| 东亚 | 8 | 3 | 0 | 80 | 13 | 0 | 1 | 0 | 0 | 3 | 0 | 108 |
| 中亚北亚 | 8 | 3 | 0 | 14 | 1 | 4 | 5 | 1 | 21 | 21 | 17 | 95 |
| 南亚 | 14 | 1 | 0 | 43 | 0 | 0 | 28 | 0 | 5 | 0 | 0 | 91 |
| 西欧 | 25 | 3 | 0 | 21 | 23 | 0 | 9 | 8 | 1 | 0 | 0 | 90 |
| 中东 | 14 | 3 | 2 | 41 | 0 | 0 | 2 | 2 | 14 | 0 | 0 | 78 |
| 东欧 | 21 | 5 | 0 | 18 | 2 | 2 | 8 | 3 | 10 | 0 | 0 | 69 |
| 北欧波罗的 | 7 | 5 | 0 | 10 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 26 |
| 无地块 | 1 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 4 |


## 三、各类别目标文化 Top

### 8 需建融合文化（17 个）

| 文化 | 男爵领 | 目标 | 依据 |
|---|---:|---|---|
| turkish_culture（土耳其） | 86 | NEW:anatolian_turkish（安纳托利亚突厥） | EU5 土耳其=突厥蛮+希腊融合，对应 CK3 融合名 anatolian_turkish |
| neapolitan（那不勒斯） | 53 | NEW:neapolitan_hybrid（那不勒斯） | 对应 CK3 融合文化名 neapolitan_hybrid |
| arpitan（阿尔卑坦） | 44 | NEW:arpitan_hybrid（阿尔卑坦） | 对应 CK3 融合文化名 arpitan_hybrid |
| tunisian（突尼斯） | 40 | NEW:tunisian_hybrid（突尼斯） | 对应 CK3 融合文化名 tunisian_hybrid |
| moroccan（摩洛哥） | 28 | NEW:moroccan_hybrid（摩洛哥） | 对应 CK3 融合文化名 moroccan_hybrid |
| algerian（阿尔及利亚） | 16 | NEW:algerian_hybrid（阿尔及利亚） | 对应 CK3 融合文化名 algerian_hybrid |
| angevin（安茹） | 16 | NEW:angevin_hybrid（安茹） | 对应 CK3 融合文化名 angevin_hybrid |
| transylvanian（特兰西瓦尼亚） | 16 | NEW:transylvanian（特兰西瓦尼亚） | 对应 CK3 融合文化名 transylvanian |
| gallo（加洛） | 14 | NEW:gallo（加洛） | 对应 CK3 融合文化名 gallo |
| gyalrong_culture（嘉绒） | 11 | NEW:gyalrong（嘉绒） | 对应 CK3 融合文化名 gyalrong |
| azeri_culture（阿塞拜疆） | 9 | NEW:azeri_hybrid（阿塞拜疆） | 对应 CK3 融合文化名 azeri_hybrid |
| dalmatian（达尔马提亚） | 9 | NEW:dalmatian_hybrid（达尔马提亚） | 对应 CK3 融合文化名 dalmatian_hybrid |
| romansh（罗曼什） | 9 | NEW:romansh_hybrid（罗曼什） | 对应 CK3 融合文化名 romansh_hybrid |
| norse_gael（诺斯‑盖尔） | 6 | NEW:norse_gael（诺斯‑盖尔） | 与 CK 融合名同名 |
| anglo_irish（盎格鲁‑爱尔兰） | 3 | NEW:anglo_irish（盎格鲁‑爱尔兰） | 英爱融合 |
| aromanian（阿罗马尼亚） | 3 | NEW:aromanian（阿罗马尼亚） | 对应 CK3 融合文化名 aromanian |
| griko_culture（格里科） | 0 | NEW:griko_hybrid（意大利‑希腊） | 对应 CK3 融合文化名 griko_hybrid |

### 9 需建分离文化（74 个）

| 文化 | 男爵领 | 目标 | 依据 |
|---|---:|---|---|
| evenk_culture（鄂温克） | 65 | NEW:evenk（鄂温克） | 鄂温克诸部，CK3 无对应，从靺鞨/女真分离 |
| makhuwa_culture（马夸） | 27 | NEW:makhuwa（马夸） | 参考 CK 东班图文化传统；CK3 地图内，从同语系文化分离 |
| zo_culture（佐） | 19 | NEW:meitei（梅泰） | 曼尼普尔，CK3 无对应 |
| bantoid（类班图） | 18 | NEW:bantoid（类班图） | 类班图，参考东班图传统；CK3 地图内，从同语系文化分离 |
| khakas_culture（哈卡斯） | 16 | NEW:turkic_steppe（突厥草原） | 西伯利亚突厥诸部，参考 CK 突厥传统；CK3 地图内，从同语系文化分离 |
| circassian_culture（切尔克斯） | 15 | NEW:circassian（切尔克斯） | 北高加索诸族，CK3 只有格鲁吉亚/亚美尼亚 |
| bassa_culture（巴萨） | 14 | NEW:bassa（巴萨） | 巴萨，CK3 无对应 |
| sym_culture（瑟姆） | 14 | NEW:evenk（鄂温克） | 鄂温克诸部，CK3 无对应，从靺鞨/女真分离 |
| obgints_culture（奥布金茨） | 11 | NEW:evenk（鄂温克） | 鄂温克诸部，CK3 无对应，从靺鞨/女真分离 |
| silyagir_culture（希利亚吉尔） | 11 | NEW:evenk（鄂温克） | 鄂温克诸部，CK3 无对应，从靺鞨/女真分离 |
| vargagaits_culture（瓦尔加盖茨） | 11 | NEW:evenk（鄂温克） | 鄂温克诸部，CK3 无对应，从靺鞨/女真分离 |
| selogon_culture（谢洛贡） | 10 | NEW:evenk（鄂温克） | 鄂温克诸部，CK3 无对应，从靺鞨/女真分离 |
| tani_culture（珞巴） | 10 | NEW:meitei（梅泰） | 曼尼普尔，CK3 无对应 |
| tuvan_culture（图瓦） | 10 | NEW:turkic_steppe（突厥草原） | 西伯利亚突厥诸部，参考 CK 突厥传统；CK3 地图内，从同语系文化分离 |
| yao_culture（亚奥） | 10 | NEW:yao_malawi（马拉维瑶） | 非洲瑶族（班图语支，马拉维/莫桑比克），与 CK3 瑶族（苗语支）同名异族；CK3 地图内，从同语系文化分离 |
| cemdal_culture（切姆达尔） | 9 | NEW:evenk（鄂温克） | 鄂温克诸部，CK3 无对应，从靺鞨/女真分离 |
| ijaw（伊乔） | 9 | NEW:ijaw（伊乔） | 伊乔，CK3 无对应 |
| lezgin_culture（列兹金） | 9 | NEW:dagestanian（达吉斯坦） | 北高加索诸族，CK3 只有格鲁吉亚/亚美尼亚 |
| matuumbi_culture（马通比） | 9 | NEW:rufiji_ruvuma（鲁菲吉‑鲁武马） | 参考 CK 东班图文化传统；CK3 地图内，从同语系文化分离 |
| naga_culture（那加） | 9 | NEW:meitei（梅泰） | 曼尼普尔，CK3 无对应 |
| nanagir_culture（纳纳吉尔） | 9 | NEW:evenk（鄂温克） | 鄂温克诸部，CK3 无对应，从靺鞨/女真分离 |
| uchami_culture（乌恰米） | 8 | NEW:evenk（鄂温克） | 鄂温克诸部，CK3 无对应，从靺鞨/女真分离 |
| ilimpeya_culture（锡尼格尔） | 7 | NEW:evenk（鄂温克） | 鄂温克诸部，CK3 无对应，从靺鞨/女真分离 |
| oroqen_culture（鄂伦春） | 7 | NEW:evenk（鄂温克） | 鄂温克诸部，CK3 无对应，从靺鞨/女真分离 |
| nakh_culture（纳赫） | 6 | NEW:dagestanian（达吉斯坦） | 北高加索诸族，CK3 只有格鲁吉亚/亚美尼亚 |

### 3 同名错位（2 个）

| 文化 | 男爵领 | 目标 | 依据 |
|---|---:|---|---|
| khorezmian_culture（花剌子模） | 141 | karluk（葛逻禄） | CK3 khwarezmian 是东伊朗语（斯基泰语支），EU5 花剌子模已突厥化、讲葛逻禄语 |
| turkmen_culture（土库曼） | 26 | turkish（乌古斯） | EU5 土库曼≠CK 同名 turkmen；CK3 的 turkish 显示名就是「乌古斯」，指乌古斯人 |

### 2 异名同族（30 个）

| 文化 | 男爵领 | 目标 | 依据 |
|---|---:|---|---|
| novgorodian（诺夫哥罗德） | 165 | ilmenian（伊尔门） | 诺夫哥罗德=伊尔门 |
| korean_culture（朝鲜） | 132 | goryeo（高丽） | 朝鲜=高丽 |
| utsang_culture（卫藏） | 78 | bodpa（吐蕃） | 卫藏=吐蕃核心，CK3 k_u 主体 bodpa |
| khampa_culture（康巴） | 69 | bodpa（吐蕃） | 康巴，CK3 k_kham 主体 bodpa（58） |
| leonese（莱昂） | 49 | asturleonese（阿斯图尔‑莱昂） | 莱昂=阿斯图里亚斯-莱昂 |
| moldovan（摩尔多瓦） | 45 | vlach（瓦拉几亚） | 罗马尼亚=弗拉赫 |
| highland（高地盖尔） | 34 | gaelic（盖尔） | 苏格兰盖尔=盖尔 |
| kashubian（卡舒比） | 30 | pommeranian（波美拉尼亚） | 卡舒比=波美拉尼亚 |
| kyrgyz_culture（吉尔吉斯） | 26 | kirghiz（黠戛斯） | 吉尔吉斯=黠戛斯，CK3 有 kirghiz |
| pomor（波莫尔） | 25 | ilmenian（伊尔门） | 诺夫哥罗德=伊尔门 |
| andalusi（安达卢斯） | 23 | andalusian（安达卢西亚） | 安达卢西=安达卢西亚 |
| slovak（斯洛伐克） | 22 | slovien（斯洛伐克） | 斯洛伐克=slovien |
| amhara（阿姆哈拉） | 21 | ethiopian（埃塞俄比亚） | 埃塞俄比亚 |
| latvian（拉脱维亚） | 21 | latgalian（拉特加尔） | 拉脱维亚=拉特加尔 |
| slovene（斯洛文尼亚） | 19 | carantanian（卡兰塔尼亚） | 斯洛文尼亚=卡兰塔尼亚 |
| pruthenian（普鲁赛尼亚） | 15 | prussian（普鲁士） | 西波罗的=普鲁士 |
| changpa_culture（羌巴） | 14 | bodpa（吐蕃） | 羌塘，CK3 无专名，随吐蕃 |
| tigrinya（提格利尼亚） | 12 | ethiopian（埃塞俄比亚） | 北埃塞俄比亚 |
| sudovian（苏多维亚） | 9 | prussian（普鲁士） | 西波罗的=普鲁士 |
| curonian（库罗尼亚） | 6 | prussian（普鲁士） | 西波罗的=普鲁士 |
| gurage（古拉盖） | 6 | ethiopian（埃塞俄比亚） | 埃塞俄比亚 |
| tigre（提格雷） | 5 | ethiopian（埃塞俄比亚） | 北埃塞俄比亚 |
| turkoman_culture（突厥蛮） | 4 | turkmen（土库曼） | 突厥蛮=CK 土库曼（CK3 turkmen 显示名「土库曼」） |
| harla_culture（哈尔拉） | 3 | ethiopian（埃塞俄比亚） | 埃塞俄比亚 |
| makassarese_culture（望加锡） | 3 | bugis（布吉） | 布吉语=布吉斯 |

### 6 按文化组并入（17 个）

| 文化 | 男爵领 | 目标 | 依据 |
|---|---:|---|---|
| zenati（泽纳塔） | 66 | butr（布特尔） | 柏柏尔文化组 |
| tuareg（图阿雷格） | 45 | butr（布特尔） | 柏柏尔文化组 |
| chiyalik_culture（奇亚利克） | 40 | hungarian（匈牙利） | 奇亚利克是马扎尔文化组仅存文化 |
| sanhaja（桑哈贾） | 34 | butr（布特尔） | 柏柏尔文化组 |
| udmurt（乌德穆尔特） | 32 | komi（彼尔姆） | 彼尔姆文化组，CK3 只有科米 |
| masmuda（马斯穆达） | 31 | butr（布特尔） | 柏柏尔文化组 |
| eastern_amazigh（东阿马齐格） | 27 | butr（布特尔） | 柏柏尔文化组 |
| hurga_culture（虎尔哈） | 23 | jurchen（女真） | 那乃/赫哲属通古斯，并入女真 |
| chaoui（沙维亚） | 22 | butr（布特尔） | 柏柏尔文化组 |
| mozabite（姆扎卜） | 17 | butr（布特尔） | 柏柏尔文化组 |
| kabyle（卡比尔） | 16 | butr（布特尔） | 柏柏尔文化组 |
| udege_culture（兀狄哈） | 16 | jurchen（女真） | 乌德盖属通古斯，并入女真 |
| lamtuna_culture（兰图纳） | 12 | butr（布特尔） | 柏柏尔文化组 |
| ulch_culture（乌尔奇） | 8 | jurchen（女真） | 那乃/赫哲属通古斯，并入女真 |
| messufa_culture（梅苏法） | 7 | butr（布特尔） | 柏柏尔文化组 |
| godala_culture（戈达拉） | 6 | butr（布特尔） | 柏柏尔文化组 |
| oroch_culture（奥罗奇） | 4 | jurchen（女真） | 乌德盖属通古斯，并入女真 |

### 7 按地理并入（150 个）

| 文化 | 男爵领 | 目标 | 依据 |
|---|---:|---|---|
| uzbek_culture（乌兹别克） | 122 | karluk（葛逻禄） | 乌兹别克属葛逻禄-察合台支，CK3 有 karluk |
| smolenskian_culture（斯摩棱斯克） | 80 | severian（谢韦里亚） | 白俄罗斯按地理入谢韦里安 |
| ruthenian（鲁塞尼亚） | 76 | volhynian（沃利尼亚） | 乌克兰按地理入沃里尼亚 |
| nogai（诺盖） | 73 | kipchak（钦察） | 诺盖属钦察支，CK3 有 kipchak |
| astrakhani（阿斯特拉罕） | 70 | kipchak（钦察） | 阿斯特拉罕为钦察/诺盖故地，CK3 有 kipchak |
| polesian_culture（波列西耶） | 70 | severian（谢韦里亚） | 白俄罗斯按地理入谢韦里安 |
| amdowa_culture（安多） | 65 | sumpa（苏毗） | 安多，CK3 k_amdo 有 sumpa（30），苏毗即安多/青唐故地 |
| polatskian_culture（波洛茨克） | 59 | severian（谢韦里亚） | 白俄罗斯按地理入谢韦里安 |
| kazani（喀山） | 41 | bolghar（保加尔） | 喀山鞑靼=伏尔加保加尔后裔，CK3 有 bolghar |
| halychian_culture（哈利奇） | 35 | volhynian（沃利尼亚） | 乌克兰按地理入沃里尼亚 |
| mishar（米萨） | 32 | kipchak（钦察） | 米沙鞑靼属钦察支，CK3 有 kipchak |
| emilian（艾米利亚） | 26 | cisalpine（山南） | 艾米利亚按地理入内高卢 |
| kayan_culture（卡扬） | 23 | dayak（达雅） | 卡扬语按地理入达雅 |
| ngaju_culture（雅朱） | 22 | dayak（达雅） | 巴里托语按地理入达雅 |
| venetian（威尼斯） | 20 | cisalpine（山南） | 威尼托按地理入内高卢 |
| newar_culture（尼瓦尔） | 19 | nepali（尼波罗） | 尼瓦尔，CK3 k_himalaya 有 culture = nepali #Newar |
| batak_culture（巴塔克） | 17 | malay（末罗瑜） | 巴塔克语按地理入马来 |
| minangkabau_culture（米南加保） | 17 | malay（末罗瑜） | 米南加保语按地理入马来 |
| bhil（比尔） | 16 | rajput（罗阇萨傥那） | 比尔语按地理入拉杰普特 |
| piedmontese（皮埃蒙特） | 16 | cisalpine（山南） | 皮埃蒙特按地理入内高卢 |
| sundanese_culture（巽他） | 16 | javanese（阇婆） | 巽他语按地理入爪哇 |
| banjar_culture（班贾尔） | 15 | malay（末罗瑜） | 班贾尔语按地理入马来 |
| dusun_culture（杜顺） | 15 | dayak（达雅） | 婆罗洲语按地理入达雅 |
| sorbian（索布） | 13 | polabian（波拉布） | 索布与波拉布地理相邻 |
| iban_culture（伊班） | 11 | dayak（达雅） | 伊班语按地理入达雅 |

## 四、需人工裁定

### 4.1 低置信 / 未判定（0 个）

| 文化 | 类别 | 目标 | 说明 |
|---|---:|---|---|

### 4.2 同名异族（名字撞 CK3，但不是同一人群）

| 文化 | 类别 | 目标 | 理由 |
|---|---:|---|---|
| avar_culture（阿瓦尔） | 9 | NEW:caucasian_avar（高加索阿瓦尔） | 高加索阿瓦尔人（东北高加索语），与 CK3 潘诺尼亚阿瓦尔（突厥/乌古尔语）同名异族 |
| khorezmian_culture（花剌子模） | 3 | karluk（葛逻禄） | CK3 khwarezmian 是东伊朗语（斯基泰语支），EU5 花剌子模已突厥化、讲葛逻禄语 |
| prussian（普鲁士） | 5 | saxon（萨克森） | EU5 普鲁士为德语人口（低地德语），非 CK3 的波罗的普鲁士人 |
| turkmen_culture（土库曼） | 3 | turkish（乌古斯） | EU5 土库曼≠CK 同名 turkmen；CK3 的 turkish 显示名就是「乌古斯」，指乌古斯人 |
| yao_culture（亚奥） | 9 | NEW:yao_malawi（马拉维瑶） | 非洲瑶族（班图语支，马拉维/莫桑比克），与 CK3 瑶族（苗语支）同名异族；CK3 地图内，从同语系文化分离 |

### 4.3 判定所依据的传承可疑（与 CK3 原版同名文化不一致）

| 文化 | 我们的传承 | CK3 原版同名传承 | 类别 |
|---|---|---|---:|
| yi_culture（彝） | heritage_burman | heritage_chinese | 1 |
| ainu_culture（阿伊努） | ainu_culture_group | heritage_ainuic | 1 |
| hausa（豪萨） | heritage_west_african | heritage_central_african | 1 |
| nubian（努比亚） | nubian_group | heritage_east_african | 1 |
| mossi（莫西） | heritage_west_african | heritage_sahelian | 1 |
| tujia_culture（土家） | heritage_burman | heritage_tai | 1 |
| akan（阿肯） | heritage_yoruba | heritage_akan | 1 |
| soninke（索宁克） | heritage_west_african | heritage_sahelian | 1 |
| mari_culture（马里） | mari_culture_group | heritage_volga_finnic | 1 |
| sao_culture（萨奥） | heritage_west_african | heritage_central_african | 1 |
| khanty_culture（汉特） | khanty_culture_group | heritage_ugro_permian | 1 |
| songhai（桑海） | heritage_west_african | heritage_sahelian | 1 |
| scottish（苏格兰） | heritage_goidelic | heritage_west_germanic | 1 |
| albanian（阿尔巴尼亚） | albanian_group | heritage_albanian | 1 |
| bai_culture（白） | heritage_korean | heritage_chinese | 1 |
| daju_culture（达朱） | heritage_sahelian | heritage_east_african | 1 |
| prussian（普鲁士） | heritage_central_germanic | heritage_baltic | 5 |
| yao_culture（亚奥） | heritage_bantu | heritage_hmongic | 9 |
| beja_culture（贝贾） | heritage_somalian | heritage_east_african | 1 |
| nivkh_culture（尼夫赫） | heritage_tungusic | heritage_nivkh | 1 |
| polabian（波拉布） | heritage_south_slavic | heritage_west_slavic | 1 |
| merya_culture（梅里亚） | merya_culture_group | heritage_volga_finnic | 1 |
| nupe（努佩） | heritage_yoruba | heritage_central_african | 1 |
| brahui_culture（布拉灰） | heritage_dravidian | heritage_indo_aryan | 1 |
| alan_culture（阿兰） | alan_culture_group | heritage_iranian | 1 |
| cuman_culture（库曼） | heritage_west_slavic | heritage_turkic | 1 |
| avar_culture（阿瓦尔） | heritage_caucasian | heritage_turkic | 9 |
| zaghawa_culture（扎加瓦） | heritage_west_african | heritage_berber | 1 |
| gothic_culture（哥特） | heritage_byzantine | heritage_gothic | 1 |
| roman_culture（拉丁） | heritage_byzantine | heritage_latin | 1 |

合计 30 个同名文化的传承与原版不一致；上表只列男爵领前 30。

### 4.4 CK3 原版 key 与显示名不一致的文化（判「同名」必须看显示名）

| CK3 key | 中文显示名 | 英文显示名 | 已用到的映射 |
|---|---|---|---|
| ancient_egyptian | 古埃及 | Ancient Egyptian |  |
| anglo_saxon | 盎格鲁‑撒克逊 | Anglo-Saxon |  |
| assamese | 迦摩缕波 | Kamrupi |  |
| assyrian | 亚述 | Syriac | EU5 Syriac → 此处（cat1） |
| east_bantu | 东班图 | East Bantu |  |
| hindustani | 葛那及 | Kannauji | EU5 Kannauji → 此处（cat1） |
| japanese | 大和 | Yamato |  |
| khanty | 奥斯佳克 | Ostyak |  |
| komi | 彼尔姆 | Permian |  |
| levantine | 马什里克 | Mashriqi |  |
| maluku | 文老古 | Moluccan |  |
| mogyer | 马扎尔 | Mogyër |  |
| old_saxon | 古撒克逊 | Old Saxon |  |
| ongud | 汪古惕 | Öngüd |  |
| pommeranian | 波美拉尼亚 | Pomeranian |  |
| rajput | 罗阇萨傥那 | Rajasthani |  |
| samoyed | 比亚尔米亚 | Bjarmian | EU5 Bjarmian → 此处（cat1） |
| scottish | 苏格兰 | Scots |  |
| turkish | 乌古斯 | Oghuz | EU5 土库曼 → 此处（cat3） |

上表只列显示名与 key 明显不同的；`turkmen`（土库曼）、`karluk`（葛逻禄）、`guanches`（Guanche）、`bodpa`（吐蕃）等 key 与显示名一致的未列出，但它们同样被用作目标。

### 4.5 按 CK3 原版王国文化分布细分的两处（藏区 / 突厥语支）

原先「藏语→bodpa」「突厥语→cuman」两条语言规则把整片语族并成一个文化。按 CK3 原版 `history/provinces/k_{u,tsang,kham,amdo,guge,gyalrong,lhomon,himalaya,maryul}.txt` 的实际 culture 分布重新落点：

**藏区 / 喜马拉雅（16 个）**

| 文化 | 男爵领 | 类别 | 目标 | 依据 |
|---|---:|---:|---|---|
| utsang_culture（卫藏） | 78 | 2 | bodpa（吐蕃） | 卫藏=吐蕃核心，CK3 k_u 主体 bodpa |
| khampa_culture（康巴） | 69 | 2 | bodpa（吐蕃） | 康巴，CK3 k_kham 主体 bodpa（58） |
| changpa_culture（羌巴） | 14 | 2 | bodpa（吐蕃） | 羌塘，CK3 无专名，随吐蕃 |
| amdowa_culture（安多） | 65 | 7 | sumpa（苏毗） | 安多，CK3 k_amdo 有 sumpa（30），苏毗即安多/青唐故地 |
| tebbu_culture（迭部） | 1 | 7 | sumpa（苏毗） | 迭部在甘南，属安多，随苏毗 |
| ladakh_culture（拉达克） | 8 | 7 | zhangzhung（象雄） | 拉达克=麻域（k_maryul），CK3 主体 zhangzhung（20） |
| balti_culture（巴尔蒂） | 6 | 7 | zhangzhung（象雄） | 巴尔蒂斯坦同属阿里/麻域圈，CK3 归象雄 |
| ngalop_culture（阿洛） | 9 | 7 | lhomon（珞门） | 阿洛=不丹主体民族，CK3 k_lhomon 全为 lhomon |
| sikkim_culture（锡金） | 4 | 7 | lhomon（珞门） | 锡金=哲孟雄，CK3 珞门含 Lepcha（#Lepcha） |
| monpa_culture（门巴） | 5 | 7 | lhomon（珞门） | 门巴，CK3 k_kham/k_lhomon 均标 #Monpa 于 lhomon |
| newar_culture（尼瓦尔） | 19 | 7 | nepali（尼波罗） | 尼瓦尔，CK3 k_himalaya 有 culture = nepali #Newar |
| magar_culture（马加尔） | 3 | 7 | kirati（罽罗多） | 马加尔为尼泊尔山地民族，CK3 k_himalaya 有 kirati（8） |
| gurung_culture（古隆） | 0 | 7 | kirati（罽罗多） | 古隆同上，随罽罗多 |
| tamang_culture（塔芒） | 0 | 7 | kirati（罽罗多） | 塔芒同上，随罽罗多 |
| limbu_culture（林布） | 1 | 7 | kirati（罽罗多） | 林布是罽罗多核心族群 |
| sherpa_culture（夏尔巴） | 0 | 7 | tsangpa（藏巴） | 夏尔巴，CK3 k_himalaya 有 culture = tsangpa #Sherpa |

**突厥语支（6 个，其余无 CK3 对应者仍留 cuman）**

| 文化 | 男爵领 | 类别 | 目标 | 依据 |
|---|---:|---:|---|---|
| kyrgyz_culture（吉尔吉斯） | 26 | 2 | kirghiz（黠戛斯） | 吉尔吉斯=黠戛斯，CK3 有 kirghiz |
| kazani（喀山） | 41 | 7 | bolghar（保加尔） | 喀山鞑靼=伏尔加保加尔后裔，CK3 有 bolghar |
| uzbek_culture（乌兹别克） | 122 | 7 | karluk（葛逻禄） | 乌兹别克属葛逻禄-察合台支，CK3 有 karluk |
| nogai（诺盖） | 73 | 7 | kipchak（钦察） | 诺盖属钦察支，CK3 有 kipchak |
| astrakhani（阿斯特拉罕） | 70 | 7 | kipchak（钦察） | 阿斯特拉罕为钦察/诺盖故地，CK3 有 kipchak |
| mishar（米萨） | 32 | 7 | kipchak（钦察） | 米沙鞑靼属钦察支，CK3 有 kipchak |

