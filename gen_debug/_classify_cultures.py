# -*- coding: utf-8 -*-
"""按 11 类标准给每个文化分类。

判据优先级：CULT_RULE > LANG_RULE > GROUP_RULE > 自动（同名 / 语言唯一 / 传承唯一）

类别：
 1 同名同地可直接对上
 2 异名同族（族群演变）
 3 同名但错位，应改指另一个 CK3 文化
 4 按语言并入 CK3 文化
 5 按方言并入 CK3 文化
 6 按文化组并入 CK3 文化
 7 按地理并入 CK3 文化
 8 CK3 无此文化，需建融合文化（名称与 CK3 融合名对应）
 9 CK3 无此文化，需建分离文化
10 CK3 地图外，但可参考同类文化的传统
11 CK3 地图外且无关联，需自创传统
"""
import io, os, re, csv, collections

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
BASE = os.path.join(MOD, "gen_debug", "_culture_classify_base.csv")
VAN = os.path.join(MOD, "gen_debug", "_ck3_vanilla_cultures.csv")
OUT = os.path.join(MOD, "gen_debug", "_culture_classification.csv")

CAT_LABEL = {
    1: "同名同地",
    2: "异名同族",
    3: "同名错位",
    4: "按语言并入",
    5: "按方言并入",
    6: "按文化组并入",
    7: "按地理并入",
    8: "需建融合文化",
    9: "需建分离文化",
    10: "图外可参考",
    11: "图外自创",
}


def r(cat, target, note="", conf="high"):
    return (cat, target, note, conf)


# ============ 大洲（按主导王国判定）============
# 用于在 CSV 里给每个文化标一个大洲，方便按洲筛选阅览。
# 少数跨洲的按主体归：高加索→亚洲、马卡罗尼西亚→非洲、
# north_atlantic_islands→欧洲（冰岛/法罗）、great_lakes 在本数据里是**非洲**大湖地区
# （卢旺达/布隆迪/乌干达一带，不是北美五大湖）。
CONTINENT = {}
for _cont, _ks in {
    "欧洲": "france great_britain ireland iberia italy north_german south_german "
            "scandinavian baltic carpathia balkan ruthenia russian ural north_atlantic_islands",
    "亚洲": "anatolia arabia crescent persia khorasan caucasus steppes "
            "central_india deccan hindustan bengal western_india "
            "tibet xinjiang mongolia manchuria west_siberia east_siberia "
            "north_china south_china east_china west_china korea japan "
            "indochina indonesia",
    "非洲": "egypt nubia maghreb sahel guinea central_africa kongo southern_africa "
            "zimbabwe swahili_coast great_lakes ethiopia somalia madagascar macaronesia",
    "北美洲": "alaska canada great_plains east_coast west_coast "
              "aridoamerica mesoamerica central_america caribbean",
    "南美洲": "andes colombia brazil la_plata chaco",
    "大洋洲": "australia new_zealand melanesia micronesia polynesia",
}.items():
    for _k in _ks.split():
        CONTINENT[_k] = _cont


