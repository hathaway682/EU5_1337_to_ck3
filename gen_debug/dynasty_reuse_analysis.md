# EU5 mod 家族 vs CK3 原版家族 复用分析

生成时间：2026-10-18

## 重要前提：ID 体系不同

mod 与 CK3 原版（vanilla）的家族**用两套完全不同的 ID 体系**：

| | mod（`zz_eu5_dynasties.txt`） | CK3 原版（`00_dynasties.txt` 等） |
|---|---|---|
| dynasty key | 命名 key，如 `borjigin_dynasty` | 数字 ID，如 `11100` |
| name 字段 | `xxx_dynasty` 或 `name_xxx` | `dynn_XXX` |
| 角色引用方式 | `dynasty = borjigin_dynasty` | `dynasty = 11100` |

所以"复用"不是指"key 完全相同直接能用"，而是指：
**把 mod 里用 `xxx_dynasty` 命名 key 定义的那一份删掉，改用 vanilla 里数字 ID 对应的同名家族**——
vanilla 的家族已经带了 coat of arms、prefix、本地化等所有数据，直接用就行，不必 mod 自己再定义一遍。

本表只给"同名"匹配，是否真的语义相同（同一历史家族）需逐条核对，尤其 C 类和多对多那几节。

## 总览

| 项 | 数量 |
|---|---|
| CK3 原版 dynasty 总数 | 4214 |
| EU5 mod dynasty 总数 | 1272 |
| 语义同名匹配（可考虑复用） | 257 |

## 分类

| 类别 | 数量 | 说明 |
|---|---|---|
| A 直接可复用 | 50 | culture 完全一致，用 vanilla 的数字 ID 即可，已有本地化 |
| B 复用并补 culture | 52 | mod 里 culture 为空，直接用 vanilla 的定义 |
| C culture 不一致 | 155 | mod 用细分文化（如 italian_culture），vanilla 用父类（italian）；或反之；实际可统一用 vanilla 定义 |

## A 类：直接可复用（culture 一致，共 50 条）

