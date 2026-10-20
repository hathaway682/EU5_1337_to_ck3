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
    "chiyalik_culture":     r(6, "hungarian", "奇亚利克是马扎尔文化组仅存文化"),
    "norse_gael":           r(8, "norse_gael", "与 CK 融合名同名"),
    "anglo_irish":          r(8, "anglo_irish", "英爱融合"),
    "turkish":              r(8, "anatolian_turkish", "突厥蛮+希腊融合，对应安纳托利亚突厥"),
    "turkish_culture":      r(8, "anatolian_turkish", "EU5 土耳其=突厥蛮+希腊融合，对应 CK3 融合名 anatolian_turkish"),
    # —— 其他关键个案 ——
    "andalusi":             r(2, "andalusian", "安达卢西=安达卢西亚"),
    "leonese":              r(2, "asturleonese", "莱昂=阿斯图里亚斯-莱昂"),
    "kochini":              r(2, "kochinim", "科钦犹太人"),
    "gothic_culture":       r(1, "gothic", "克里米亚哥特"),
    "coptic_culture":       r(4, "egyptian", "科普特语属埃及语族"),
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
    "walloon":              r(8, "walloon", "瓦隆：法兰西+荷兰融合文化（用户定，以法兰西为基础，加乡土观念）"),
    # EU5 的 francique_dialect 是奥依语支（francien，含香槟/洛林/皮卡第/瓦隆），
    # 不是日耳曼的法兰克尼亚。语言柱被错挂成 language_high_german
    # （见 _eu5_language_to_ck3.py 第 92 行），此处按实际语支落 french。
    "champenais":           r(5, "french", "香槟方言属奥依语（语言柱误挂 high_german，实为 francique=奥依）"),
    "lorrain":              r(5, "french", "洛林方言属奥依语（同上）"),
    "picard":               r(5, "french", "皮卡第方言属奥依语（同上）"),
    # —— 法国：用户 2026-10-21 定的备选新文化，本轮均不建，回到所属语支 ——
    "gallo":                r(4, "french", "加洛属奥依语；融合文化列为备选（规模过小），暂并入法兰西"),
    "angevin":              r(4, "french", "安茹方言属奥依语；安茹融合列为备选，暂并入法兰西"),
    "arpitan":              r(4, "occitan", "阿尔卑坦语属奥克-罗曼；因意大利 DLC 暂不建，按语支入奥克"),
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
    "yao_culture":          r(10, "yao_malawi", "非洲瑶族（班图语支，马拉维/莫桑比克），与 CK3 瑶族（苗语支）同名异族", "high"),
    "avar_culture":         r(9, "caucasian_avar", "高加索阿瓦尔人（东北高加索语），与 CK3 潘诺尼亚阿瓦尔（突厥/乌古尔语）同名异族", "high"),
    # —— 德国波罗的海沿岸（用户 2026-10-21 定）——
    # EU5 的波美拉尼亚（western/eastern_pomeranian）是低地德语的德意志人口，
    # 与 CK3 的 pommeranian（实为莱赫语的卡舒比人，见 kashubian）不是同一人群
    # → 新建 萨克森+卡舒比 融合文化，本地化取「波美拉尼亚」。
    # EU5 的 prussian 是低地德语德意志人口，与 CK3 波罗的古普鲁士同名异族
    # → 从萨克森分离（圣战产物，不融合），本地化取「普鲁士」。
    "western_pomeranian":   r(8, "pomeranian", "西波美拉尼亚（低地德语）：萨克森+卡舒比融合文化，用户定"),
    "eastern_pomeranian":   r(8, "pomeranian", "东波美拉尼亚（低地德语）：萨克森+卡舒比融合文化，用户定"),
    "prussian":             r(9, "prussian_german", "EU5 普鲁士是低地德语的德意志人口，与 CK3 波罗的普鲁士（原版仅 k_lithuania 10 省）同名异族，从萨克森分离另立（圣战产物，不融合）", "high"),
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

    # —— 突厥语支细分 ——
    # 原先 language_turkic 一律→cuman，把乌兹别克/诺盖/喀山/吉尔吉斯全吞进库曼。
    # 库曼只留 CK3 的 cuman_culture（3 男爵领在匈牙利，符合库曼人西迁史实）。
    # 钦察语其余文化：带草原族群文化组（steppe_group）的 5 个鞑靼-钦察游牧与蒙古混居，
    # 对应 CK3 融合名 kazakh（哈萨克＝钦察-蒙古融合体）；不带草原组的走 kipchak。
    # 注意：CK3 官方中文把 kazakh 译作「乌兹别克」，与本 mod 用法冲突，本地化需覆盖为「哈萨克」。
    "astrakhani":           r(8, "kazakh", "阿斯特拉罕鞑靼，草原组，钦察-蒙古融合"),
    "crimean":              r(8, "kazakh", "克里米亚鞑靼，草原组，钦察-蒙古融合"),
    "kazani":               r(8, "kazakh", "喀山鞑靼，草原组，钦察-蒙古融合"),
    "mishar":               r(8, "kazakh", "米沙鞑靼，草原组，钦察-蒙古融合"),
    "nogai":                r(8, "kazakh", "诺盖，草原组，钦察-蒙古融合"),

    # —— 柏柏尔：按地理分配 ——
    # CK3 原版落点：butr 在 k_tahert(17) k_africa(12) k_anbiya(11) k_sahara(9) k_egypt(7)
    #   k_maghreb(6) k_hausaland(4) k_songhay(4) k_ghana(1)；
    # baranis 只在 k_maghreb(15) k_africa(7) k_tahert(2)，即摩洛哥一带。
    # 故阿尔及利亚/突尼斯/撒哈拉诸族→butr，摩洛哥诸族→baranis。
    "zenati":               r(6, "butr", "泽纳塔，阿尔及利亚/突尼斯内陆，落 k_tahert（butr 17 : baranis 2）"),
    "mozabite":             r(6, "butr", "姆扎卜在阿尔及利亚北部撒哈拉，同 k_tahert/k_sahara 的 butr"),
    "chaoui":               r(6, "butr", "沙维在奥雷斯山（阿尔及利亚东部），同 k_tahert 的 butr"),
    "eastern_amazigh":      r(6, "butr", "东柏柏尔在突尼斯/的黎波里塔尼亚，CK3 k_africa/k_anbiya 为 butr"),
    "kabyle":               r(6, "butr", "卡比利亚在阿尔及利亚北部，落 k_tahert（butr 17 : baranis 2）"),
    "lamtuna_culture":      r(6, "butr", "兰图纳在毛里塔尼亚/西撒哈拉，CK3 k_sahara/k_ghana 为 butr"),
    "godala_culture":       r(6, "butr", "古达拉在毛里塔尼亚，同 k_sahara/k_songhay 的 butr"),
    "messufa_culture":      r(6, "butr", "梅苏法在撒哈拉西部，同 k_sahara 的 butr"),
    "tuareg":               r(6, "butr", "图阿雷格在撒哈拉，同 k_sahara 的 butr"),
    "sanhaja":              r(6, "baranis", "桑哈贾在摩洛哥/西撒哈拉，CK3 k_maghreb 主体 baranis（15）"),
    "masmuda":              r(6, "baranis", "马斯穆达为摩洛哥主体柏柏尔，CK3 k_maghreb 主体 baranis（15）"),

    # —— 苏丹-阿拉伯：阿拉伯人 + 努比亚人融合 ——
    "sudanese_arab":        r(8, "sudanese_arab", "苏丹阿拉伯＝阿拉伯+努比亚融合，CK3 无对应，建融合文化"),
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
    "arpitan_dialect":          r(4, "occitan", "阿尔皮坦语属奥克-罗曼"),
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
    "coptic_language":          r(4, "egyptian", "科普特语属埃及语族"),
    # —— 伊朗 ——
    "persian_language":         r(1, "persian", "波斯语"),
    "kurdish_language":         r(1, "kurdish", "库尔德语"),
    "balochi_language":         r(1, "baloch", "俾路支语"),
    "afghani_language":         r(1, "afghan", "阿富汗语"),
    "tajik_language":           r(1, "tajik", "塔吉克语"),
    "adharic_language":         r(4, "turkish", "阿塞拜疆语属突厥语族"),
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
    "jurchen_language":         r(1, "jurchen", "女真语"),
    "evenk_language":           r(9, "evenk", "鄂温克诸部，CK3 无对应，从靺鞨/女真分离"),
    "nanai_language":           r(6, "jurchen", "那乃/赫哲属通古斯，并入女真"),
    "udege_language":           r(6, "jurchen", "乌德盖属通古斯，并入女真"),
    "nivkh_language":           r(1, "nivkh", "尼夫赫语"),
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
    "nicobarese_language":      r(9, "nicobarese", "尼科巴语，CK3 无对应"),
    "hmong_language":           r(1, "hmong", "苗语"),
    "yao_language":             r(1, "yao", "瑶语"),
    "thai_dialect":             r(4, "tai", "泰语诸文化并入傣"),
    "lao_dialect":              r(4, "tai", "老挝语并入傣"),
    "dai_dialect":              r(4, "tai", "傣语并入傣"),
    "shan_dialect":             r(9, "shan", "掸文化，CK3 泰人未入掸邦，从傣分离"),
    "zhuang_language":          r(1, "bouxcuengh", "壮语=布僮"),
    "kam_language":             r(4, "tai", "侗水语支并入傣"),
    "kra_language":             r(4, "hlai", "仡央语支并入黎"),
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
    "saharan_language":         r(4, "kanuri", "撒哈拉语支并入卡努里"),
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
    "formosan_language":        r(10, "formosan", "台湾南岛语，CK3 无对应，参考南岛"),
    # —— 零散 ——
    "bhili_language":           r(7, "rajput", "比尔语按地理入拉杰普特"),
    "bantoid_language":         r(10, "bantoid", "类班图，参考东班图传统"),
    "chukotko_kamchatkan_language": r(11, "chukchi", "楚科奇-堪察加，CK3 无对应"),
    "yukaghir_language":        r(11, "yukaghir", "尤卡吉尔，CK3 无对应"),
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
    "lamut_language":           r(9, "evenk", "埃文/拉穆特并入鄂温克"),
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
    # 判据顺序：文化级显式 > 自动同名（撞名异族除外）> 语言级 > 文化组级 > 语言唯一 > 传承唯一
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