# ============ 文化级例外（用户点名 + 关键个案）============
CULT_RULE = {
    # —— 用户点名 ——
    "czech":                r(1, "czech", "地理完全对得上"),
    "cuman_culture":        r(1, "cuman", "地理不重合，但符合库曼人迁入匈牙利的历史"),
    "bedouin":              r(1, "bedouin", "EU5 把内志等地拆出贝都因，地理略偏"),
    "uyghur_culture":       r(2, "uyghur", "维吾尔=回鹘"),
    "korean_culture":       r(2, "goryeo", "朝鲜=高丽"),
    "latvian":              r(2, "latgalian", "拉脱维亚=拉特加尔"),
    "slovene":              r(2, "carantanian", "斯洛文尼亚=卡兰塔尼亚"),
    "turkoman_culture":     r(2, "turkmen", "突厥蛮=CK 土库曼（CK3 turkmen 显示名「土库曼」）"),
    "turkmen_culture":      r(3, "turkish", "EU5 土库曼≠CK 同名 turkmen；CK3 的 turkish 显示名就是「乌古斯」，指乌古斯人"),
    "khorezmian_culture":   r(3, "karluk", "CK3 khwarezmian 是东伊朗语（斯基泰语支），EU5 花剌子模已突厥化、讲葛逻禄语"),
    "chiyalik_culture":     r(6, "mogyer", "奇亚利克是马札尔文化组仅存文化；落 CK3 mogyer（马扎尔）——它是 hungarian 的父文化（created 1000.1.1），比匈牙利更早，用户定"),
    # —— 新版官方要加的文化，本轮一律不建，全部落已有文化（用户 2026-10-22 定）——
    "norse_gael":           r(7, "gaelic", "诺斯-盖尔：新版官方将加入 norse_gael，不建；1337 群岛领主已盖尔化，用户定入盖尔"),
    "anglo_irish":          r(7, "english", "盎格鲁-爱尔兰：新版官方将加入，不建；爱尔兰的英格兰移民后裔，用户定入英格兰"),
    "turkish":              r(8, "anatolian_turkish", "突厥蛮+希腊融合，对应安纳托利亚突厥"),
    "turkish_culture":      r(4, "turkmen", "EU5 土耳其＝安纳托利亚突厥，用户定入 CK3 turkmen（土库曼）；注意 CK3 turkish 显示名是「乌古斯」不是土耳其"),
    "azeri_culture":        r(4, "turkish", "名为「阿塞拜疆」的文化（乌古斯-伊朗）→ CK3 turkish（显示名「乌古斯」）；用户 2026-10-27 澄清：此条只针对 azeri_culture，不含 adhari"),
    "zaza_culture":         r(6, "kurdish", "扎扎语属库尔德语支（西北伊朗语），EU5 误归 adharic_language；用户 2026-10-27 定入 kurdish"),
    # —— 其他关键个案 ——
    "andalusi":             r(2, "andalusian", "安达卢西=安达卢西亚"),
    "leonese":              r(2, "asturleonese", "莱昂=阿斯图里亚斯-莱昂"),
    "kochini":              r(2, "kochinim", "科钦犹太人"),
    "gothic_culture":       r(1, "gothic", "克里米亚哥特"),
    "coptic_culture":       r(2, "ancient_egyptian", "科普特人是古埃及人后裔（用户 2026-10-27 定入古埃及）"),
    "maltese":              r(7, "sicilian", "马耳他语，按用户定入西西里（仅一个岛，不单独建文化）"),
    "romani":               r(11, "romani", "CK3 原版无 romani 文化定义、无罗姆人角色（已查 history/characters），且 0 男爵领，不建"),
    "icelandic":            r(4, "norwegian", "CK3 无冰岛文化，按北日耳曼并入挪威"),
    "silesian":             r(5, "polish", "西里西亚方言属莱赫语支"),
    "sorbian":              r(7, "polabian", "索布与波拉布地理相邻"),
    "sorb":                 r(7, "polabian", "索布与波拉布地理相邻"),
    "kashubian":            r(2, "pommeranian", "卡舒比=波美拉尼亚"),
    "slovak":               r(2, "slovien", "斯洛伐克=slovien"),
    "rusyn_culture":        r(7, "russian", "鲁塞尼亚人，CK3 原版东斯拉夫一律 russian（volhynian 原版 0 省份）"),
    "ukrainian":            r(7, "russian", "乌克兰，CK3 原版东斯拉夫一律 russian（volhynian 原版 0 省份）"),
    "belarusian":           r(7, "russian", "白俄罗斯，CK3 原版东斯拉夫一律 russian（severian 原版 0 省份）"),
    "volhynian_culture":    r(7, "russian", "沃里尼亚，CK3 的 volhynian 原版 0 省份，k_ruthenia 22 省全 russian"),
    "severian":             r(7, "russian", "谢韦里安，CK3 的 severian 原版 0 省份，k_ruthenia 22 省全 russian"),
    "novgorodian":          r(2, "russian", "诺夫哥罗德=罗斯；CK3 的 ilmenian 虽有定义但原版 0 省份，不能当落点"),
    "udmurt":               r(6, "komi", "彼尔姆文化组，CK3 只有科米"),
    "moksha":               r(4, "mordvin", "莫尔多瓦语支"),
    "erzya":                r(4, "mordvin", "莫尔多瓦语支"),
    "ingrian":              r(4, "karelian", "因格里亚，用户定与卡累利阿同归卡累利阿"),
    "besermyan":            r(6, "komi", "别谢尔米亚人属彼尔姆文化组（乌德穆尔特一支），随彼尔姆"),
    "livonian":             r(4, "estonian", "利沃尼亚语属南芬兰语支"),
    "votic":                r(4, "finnish", "沃提克语属芬兰语支"),
    "gutnish":              r(4, "swedish", "哥特兰语属北日耳曼"),
    "szekely":              r(4, "hungarian", "塞凯伊属匈牙利语"),
    "csango":               r(4, "hungarian", "昌戈属匈牙利语"),
    "montenegrin":          r(4, "serbian", "黑山属塞尔维亚语"),
    "megleno_romanian":     r(4, "vlach", "属弗拉赫"),
    "istroromanian":        r(4, "vlach", "属弗拉赫"),
    # —— 巴尔干（用户 2026-10-21 定）——
    # 罗马尼亚语系一律 → 瓦拉几亚（vlach）；匈牙利+塞凯伊 → 匈牙利；希腊语 → 希腊。
    # 特兰西瓦尼亚 / 阿罗马尼亚 / 达尔马提亚均为备选，本轮不建。
    "transylvanian":        r(4, "vlach", "特兰西瓦尼亚（罗马尼亚+匈牙利）列为备选，本轮并入瓦拉几亚"),
    "aromanian":            r(4, "vlach", "阿罗马尼亚人数过少，不建，并入瓦拉几亚"),
    "dalmatian":            r(7, "croatian", "达尔马提亚语规模过小不建，按地理入克罗地亚"),
    # —— 意大利（用户 2026-10-21 定）——
    # 高卢-意大利语支 → 山南（cisalpine）；西西里/那不勒斯/马耳他 → 西西里；
    # 撒丁/科西嘉 → 撒丁；其余意大利语 → 意大利。
    # 意大利 DLC 未出，本轮不建任何新意大利文化（格里科/那不勒斯/罗曼什/阿尔卑坦一律不建）。
    "ladin":                r(7, "cisalpine", "拉登语属雷蒂亚语，按地理入山南"),
    "friulian":             r(7, "cisalpine", "弗留利语属雷蒂亚语，按地理入山南"),
    "romansh":              r(7, "cisalpine", "罗曼什属雷蒂亚语；新文化列为备选（意大利 DLC 未出），按语支入山南"),
    "lombard":              r(7, "cisalpine", "伦巴第语属高卢-意大利语支，按用户定入山南"),
    "southern_gallo_italic": r(7, "cisalpine", "南高卢-意大利语，按用户定入山南"),
    "venetian":             r(7, "cisalpine", "威尼托语属高卢-意大利语支，入山南"),
    "ligurian":             r(7, "cisalpine", "利古里亚语属高卢-意大利语支，入山南"),
    "piedmontese":          r(7, "cisalpine", "皮埃蒙特语属高卢-意大利语支，入山南"),
    "emilian":              r(7, "cisalpine", "艾米利亚语属高卢-意大利语支，入山南"),
    "romagnol":             r(7, "cisalpine", "罗马涅语属高卢-意大利语支，入山南"),
    "marchigiano":          r(7, "cisalpine", "马尔凯语属高卢-意大利语支，入山南"),
    "cosentino":            r(7, "sicilian", "南意卡拉布里亚，按用户定入西西里"),
    "neapolitan":           r(7, "sicilian", "那不勒斯语，按用户定入西西里（新文化列为备选，意大利 DLC 未出）"),
    "sicilian":             r(1, "sicilian", "同名"),
    "tuscan":               r(4, "italian", "托斯卡纳语=意大利标准语"),
    "median_dialect":       r(4, "italian", "中意大利方言，归意大利"),
    "corsican":             r(7, "sardinian", "科西嘉语，按用户定与萨丁同归撒丁"),
    "sardinian":            r(1, "sardinian", "同名"),
    "sassarese":            r(1, "sardinian", "撒丁岛"),
    "gallurese":            r(1, "sardinian", "撒丁岛"),
    "griko_culture":        r(4, "italian", "格里科（南意希腊语残留）人数过少无地块，不建文化，归意大利"),
    "italki":               r(4, "radhanite", "意大利犹太人语言，属犹太散居，随拉丹尼特"),
    # 无地意大利银行家族文化（0 男爵领），用户定一律归意大利
    "acciaioli_bank_culture": r(4, "italian", "佛罗伦萨阿恰约利银行家族，无地，归意大利"),
    "bardi_bank_culture":     r(4, "italian", "佛罗伦萨巴尔迪银行家族，无地，归意大利"),
    "peruzzi_bank_culture":   r(4, "italian", "佛罗伦萨佩鲁齐银行家族，无地，归意大利"),
    # 拉丁（EU5 roman_culture，拜占庭境内的拉丁语人群）→ CK3 roman
    # 注：CK3 原版 roman 有文化定义，但 history/characters 里 0 个角色使用、0 个省份，属空定义文化
    "roman_culture":          r(2, "roman", "拉丁＝罗马；CK3 原版 roman 有定义但无省份无角色，用户点名要 roman"),
    "walloon":              r(4, "french", "瓦隆语属奥依语；新版官方将加入 walloon，不建融合文化，用户定入法兰西"),
    # EU5 的 francique_dialect 是奥依语支（francien，含香槟/洛林/皮卡第/瓦隆），
    # 不是日耳曼的法兰克尼亚。语言柱被错挂成 language_high_german
    # （见 _eu5_language_to_ck3.py 第 92 行），此处按实际语支落 french。
    "champenais":           r(5, "french", "香槟方言属奥依语（语言柱误挂 high_german，实为 francique=奥依）"),
    "lorrain":              r(5, "french", "洛林方言属奥依语（同上）"),
    "picard":               r(5, "french", "皮卡第方言属奥依语（同上）"),
    # —— 法国：用户 2026-10-21 定的备选新文化，本轮均不建，回到所属语支 ——
    "gallo":                r(7, "breton", "上布列塔尼的加洛语（奥依语），用户 2026-10-22 定按地理入布列塔尼"),
    "angevin":              r(4, "french", "安茹方言属奥依语；安茹融合列为备选，暂并入法兰西"),
    "arpitan":              r(4, "french", "阿尔卑坦语 EU5 归法语支（french_group;swiss_group），用户 2026-10-27 定入法兰西"),
    "luxembourgeois":       r(5, "franconian", "卢森堡语属中德方言"),
    "alsatian":             r(5, "swabian", "阿尔萨斯语属阿勒曼尼"),
    "swiss_german":         r(5, "swabian", "瑞士德语属阿勒曼尼"),
    "frisian":              r(1, "frisian", "同名"),
    "dutch":                r(1, "dutch", "同名"),
    "flamand":              r(1, "dutch", "佛兰德属荷兰语"),
    "brabantian":           r(1, "dutch", "布拉班特属荷兰语"),
    "limburgish":           r(1, "dutch", "林堡属荷兰语"),
    "gronings":             r(5, "saxon", "格罗宁根属低地萨克森"),
    "low_saxon":            r(5, "saxon", "低地萨克森"),
    "plattdeutsch":         r(5, "saxon", "低地德语"),
    "ripuarian":            r(5, "franconian", "中法兰克方言"),
    "moselle_franconian":   r(5, "franconian", "摩泽尔法兰克"),
    "palatine_german":      r(5, "franconian", "普法尔茨属法兰克"),
    "east_franconian":      r(5, "franconian", "东法兰克"),
    "thuringian":           r(5, "franconian", "图林根属中德"),
    "upper_saxon":          r(5, "franconian", "上萨克森属中德"),
    "silesian_german":      r(5, "saxon", "西里西亚德语"),
    "bavarian":             r(1, "bavarian", "同名"),
    "austrian":             r(1, "bavarian", "奥地利属巴伐利亚"),
    "tyrolean":             r(1, "bavarian", "蒂罗尔属巴伐利亚"),
    "carinthian":           r(1, "bavarian", "克恩顿属巴伐利亚"),
    "swabian":              r(1, "swabian", "同名"),
    "alemannic":            r(5, "swabian", "阿勒曼尼"),
    "franconian":           r(1, "franconian", "同名"),
    "saxon":                r(1, "saxon", "同名"),
    "german":               r(1, "german", "同名"),
    # —— 无 EU5 数据 / 占位 ——
    "cunco_culture":        r(11, "cunco", "美洲，EU5 无语言数据"),
    "manekenk_culture":     r(11, "manekenk", "美洲，EU5 无语言数据"),
    "yaros_culture":        r(11, "yaros", "美洲，EU5 无语言数据"),
    "gen_culture_unsettled": r(11, "unsettled", "无主之地占位文化，保持原样"),
    # —— 同名异族（名字撞上 CK3，但不是同一个人群，必须显式拦下）——
    "yao_culture":          r(6, "east_bantu", "非洲瑶族（班图语支，马拉维/莫桑比克），与 CK3 瑶族（苗语支）同名异族；班图语族统一并入东班图，用户 2026-10-27", "high"),
    # avar_culture 见文末「亚洲按语族并入」段（高加索阿瓦尔 → alan）
    # —— 德国波罗的海沿岸（用户 2026-10-22 定，不建新文化）——
    # EU5 的波美拉尼亚（western/eastern_pomeranian）是低地德语的德意志人口，
    # 与 CK3 的 pommeranian（实为莱赫语的卡舒比人，见 kashubian）不是同一人群 → 入萨克森。
    # EU5 的 prussian 同样是低地德语德意志人口，与 CK3 波罗的古普鲁士同名异族 → 也入萨克森。
    # CK3 的 prussian 保留给波罗的普鲁士人（pruthenian/sudovian/curonian 的落点）。
    "western_pomeranian":   r(7, "saxon", "西波美拉尼亚（低地德语），用户定入萨克森（不建融合文化）"),
    "eastern_pomeranian":   r(7, "saxon", "东波美拉尼亚（低地德语），用户定入萨克森（不建融合文化）"),
    "prussian":             r(7, "saxon", "EU5 普鲁士是低地德语的德意志人口，用户定入萨克森；CK3 prussian 留给波罗的普鲁士人", "high"),
    "merya":                r(1, "merya", "CK3 有 merya，同名同地"),
    "mossi":                r(1, "mossi", "CK3 有 mossi，同名同地"),
    "she_culture":          r(4, "han", "畲族无 EU5 数据、0 男爵领，按汉语并入汉（另可选 hmong）", "medium"),

    # —— 藏区 / 喜马拉雅细分 ——
    # 依据：CK3 原版把青藏高原拆成 9 个王国，各王国的 culture 分布见
    # game/history/provinces/k_{u,tsang,kham,amdo,guge,gyalrong,lhomon,himalaya,maryul}.txt
    #   k_u         bodpa 16 / sumpa 10 / zhangzhung 2
    #   k_tsang     tsangpa 10 / bodpa 8 / zhangzhung 3
    #   k_kham      bodpa 58 / sumpa 32 / qiang 27 / lhomon 11
    #   k_amdo      bodpa 40 / tuyuhun 31 / sumpa 30
    #   k_guge      zhangzhung 38 / bodpa 36 / tsangpa 3
    #   k_gyalrong  bodpa 29 / qiang 25 / tangut 23
    #   k_lhomon    lhomon 17 / kirati 1
    #   k_himalaya  nepali 36（含 #Newar）/ kirati 8 / tsangpa 1（#Sherpa）
    #   k_maryul    zhangzhung 20 / kashmiri 20 / bodpa 29
    # 原先一律走「藏语→bodpa」，把尼泊尔、不丹、拉达克也吞进吐蕃，故按 CK3 落点分流。
    "utsang_culture":       r(2, "bodpa", "卫藏=吐蕃核心，CK3 k_u 主体 bodpa"),
    "khampa_culture":       r(2, "bodpa", "康巴，CK3 k_kham 主体 bodpa（58）"),
    "changpa_culture":      r(2, "bodpa", "羌塘，CK3 无专名，随吐蕃"),
    "amdowa_culture":       r(7, "sumpa", "安多，CK3 k_amdo 有 sumpa（30），苏毗即安多/青唐故地"),
    "tebbu_culture":        r(7, "sumpa", "迭部在甘南，属安多，随苏毗"),
    "ladakh_culture":       r(7, "zhangzhung", "拉达克=麻域（k_maryul），CK3 主体 zhangzhung（20）"),
    "balti_culture":        r(7, "zhangzhung", "巴尔蒂斯坦同属阿里/麻域圈，CK3 归象雄"),
    "ngalop_culture":       r(7, "lhomon", "阿洛=不丹主体民族，CK3 k_lhomon 全为 lhomon"),
    "sikkim_culture":       r(7, "lhomon", "锡金=哲孟雄，CK3 珞门含 Lepcha（#Lepcha）"),
    "monpa_culture":        r(7, "lhomon", "门巴，CK3 k_kham/k_lhomon 均标 #Monpa 于 lhomon"),
    "newar_culture":        r(7, "nepali", "尼瓦尔，CK3 k_himalaya 有 culture = nepali #Newar"),
    "magar_culture":        r(7, "kirati", "马加尔为尼泊尔山地民族，CK3 k_himalaya 有 kirati（8）"),
    "gurung_culture":       r(7, "kirati", "古隆同上，随罽罗多"),
    "tamang_culture":       r(7, "kirati", "塔芒同上，随罽罗多"),
    "limbu_culture":        r(7, "kirati", "林布是罽罗多核心族群"),
    "sherpa_culture":       r(7, "tsangpa", "夏尔巴，CK3 k_himalaya 有 culture = tsangpa #Sherpa"),
    "gyalrong_culture":     r(7, "qiang", "嘉绒（羌-藏过渡），用户定入羌（k_gyalrong 原版 qiang 25 省）"),

    # —— 突厥语支细分（用户 2026-10-22 定，不建融合文化）——
    # 按 EU5 的草原族群文化组（steppe_group）分东西支：
    #   带 steppe_group（tatar_group;turkic_group;steppe_group）→ CK3 cuman（库曼，西支）
    #   不带 steppe_group 的钦察语 → CK3 kipchak（钦察，东支）
    # 即：astrakhani / crimean / nogai → cuman；uzbek / kyrgyz / telengit / teleut /
    #     yerle_qaliq → kipchak。
    # 例外①：kazani / mishar 虽然也带 steppe_group，但它们是伏尔加保加尔底子
    #       （喀山汗国的前身），另归 bolghar，不参与这条东西支划分。
    # 例外②：高加索突厥 balkar / karachay / kumyk 只有 turkic_group、不带 steppe_group，
    #       但用户 2026-10-27 定**不算钦察、算阿兰**（见下三行）。
    # 不并入 kazakh（哈萨克）：1337 年还没有哈萨克汗国，那是 15 世纪的事。
    "astrakhani":           r(7, "cuman", "阿斯特拉罕鞑靼，带 steppe_group，西支入库曼"),
    "crimean":              r(7, "cuman", "克里米亚鞑靼，带 steppe_group，西支入库曼"),
    "kazani":               r(7, "bolghar", "喀山鞑靼＝伏尔加保加尔底子，入保加尔（虽带草原组，不参与东西支划分）"),
    "mishar":               r(7, "bolghar", "米沙鞑靼属伏尔加系，随喀山入保加尔"),
    "nogai":                r(7, "cuman", "诺盖，带 steppe_group，西支入库曼"),
    # 高加索突厥（只 turkic_group、无 steppe_group）→ khazar（可萨）。它们在 EU5 里语言是
    # kipchak_language，会被 LANG_RULE 收走，故必须在此用 CULT_RULE 覆盖。
    # 2026-10-27 用户改口：原定 alan，后改为可萨更合适。
    "balkar_culture":       r(6, "khazar", "巴尔卡尔（高加索突厥，无 steppe_group），用户 2026-10-27 定入可萨"),
    "karachay_culture":     r(6, "khazar", "卡拉恰伊（高加索突厥，无 steppe_group），用户 2026-10-27 定入可萨"),
    "kumyk_culture":        r(6, "khazar", "库梅克（高加索突厥，无 steppe_group），用户 2026-10-27 定入可萨"),
    # 能独立的一律保留：CK3 00_turkic.txt 有 kirghiz（黠戛斯），不并进 kipchak。
    "kyrgyz_culture":       r(2, "kirghiz", "吉尔吉斯＝CK3 kirghiz（黠戛斯，叶尼塞/天山吉尔吉斯），原版有独立文化，保留"),

    # —— 柏柏尔：按地理分配 ——
    # CK3 原版落点：butr 在 k_tahert(17) k_africa(12) k_anbiya(11) k_sahara(9) k_egypt(7)
    #   k_maghreb(6) k_hausaland(4) k_songhay(4) k_ghana(1)；
    # baranis 只在 k_maghreb(15) k_africa(7) k_tahert(2)，即摩洛哥一带。
    # 故阿尔及利亚/突尼斯/撒哈拉诸族→butr，摩洛哥诸族→baranis。
    "zenati":               r(6, "butr", "泽纳塔，阿尔及利亚/突尼斯内陆，落 k_tahert（butr 17 : baranis 2）"),
    "mozabite":             r(6, "butr", "姆扎卜在阿尔及利亚北部撒哈拉，同 k_tahert/k_sahara 的 butr"),
    "chaoui":               r(6, "baranis", "沙维（奥雷斯山）：CU 3 行 baranis 2 / maghrebi 1、无 butr，用户 2026-10-27 定 baranis"),
    "eastern_amazigh":      r(6, "butr", "东柏柏尔在突尼斯/的黎波里塔尼亚，CK3 k_africa/k_anbiya 为 butr"),
    "kabyle":               r(6, "baranis", "卡比尔（卡比利亚）：CU 1 行 baranis 1、无 butr，用户 2026-10-27 定 baranis"),
    "lamtuna_culture":      r(6, "butr", "兰图纳在毛里塔尼亚/西撒哈拉，CK3 k_sahara/k_ghana 为 butr"),
    "godala_culture":       r(6, "butr", "古达拉在毛里塔尼亚，同 k_sahara/k_songhay 的 butr"),
    "messufa_culture":      r(6, "butr", "梅苏法在撒哈拉西部，同 k_sahara 的 butr"),
    "tuareg":               r(6, "butr", "图阿雷格在撒哈拉，同 k_sahara 的 butr"),
    "sanhaja":              r(6, "baranis", "桑哈贾在摩洛哥/西撒哈拉，CK3 k_maghreb 主体 baranis（15）"),
    "masmuda":              r(6, "baranis", "马斯穆达为摩洛哥主体柏柏尔，CK3 k_maghreb 主体 baranis（15）"),

    # —— 马格里布三国（用户 2026-10-22 定，不建融合文化）——
    # 与已定的 libyan_arabic→maghrebi 同一口径：整个马格里布阿拉伯语区落 CK3 maghrebi。
    # 注：moroccan/tunisian 的 CU 匹配范围虽以 baranis 最多，但用户 2026-10-27 明确
    # **阿拉伯语文化不按 CU 改**，保持 maghrebi；CU 口径只适用于柏柏尔文化（kabyle/chaoui 等）。
    "algerian":             r(7, "maghrebi", "阿尔及利亚阿拉伯语，入马格里布（不建 algerian_hybrid）"),
    "moroccan":             r(7, "maghrebi", "摩洛哥阿拉伯语，入马格里布（不建 moroccan_hybrid）"),
    "tunisian":             r(7, "maghrebi", "突尼斯阿拉伯语，入马格里布（不建 tunisian_hybrid）"),

    # —— 苏丹-阿拉伯（用户 2026-10-22 定）——
    "sudanese_arab":        r(7, "bedouin", "苏丹阿拉伯，用户定入贝都因（不建融合文化）"),

    # —— 哈德拉毛（用户 2026-10-28 定）——
    # 挂 peninsular_dialect，LANG_RULE 会整组收成 bedouin；但 hadhrami 是也门东南部
    # （哈德拉毛/穆卡拉一带），与 yemeni 同属南阿拉伯，故单独覆盖成 yemeni。
    # 同组其余（najdi/hijazi/omani/kaliji/bahrani/dhofari/shihhi）仍走 LANG_RULE→bedouin。
    "hadhrami_culture":     r(4, "yemeni", "哈德拉毛（也门东南），用户 2026-10-28 定入也门而非贝都因"),

    # —— 尼罗-撒哈拉（用户 2026-10-27 定：按文化组一律入达朱）——
    # EU5 把苏丹-埃塞俄比亚边境的尼罗-撒哈拉族群拆成一堆小文化，部分还错标成
    # `egyptian_dialect`（埃及方言），按语言并入会全变 CK3 `egyptian`（撒南出现埃及文化的原因）。
    # 口径：CK3 原版 `daju`（达朱，00_east_african.txt:93，nubia/达尔富尔）当代表。
    # 组级规则见 GROUP_RULE["nilosahelian_group"]；下面逐个写是为了压过 LANG_RULE
    # （dinka_language / nubian_language / saharan_language / egyptian_dialect 都在这几个身上）。
    "berta_culture":        r(6, "daju", "贝尔塔（尼罗-撒哈拉），用户定入达朱"),
    "fur_culture":          r(6, "daju", "富尔（达尔富尔，尼罗-撒哈拉），EU5 误标 egyptian_dialect，用户定入达朱"),
    "gumuz_culture":        r(6, "daju", "古穆兹（埃塞俄比亚西部，尼罗-撒哈拉），EU5 误标 egyptian_dialect，用户定入达朱"),
    "kadu_culture":         r(6, "daju", "卡杜（努巴山地，尼罗-撒哈拉），用户定入达朱"),
    "katla_culture":        r(6, "daju", "卡特拉（努巴山地，尼罗-撒哈拉），用户定入达朱"),
    "kunama_culture":       r(6, "daju", "库纳马（厄立特里亚-苏丹，尼罗-撒哈拉），EU5 误标 egyptian_dialect，用户定入达朱"),
    "moru_culture":         r(6, "daju", "莫鲁（南苏丹，尼罗-撒哈拉），用户定入达朱"),
    "nuba":                 r(6, "daju", "努巴（努巴山地，尼罗-撒哈拉），用户定入达朱"),
    "nyimang_culture":      r(6, "daju", "尼曼（努巴山地，尼罗-撒哈拉），用户定入达朱"),
    "surma_culture":        r(6, "daju", "苏尔马（埃塞俄比亚西南，尼罗-撒哈拉），用户定入达朱"),
    # —— 撒哈拉语族（用户 2026-10-27 定：都并入扎加瓦，加奈姆布例外）——
    # LANG_RULE["saharan_language"] 已改 zaghawa，自动带走 bilala / maba_africa / masalit / runga。
    # 下面两条必须显式写：toubou 挂在 nilosahelian_group，会被 GROUP_RULE_STRONG 截成 daju；
    # kanembu 是「除加奈姆布外」的那个例外。
    "toubou_culture":       r(4, "zaghawa", "图布（提贝斯提，撒哈拉语族），用户 2026-10-27 定入扎加瓦（原达朱口径已改）"),
    "kanembu_culture":      r(4, "kanuri", "加奈姆布（卡努里语方言），用户 2026-10-27 定唯一保留卡努里"),
    # 下面两个 EU5 没标文化组（eu5_groups 为空），但实为尼罗-撒哈拉：
    "tunjur_culture":       r(7, "daju", "通朱尔（达尔富尔/乍得，尼罗-撒哈拉；EU5 未标组、误标 egyptian_dialect），用户定入达朱"),
    "funj_culture":         r(7, "daju", "芬吉（青尼罗河，尼罗-撒哈拉；EU5 未标组、误标 egyptian_dialect），用户定入达朱"),

    # ============ 非洲/安达曼收尾（用户 2026-10-27，只针对 CU 地图内剩下的 13 个）============
    # 用户逐条点名：库希特→索马里、尼罗特→沃莱塔、西非+中非→萨奥、伊乔→伊博、
    # 类班图→班图（east_bantu）、Ket→靺鞨、安达曼→CK3 原版那旺（nakkavaram）。
    # 注意：这里刻意**不写组级规则**——cushitic_group 有 17 个、nilotic_group 有 11 个、
    # west_african_group;central_african_group 有 13 个，组级会把 afar/beja/welayta/ethiopian
    # 这些本来已经落对的也一起冲掉，而用户点的是 CU 范围内那几个。
    "oromo_culture":        r(7, "somali", "奥罗莫（库希特），用户 2026-10-27 定入索马里"),
    "south_cushitic_culture": r(7, "somali", "南库希特（伊拉克w 等），用户 2026-10-27 定入索马里"),
    "dinka_culture":        r(7, "welayta", "丁卡（尼罗特），用户 2026-10-27 定入沃莱塔"),
    "kalenjin_culture":     r(7, "welayta", "卡伦金（尼罗特），用户 2026-10-27 定入沃莱塔"),
    "maasai_culture":       r(7, "welayta", "马赛（尼罗特），用户 2026-10-27 定入沃莱塔"),
    "ongamo_culture":       r(7, "welayta", "翁加莫（尼罗特），用户 2026-10-27 定入沃莱塔"),
    "adamawa_culture":      r(7, "sao", "阿达马瓦（西非+中非组），用户 2026-10-27 定入萨奥"),
    "baguirmi_culture":     r(7, "sao", "巴吉尔米（西非+中非组），用户 2026-10-27 定入萨奥"),
    "ijaw":                 r(7, "igbo", "伊乔（尼日尔三角洲），用户 2026-10-27 定入伊博"),
    "bantoid":              r(6, "east_bantu", "类班图（bantoid，班图的上位），用户 2026-10-27 定入东班图"),
    "benue":                r(6, "east_bantu", "贝努埃（类班图），用户 2026-10-27 定入东班图"),
    "ket_culture":          r(7, "mohe", "凯特（叶尼塞语系孤岛，EU5 无组），用户 2026-10-27 定入靺鞨"),
    # 安达曼：CK3 原版就把安达曼群岛（c_andamans，province 11248 Marakele / Great Andaman）
    # 定成 nakkavaram（那旺，00_nakkavaram.txt），历史角色 andaman_1..6 也是 nakkavaram。
    "andamanese_culture":   r(7, "nakkavaram", "安达曼人，CK3 原版安达曼群岛即 nakkavaram（那旺），用户 2026-10-27 定"),

    # —— 库希特/尼罗特同组剩余成员（用户 2026-10-27「动」：按组一并收，不限 CU 范围）——
    # 上面 13 条只覆盖了 CU 地图内的人口多数文化；cushitic_group / nilotic_group 里还有
    # 13 个成员挂在 `NEW:highland_cushitic` / `NEW:luo` / `NEW:lotuko` / `NEW:kalenjin` /
    # `NEW:dinka` / `NEW:dahalo` 上，用户拍板按「库希特→索马里、尼罗特→沃莱塔」一并收掉。
    # 仍然只写文化级：组里 somali/afar/beja(cat1) 与 agaw→ethiopian、gonga/omo/ometo→welayta
    # 已经落对，写组级会把 afar/beja/ethiopian 一起冲掉。
    "sidama_culture":       r(7, "somali", "西达马（库希特），用户 2026-10-27 定入索马里"),
    "burji_culture":        r(7, "somali", "布尔吉（库希特），用户 2026-10-27 定入索马里"),
    "hadiya_culture":       r(7, "somali", "哈迪亚（库希特），用户 2026-10-27 定入索马里"),
    "kambaata_culture":     r(7, "somali", "坎巴塔（库希特），用户 2026-10-27 定入索马里"),
    "gedeo_culture":        r(7, "somali", "盖德奥（库希特），用户 2026-10-27 定入索马里"),
    "dahalo_culture":       r(7, "somali", "达哈洛（库希特，肯尼亚沿海），用户 2026-10-27 定入索马里"),
    "turkana_culture":      r(7, "welayta", "图尔卡纳（尼罗特），用户 2026-10-27 定入沃莱塔"),
    "otuho_culture":        r(7, "welayta", "奥图霍（尼罗特），用户 2026-10-27 定入沃莱塔"),
    "anuak_culture":        r(7, "welayta", "阿努阿克（尼罗特），用户 2026-10-27 定入沃莱塔"),
    "luo_culture":          r(7, "welayta", "卢奥（尼罗特），用户 2026-10-27 定入沃莱塔"),
    "shilluk_culture":      r(7, "welayta", "希卢克（尼罗特），用户 2026-10-27 定入沃莱塔"),
    "tatoga_culture":       r(7, "welayta", "塔托加（尼罗特），用户 2026-10-27 定入沃莱塔"),
    "nuer_culture":         r(7, "welayta", "努埃尔（尼罗特），用户 2026-10-27 定入沃莱塔"),

    # ============ 中非内陆收尾（用户 2026-10-27：双组→萨奥、单中非→达朱、多贡塞努福按 CU）============
    # 这批是非洲最后 16 个还挂 NEW: 的文化。分组实测如下，**不能写组级**：
    #   west_african_group;central_african_group 组合全局只有 13 个，其中 adamawa_culture /
    #   baguirmi_culture 已落 sao；写组级会把整个西非一起吞掉。
    #   只有 central_african_group 的全局只有 3 个（gyele/seru/zande），也逐个写。
    # 多贡、塞努福只挂 west_african_group，按用户口径走 CU 对照表：
    #   dogon  → cu_culture = marka（2 个 barony：douentza / kanibonzon）
    #   senufo → cu_culture = bobo （1 个 barony：korhogo）
    #   marka / bobo 都是 CK3 原版文化（_ck3_vanilla_cultures.csv 228/230 行）。
    # —— 双组（西非+中非）→ 萨奥 ——
    "baka_culture":         r(6, "sao", "巴卡（西非+中非组），用户 2026-10-27 定入萨奥"),
    "banda_culture":        r(6, "sao", "班达（西非+中非组），用户 2026-10-27 定入萨奥"),
    "bomassa_culture":      r(6, "sao", "博马萨（西非+中非组），用户 2026-10-27 定入萨奥"),
    "gbaya_culture":        r(6, "sao", "格巴亚（西非+中非组），用户 2026-10-27 定入萨奥"),
    "gula_iro_culture":     r(6, "sao", "古拉伊罗（西非+中非组），用户 2026-10-27 定入萨奥"),
    "lugbara_culture":      r(6, "sao", "卢格巴拉（西非+中非组，EU5 里 0 地块），用户 2026-10-27 定入萨奥"),
    "madi_culture":         r(6, "sao", "马迪（西非+中非组），用户 2026-10-27 定入萨奥"),
    "mandja_culture":       r(6, "sao", "曼贾（西非+中非组），用户 2026-10-27 定入萨奥"),
    "mbay_culture":         r(6, "sao", "姆拜（西非+中非组），用户 2026-10-27 定入萨奥"),
    "ngbandi_culture":      r(6, "sao", "恩班迪（西非+中非组），用户 2026-10-27 定入萨奥"),
    "sara_culture":         r(6, "sao", "萨拉（西非+中非组），用户 2026-10-27 定入萨奥"),
    # —— 只挂中非组 → 达朱 ——
    "gyele_culture":        r(6, "daju", "吉耶莱（仅中非组），用户 2026-10-27 定入达朱"),
    "seru_culture":         r(6, "daju", "塞鲁（仅中非组），用户 2026-10-27 定入达朱"),
    "zande_culture":        r(6, "daju", "赞德（仅中非组），用户 2026-10-27 定入达朱"),
    # —— 只挂西非组：按 CU 对照表 ——
    "dogon":                r(7, "marka", "多贡，按 CU 对照表落 marka（用户 2026-10-27 定）"),
    "senufo":               r(7, "bobo", "塞努福，按 CU 对照表落 bobo（用户 2026-10-27 定）"),

    # —— 班图语族：唯一保留的斯瓦希里（用户 2026-10-27）——
    # 其余 94 个 bantu_group 文化由 GROUP_RULE_STRONG["bantu_group"] 统一并入 east_bantu；
    # swahili_culture 的 eu5_groups 首位也是 bantu_group，不在这里挡一下会被强组层吃掉。
    "swahili_culture":      r(1, "swahili", "斯瓦希里，用户 2026-10-27 定班图语族里唯一不并入东班图的文化"),

    # ============ 亚洲按语族并入（用户 2026-10-22 定）============
    # 口径：CK3 原版地图内，按 EU5 的 eu5_language（语族）整体落，不建新文化。
    # 落点全部取自 CK3 原版 00_*.txt 已有文化，且多数是 0 省空文化。

    # —— 通古斯语族（tungusic_group）—— 
    # 用户 2026-10-27 拍板三分，**组判定优先于语言判定**（LANG_RULE 的 jurchen_language 等不再决定落点）：
    #   ① eu5_groups 含 jurchen_group          → jurchen（女真）
    #   ② 含 mongolian_group + tungusic_group  → shiwei（室韦）
    #   ③ 只有 tungusic_group                  → mohe（靺鞨）
    # 合规 jurchen 的 4 个（jurchen / haixi / hurga / udege，均 jurchen_group;tungusic_group）
    # 走 GROUP_RULE 与同名自动，不在此列。
    "evenk_culture":        r(7, "mohe", "鄂温克（只 tungusic_group，无 jurchen_group），用户定入靺鞨"),
    "oroqen_culture":       r(7, "mohe", "鄂伦春（只 tungusic_group，无 jurchen_group），用户定入靺鞨"),
    "ulch_culture":         r(7, "mohe", "乌利奇/那乃（只 tungusic_group，无 jurchen_group），用户定入靺鞨"),
    "oroch_culture":        r(7, "mohe", "鄂罗奇/乌德盖（只 tungusic_group，无 jurchen_group），用户定入靺鞨"),
    "sibe_culture":         r(6, "shiwei", "锡伯（mongolian_group + tungusic_group，无 jurchen_group），用户定入室韦"),
    # 尼夫赫是古西伯利亚孤立语，EU5 把它挂在 tungusic_group 下；不加这条会被强组层拖进靺鞨。
    "nivkh_culture":        r(1, "nivkh", "尼夫赫（古西伯利亚孤立语），EU5 误挂 tungusic_group，保持尼夫赫"),
    "sym_culture":          r(7, "mohe", "瑟姆（西西伯利亚通古斯），非女真组，用户定入靺鞨"),
    "obgints_culture":      r(7, "mohe", "奥布金茨（西西伯利亚通古斯），非女真组，用户定入靺鞨"),
    "silyagir_culture":     r(7, "mohe", "希利亚吉尔（西西伯利亚通古斯），非女真组，用户定入靺鞨"),
    "vargagaits_culture":   r(7, "mohe", "瓦尔加盖茨（西西伯利亚通古斯），非女真组，用户定入靺鞨"),
    "selogon_culture":      r(7, "mohe", "谢洛贡（西西伯利亚通古斯），非女真组，用户定入靺鞨"),
    "cemdal_culture":       r(7, "mohe", "切姆达尔（西西伯利亚通古斯），非女真组，用户定入靺鞨"),
    "nanagir_culture":      r(7, "mohe", "纳纳吉尔（东西伯利亚通古斯），非女真组，用户定入靺鞨"),
    "uchami_culture":       r(7, "mohe", "乌恰米（西西伯利亚通古斯），非女真组，用户定入靺鞨"),
    "ilimpeya_culture":     r(7, "mohe", "锡尼格尔（西西伯利亚通古斯），非女真组，用户定入靺鞨"),
    "nyurilc_culture":      r(7, "mohe", "纽里尔茨（西西伯利亚通古斯），非女真组，用户定入靺鞨"),
    "kondogir_culture":     r(7, "mohe", "孔多吉尔（西西伯利亚通古斯），非女真组，用户定入靺鞨"),

    # —— 藏缅语族（meitei_language，tibeto_burman_group）6 个 / 46 省 ——
    # CK3 lhomon 原版注释：Lhomon (Monpa; Lhoba; Kho-Bwa; Mishmi; Memba; etc.)，
    # 正是阿萨姆-藏南这条线，tani（珞巴）和 mishmi（僜）直接命中。
    # zo（佐/库基-钦）在孟加拉东部-印缅边境，那加/米基尔/梅泰同属东北印度藏缅山地，
    # CK3 无更细落点，一并入 lhomon。
    "tani_culture":         r(7, "lhomon", "珞巴，CK3 lhomon 注释直接含 Lhoba"),
    "mishmi_culture":       r(7, "lhomon", "僜，CK3 lhomon 注释直接含 Mishmi"),
    "zo_culture":           r(7, "lhomon", "佐（库基-钦），东北印度藏缅山地，随珞门"),
    "naga_culture":         r(7, "lhomon", "那加，东北印度藏缅山地，随珞门"),
    "karbi_culture":        r(7, "lhomon", "米基尔（阿萨姆山地藏缅），随珞门"),
    "meitei_culture":       r(7, "lhomon", "梅泰（曼尼普尔藏缅），随珞门"),

    # —— 突厥语族南西伯利亚（turkic_language，turkic_group）6 个 / 37 省 ——
    # CK3 uriankhai 原版注释：「these are western "Uriankhai", in this case
    # specifically the Khakas and the Tuvans」—— 原版点名要装的就是这两个。
    # 用户 2026-10-27：「突厥语族给兀良孩」—— 雅库特 / 索约特随兀良孩。
    # 哈卡斯曾一度改落 kirghiz（黠戛斯），同日又按用户指示改回 uriankhai，
    # 与 CK3 原版注释「specifically the Khakas and the Tuvans」一致。
    "khakas_culture":       r(7, "uriankhai", "哈卡斯，CK3 uriankhai 注释点名 Khakas（用户 2026-10-27 先改黠戛斯、后改回兀良孩）"),
    "tuvan_culture":        r(7, "uriankhai", "图瓦，CK3 uriankhai 注释点名 Tuvans"),
    "chelkans_culture":     r(7, "uriankhai", "切尔坎（阿尔泰北部突厥），随兀良孩"),
    "tubalar_culture":      r(7, "uriankhai", "图巴拉尔（阿尔泰北部突厥），随兀良孩"),
    "shor_culture":         r(7, "uriankhai", "绍尔（库兹涅茨克突厥），随兀良孩"),
    "kumandin_culture":     r(7, "uriankhai", "库曼丁（阿尔泰北部突厥），随兀良孩"),
    # 西伯利亚突厥（原走 LANG_RULE 的 turkic_language → NEW:turkic_steppe）
    "sakha_culture":        r(6, "uriankhai", "雅库特（突厥语族），用户 2026-10-27 定入兀良孩"),
    "soyot_culture":        r(6, "uriankhai", "索约特（突厥语族，EU5 里 0 地块），用户 2026-10-27 定入兀良孩"),

    # —— 高加索诸语族（caucasian_group）11 个 / 51 省 ——
    # CK3 的 heritage_caucasian 只有 georgian / armenian 两个文化，缺西北与东北高加索。
    # 用户拍板：西北（切尔克斯/阿布哈兹/阿巴扎）+ 东北（达吉斯坦五族）都落 alan（阿兰），
    # 按地理贴北高加索；卡特维尔语系（拉兹/斯万/明格列尔）落 georgian。
    "circassian_culture":   r(7, "alan", "切尔克斯（西北高加索），CK3 无对应文化，用户定入阿兰"),
    "abkhazian_culture":    r(7, "alan", "阿布哈兹（西北高加索），用户定入阿兰"),
    "abazin_culture":       r(7, "alan", "阿巴扎（西北高加索），用户定入阿兰"),
    "lezgin_culture":       r(7, "alan", "列兹金（达吉斯坦），CK3 无对应文化，用户定入阿兰"),
    "nakh_culture":         r(7, "alan", "纳赫（车臣-印古什，东北高加索），用户定入阿兰"),
    "avar_culture":         r(7, "alan", "高加索阿瓦尔（达吉斯坦），与 CK3 潘诺尼亚阿瓦尔同名异族，用户定入阿兰"),
    "dargin_culture":       r(7, "alan", "达尔金（达吉斯坦），用户定入阿兰"),
    "lak_culture":          r(7, "alan", "拉克（达吉斯坦），用户定入阿兰"),
    "laz_culture":          r(7, "georgian", "拉兹（卡特维尔语系，格鲁吉亚西南），入格鲁吉亚"),
    "svan_culture":         r(7, "georgian", "斯万（卡特维尔语系），入格鲁吉亚"),
    "mingrelian_culture":   r(7, "georgian", "明格列尔（卡特维尔语系），入格鲁吉亚"),

    # ============ 大洋洲 / 台湾（用户 2026-10-27 拍板「先 A」）============
    # 口径：CU 地图范围内 target=NEW: 的文化，优先并入 CK3 原版已有文化，不建新文化。
    # 只对下面点名的 9 个文化生效；papuan_group 还有 ~180 个同类文化在 CU 图外，
    # **不动 GROUP_RULE 的 papuan_group**，避免顺带把图外的也改掉。
    #   * 新几内亚 8 个 → CK3 `papuan`（00_malayic.txt:364，原版注释
    #     "Represents the wide array of different groups that populate New Guinea
    #      and its surroundings"，本就是新几内亚总代表）
    #   * 台湾 formosan → CK3 `amis`（00_malayic.txt:396，原版注释 "indigenous Taiwanese"）
    "bife_culture":         r(7, "papuan", "比费（新几内亚），并入 CK3 原版 papuan（新几内亚总代表）"),
    "buruwai_culture":      r(7, "papuan", "布鲁瓦伊（新几内亚），并入 CK3 原版 papuan"),
    "iwur_culture":         r(7, "papuan", "伊乌尔（新几内亚），并入 CK3 原版 papuan"),
    "kamoro_culture":       r(7, "papuan", "卡莫罗（新几内亚），并入 CK3 原版 papuan"),
    "kimaama_culture":      r(7, "papuan", "基马马（新几内亚），并入 CK3 原版 papuan"),
    "marind_culture":       r(7, "papuan", "马林德（新几内亚），并入 CK3 原版 papuan"),
    "moi_culture":          r(7, "papuan", "莫伊（新几内亚鸟头），并入 CK3 原版 papuan"),
    "wamesa_culture":       r(7, "papuan", "瓦梅萨（亚彭湾），并入 CK3 原版 papuan"),
    "formosan_culture":     r(7, "amis", "台湾原住民，并入 CK3 原版 amis（阿美，注释 indigenous Taiwanese）"),

    # 小巽他群岛东端（alor / makasae / bunak / fataluku）原先单独点名落 maluku，
    # 用户 2026-10-27 改为「所有 papuan_group 一律入 papuan」，已删除这 4 条，
    # 统一由 GROUP_RULE_STRONG["papuan_group"] 处理。

    # —— 傣语：shan_dialect（傣隆/傣仂/傣那）整体已在 LANG_RULE 落 tai ——
    # 用户 2026-10-27 定「不建新文化」，原先 tai_lu / tai_nua 的 NEW:shan 作废。
}