| mod_key | mod_culture | vanilla_id | vanilla_name | vanilla_culture |
|---|---|---|---|---|
| aberffraw_dynasty | welsh | 101920 | dynn_Aberffraw | welsh |
| angelos_dynasty | greek_culture | 195 | dynn_Angelos | greek |
| aryacakravarti_dynasty | tamil | 1029178 | dynn_Aryacakravarti | tamil |
| asen_dynasty | bulgarian | 185 | dynn_Asen | bulgarian |
| aydinids_dynasty | turkish_culture | 12107 | dynn_Aydin | turkish |
| ayyubids_dynasty | kurdish_culture | 24000 | dynn_Ayyubid | kurdish |
| barcelona_dynasty | catalan | 100204 | dynn_Barcelona | catalan |
| bohun_dynasty | english | 359 | dynn_Bohun | english |
| bosonid_dynasty | french | 7052 | dynn_Bosonid | french |
| candarids_dynasty | turkish_culture | 20089 | dynn_Candar | turkish |
| chudasama_dynasty | gujarati | 1042088 | dynn_Chudasama | gujarati |
| courtenay_dynasty | french | 9301 | dynn_Courtenay | french |
| douglas_dynasty | scottish | 3125 | dynn_Douglas | scottish |
| doukas_dynasty | greek_culture | 633 | dynn_Doukas | greek |
| dreux_dynasty | french | 86 | dynn_Dreux | french |
| dunbar_dynasty | scottish | 370 | dynn_Dunbar | scottish |
| dunkeld_dynasty | scottish | 1687 | dynn_Dunkeld | scottish |
| erik_dynasty | swedish | 381 | dynn_Erik | swedish |
| estrid_dynasty | danish | 487 | dynn_Estrid | danish |
| germiyanids_dynasty | turkish_culture | 12104 | dynn_Germiyan | turkish |
| hohenstaufen_dynasty | swabian | 529 | dynn_Hohenstaufen | swabian |
| jadeja_dynasty | gujarati | 1042085 | dynn_Jadeja | gujarati |
| jaqeli_dynasty | georgian_culture | 42 | dynn_Jaqeli | georgian |
| kantakouzenos_dynasty | greek_culture | 46 | dynn_Kantakouzenos | greek |
| karamanids_dynasty | turkish_culture | 12108 | dynn_Karaman | turkish |
| komnenos_dynasty | greek_culture | 634 | dynn_Komnenos | greek |
| laskaris_dynasty | greek_culture | 101107 | dynn_Laskaris | greek |
| lazarevic_dynasty | serbian | 18002 | dynn_Lazarevic | serbian |
| mallabhum_dynasty | bengali | 1044324 | dynn_Mallabhum | bengali |
| mansfeld_dynasty | saxon | 12403 | dynn_Mansfeld | saxon |
| mathrafal_dynasty | welsh | 548 | dynn_Mathrafal | welsh |
| mentese_dynasty | turkish_culture | 12106 | dynn_Mentese | turkish |
| molina_dynasty | castilian | 782 | dynn_Molina | castilian |
| montagu_dynasty | english | 9107 | dynn_Montagu | english |
| montfort_dynasty | french | 4003 | dynn_Montfort | french |
| montoire_dynasty | french | 101861 | dynn_Montoire | french |
| murray_dynasty | scottish | 100040 | dynn_Murray | scottish |
| pagan_dynasty | burmese_culture | 2000000 | dynn_Pagan | burmese |
| palaiologos_dynasty | greek_culture | 48 | dynn_Palaiologos | greek |
| pandya_dynasty | tamil | 1043009 | dynn_Pandya | tamil |
| querfurt_dynasty | saxon | 12402 | dynn_Querfurt | saxon |
| shishman_dynasty | bulgarian | 41 | dynn_Shishman | bulgarian |
| stewart_dynasty | scottish | 3134 | dynn_Stewart | scottish |
| stratford_dynasty | english | 1027031 | dynn_Stratford | english |
| sully_dynasty | french | 94 | dynn_Sully | french |
| sverker_dynasty | swedish | 496 | dynn_Sverker | swedish |
| synadenos_dynasty | greek_culture | 101141 | dynn_Synadenos | greek |
| terter_dynasty | bulgarian | 40 | dynn_Terter | bulgarian |
| valois_dynasty | french | 101 | dynn_Valois | french |
| vilaragut_dynasty | catalan | 8767 | dynn_Vilaragut | catalan |

## B 类：复用 vanilla 补 culture（mod 无 culture，共 52 条）

| mod_key | vanilla_id | vanilla_name | vanilla_culture |
|---|---|---|---|
| albuquerque_dynasty | 767 | dynn_Albuquerque | portuguese |
| alupa_dynasty | 12327 | dynn_Alupa | kannada |
| anglesola_dynasty | 12136 | dynn_Anglesola | catalan |
| argyropoulos_dynasty | 101196 | dynn_Argyropoulos | greek |
| badoer_dynasty | 1040023 | dynn_Badoer | italian |
| balsic_dynasty | 18004 | dynn_Balsic | serbian |
| rtr_bayad_dynasty | 1051138 | dynn_Bayad | mongol |
| beauchamp_dynasty | 102008 | dynn_Beauchamp | english |
| beaujeu_dynasty | 5092 | dynn_Beaujeu | occitan |
| cabrera_dynasty | 101701 | dynn_Cabrera | catalan |
| cardona_dynasty | 10029 | dynn_Cardona | catalan |
| dovara_dynasty | 8683 | dynn_Dovara | italian |
| faucogney_dynasty | 101604 | dynn_Faucogney | french |
| fiennes_dynasty | 7242 | dynn_Fiennes | french |
| hanover_dynasty | 2001107 | dynn_Hanover | saxon |
| harcourt_dynasty | 530 | dynn_Harcourt | french |
| haro_dynasty | 778 | dynn_Haro | basque |
| hohenzollern_brandenburg_dynasty | 12476 | dynn_Hohenzollern | swabian |
| holland_dynasty | 4035 | dynn_Holland | english |
| ibelin_armenia_dynasty | 23102 | dynn_Ibelin | french |
| kontostephanos_dynasty | 101103 | dynn_Kontostephanos | greek |
| lauria_dynasty | 7050 | dynn_Lauria | italian |
| lorraine_dynasty | 715 | dynn_Lorraine | french |
| lvov_dynasty | 100551 | dynn_Lvov | russian |
| matha_dynasty | 13106 | dynn_Matha | french |
| mendoza_dynasty | 101909 | dynn_Mendoza | castilian |
| monomachos_dynasty | 636 | dynn_Monomachos | greek |
| montcada_dynasty | 336 | dynn_Montcada | catalan |
| montmorency_dynasty | 5073 | dynn_Montmorency | french |
| morozov_dynasty | 100567 | dynn_Morozov | russian |
| orange_dynasty | 7248 | dynn_Orange | occitan |
| osorio_dynasty | 8620 | dynn_Osorio | castilian |
| oviedo_dynasty | 402 | dynn_Oviedo | castilian |
| pacheco_dynasty | 7035 | dynn_Pacheco | castilian |
| de_peralta_dynasty | 101911 | dynn_Peralta | castilian |
| pio_dynasty | 1022223 | dynn_Pius | roman |
| polani_dynasty | 7236 | dynn_Polani | italian |
| prado_dynasty | 7046 | dynn_Prado | castilian |
| ramberti_dynasty | 8672 | dynn_Ramberti | italian |
| romanov_dynasty | 100397 | dynn_Romanov | russian |
| shabankarai_dynasty | 101690 | dynn_Shabankarai | kurdish |
| silva_dynasty | 12163 | dynn_Silva | castilian |
| soomra_dynasty | 1042090 | dynn_Soomra | sindhi |
| sousa_arronches_dynasty | 1020118 | dynn_Sousa_Arronches | portuguese |
| sousa_chichorro_dynasty | 1020117 | dynn_Sousa_Chichorro | portuguese |
| tarchaneiotes_dynasty | 101145 | dynn_Tarchaneiotes | greek |
| ubaldini_dynasty | 12248 | dynn_Ubaldini | italian |
| valperga_dynasty | 8729 | dynn_Valperga | italian |
| vasconcelos_dynasty | 1020112 | dynn_Vasconcelos | portuguese |
| villalobos_dynasty | 7011 | dynn_Villalobos | castilian |
| wanyan_dynasty | 1051112 | dynn_Wanyan | jurchen |
| rtr_ming_zhu_dynasty | 2003017 | dynn_Zhu | tsangpa |

## C 类：culture 不一致（共 155 条）