# 名字与 CK3 撞车但不是同一人群的，禁止走「自动同名」
SAME_NAME_DIFF = {"yao", "avar", "prussian", "khorezmian", "turkmen"}

# ============ 显示名同名但 key 不同 ============
# CK3 有 16 个文化的本地化显示名和 key 对不上（例：turkish 显示「乌古斯」、
# assyrian 显示「Syriac」、samoyed 显示「Bjarmian」）。判「同名」要按显示名来。
DISPLAY_ALIAS = {
    "bjarmian":     "samoyed",     # CK3 samoyed 显示 Bjarmian
    "guanche":      "guanches",    # CK3 guanches 显示 Guanche
    "syriac":       "assyrian",    # CK3 assyrian 显示 Syriac
    "kannauji":     "hindustani",  # CK3 hindustani 显示 Kannauji
    "kochini":      "kochinim",    # CK3 kochinim 显示 Kochini
}

# ============ 与 CK3 融合文化名（creation_names/00_names_hybrid.txt）同名的，归 cat8 ============
# 名单取自 CK3 原版，key 去掉 _hybrid 后缀后与我们的文化 key 对应
HYBRID_NAMES = {
    "azeri":            "azeri_hybrid",        # 突厥 + 伊朗
    "romansh":          "romansh_hybrid",      # 罗曼 + 阿勒曼尼
    "transylvanian":    "transylvanian",       # 弗拉赫 + 匈牙利/德意志
    "angevin":          "angevin_hybrid",      # 法兰西 + 英格兰
    "moroccan":         "moroccan_hybrid",     # 马格里布 + 安达卢西
    "algerian":         "algerian_hybrid",
    "tunisian":         "tunisian_hybrid",
    "gyalrong":         "gyalrong",            # 羌 + 藏
    "arpitan":          "arpitan_hybrid",      # 法兰西 + 奥克
    "aromanian":        "aromanian",           # 弗拉赫 + 希腊
    "dalmatian":        "dalmatian_hybrid",    # 罗曼 + 南斯拉夫
    "neapolitan":       "neapolitan_hybrid",   # 意大利 + 诺曼/希腊
    "gallo":            "gallo",               # 奥依 + 布列塔尼
    "griko":            "griko_hybrid",        # 希腊 + 意大利
    "norse_gael":       "norse_gael",          # 诺斯 + 盖尔
    "anglo_irish":      "anglo_irish",         # 英格兰 + 爱尔兰（CK3 融合名表无，mod 自加）
    "turkish":          "anatolian_turkish",   # 突厥蛮 + 希腊
}

# ============ 按中文显示名判同名 ============
# 11 类标准里的「同名」指显示名，不是 key。CK3 的 key 常和显示名对不上
# （turkish=乌古斯、bodpa=吐蕃、assyrian=Syriac…），我们的 key 也常是 EU5 拼法
# （torajan_culture vs CK3 toraja、mi_niah_culture vs CK3 tangut）。
# 这些只有比中文名才能发现。
ZH_NAME_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_eu5_culture_zh.csv")

# 中文名撞车但指的是两码事，禁止走「显示名同名」
ZH_HOMOGRAPH = {
    "yue_wu_culture": "「越」在中文里既指越南（CK3 viet）也指江浙（本文化是吴语），不是同一人群",
}

# ============ CK3 原版地图覆盖的王国（用于 9 类 / 10·11 类的分界）============
# 覆盖 = CK3 原版有实际地块，可以在原版文化上做分离
COVERED_KINGDOMS = set("""
anatolia arabia balkan baltic bengal carpathia caucasus central_india crescent deccan
egypt ethiopia france great_britain guinea hindustan iberia indochina ireland italy
khorasan macaronesia maghreb manchuria mongolia north_atlantic_islands north_german
nubia persia russian ruthenia sahel scandinavian somalia south_german steppes
swahili_coast tibet ural west_siberia western_india xinjiang
""".split())