| mod_key | mod_culture | vanilla_id | vanilla_name | vanilla_culture |
|---|---|---|---|---|
| ahom_dynasty | tai_nua_culture | 1044361 | dynn_Ahom | assamese |
| albon_dynasty | arpitan | 232 | dynn_Albon | occitan |
| albret_dynasty | gascon | 100150 | dynn_Albret | occitan |
| alsace_dynasty | lorrain | 428 | dynn_Alsace | french |
| altenburg_dynasty | prussian | 12477 | dynn_Altenburg | franconian |
| anjou_dynasty | neapolitan | 81 | dynn_Anjou | french |
| antelminelli_dynasty | tuscan | 101817 | dynn_Antelminelli | italian |
| arnsberg_dynasty | lower_saxon | 101896 | dynn_Arnsberg | franconian |
| artois_dynasty | picard | 100 | dynn_Artois | french |
| ashina_dynasty | touhoku_culture | 12269 | dynn_Ashina | khazar |
| audley_dynasty | english | 4023 | dynn_Audley | norman |
| auvergne_dynasty | auvergnat | 733 | dynn_Auvergne | occitan |
| avesnes_dynasty | picard | 5060 | dynn_Avesnes | french |
| baghela_dynasty | bagheli | 1044349 | dynn_Baghela | hindustani |
| bahri_dynasty | crimean | 762 | dynn_Bahri | egyptian |
| balliol_dynasty | scottish | 103 | dynn_Balliol | norman |
| basarab_dynasty | wallachian | 764 | dynn_Basarab | vlach |
| baux_dynasty | provencal | 5117 | dynn_Baux | occitan |
| beaumont_dynasty | angevin | 710 | dynn_Beaumont | norman |
| beccaria_dynasty | lombard | 101819 | dynn_Beccaria | italian |
| belforti_dynasty | tuscan | 1042023 | dynn_Belforti | italian |
| berthout_dynasty | low_franconian | 7175 | dynn_Berthout | dutch |
| bhatti_dynasty | bagri | 1042091 | dynn_Bhatti | rajput |
| blois_dynasty | champenais | 721 | dynn_Blois | french |
| boccanegra_dynasty | ligurian | 13001 | dynn_Boccanegra | italian |
| borjigin_dynasty | mongolian_culture | 11100 | dynn_Borjigin | mongol |
| bourbon_dynasty | berrichon | 329 | dynn_Bourbon | french |
| bundela_dynasty | bundeli | 1044351 | dynn_Bundela | hindustani |
| burgundy_dynasty | burgundian | 9616 | dynn_Burgundy | french |
| butler_dynasty | anglo_irish | 4040 | dynn_Butler | english |
| carceri_dynasty | venetian | 100472 | dynn_Carceri | italian |
| carrara_dynasty | venetian | 101823 | dynn_Carrara | italian |
| champlitte_dynasty | franc_comtois | 102026 | dynn_Champlitte | french |
| chand_dynasty | kumaoni | 105843 | dynn_Chand |  |
| chanda_dynasty | gond | 1044337 | dynn_Chanda | hindustani |
| chandela_dynasty | bundeli | 1042067 | dynn_Chandela | hindustani |
| chauhan_dynasty | shekhawati | 1042081 | dynn_Chauhan | rajput |
| clermont_dynasty | auvergnat | 89 | dynn_Clermont | french |
| commercy_dynasty | westphalian | 1062190 | dynn_Commercy |  |
| comyn_dynasty | scottish | 101600 | dynn_Comyn | norman |
| contarini_dynasty | venetian | 516 | dynn_Contarini | cisalpine |
| correggio_dynasty | emilian | 13064 | dynn_Correggio | italian |
| coucy_dynasty | picard | 5081 | dynn_Coucy | french |
| dampierre_dynasty | champenais | 92 | dynn_Dampierre | french |
| dandolo_dynasty | venetian | 13027 | dynn_Dandolo | italian |
| darcy_dynasty | anglo_irish | 4039 | dynn_Darcy | english |
| diepholz_dynasty | lower_saxon | 52 | dynn_Diepholz | saxon |
| donzy_dynasty | burgundian | 5093 | dynn_Donzy | french |
| doria_dynasty | ligurian | 13041 | dynn_Doria | italian |
| dulkadirids_dynasty | turkmen_culture | 7362 | dynn_Dulkadir | turkish |
| enghien_dynasty | walloon | 12235 | dynn_Enghien | french |
| eppstein_dynasty | rhine_franconian | 289 | dynn_Eppstein | franconian |
| fitzalan_bedale_dynasty | northumbrian | 101899 | dynn_FitzAlan | english |
| gabras_dynasty | pontic_greek_culture | 7314 | dynn_Gabras | greek |
| galloway_dynasty | norse_gael | 371 | dynn_Galloway | scottish |
| gherardesca_dynasty | tuscan | 13031 | dynn_Gherardesca | italian |
| ghisi_dynasty | venetian | 7218 | dynn_Ghisi | italian |
| godwin_dynasty | english | 756 | dynn_Godwin | anglo_saxon |
| gonzaga_dynasty | emilian | 13052 | dynn_Gonzaga | italian |
| gradenigo_dynasty | venetian | 13007 | dynn_Gradenigo | italian |
| grandson_dynasty | arpitan | 1029990 | dynn_Grandson | french |
| grimaldi_dynasty | ligurian | 13016 | dynn_Grimaldi | italian |
| gryf_dynasty | western_pomeranian | 21012 | dynn_Gryf | polish |
| hafsid_dynasty | masmuda | 7276 | dynn_Hafsid | maghrebi |
| haihaya_dynasty | chhattisgarhi | 1044338 | dynn_Haihaya | gond |
| hastings_dynasty | english | 540 | dynn_Hastings | anglo_saxon |
| hazaraspid_dynasty | lur_culture | 7333 | dynn_Hazaraspid | kurdish |
| henneberg_dynasty | rhine_franconian | 7165 | dynn_Henneberg | franconian |
| hohenlohe_dynasty | east_franconian | 7138 | dynn_Hohenlohe | franconian |
| hoya_dynasty | lower_saxon | 7131 | dynn_Hoya | saxon |
| hoysala_dynasty | kannadiga | 12325 | dynn_Hoysala | kannada |
| injuid_dynasty | farsi_culture | 101913 | dynn_Injuid | mongol |
| jadon_dynasty | dhundhari | 1044375 | dynn_Jadon | hindustani |
| jarwanid_dynasty | bahrani_culture | 7309 | dynn_Jarwanid | bedouin |
| joinville_dynasty | arpitan | 241 | dynn_Joinville | french |
| kakatiya_dynasty | chhattisgarhi | 1029179 | dynn_Kakatiya | telugu |
| keita_dynasty | mandinka | 1030002 | dynn_Keita | malinke |
| kleve_dynasty | westphalian | 1062189 | dynn_Kleve |  |
| lackfi_dynasty | hungarian | 100465 | dynn_Lackfi | croatian |
| lancaster_dynasty | northumbrian | 100058 | dynn_Lancaster | english |
| laval_dynasty | angevin | 319 | dynn_Laval | french |
| leiningen_dynasty | westphalian | 12433 | dynn_Leiningen | franconian |
| lichtenberg_dynasty | rhine_alemannic | 7285 | dynn_Lichtenberg | swabian |
| loairn_dynasty | highland | 554 | dynn_Loairn | irish |
| lohara_dynasty | kashmiri_culture | 1042093 | dynn_Lohara | punjabi |
| lomagne_dynasty | gascon | 5100 | dynn_Lomagne | french |
| ludowinger_dynasty | rhine_franconian | 257 | dynn_Ludowinger | franconian |
| luna_dynasty | aragonese | 7033 | dynn_Luna | castilian |
| lusignan_dynasty | poitevin | 93 | dynn_Lusignan | french |
| malatesta_dynasty | emilian | 13059 | dynn_Malatesta | italian |
| marinid_dynasty | zenati | 101732 | dynn_Marinid | maghrebi |
| mello_dynasty | picard | 5057 | dynn_Mello | french |
| mihrabanid_dynasty | farsi_culture | 7339 | dynn_Mihrabanid | persian |
| montfaucon_dynasty | franc_comtois | 7287 | dynn_Montfaucon | french |
| morosini_dynasty | venetian | 13070 | dynn_Morosini | italian |
| mortimer_dynasty | english | 4001 | dynn_Mortimer | norman |
| mowbray_dynasty | northumbrian | 558 | dynn_Mowbray | norman |
| nasrid_dynasty | andalusi | 577 | dynn_Nasrid | levantine |
| nassau_dynasty | rhine_franconian | 263 | dynn_Nassau | franconian |
| neuchatel_dynasty | franc_comtois | 100241 | dynn_Neuchatel | swabian |
| oldenburg_dynasty | lower_saxon | 224 | dynn_Oldenburg | saxon |
| orsini_aldobrandeschi_dynasty | median | 2 | dynn_Orsini | italian |
| panwar_dynasty | garhwali | 1044380 | dynn_Panwar | rajput |
| paramara_dynasty | bhil | 1042077 | dynn_Paramara | malvi |
| pepoli_dynasty | emilian | 8674 | dynn_Pepoli | italian |
| perigord_dynasty | limousin | 100216 | dynn_Perigord | occitan |
| piast_dynasty | silesian | 699 | dynn_Piast | polish |
| poitiers_dynasty | vivaro_alpine | 413 | dynn_Poitiers | occitan |
| pratihara_dynasty | marwari | 1042066 | dynn_Pratihara | rajput |
| randolph_dynasty | scottish | 3146 | dynn_Randolph | english |
| rasulid_dynasty | yemeni_culture | 139 | dynn_Rasulid | bedouin |
| rathore_dynasty | marwari | 1044388 | dynn_Rathore | rajput |
| ravensberg_dynasty | westphalian | 7126 | dynn_Ravensberg | saxon |
| regenstein_dynasty | saxon | 101902 | dynn_Regenstein | franconian |
| reginar_dynasty | low_franconian | 7198 | dynn_Reginar | dutch |
| rossi_dynasty | emilian | 101841 | dynn_Rossi | italian |
| rusconi_dynasty | lombard | 1062032 | dynn_Rusconi | cisalpine |
| sahara_dynasty | tougoku_culture | 1042176 | dynn_Sahara | malinke |
| salm_dynasty | lorrain | 12437 | dynn_Salm | franconian |
| samma_dynasty | sindhi | 1042086 | dynn_Samma | gujarati |
| sangama_dynasty | kannadiga | 12318 | dynn_Sangama | kannada |
| sanudo_dynasty | venetian | 102020 | dynn_Sanudo | greek |
| sayfawa_dynasty | kanembu_culture | 1959974 | dynn_Sayfawa | kanuri |
| sayn_dynasty | moselle_franconian | 12445 | dynn_Sayn | franconian |
| scala_dynasty | venetian | 13032 | dynn_Scala | italian |
| scarponnois_dynasty | high_alemannic | 88 | dynn_Scarponnois | french |
| schauenburg_dynasty | holsatian | 12463 | dynn_Schauenburg | saxon |
| schwarzburg_dynasty | saxon | 7230 | dynn_Schwarzburg | franconian |
| schwerin_dynasty | western_pomeranian | 7154 | dynn_Schwerin | saxon |
| shah_dynasty | bengali | 2003035 | dynn_Shah | persian |
| siri_sanga_bo_dynasty | sinhalese | 1029174 | dynn_Siri_Sanga_Bo | sinhala |
| sisodia_dynasty | mewari | 1042098 | dynn_Sisodia | rajput |
| solomonid_dynasty | amhara | 7246 | dynn_Solomonid | ethiopian |
| soranzo_dynasty | venetian | 7238 | dynn_Soranzo | italian |
| spinola_dynasty | ligurian | 50 | dynn_Spinola | italian |
| sponheim_dynasty | westphalian | 12439 | dynn_Sponheim | franconian |
| steinfurt_dynasty | lower_saxon | 7122 | dynn_Steinfurt | saxon |
| strathclyde_dynasty | welsh | 100047 | dynn_Strathclyde | scottish |
| strathearn_dynasty | highland | 124 | dynn_Strathearn | scottish |
| thouars_dynasty | poitevin | 79 | dynn_Thouars | french |
| tiepolo_dynasty | venetian | 13006 | dynn_Tiepolo | italian |
| tomara_dynasty | bundeli | 1040200 | dynn_Tomara | hindustani |
| varman_dynasty | khmer_culture | 1044003 | dynn_Varman | assamese |
| vianden_dynasty | walloon | 283 | dynn_Vianden | franconian |
| vijaya_dynasty | vietnamese_culture | 1040024 | dynn_Vijaya | sogdian |
| villeneuve_dynasty | provencal | 3 | dynn_Villeneuve | norman |
| visconti_dynasty | lombard | 234 | dynn_Visconti | italian |
| walashma_dynasty | somali_culture | 7273 | dynn_Walashma | bedouin |
| waldeck_dynasty | rhine_franconian | 7125 | dynn_Waldeck | franconian |
| warenne_dynasty | english | 748 | dynn_Warenne | norman |
| welfen_dynasty | lower_saxon | 650 | dynn_Welfen | swabian |
| wessex_dynasty | english | 100072 | dynn_Wessex | anglo_saxon |
| yadava_dynasty | telugu | 1044302 | dynn_Yadava | hindustani |
| ziegenhain_dynasty | rhine_franconian | 7173 | dynn_Ziegenhain | franconian |
| zorzi_dynasty | venetian | 8734 | dynn_Zorzi | italian |