# 图外：CK3 原版无地块
OFFMAP_KINGDOMS = set("""
alaska andes aridoamerica australia brazil canada caribbean central_africa
central_america chaco colombia east_china east_coast east_siberia great_lakes
great_plains indonesia japan kongo korea la_plata madagascar melanesia mesoamerica
micronesia new_zealand north_atlantic_ocean north_china polynesia south_atlantic
south_china southern_africa west_china west_coast zimbabwe
""".split())

# ============ 语言级规则（EU5 language -> 目标）============
LANG_RULE = {
    # —— 不列颠 ——
    "english_dialect":          r(4, "english", "英语方言并入英格兰"),
    "northumbrian_dialect":     r(5, "english", "诺森布里亚方言→英语"),
    "scots_dialect":            r(2, "scottish", "Scots=苏格兰人"),
    "scottish_gaelic_dialect":  r(2, "gaelic", "苏格兰盖尔=盖尔"),
    "welsh_dialect":            r(1, "welsh", "同名"),
    "cornish_dialect":          r(1, "cornish", "同名"),
    "breton_dialect":           r(1, "breton", "同名"),
    "irish_dialect":            r(1, "irish", "同名"),
    "manx_dialect":             r(4, "gaelic", "马恩岛属盖尔语支"),
    "hiberno_english_dialect":  r(8, "anglo_irish", "英爱融合"),
    # —— 日耳曼 ——
    "low_german_dialect":       r(5, "saxon", "低地德语→萨克森"),
    "central_german_dialect":   r(5, "franconian", "中德方言→法兰克尼亚"),
    "upper_german_dialect":     r(5, "bavarian", "上德方言→巴伐利亚"),
    "alemannic_dialect":        r(5, "swabian", "阿勒曼尼→施瓦本"),
    # EU5 的 francique 是奥依语支（francien，含香槟/洛林/皮卡第/瓦隆），
    # 不是日耳曼的法兰克尼亚。语言柱被错挂成 language_high_german
    # （见 _eu5_language_to_ck3.py 第 92 行），此处按实际语支落 french。
    "francique_dialect":        r(5, "french", "法兰克方言实为奥依语支→法兰西（语言柱误挂 high_german）"),
    "dutch_dialect":            r(1, "dutch", "荷兰语"),
    "frisian_language":         r(1, "frisian", "弗里斯兰语"),
    "yiddish_dialect":          r(2, "ashkenazi", "意第绪=阿什肯纳兹"),
    "czech_dialect":            r(1, "czech", "捷克语"),
    "sorbian_dialect":          r(7, "polabian", "索布按地理入波拉布"),
    "polabian_dialect":         r(1, "polabian", "波拉布语"),
    "silesian_dialect":         r(5, "polish", "西里西亚方言属莱赫语支"),
    "icelandic_dialect":        r(4, "norwegian", "冰岛语并入挪威"),
    "swedish_dialect":          r(1, "swedish", "瑞典语"),
    "danish_dialect":           r(1, "danish", "丹麦语"),
    "norwegian_dialect":        r(1, "norwegian", "挪威语"),
    "gutnish_dialect":          r(4, "swedish", "哥特兰语"),
    # —— 罗曼 ——
    "french_language":          r(1, "french", "法语"),
    "angevin_dialect":          r(4, "french", "安茹方言→法语"),
    "poitevin_dialect":         r(4, "french", "普瓦图方言→法语"),
    "burgundian_dialect":       r(4, "french", "勃艮第方言→法语"),
    "norman_dialect":           r(1, "norman", "诺曼语"),
    "occitan_dialect":          r(4, "occitan", "奥克语→奥克"),
    "gascon_dialect":           r(4, "occitan", "加斯科涅语属奥克语"),
    "arpitan_dialect":          r(4, "french", "阿尔皮坦语 EU5 归法语支，入法兰西"),
    "castilian_dialect":        r(1, "castilian", "卡斯蒂利亚"),
    "catalan_dialect":          r(1, "catalan", "加泰罗尼亚"),
    "aragonese_dialect":        r(1, "aragonese", "阿拉贡"),
    "galician_dialect":         r(1, "galician", "加利西亚"),
    "leonese_dialect":          r(2, "asturleonese", "莱昂=阿斯图里亚斯-莱昂"),
    "portuguese_dialect":       r(1, "portuguese", "葡萄牙"),
    "ladino_dialect":           r(2, "sephardi", "拉迪诺=塞法迪"),
    "basque_language":          r(1, "basque", "巴斯克"),
    "maghrebi_dialect":         r(1, "maghrebi", "马格里布阿拉伯语"),
    "peninsular_dialect":       r(4, "bedouin", "半岛阿拉伯语→贝都因"),
    "tuscan_dialect":           r(4, "italian", "托斯卡纳=意大利"),
    "roman_dialect":            r(1, "roman", "罗马"),
    "sicilian_dialect":         r(1, "sicilian", "西西里"),
    "neapolitan_dialect":       r(7, "sicilian", "那不勒斯按地理入西西里"),
    "lombard_dialect":          r(7, "cisalpine", "伦巴第语属高卢-意大利语支→山南"),
    "ligurian_dialect":         r(7, "cisalpine", "利古里亚→内高卢"),
    "piedmontese_dialect":      r(7, "cisalpine", "皮埃蒙特→内高卢"),
    "emilian_dialect":          r(7, "cisalpine", "艾米利亚→内高卢"),
    "romagnol_dialect":         r(7, "cisalpine", "罗马涅→内高卢"),
    "venetian_dialect":         r(7, "cisalpine", "威尼托→内高卢"),
    "marchigiano_dialect":      r(7, "cisalpine", "马尔凯→内高卢"),
    "median_dialect":           r(4, "italian", "中意大利方言"),
    "dalmatian_dialect":        r(7, "croatian", "达尔马提亚按地理入克罗地亚"),
    "rhaetian_dialect":         r(7, "cisalpine", "雷蒂亚语→内高卢"),
    "maltese_dialect":          r(7, "sicilian", "马耳他语按用户定入西西里"),
    "istriot_dialect":          r(7, "cisalpine", "伊斯特里亚→内高卢"),
    "sardinian_dialect":        r(1, "sardinian", "撒丁"),
    # —— 希腊 ——
    "greek_language":           r(1, "greek", "希腊语"),
    "gothic_language":          r(1, "gothic", "克里米亚哥特"),
    "ancient_greek":            r(1, "macedonian", "古希腊语"),
    # —— 斯拉夫 ——
    "russian_dialect":          r(1, "russian", "俄语"),
    "novgorodian_dialect":      r(2, "russian", "诺夫哥罗德方言=罗斯（ilmenian 原版 0 省份，不可作落点）"),
    "ukrainian_dialect":        r(7, "russian", "乌克兰方言，CK3 原版东斯拉夫一律 russian（volhynian 原版 0 省份）"),
    "belarusian_dialect":       r(7, "russian", "白俄罗斯方言，CK3 原版东斯拉夫一律 russian（severian 原版 0 省份）"),
    "polish_dialect":           r(1, "polish", "波兰语"),
    "kashubian_dialect":        r(2, "pommeranian", "卡舒比=波美拉尼亚"),
    "slovak_dialect":           r(2, "slovien", "斯洛伐克=slovien"),
    "serbian_dialect":          r(1, "serbian", "塞尔维亚语"),
    "croatian_dialect":         r(1, "croatian", "克罗地亚语"),
    "bulgarian_language":       r(1, "bulgarian", "保加利亚语"),
    "slovene_dialect":          r(2, "carantanian", "斯洛文尼亚=卡兰塔尼亚"),
    # —— 波罗的 / 芬兰 ——
    "lithuanian_dialect":       r(1, "lithuanian", "立陶宛语"),
    "latvian_dialect":          r(2, "latgalian", "拉脱维亚=拉特加尔"),
    "western_baltic_dialect":   r(2, "prussian", "西波罗的=普鲁士"),
    "estonian_dialect":         r(1, "estonian", "爱沙尼亚语"),
    "finnish_dialect":          r(1, "finnish", "芬兰语"),
    "karelian_language":        r(1, "karelian", "卡累利阿语"),
    "vepsian_language":         r(1, "vepsian", "维普森语"),
    "permic_language":          r(2, "komi", "彼尔姆语支→科米"),
    "mordvinic_language":       r(1, "mordvin", "莫尔多瓦语"),
    "mari_language":            r(1, "mari", "马里语"),
    "khanty_language":          r(1, "khanty", "汉特语"),
    "samoyed_language":         r(1, "samoyed", "萨莫耶德语"),
    "nenets_language":          r(1, "samoyed", "涅涅茨属萨莫耶德"),
    # —— 阿拉伯 / 柏柏尔 ——
    "egyptian_dialect":         r(1, "egyptian", "埃及阿拉伯语"),
    "levantine_dialect":        r(1, "levantine", "黎凡特阿拉伯语"),
    "iraqi_dialect":            r(4, "levantine", "伊拉克阿拉伯语并入黎凡特"),
    "south_arabic_language":    r(4, "yemeni", "南阿拉伯语→也门"),
    "aramaic_language":         r(4, "assyrian", "阿拉米语→亚述"),
    "tamazight_language":       r(6, "butr", "柏柏尔语（兜底 butr；具体文化见 CULT_RULE 按地理分流）"),
    "coptic_language":          r(2, "ancient_egyptian", "科普特语=古埃及语最后阶段（用户 2026-10-27 定入古埃及）"),
    # —— 伊朗 ——
    "persian_language":         r(1, "persian", "波斯语"),
    "kurdish_language":         r(1, "kurdish", "库尔德语"),
    "balochi_language":         r(1, "baloch", "俾路支语"),
    "afghani_language":         r(1, "afghan", "阿富汗语"),
    "tajik_language":           r(1, "tajik", "塔吉克语"),
    "adharic_language":         r(6, "persian", "阿扎里/塔利什/扎扎在 EU5 均归 adharic_language 且 eu5_groups=iranian_group（波斯组），用户 2026-10-27 定按波斯组落 persian"),
    "tabaristani_language":     r(4, "daylamite", "塔巴里斯坦→德莱木"),
    "sogdian_language":         r(1, "sogdian", "粟特语"),
    "khwarezmian_language":     r(3, "karluk", "花剌子模语为葛逻禄语"),
    "saka_language":            r(1, "saka", "塞语"),
    "alan_language":            r(1, "alan", "阿兰语"),
    "daylamite_language":       r(1, "daylamite", "德莱木语"),
    # —— 突厥 / 蒙古 ——
    "kipchak_language":         r(4, "kipchak", "钦察语→钦察（库曼只留给 cuman_culture，草原组另走 kazakh 融合）"),
    "turkmen_dialect":          r(2, "turkmen", "突厥蛮=土库曼"),
    "oghhuric_language":        r(6, "bolghar", "乌古尔语支→保加尔"),
    "oguric_language":          r(6, "bolghar", "乌古尔语支→保加尔"),
    "azeri_dialect":            r(4, "turkish", "阿塞拜疆语"),
    "karluk_language":          r(1, "karluk", "葛逻禄语"),
    "turkish_dialect":          r(8, "anatolian_turkish", "安纳托利亚突厥融合"),
    "mongolian_language":       r(1, "mongol", "蒙古语"),
    "jurchen_language":         r(1, "jurchen", "女真语（仅 jurchen_group 成员；sibe 已在 CULT_RULE 分流到 shiwei）"),
    "evenk_language":           r(9, "evenk", "鄂温克诸部，CK3 无对应，从靺鞨/女真分离"),
    "nanai_language":           r(6, "jurchen", "那乃语（仅 jurchen_group 成员；ulch 已在 CULT_RULE 分流到 mohe）"),
    "udege_language":           r(6, "jurchen", "乌德盖语（仅 jurchen_group 成员；oroch 已在 CULT_RULE 分流到 mohe）"),
    "nivkh_language":           r(1, "nivkh", "尼夫赫语"),
    # —— 侗台（台语支 / 侗水语支 / 仡央语支）——
    # 用户 2026-10-27 定：**不建新文化**。台语支一律入 CK3 tai（傣）；
    # 侗水语支（侗/毛南/仫佬/水）与仡央语支（仡佬/波）一律入 CK3 bouxcuengh（布僮，
    # 原版 00_tai.txt:47，中文「布僮」）。原先 tai_lu / tai_nua 挂 NEW:shan 已作废。
    "shan_dialect":             r(4, "tai", "掸语支（傣隆/傣仂/傣那）→ CK3 tai（傣），不建 shan 新文化"),
    "kam_language":             r(6, "bouxcuengh", "侗水语支（侗/毛南/仫佬/水）→ CK3 bouxcuengh（布僮）"),
    "kra_language":             r(6, "bouxcuengh", "仡央语支（仡佬/波）→ CK3 bouxcuengh（布僮）"),
    # —— 藏缅 / 汉 ——
    "tibetan_language":         r(2, "bodpa", "藏=bodpa"),
    "yi_language":              r(1, "yi", "彝语"),
    "bai_language":             r(1, "bai", "白语"),
    "brahmaputran_language":    r(7, "kachin", "布拉马普特拉诸语按地理入景颇"),
    "meitei_language":          r(9, "meitei", "曼尼普尔，CK3 无对应"),
    "qiangic_language":         r(1, "qiang", "羌语支"),
    "burmese_language":         r(1, "burmese", "缅语"),
    "kachinic_language":        r(1, "kachin", "景颇语"),
    "karenic_language":         r(1, "karen", "克伦语"),
    "tujia_language":           r(1, "tujia", "土家语"),
    "northern_mandarin_dialect": r(5, "han", "北方官话→汉"),
    "southern_mandarin_dialect": r(5, "han", "南方官话→汉"),
    "jin_language":             r(4, "han", "晋语→汉"),
    "shu_language":             r(4, "han", "蜀语→汉"),
    "gan_language":             r(4, "han", "赣语→汉"),
    "xiang_language":           r(4, "han", "湘语→汉"),
    "wu_language":              r(4, "han", "吴语→汉"),
    "min_language":             r(4, "han", "闽语→汉"),
    "yue_language":             r(4, "han", "粤语→汉"),
    "kejia_language":           r(4, "han", "客家语→汉"),
    "huizhou_language":         r(4, "han", "徽语→汉"),
    "ping_language":            r(4, "han", "平话→汉"),
    "korean_language":          r(2, "goryeo", "朝鲜=高丽"),
    "japanese_language":        r(1, "japanese", "日语"),
    "ainu_language":            r(1, "ainu", "阿伊努语"),
    # —— 印度 ——
    "hindustani_language":      r(1, "hindustani", "印度斯坦语"),
    "rajasthani_language":      r(1, "rajput", "拉贾斯坦=拉杰普特"),
    "malvi_language":           r(1, "malvi", "马尔瓦语"),
    "bihari_language":          r(4, "hindustani", "比哈尔语并入印度斯坦"),
    "bengali_language":         r(1, "bengali", "孟加拉语"),
    "oriya_language":           r(1, "oriya", "奥里亚语"),
    "assamese_language":        r(1, "assamese", "阿萨姆语"),
    "gujarati_language":        r(1, "gujarati", "古吉拉特语"),
    "punjabi_language":         r(1, "punjabi", "旁遮普语"),
    "sindhi_language":          r(1, "sindhi", "信德语"),
    "marathi_language":         r(1, "marathi", "马拉地语"),
    "kashmiri_language":        r(1, "kashmiri", "克什米尔语"),
    "sinhala_language":         r(1, "sinhala", "僧伽罗语"),
    "nepali_language":          r(1, "nepali", "尼泊尔语"),
    "pahari_language":          r(4, "nepali", "帕哈里语并入尼泊尔"),
    "brahui_language":          r(1, "brahui", "布拉灰语"),
    "tamil_language":           r(1, "tamil", "泰米尔语"),
    "telugu_language":          r(1, "telugu", "泰卢固语"),
    "kannada_language":         r(1, "kannada", "卡纳达语"),
    "malayalam_language":       r(4, "tamil", "马拉雅拉姆语并入泰米尔"),
    "north_dravidian_language": r(4, "brahui", "北达罗毗荼→布拉灰"),
    "gondi_language":           r(4, "gond", "贡德语"),
    "munda_language":           r(7, "gond", "蒙达诸语按地理入贡德"),
    "khasi_language":           r(7, "gond", "卡西语按地理入贡德"),
    # —— 东南亚 ——
    "vietnamese_language":      r(1, "viet", "越语"),
    "khmer_language":           r(1, "khmer", "高棉语"),
    "mon_language":             r(1, "mon", "孟语"),
    "khmu_language":            r(1, "khmu", "克木语"),
    "palaungic_language":       r(4, "khmu", "佤德昂语支并入克木"),
    "bahnaric_language":        r(4, "khmer", "巴拿语支并入高棉"),
    "katuic_language":          r(4, "khmer", "卡都语支并入高棉"),
    "aslian_language":          r(1, "senoi", "塞诺伊语"),
    "nicobarese_language":      r(4, "nakkavaram", "尼科巴语，与安达曼同处理入那旺（用户 2026-10-27 定）"),
    "hmong_language":           r(1, "hmong", "苗语"),
    "yao_language":             r(1, "yao", "瑶语"),
    "thai_dialect":             r(4, "tai", "泰语诸文化并入傣"),
    "lao_dialect":              r(4, "tai", "老挝语并入傣"),
    "dai_dialect":              r(4, "tai", "傣语并入傣"),
    # 下面三条曾在这里重复定义（shan_dialect→shan / kam_language→tai / kra_language→hlai），
    # Python 字典后写覆盖前写，把上面第 621-623 行用户 2026-10-27 的侗台三分口径整段吃掉。
    # 2026-10-27 已删除，落点以第 621-623 行为准：shan_dialect→tai、kam/kra→bouxcuengh。
    "zhuang_language":          r(1, "bouxcuengh", "壮语=布僮"),
    "hlai_language":            r(1, "hlai", "黎语"),
    # —— 非洲 ——
    "swahili_language":         r(1, "swahili", "斯瓦希里"),
    "somali_dialect":           r(1, "somali", "索马里"),
    "afar_dialect":             r(1, "afar", "阿法尔"),
    "oromo_dialect":            r(9, "oromo", "奥罗莫，CK3 无对应"),
    "agaw_language":            r(4, "ethiopian", "阿高语并入埃塞俄比亚"),
    "ethiopic_language":        r(2, "ethiopian", "埃塞俄比亚"),
    "north_ethiopic_language":  r(2, "ethiopian", "北埃塞俄比亚"),
    "nubian_language":          r(1, "nubian", "努比亚"),
    "beja_language":            r(1, "beja", "贝贾"),
    "daju_language":            r(1, "daju", "达朱"),
    "dinka_language":           r(9, "dinka", "丁卡，CK3 无对应"),
    "luo_language":             r(9, "luo", "卢奥，CK3 无对应"),
    "kalenjin_language":        r(9, "kalenjin", "卡伦金，CK3 无对应"),
    "lotuko_language":          r(9, "lotuko", "洛图科，CK3 无对应"),
    "hausa_language":           r(1, "hausa", "豪萨"),
    "kanuri_language":          r(1, "kanuri", "卡努里"),
    "nupe_language":            r(1, "nupe", "努佩"),
    "sao_language":             r(1, "sao", "萨奥"),
    "yoruba_language":          r(1, "yoruba", "约鲁巴"),
    "edo_language":             r(1, "edo", "埃多"),
    "igbo_language":            r(1, "igbo", "伊博"),
    "ewe_language":             r(1, "ewe", "埃维"),
    "akan_language":            r(1, "akan", "阿肯"),
    "guan_language":            r(1, "guan", "瓜恩"),
    "kru_language":             r(1, "kru", "克鲁"),
    "mande_language":           r(4, "malinke", "曼德语并入马林凯"),
    "gur_language":             r(1, "gur", "古尔"),
    "dogon_language":           r(9, "dogon", "多贡，CK3 无对应"),
    "senegambian_language":     r(4, "wolof", "塞内冈比亚语并入沃洛夫"),
    "mel_language":             r(1, "mel", "梅尔"),
    "soninke_language":         r(1, "soninke", "索宁克"),
    "bozo_language":            r(1, "bozo", "博佐"),
    "mossi_language":           r(1, "mossi", "莫西"),
    "songhai_language":         r(1, "songhai", "桑海"),
    "sorko_language":           r(1, "sorko", "索尔科"),
    "gaw_language":             r(1, "gaw", "加奥"),
    # 撒哈拉语族（用户 2026-10-27 定）：一律并入 CK3 原版 zaghawa（扎加瓦）；
    # 唯一例外加奈姆布（Kanembu，卡努里语方言）在 CULT_RULE 里显式保留 kanuri。
    "saharan_language":         r(4, "zaghawa", "撒哈拉语族并入扎加瓦，加奈姆布例外保留卡努里（用户 2026-10-27 定）"),
    "tubu_language":            r(1, "zaghawa", "图布=扎加瓦"),
    "adamawa_language":         r(9, "adamawa", "阿达马瓦，CK3 无对应"),
    "ubangian_language":        r(9, "ubangi", "乌班吉，CK3 无对应"),
    "bassa_language":           r(9, "bassa", "巴萨，CK3 无对应"),
    "baguirmi_language":        r(9, "bagirmi", "巴吉尔米，CK3 无对应"),
    "moru_madi_language":       r(9, "moru_madi", "莫鲁-马迪，CK3 无对应"),
    "bua_language":             r(9, "bua", "布阿，CK3 无对应"),
    "kordofan_language":        r(9, "kordofan", "科尔多凡，CK3 无对应"),
    "ijaw_language":            r(9, "ijaw", "伊乔，CK3 无对应"),
    # —— 南洋群岛（CK3 有 15 个南岛文化）——
    "ilocano_language":         r(7, "iloko", "伊洛卡诺按地理入伊洛科"),
    "tagalog_language":         r(1, "tagalog", "他加禄"),
    "cebuano_dialect":          r(4, "bisayan", "宿务语并入米沙鄢"),
    "hiligaynon_dialect":       r(4, "bisayan", "希利盖农并入米沙鄢"),
    "southern_visayan_dialect": r(4, "bisayan", "南米沙鄢语"),
    "danao_dialect":            r(7, "bisayan", "达瑙语按地理入米沙鄢"),
    "manobo_dialect":           r(7, "bisayan", "马诺博语按地理入米沙鄢"),
    "subanon_dialect":          r(7, "bisayan", "苏巴农语按地理入米沙鄢"),
    "bikol_language":           r(7, "bisayan", "比科尔语按地理入米沙鄢"),
    "palawanic_dialect":        r(7, "tagalog", "巴拉望语按地理入他加禄"),
    "kapampangan_language":     r(7, "tagalog", "邦板牙语按地理入他加禄"),
    "malay_dialect":            r(1, "malay", "马来语"),
    "banjarese_dialect":        r(7, "malay", "班贾尔语按地理入马来"),
    "kutai_dialect":            r(7, "malay", "库台语按地理入马来"),
    "lampung_language":         r(7, "malay", "楠榜语按地理入马来"),
    "minangkabau_dialect":      r(7, "malay", "米南加保语按地理入马来"),
    "rejang_language":          r(7, "malay", "雷让语按地理入马来"),
    "batak_language":           r(7, "malay", "巴塔克语按地理入马来"),
    "javanese_language":        r(1, "javanese", "爪哇语"),
    "balinese_language":        r(7, "javanese", "巴厘语按地理入爪哇"),
    "madurese_language":        r(7, "javanese", "马都拉语按地理入爪哇"),
    "buginese_language":        r(2, "bugis", "布吉语=布吉斯"),
    "celebic_language":         r(7, "toraja", "西里伯斯语按地理入托拉查"),
    "gorontalo_language":       r(7, "toraja", "哥伦打洛语按地理入托拉查"),
    "sumba_language":           r(7, "toraja", "松巴语按地理入托拉查"),
    "bornean_language":         r(7, "dayak", "婆罗洲语按地理入达雅"),
    "barito_language":          r(7, "dayak", "巴里托语按地理入达雅"),
    "kayanic_language":         r(7, "dayak", "卡扬语按地理入达雅"),
    "iban_dialect":             r(7, "dayak", "伊班语按地理入达雅"),
    "dayak_language":           r(1, "dayak", "达雅"),
    "maluku_language":          r(1, "maluku", "马鲁古"),
    "ternate_language":         r(7, "maluku", "特尔纳特语按地理入马鲁古"),
    "halmaheran_language":      r(7, "maluku", "哈马黑拉语按地理入马鲁古"),
    "timoric_language":         r(7, "maluku", "帝汶语按地理入马鲁古"),
    "tanimbar_language":        r(7, "maluku", "塔宁巴尔语按地理入马鲁古"),
    "aru_language":             r(7, "maluku", "阿鲁语按地理入马鲁古"),
    "sama_language":            r(7, "maluku", "萨马语按地理入马鲁古"),
    "cham_dialect":             r(1, "cham", "占语"),
    "achenese_dialect":         r(1, "acehnese", "亚齐"),
    "formosan_language":        r(7, "amis", "台湾南岛语 → CK3 原版 amis（阿美，注释 indigenous Taiwanese），用户 2026-10-27 定不建新文化"),
    # —— 零散 ——
    "bhili_language":           r(7, "rajput", "比尔语按地理入拉杰普特"),
    "bantoid_language":         r(10, "bantoid", "类班图，参考东班图传统"),
    "chukotko_kamchatkan_language": r(4, "nivkh", "楚科奇-堪察加（古西伯利亚孤立语系），用户 2026-10-27 定入尼夫赫"),
    "yukaghir_language":        r(4, "nivkh", "尤卡吉尔（古西伯利亚孤立语系），用户 2026-10-27 定入尼夫赫"),
    "andamanese_language":      r(11, "andamanese", "安达曼，CK3 无对应"),
    # —— 补漏（第一轮未判定）——
    "turkic_language":          r(10, "turkic_steppe", "西伯利亚突厥诸部，参考 CK 突厥传统"),
    "highland_cushitic_dialect": r(9, "highland_cushitic", "高地库希特诸族，CK3 无对应"),
    "dahalo_dialect":           r(9, "dahalo", "达哈洛，CK3 无对应"),
    "daasanach_dialect":        r(4, "somali", "达萨纳克属索马里语支"),
    "rendille_dialect":         r(4, "somali", "伦迪尔属索马里语支"),
    "south_cushitic_language":  r(9, "iraqw", "南库希特诸族，CK3 无对应"),
    "chibchan_language":        r(11, "chibchan", "美洲"),
    "iroquoian_language":       r(11, "iroquoian", "美洲"),
    "lamut_language":           r(4, "mohe", "埃文/拉穆特（通古斯语族），用户 2026-10-27 定入靺鞨"),
    "nigerian_language":        r(4, "nupe", "尼日尔诸语并入努佩"),
    "kwa_language":             r(4, "ewe", "夸语支并入埃维"),
    "alanic_language":          r(1, "alan", "阿兰"),
    "kamarupi_language":        r(7, "assamese", "迦摩缕波按地理入阿萨姆"),
    "yeniseian_language":       r(11, "ket", "叶尼塞语，CK3 无对应"),
    "ugrian_language":          r(4, "khanty", "乌戈尔语并入汉特"),
    "ryukyu_language":          r(1, "ryukyuan", "琉球"),
    "hebrew_language":          r(1, "hebrew", "希伯来"),
    "senufo_language":          r(9, "senufo", "塞努福，CK3 无对应"),
    "sundanese_language":       r(7, "javanese", "巽他语按地理入爪哇"),
    "waray_dialect":            r(4, "bisayan", "瓦莱语并入米沙鄢"),
    "yupik_language":           r(11, "yupik", "北极圈，CK3 无对应"),
    "movima_language":          r(11, "movima", "美洲"),
    "henia_kamiare_language":   r(11, "henia_kamiare", "美洲"),
    "atacame_language":         r(11, "atacame", "美洲"),
    "malibu_language":          r(11, "malibu", "美洲"),
    "napuruna_language":        r(11, "napuruna", "美洲"),
    "pume_language":            r(11, "pume", "美洲"),
    "warao_language":           r(11, "warao", "美洲"),
    "xinka_language":           r(11, "xinka", "美洲"),
}

# ============ 强文化组规则（优先于 LANG_RULE）============
# 用户 2026-10-27 定：加一层「强组」。
# 背景：GROUP_RULE 主体是占位表（157 条里绝大多数 r(10,"") / r(11,"") = 图外不表态），
#       所以整体把 GROUP_RULE 提到 LANG_RULE 之前会误伤 —— 实测 34 个文化改判，其中 17 个是坏的
#       （9 个犹太人全压成 radhanite、4 个 swahili_language 退化成 NEW:swahili、
#        khas/tharu 压成 bodpa、maden 退化 NEW:halmaheran、nivkh 被拖进靺鞨）。
# 做法：只有这里列出的组才「表态」，在 LANG_RULE 之前查；其余组仍走原顺序。
# 判据优先级变为：CULT_RULE > GROUP_RULE_STRONG > LANG_RULE > GROUP_RULE > 自动
GROUP_RULE_STRONG = {
    # 单通古斯组（无 jurchen_group / mongolian_group）→ 靺鞨
    "tungusic_group":     r(7, "mohe", "只属通古斯组（无 jurchen_group / mongolian_group）→ 靺鞨"),
    # 尼罗-撒哈拉诸族 → 达朱
    "nilosahelian_group": r(6, "daju", "尼罗-撒哈拉诸族并入达朱（用户 2026-10-27 定）"),
    # 班图语族 → CK3 原版 east_bantu（东班图），本地化改称「班图」
    # 用户 2026-10-27：除斯瓦希里外全部并入；swahili_culture 已在 CULT_RULE 保住 swahili。
    "bantu_group":        r(6, "east_bantu", "班图语族（除斯瓦希里）并入 CK3 原版 east_bantu（东班图），用户 2026-10-27 定"),
    # 科伊桑 / 马尔加什：CK3 原版没有这两个文化，用户 2026-10-27 要求各自新建一个。
    # 文化定义手写在 common/culture/cultures/zz_eu5_culture_new.txt，
    # heritage/language 复用 00_generated_pillars.txt 里的 khoisan_group / malagasy_group 及其 eu5_heritage_*。
    # 两组的 eu5_groups 都是单组，首位即本组，强组层可直接决断。
    "khoisan_group":      r(6, "khoisan", "科伊桑文化组 19 个部族并入新建的 khoisan，用户 2026-10-27 定"),
    "malagasy_group":     r(6, "malagasy", "马尔加什文化组 19 个部族并入新建的 malagasy，用户 2026-10-27 定"),
    # 巴布亚文化组：139 个成员全部并入 CK3 原版 papuan（00_malayic.txt:364）。
    # 用户 2026-10-27「姆巴哈姆和所有巴布亚文化组的都改成巴布亚文化」。
    # 此前 CULT_RULE 里 alor/makasae/bunak/fataluku 单独落 maluku 的 4 条已删除，
    # 让它们回到组规则统一处理（maden 本来走 LANG_RULE 的 halmaheran_language→maluku，
    # 也会被本强组层先截住）。
    "papuan_group":       r(6, "papuan", "巴布亚文化组全部并入 CK3 原版 papuan，用户 2026-10-27 定"),
}