## 多对多匹配（需要手工核对）

### mod 有多个 key 对应同一 vanilla 家族

| token | mod_keys | vanilla_ids |
|---|---|---|
| anjou | anjou_dynasty / anjou_jerusalem_dynasty / valois_anjou_dynasty | 81 / 723 |
| burgundy | burgundy_dynasty / burgundy_portuguese_dynasty | 9616 |
| chauhan | chauhan_dynasty / chauhan_jalore_dynasty / chauhan_patna_dynasty | 1042081 / 1044367 |
| fitzalan | fitzalan_bedale_dynasty / fitzalan_dynasty | 101899 |
| haro | haro_dynasty / haro_orduna_dynasty | 778 |
| hohenzollern | hohenzollern_brandenburg_dynasty / hohenzollern_dynasty / hohenzollern_nurnberg_dynasty | 12476 |
| ibelin | ibelin_armenia_dynasty / ibelin_dynasty | 23102 |
| komnenos | komnenos_dynasty / megas_komnenos_dynasty | 634 |
| orsini | orsini_aldobrandeschi_dynasty / orsini_dynasty / orsini_monterotondo_dynasty | 2 / 7215 |
| palaiologos | palaiologos_dynasty / palaiologos_monferrato_dynasty | 48 / 628 |
| peralta | de_peralta_dynasty / peralta_dynasty | 101911 |