# ============ 文化组级规则 ============
GROUP_RULE = {
    # —— 美洲（全部 11）——
    "andean_group": r(11, "", "美洲，按语言/组自创传统"),
    "quechuan_group": r(11, "", "美洲"),
    "aymara_group": r(11, "", "美洲"),
    "panzaleo_group": r(11, "", "美洲"),
    "quingnam_group": r(11, "", "美洲"),
    "muchik_group": r(11, "", "美洲"),
    "pukina_group": r(11, "", "美洲"),
    "culli_group": r(11, "", "美洲"),
    "ckunsa_group": r(11, "", "美洲"),
    "atallan_group": r(11, "", "美洲"),
    "chicham_group": r(11, "", "美洲"),
    "mapudungun_group": r(11, "", "美洲"),
    "tshon_group": r(11, "", "美洲"),
    "kawesqar_group": r(11, "", "美洲"),
    "chono_group": r(11, "", "美洲"),
    "yaghan_group": r(11, "", "美洲"),
    "charrua_group": r(11, "", "美洲"),
    "mataco_guaicuru_group": r(11, "", "美洲"),
    "maskoy_group": r(11, "", "美洲"),
    "zamuco_group": r(11, "", "美洲"),
    "guahibo_group": r(11, "", "美洲"),
    "timoto_group": r(11, "", "美洲"),
    "tayrona_group": r(11, "", "美洲"),
    "sinu_group": r(11, "", "美洲"),
    "choco_group": r(11, "", "美洲"),
    "barbakoan_group": r(11, "", "美洲"),
    "calima_group": r(11, "", "美洲"),
    "pijao_group": r(11, "", "美洲"),
    "panche_group": r(11, "", "美洲"),
    "caribe_group": r(11, "", "美洲"),
    "ta_arawakan_group": r(11, "", "美洲"),
    "tucanoan_group": r(11, "", "美洲"),
    "bora_huitoto_group": r(11, "", "美洲"),
    "pano_group": r(11, "", "美洲"),
    "moseten_group": r(11, "", "美洲"),
    "mura_group": r(11, "", "美洲"),
    "tupi_group": r(11, "", "美洲"),
    "macro_je_group": r(11, "", "美洲"),
    "chibchan_group": r(11, "", "美洲"),
    "misumalpan_group": r(11, "", "美洲"),
    "jirajaran_group": r(11, "", "美洲"),
    "cuicas_group": r(11, "", "美洲"),
    "waqha_group": r(11, "", "美洲"),
    "uru_group": r(11, "", "美洲"),
    "cacan_group": r(11, "", "美洲"),
    "lule_group": r(11, "", "美洲"),
    "warpe_group": r(11, "", "美洲"),
    "hokan_group": r(11, "", "美洲"),
    "penutian_group": r(11, "", "美洲"),
    "salishan_group": r(11, "", "美洲"),
    "wakashan_group": r(11, "", "美洲"),
    "haida_group": r(11, "", "美洲"),
    "tsimshian_group": r(11, "", "美洲"),
    "ktunaxa_group": r(11, "", "美洲"),
    "yuki_group": r(11, "", "美洲"),
    "chumashan_group": r(11, "", "美洲"),
    "takic_group": r(11, "", "美洲"),
    "tanoan_group": r(11, "", "美洲"),
    "keres_group": r(11, "", "美洲"),
    "zuni_group": r(11, "", "美洲"),
    "puebloan_group": r(11, "", "美洲"),
    "yutonahua_group": r(11, "", "美洲"),
    "nahua_group": r(11, "", "美洲"),
    "maya_group": r(11, "", "美洲"),
    "otopamean_group": r(11, "", "美洲"),
    "totozoquean_group": r(11, "", "美洲"),
    "eastern_otomanguean_group": r(11, "", "美洲"),
    "purepecha_group": r(11, "", "美洲"),
    "cuitlatec_group": r(11, "", "美洲"),
    "coahuilteco_group": r(11, "", "美洲"),
    "timucua_group": r(11, "", "美洲"),
    "caddoan_group": r(11, "", "美洲"),
    "atakapa_group": r(11, "", "美洲"),
    "chitimacha_group": r(11, "", "美洲"),
    "chiwere_group": r(11, "", "美洲"),
    "natchez_group": r(11, "", "美洲"),
    "muskogee_group": r(11, "", "美洲"),
    "myaamia_group": r(11, "", "美洲"),
    "powhatan_group": r(11, "", "美洲"),
    "cree_group": r(11, "", "美洲"),
    "dakota_group": r(11, "", "美洲"),
    "dhegiha_group": r(11, "", "美洲"),
    "chickasaw_choctaw_group": r(11, "", "美洲"),
    "cherokee_group": r(11, "", "美洲"),
    "haudenosaunee_group": r(11, "", "美洲"),
    "iroquoian_group": r(11, "", "美洲"),
    "lenape_group": r(11, "", "美洲"),
    "massachusett_group": r(11, "", "美洲"),
    "shawnee_group": r(11, "", "美洲"),
    "tutelo_group": r(11, "", "美洲"),
    "wendat_group": r(11, "", "美洲"),
    "skarureh_group": r(11, "", "美洲"),
    "tsehesenestsestotse_group": r(11, "", "美洲"),
    "siksika_group": r(11, "", "美洲"),
    "apsaalooke_hiraaca_group": r(11, "", "美洲"),
    "nuuchi_nuwu_group": r(11, "", "美洲"),
    "shoshoni_group": r(11, "", "美洲"),
    "paiute_group": r(11, "", "美洲"),
    "hinonoeitiit_group": r(11, "", "美洲"),
    "abenakian_group": r(11, "", "美洲"),
    "algic_group": r(11, "", "美洲"),
    "anishinabe_group": r(11, "", "美洲"),
    "seeptsa_group": r(11, "", "美洲"),
    "sihni_group": r(11, "", "美洲"),
    "tarairiu_group": r(11, "", "美洲"),
    "truka_group": r(11, "", "美洲"),
    "txapakura_group": r(11, "", "美洲"),
    "manoki_group": r(11, "", "美洲"),
    "kwaza_group": r(11, "", "美洲"),
    "kambiwa_group": r(11, "", "美洲"),
    "besiro_group": r(11, "", "美洲"),
    "aikana_group": r(11, "", "美洲"),
    "aingae_group": r(11, "", "美洲"),
    "bagua_group": r(11, "", "美洲"),
    "kanisian_group": r(11, "", "美洲"),
    "inuit_group": r(11, "", "北极圈，CK3 无对应"),
    "yupik_group": r(11, "", "北极圈，CK3 无对应"),
    # —— 澳洲 / 大洋洲 ——
    "australian_group": r(11, "", "澳洲土著，CK3 无对应"),
    "papuan_group": r(10, "", "参考 CK 巴布亚文化传统"),
    "micronesian_group": r(10, "", "参考 CK 南岛语文化传统"),
    "polynesian_group": r(10, "", "参考 CK 南岛语文化传统"),
    "malagasy_group": r(10, "", "参考 CK 南岛语文化传统"),
    # —— 非洲 ——
    "bantu_group": r(10, "", "参考 CK 东班图文化传统"),
    "kongo_group": r(10, "", "参考 CK 东班图文化传统"),
    "luba_group": r(10, "", "参考 CK 东班图文化传统"),
    "great_lakes_kingdoms_group": r(10, "", "参考 CK 东班图文化传统"),
    "east_african_coast_group": r(10, "", "参考 CK 斯瓦希里文化传统"),
    "nguni_group": r(10, "", "参考 CK 东班图文化传统"),
    "sotho_tswana_group": r(10, "", "参考 CK 东班图文化传统"),
    "shona_group": r(10, "", "参考 CK 东班图文化传统"),
    "chokwe_group": r(10, "", "参考 CK 东班图文化传统"),
    "khoisan_group": r(11, "", "科伊桑，CK3 无对应"),
    # —— 其他 ——
    "caucasian_group": r(9, "", "北高加索诸族，CK3 只有格鲁吉亚/亚美尼亚"),
    "jurchen_group": r(6, "jurchen", "女真诸文化并入女真"),
    "shan_group": r(9, "shan", "掸文化，从傣分离"),
    "romani_group": r(9, "romani", "CK3 无罗姆文化"),
    "rhaetian_group": r(7, "cisalpine", "雷蒂亚语按地理入内高卢"),
    "tatar_group": r(4, "kipchak", "鞑靼诸文化并入钦察（草原组已在 CULT_RULE 分流到 kazakh）"),
    "jewish_group": r(4, "radhanite", "犹太散居，按语言分流（默认拉丹尼特）"),
    "amazigh_group": r(6, "butr", "柏柏尔文化组"),
    "permic_group": r(2, "komi", "彼尔姆语支→科米"),
    "mordvinic_group": r(1, "mordvin", "莫尔多瓦"),
    "hungarian_group": r(1, "hungarian", "匈牙利"),
    "romanian_group": r(2, "vlach", "罗马尼亚=弗拉赫"),
    "nepali_group": r(2, "bodpa", "尼泊尔藏语支→bodpa"),
    # —— 补漏 ——
    "nadene_group": r(11, "", "美洲"),
    "movima_group": r(11, "", "美洲"),
    "henia_kamiare_group": r(11, "", "美洲"),
    "atacame_group": r(11, "", "美洲"),
    "malibu_group": r(11, "", "美洲"),
    "napuruna_group": r(11, "", "美洲"),
    "pume_group": r(11, "", "美洲"),
    "warao_group": r(11, "", "美洲"),
    "xinka_group": r(11, "", "美洲"),
    "cunco_culture_group": r(11, "", "美洲"),
}

# ============ 自动兜底 ============
van = list(csv.DictReader(io.open(VAN, encoding="utf-8-sig")))
VK = {x["culture"]: x for x in van}
BY_LANG = collections.defaultdict(list)
BY_HER = collections.defaultdict(list)
for x in van:
    BY_LANG[x["language"]].append(x["culture"])
    BY_HER[x["heritage"]].append(x["culture"])

rows = list(csv.DictReader(io.open(BASE, encoding="utf-8-sig")))


def _norm_name(s):
    s = (s or "").strip()
    for a, b in (("\u2011", "-"), ("\u2013", "-"), ("\u2014", "-"), ("\u00b7", ""), ("\u30fb", "")):
        s = s.replace(a, b)
    return re.sub(r"[\s\-'\u2019.]", "", s).lower()


# CK3 文化的中文显示名 → key（只收唯一对应的）
CK3_BY_ZH = collections.defaultdict(list)
_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_ck3_culture_names.csv")
if os.path.exists(_p):
    for x in csv.DictReader(io.open(_p, encoding="utf-8-sig")):
        if x["name_zh"]:
            CK3_BY_ZH[_norm_name(x["name_zh"])].append(x["culture"])

# 我们文化的中文显示名
OUR_ZH = {}
if os.path.exists(ZH_NAME_CSV):
    for x in csv.DictReader(io.open(ZH_NAME_CSV, encoding="utf-8-sig")):
        if x["name_zh"]:
            OUR_ZH[x["culture"]] = x["name_zh"]


def dom_kingdom(field):
    """取男爵领数最多的王国，作为该文化的主分布区。"""
    best, bc = "", -1
    for part in (field or "").split(";"):
        if ":" in part:
            n, cnt = part.rsplit(":", 1)
            try:
                cnt = int(cnt)
            except ValueError:
                continue
            if cnt > bc:
                bc, best = cnt, n
    return best


out = []
for row in rows:
    c = row["culture"]
    base = c[:-8] if c.endswith("_culture") else c
    eu5l = row["eu5_language"]
    grps = [g for g in row["eu5_groups"].split(";") if g]

    cat = target = note = conf = None
    src = ""
    # 判据顺序：文化级显式 > 自动同名（撞名异族除外）> 强文化组 > 语言级 > 文化组级 > 语言唯一 > 传承唯一
    # （强文化组 = GROUP_RULE_STRONG，用户 2026-10-27 加的一层，只放要决断的组）
    if c in CULT_RULE:
        cat, target, note, conf = CULT_RULE[c]
        src = "文化"
    elif base in CULT_RULE:
        cat, target, note, conf = CULT_RULE[base]
        src = "文化"
    elif base in DISPLAY_ALIAS:
        cat, target, conf = 1, DISPLAY_ALIAS[base], "high"
        note = "显示名同名（CK3 key 为 %s）" % DISPLAY_ALIAS[base]
        src = "显示名"
    elif base in HYBRID_NAMES:
        cat, target, note, conf = 8, HYBRID_NAMES[base], "对应 CK3 融合文化名 %s" % HYBRID_NAMES[base], "high"
        src = "融合名"
    elif base in VK and base not in SAME_NAME_DIFF:
        cat, target, note, conf = 1, base, "同名同地", "high"
        src = "自动-同名"
    elif (OUR_ZH.get(c) and c not in ZH_HOMOGRAPH
          and len(CK3_BY_ZH.get(_norm_name(OUR_ZH[c]), [])) == 1):
        t = CK3_BY_ZH[_norm_name(OUR_ZH[c])][0]
        if t != base:
            cat, target, conf = 1, t, "high"
            note = "中文名同名（%s，CK3 key 为 %s）" % (OUR_ZH[c], t)
            src = "中文同名"
    if cat is None:
        # 强组层：GROUP_RULE_STRONG 里的组只要排在 eu5_groups 的**第一位**就在语言之前表态。
        # 为什么要求第一位而不是「任一组命中」：jurchen_group;tungusic_group 若按任意命中，
        # 会被 tungusic_group 抢成 mohe，把 4 个女真文化（jurchen/haixi/hurga/udege）错并进靺鞨。
        # 为什么不是「只能有一个组」：班图 95 个文化里 58 个是 bantu_group;xxx_group 的组合，
        # 只认单组会漏掉一大半。EU5 的组顺序里第一位就是主属。
        if grps and grps[0] in GROUP_RULE_STRONG:
            cat, target, note, conf = GROUP_RULE_STRONG[grps[0]]
            src = "文化组"
    if cat is None:
        if eu5l in LANG_RULE:
            cat, target, note, conf = LANG_RULE[eu5l]
            src = "语言"
        else:
            for g in grps:
                if g in GROUP_RULE:
                    cat, target, note, conf = GROUP_RULE[g]
                    src = "文化组"
                    break

    if cat is None:
        # 自动：语言唯一 > 传承唯一
        if len(BY_LANG.get(row["language"], [])) == 1:
            t = BY_LANG[row["language"]][0]
            cat, target, note, conf = 4, t, "语言唯一对应 %s" % t, "medium"
            src = "自动-语言"
        elif len(BY_HER.get(row["heritage"], [])) == 1:
            t = BY_HER[row["heritage"]][0]
            cat, target, note, conf = 6, t, "传承唯一对应 %s" % t, "medium"
            src = "自动-传承"
        else:
            cat, target, note, conf = 0, "", "未判定", "low"
            src = "未判定"

    # —— 一致性校验：cat1 必须 target == 自身 key（显示名同名除外）；否则按原判据回落 ——
    if cat == 1 and target != base and src not in ("显示名", "中文同名"):
        if target not in VK:
            cat, target, note, conf = 0, "", "cat1 目标 %s 非原版文化" % target, "low"
            src = "未判定"
        elif src == "语言":
            cat, conf = 4, "medium"
        elif src == "文化组":
            cat, conf = 6, "medium"
        else:
            cat, conf = 2, "medium"
    elif cat in (2, 4, 5, 6, 7) and target == base and base in VK:
        cat, note, conf = 1, "同名同地", "high"
        src = "自动-同名"

    # —— 地理校正：cat9（建分离文化）必须在 CK3 原版地图内；图外有参照的归 cat10 ——
    domk = dom_kingdom(row["kingdoms"])
    if cat == 9 and domk in OFFMAP_KINGDOMS:
        cat, conf = 10, "medium"
        note = (note + "；" if note else "") + "CK3 地图外，按参照新建"
        src = "地理"
    elif cat == 10 and domk in COVERED_KINGDOMS:
        cat, conf = 9, "medium"
        note = (note + "；" if note else "") + "CK3 地图内，从同语系文化分离"
        src = "地理"

    # NEW 目标命名
    if cat in (8, 9, 10, 11):
        if target:
            target = "NEW:" + target
        else:
            lg = eu5l.replace("_language", "").replace("_dialect", "")
            target = "NEW:" + (lg or (grps[0].replace("_group", "") if grps else c))
    if cat in (10, 11) and not note:
        note = ""

    out.append({
        "culture": c,
        "name_en": row["name_en"],
        "heritage": row["heritage"],
        "language": row["language"],
        "eu5_language": eu5l,
        "eu5_groups": row["eu5_groups"],
        "baronies": row["baronies"],
        "kingdoms": row["kingdoms"],
        "continent": CONTINENT.get(dom_kingdom(row["kingdoms"]), ""),
        "category": cat,
        "cat_label": CAT_LABEL.get(cat, "未判定"),
        "target": target,
        "note": note,
        "confidence": conf,
        "rule_source": src,
    })

# ============ 大洲回退 ============
# 0 男爵领的文化没有主导王国，按下面顺序补：
#   1) EU5 人口最多的那个王国（_culture_pop_continent.csv，由 _build_culture_pop_continent.py 生成）
#   2) 同传承文化里最常见的大洲
#   3) 仍然没有 → 无地块（只有占位文化 gen_culture_unsettled 会走到这里）
POP_CONT = {}
_pc = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_culture_pop_continent.csv")
if os.path.exists(_pc):
    for _r in csv.DictReader(io.open(_pc, encoding="utf-8-sig")):
        POP_CONT[_r["culture"]] = _r["top_kingdom"]

for x in out:
    if x["continent"]:
        continue
    k = POP_CONT.get(x["culture"])
    if k:
        x["continent"] = CONTINENT.get(k, "")

_by_her = collections.defaultdict(collections.Counter)
for x in out:
    if x["continent"]:
        _by_her[x["heritage"]][x["continent"]] += 1
for x in out:
    if x["continent"] or x["culture"] == "gen_culture_unsettled":
        continue
    ctr = _by_her.get(x["heritage"])
    if ctr:
        x["continent"] = ctr.most_common(1)[0][0]
# 既无男爵领、EU5 里又没有 pops 的，只能手工定（目前就这一个）：
# roman_culture「拉丁」是拜占庭境内的拉丁语人群，按拜占庭传承多数会被判成亚洲，改回欧洲。
CONTINENT_MANUAL = {
    "roman_culture": "欧洲",
}
for x in out:
    if x["culture"] in CONTINENT_MANUAL:
        x["continent"] = CONTINENT_MANUAL[x["culture"]]
for x in out:
    if not x["continent"]:
        x["continent"] = "无地块"

try:
    with io.open(OUT, "w", encoding="utf-8-sig", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print("写出 %s (%d 行)" % (OUT, len(out)))
except PermissionError:
    alt = OUT.replace(".csv", ".new.csv")
    with io.open(alt, "w", encoding="utf-8-sig", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print("!! %s 被占用（多半是 Excel 开着），改写 %s (%d 行)"
          % (os.path.basename(OUT), os.path.basename(alt), len(out)))

print()
print("%-4s %-14s %6s %9s %9s" % ("类别", "名称", "文化数", "男爵领", "占比"))
tot_b = sum(int(x["baronies"]) for x in out)
for cat in sorted({x["category"] for x in out}):
    sub = [x for x in out if x["category"] == cat]
    b = sum(int(x["baronies"]) for x in sub)
    print("%-4s %-14s %6d %9d %8.1f%%"
          % (cat, CAT_LABEL.get(cat, "未判定"), len(sub), b,
             100.0 * b / tot_b if tot_b else 0))
print("%-4s %-14s %6d %9d" % ("", "合计", len(out), tot_b))

print()
print("== 按规则来源 ==")
for k, v in collections.Counter(x["rule_source"] for x in out).most_common():
    print("  %-12s %d" % (k, v))

print()
print("== 未判定（需人工）前 30 ==")
und = [x for x in out if x["category"] == 0]
print("共 %d 个" % len(und))
for x in und[:30]:
    print("  %-26s %-26s %s" % (x["culture"], x["eu5_language"], x["eu5_groups"]))