### vanilla 有多个 ID 对应同一家族

| token | mod_keys | vanilla_ids |
|---|---|---|
| anjou | anjou_dynasty / anjou_jerusalem_dynasty / valois_anjou_dynasty | 81 / 723 |
| ayyubid | ayyubids_dynasty | 24000 / 101168 |
| barcelona | barcelona_dynasty | 100204 / 629 |
| beaumont | beaumont_dynasty | 710 / 5061 |
| bourbon | bourbon_dynasty | 329 / 100146 |
| cardona | cardona_dynasty | 10029 / 10025 |
| chauhan | chauhan_dynasty / chauhan_jalore_dynasty / chauhan_patna_dynasty | 1042081 / 1044367 |
| courtenay | courtenay_dynasty | 9301 / 23100 |
| gabras | gabras_dynasty | 7314 / 101091 |
| hafsid | hafsid_dynasty | 7276 / 1029093 |
| harcourt | harcourt_dynasty | 530 / 5000 |
| joinville | joinville_dynasty | 241 / 23110 |
| monomachos | monomachos_dynasty | 636 / 5061090 |
| montcada | montcada_dynasty | 336 / 10026 |
| nasrid | nasrid_dynasty | 577 / 7338 / 100709 / 101904 |
| orsini | orsini_aldobrandeschi_dynasty / orsini_dynasty / orsini_monterotondo_dynasty | 2 / 7215 |
| palaiologos | palaiologos_dynasty / palaiologos_monferrato_dynasty | 48 / 628 |
| strathearn | strathearn_dynasty | 124 / 9101 |
| sully | sully_dynasty | 94 / 1042647 |
| terter | terter_dynasty | 40 / 17001 |
| varman | varman_dynasty | 1044003 / 1044300 |
| visconti | visconti_dynasty | 234 / 1042014 |
