# -*- coding: utf-8 -*-
"""把 _culture_classification.csv 汇总成报告：按类别、按大区、需人工裁定清单。"""
import io, os, sys, csv, collections

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
SRC = os.path.join(MOD, "gen_debug",
                   sys.argv[1] if len(sys.argv) > 1 else "_culture_classification.csv")
OUT = os.path.join(MOD, "gen_debug", "_culture_classification_report.md")

CAT_LABEL = {
    0: "未判定", 1: "同名同地", 2: "异名同族", 3: "同名错位",
    4: "按语言并入", 5: "按方言并入", 6: "按文化组并入", 7: "按地理并入",
    8: "需建融合文化", 9: "需建分离文化", 10: "图外可参考", 11: "图外自创",
}

REGION = {}
for r, ks in {
    "西欧": "france great_britain ireland iberia italy north_german south_german north_atlantic_islands macaronesia",
    "北欧波罗的": "scandinavian baltic",
    "东欧": "carpathia balkan ruthenia russian ural caucasus",
    "中东": "anatolia arabia crescent persia khorasan egypt nubia",
    "非洲": "maghreb sahel guinea central_africa kongo southern_africa zimbabwe swahili_coast great_lakes ethiopia somalia madagascar",
    "南亚": "hindustan deccan bengal western_india central_india",
    "中亚北亚": "steppes xinjiang tibet mongolia manchuria west_siberia east_siberia",
    "东亚": "north_china south_china east_china west_china korea japan",
    "东南亚": "indochina indonesia",
    "北美": "alaska canada great_plains east_coast west_coast aridoamerica mesoamerica central_america caribbean",
    "南美": "andes colombia brazil la_plata chaco",
    "大洋洲": "australia new_zealand melanesia micronesia polynesia",
    "海域": "north_atlantic_ocean south_atlantic",
}.items():
    for k in ks.split():
        REGION[k] = r


def dom_kingdom(field):
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


rows = list(csv.DictReader(io.open(SRC, encoding="utf-8-sig")))

# 中文名：CSV 自己带就用，没带（被 Excel 占着没写上）就从 .annotated.csv 补
if "name_zh" not in rows[0]:
    ann = os.path.join(MOD, "gen_debug", "_culture_classification.annotated.csv")
    zhmap = {}
    if os.path.exists(ann):
        for r in csv.DictReader(io.open(ann, encoding="utf-8-sig")):
            zhmap[r["culture"]] = (r.get("name_zh", ""), r.get("target_zh", ""))
    for x in rows:
        x["name_zh"], x["target_zh"] = zhmap.get(x["culture"], ("", ""))


def nm(x):
    """带中文名的文化显示串。"""
    z = x.get("name_zh") or ""
    return "%s（%s）" % (x["culture"], z) if z else x["culture"]


def tg(x):
    t = x.get("target") or ""
    z = x.get("target_zh") or ""
    return "%s（%s）" % (t, z) if z else t


tot_b = sum(int(x["baronies"]) for x in rows)
L = []
A = L.append

A("# EU5 → CK3 文化分类汇总")
A("")
A("口径：2088 个文化 / 21046 个男爵领。分类依据为各文化的传承（heritage）、语言（language）"
  "与 EU5 原始语言字段（eu5_language）。逐文化明细见 `_culture_classification.csv`。")
A("")

A("## 一、按类别")
A("")
A("| 类别 | 名称 | 文化数 | 男爵领 | 占比 |")
A("|---:|---|---:|---:|---:|")
for cat in range(0, 12):
    sub = [x for x in rows if int(x["category"]) == cat]
    if not sub:
        continue
    b = sum(int(x["baronies"]) for x in sub)
    A("| %d | %s | %d | %d | %.1f%% |" % (cat, CAT_LABEL[cat], len(sub), b, 100.0 * b / tot_b))
A("| | **合计** | **%d** | **%d** | **100%%** |" % (len(rows), tot_b))
A("")

A("## 二、按大洲 / 大区 × 类别（文化数）")
A("")
cats = [c for c in range(0, 12) if any(int(x["category"]) == c for x in rows)]


def emit_matrix(group_of, head, order=None):
    A("**%s**" % head)
    A("")
    A("| %s | " % head.split("×")[0].strip() + " | ".join(str(c) for c in cats) + " | 合计 |")
    A("|---|" + "---:|" * len(cats) + "---:|")
    mat = collections.defaultdict(lambda: collections.Counter())
    for x in rows:
        mat[group_of(x)][int(x["category"])] += 1
    keys = order or sorted(mat, key=lambda r: -sum(mat[r].values()))
    for reg in keys:
        if reg not in mat:
            continue
        row = mat[reg]
        A("| %s | %s | %d |" % (reg, " | ".join(str(row.get(c, 0)) for c in cats), sum(row.values())))
    A("")


# 0 男爵领的文化没有王国字段，用 EU5 人口最多的王国兜底（同分类器口径）
POPK = {}
_pc = os.path.join(MOD, "gen_debug", "_culture_pop_continent.csv")
if os.path.exists(_pc):
    for r in csv.DictReader(io.open(_pc, encoding="utf-8-sig")):
        POPK[r["culture"]] = r["top_kingdom"]


def region_of(x):
    return REGION.get(dom_kingdom(x["kingdoms"]) or POPK.get(x["culture"], ""), "无地块")

CONT_ORDER = ["亚洲", "欧洲", "非洲", "北美洲", "南美洲", "大洋洲", "无地块"]
emit_matrix(lambda x: x.get("continent") or "无地块", "大洲 × 类别", CONT_ORDER)
emit_matrix(region_of, "大区 × 类别")
A("")

A("## 三、各类别目标文化 Top")
A("")
for cat in [8, 9, 3, 2, 6, 7]:
    sub = [x for x in rows if int(x["category"]) == cat]
    if not sub:
        continue
    A("### %d %s（%d 个）" % (cat, CAT_LABEL[cat], len(sub)))
    A("")
    A("| 文化 | 男爵领 | 目标 | 依据 |")
    A("|---|---:|---|---|")
    for x in sorted(sub, key=lambda y: -int(y["baronies"]))[:25]:
        A("| %s | %s | %s | %s |" % (nm(x), x["baronies"], tg(x), x["note"][:60]))
    A("")

A("## 四、需人工裁定")
A("")
adj = [x for x in rows if x["confidence"] == "low" or int(x["category"]) == 0]
A("### 4.1 低置信 / 未判定（%d 个）" % len(adj))
A("")
A("| 文化 | 类别 | 目标 | 说明 |")
A("|---|---:|---|---|")
for x in adj:
    A("| %s | %s | %s | %s |" % (nm(x), x["category"], tg(x), x["note"][:70]))
A("")

A("### 4.2 同名异族（名字撞 CK3，但不是同一人群）")
A("")
A("| 文化 | 类别 | 目标 | 理由 |")
A("|---|---:|---|---|")
for x in rows:
    if x["culture"] in ("yao_culture", "avar_culture", "prussian", "khorezmian_culture", "turkmen_culture"):
        A("| %s | %s | %s | %s |" % (nm(x), x["category"], tg(x), x["note"][:70]))
A("")

A("### 4.3 判定所依据的传承可疑（与 CK3 原版同名文化不一致）")
A("")
A("| 文化 | 我们的传承 | CK3 原版同名传承 | 类别 |")
A("|---|---|---|---:|")
van = {r["culture"]: r for r in csv.DictReader(
    io.open(os.path.join(MOD, "gen_debug", "_ck3_vanilla_cultures.csv"), encoding="utf-8-sig"))}
bad = []
for x in rows:
    b = x["culture"][:-8] if x["culture"].endswith("_culture") else x["culture"]
    v = van.get(b)
    if v and v["heritage"] != x["heritage"]:
        bad.append((x, v))
for x, v in sorted(bad, key=lambda t: -int(t[0]["baronies"]))[:30]:
    A("| %s | %s | %s | %s |" % (nm(x), x["heritage"], v["heritage"], x["category"]))
A("")
A("合计 %d 个同名文化的传承与原版不一致；上表只列男爵领前 30。" % len(bad))
A("")

A("### 4.4 CK3 原版 key 与显示名不一致的文化（判「同名」必须看显示名）")
A("")
A("| CK3 key | 中文显示名 | 英文显示名 | 已用到的映射 |")
A("|---|---|---|---|")
_used = {"turkish": "EU5 土库曼 → 此处（cat3）",
         "samoyed": "EU5 Bjarmian → 此处（cat1）",
         "guanches": "EU5 Guanche → 此处（cat1）",
         "assyrian": "EU5 Syriac → 此处（cat1）",
         "hindustani": "EU5 Kannauji → 此处（cat1）",
         "kochinim": "EU5 Kochini（cat2）",
         "turkmen": "EU5 突厥蛮 → 此处（cat2）",
         "karluk": "EU5 花剌子模 → 此处（cat3）",
         "bodpa": "藏语诸文化 → 此处（cat2）"}
try:
    names = list(csv.DictReader(io.open(os.path.join(MOD, "gen_debug", "_ck3_culture_names.csv"),
                                       encoding="utf-8-sig")))
except Exception:
    names = []
def _core(s):
    return (s or "").lower().replace("-", "").replace(" ", "").replace("\u2011", "")
for n in names:
    if _core(n["name_en"]) and _core(n["name_en"]) not in _core(n["culture"]):
        A("| %s | %s | %s | %s |" % (n["culture"], n["name_zh"], n["name_en"],
                                    _used.get(n["culture"], "")))
A("")
A("上表只列显示名与 key 明显不同的；`turkmen`（土库曼）、`karluk`（葛逻禄）、`guanches`（Guanche）、"
  "`bodpa`（吐蕃）等 key 与显示名一致的未列出，但它们同样被用作目标。")
A("")

# —— 4.5 按 CK3 原版落点细分的几处 ——
# 这几块原先都是「一个语言/文化组规则吞掉整片」：藏语一律→bodpa、突厥语一律→cuman、
# 柏柏尔一律→butr。依据 CK3 原版 history/provinces/k_*.txt 里各王国的 culture 分布重新落点。
TIBET_BLOCK = ["utsang_culture", "khampa_culture", "changpa_culture", "amdowa_culture",
               "tebbu_culture", "ladakh_culture", "balti_culture", "ngalop_culture",
               "sikkim_culture", "monpa_culture", "newar_culture", "magar_culture",
               "gurung_culture", "tamang_culture", "limbu_culture", "sherpa_culture"]
KIPCHAK_BLOCK = ["cuman_culture", "astrakhani", "crimean", "kazani", "mishar", "nogai",
                 "balkar_culture", "bashkir", "karachay_culture", "kumyk_culture",
                 "kyrgyz_culture", "telengit_culture", "teleut_culture", "uzbek_culture",
                 "yerle_qaliq_culture"]
BERBER_BLOCK = ["zenati", "mozabite", "chaoui", "eastern_amazigh", "kabyle",
                "lamtuna_culture", "godala_culture", "messufa_culture", "tuareg",
                "sanhaja", "masmuda", "guanche"]
RUS_BLOCK = ["novgorodian", "pomor", "vepsian", "prussian"]
SUDAN_BLOCK = ["sudanese_arab"]
A("### 4.5 按 CK3 原版落点细分的几处（藏区 / 钦察语 / 柏柏尔 / 罗斯 / 苏丹）")
A("")
A("原先「藏语→bodpa」「突厥语→cuman」「柏柏尔→butr」三条语言规则把整片语族并成一个文化。"
  "按 CK3 原版 `history/provinces/k_*.txt` 的实际 culture 分布重新落点：")
A("")
_ix = {x["culture"]: x for x in rows}


def _tbl(title, keys):
    A("**%s**" % title)
    A("")
    A("| 文化 | 男爵领 | 类别 | 目标 | 依据 |")
    A("|---|---:|---:|---|---|")
    for k in keys:
        x = _ix.get(k)
        if x:
            A("| %s | %s | %s | %s | %s |" % (nm(x), x["baronies"], x["category"], tg(x), x["note"][:60]))
    A("")


_tbl("藏区 / 喜马拉雅（16 个）", TIBET_BLOCK)
_tbl("钦察语（15 个：库曼只留 cuman_culture，草原组→kazakh 融合，其余→kipchak）", KIPCHAK_BLOCK)
_tbl("柏柏尔（12 个：马格里布/撒哈拉→butr，摩洛哥→baranis，加那利→guanches）", BERBER_BLOCK)
_tbl("罗斯 / 普鲁士（4 个：ilmenian 原版 0 省份不可用，诺夫哥罗德归罗斯；普鲁士从萨克森分离）", RUS_BLOCK)
_tbl("苏丹-阿拉伯（1 个：阿拉伯+努比亚融合）", SUDAN_BLOCK)

# ============ 4.6 欧洲落实方案 ============
A("### 4.6 欧洲落实方案（2026-10-21 用户定）")
A("")
A("本节把用户的欧洲方案落到分类表。**已落游戏（2026-10-21 01:34）**："
  "省份 culture 改动 3309 行（129 个文化、113 组映射），"
  "新文化定义写入 `common/culture/cultures/zz_eu5_culture_merge.txt`，"
  "本地化写入 `localization/simp_chinese/zz_eu5_culture_merge_l_simp_chinese.yml`，"
  "省份备份 `00_generated_provinces.txt.bak_eumerge_20261021_013418`。"
  "范围仅限欧洲计划内的文化；欧洲以外与 cat1 一一对应的文化一律未动。")
A("")
A("#### 一、本轮改动的落点")
A("")
EU_CHANGES = [
    ("walloon", "4 法兰西", "8 瓦隆"),
    ("gallo", "8 加洛", "4 法兰西"),
    ("angevin", "8 安茹", "4 法兰西"),
    ("arpitan", "8 阿尔卑坦", "4 奥克"),
    ("lombard", "1 伦巴第", "7 山南"),
    ("southern_gallo_italic", "4 伦巴第", "7 山南"),
    ("corsican", "7 山南", "7 撒丁"),
    ("neapolitan", "8 那不勒斯", "7 西西里"),
    ("maltese", "9 马耳他", "7 西西里"),
    ("romansh", "8 罗曼什", "7 山南"),
    ("griko_culture", "8 格里科", "4 意大利"),
    ("italki", "4 伦巴第", "4 拉赞尼亚"),
    ("transylvanian", "8 特兰西瓦尼亚", "4 瓦拉几亚"),
    ("aromanian", "8 阿罗马尼亚", "4 瓦拉几亚"),
    ("dalmatian", "8 达尔马提亚", "7 克罗地亚"),
    ("western_pomeranian", "5 萨克森", "8 波美拉尼亚"),
    ("eastern_pomeranian", "5 萨克森", "8 波美拉尼亚"),
    ("ingrian", "4 芬兰", "4 卡累利阿"),
    ("besermyan", "4 芬兰", "6 彼尔姆"),
    ("romani_culture", "9 罗姆", "11 罗姆（不建）"),
]
A("| 文化 | 男爵领 | 原落点 | 现落点 | 依据 |")
A("|---|---:|---|---|---|")
for _k, _old, _new in EU_CHANGES:
    _x = _ix.get(_k)
    if _x:
        A("| %s | %s | %s | %s | %s |" % (nm(_x), _x["baronies"], _old, tg(_x), _x["note"][:54]))
A("")
A("语言规则层同步修正：`francique_dialect` 由法兰克尼亚改为法兰西"
  "（EU5 的 francique 实为奥依语支，语言柱误挂 `language_high_german`）；"
  "`lombard_dialect` 由伦巴第改为山南；`maltese_dialect` 由马耳他改为西西里。")
A("")
A("#### 二、确定新建的 5 个文化")
A("")
A("| key | 中文 | 类型 | 来源 | heritage | language | ethos | traditions（基础文化原版 → 调整后） |")
A("|---|---|---|---|---|---|---|---|")
A("| `anglo_irish` | 盎格鲁-爱尔兰 | 融合 | 英格兰 + 爱尔兰 | west_germanic | anglic | bureaucratic | "
  "英格兰 4（hereditary_hierarchy / chivalry / castle_keepers / longbow_competitions）"
  " − 长弓竞赛 + 牧人 / 优美诗歌 / 海洋重商主义 = **6 个** |")
A("| `norse_gael` | 诺斯-盖尔 | 融合 | 诺斯 + 盖尔 | goidelic | goidelic | bellicose | "
  "盖尔 5（fishermen / hill_dwellers / highland_warriors / strong_kinship / concubines）"
  " − 高地战士 − 丘陵居民 + 沿海战士 / 海洋重商主义 / 说书人 = **6 个** |")
A("| `pomeranian` | 波美拉尼亚 | 融合 | 萨克森 + 卡舒比 | central_germanic | saxon | stoic | "
  "萨克森 3（stand_and_fight / ruling_caste / religious_patronage）"
  " − 统治阶层 + 海洋重商主义 = **3 个** |")
A("| `walloon` | 瓦隆 | 融合 | 法兰西 + 荷兰 | frankish | french | courtly | "
  "法兰西 3（chanson_de_geste / hereditary_hierarchy / chivalry）"
  " + 乡土观念 = **4 个** |")
A("| `teutonic` | 普鲁士 | 分离 | 萨克森（不融合，圣战产物） | central_germanic | saxon | stoic | "
  "萨克森 3（stand_and_fight / ruling_caste / religious_patronage）"
  " + 以剑之名 = **4 个** |")
A("")
A("traditions 中文对照：长弓竞赛 `tradition_longbow_competitions`、牧人 `tradition_pastoralists`、"
  "优美诗歌 `tradition_poetry`、海洋重商主义 `tradition_maritime_mercantilism`、"
  "统治阶层 `tradition_ruling_caste`、高地战士 `tradition_highland_warriors`、"
  "丘陵居民 `tradition_hill_dwellers`、沿海战士 `tradition_fp1_coastal_warriors`、"
  "乡土观念 `tradition_parochialism`、以剑之名 `tradition_by_the_sword`、说书人 `tradition_storytellers`。")
A("")
A("#### 三、备选新文化（本轮不建）与设计提议")
A("")
A("| key | 中文 | 来源 | 提议的 traditions | 理由 |")
A("|---|---|---|---|---|")
A("| `silesian` | 西里西亚 | 波兰 + 捷克 | hussar / xenophilic / mountaineer_ruralism / hard_working | "
  "波兰原版只有 hussar + xenophilic；补苏台德山地的「山地农田」与捷克的「勤劳」，贴合三方交界的矿区山地 |")
A("| `northumbrian` | 诺森伯兰 | 英格兰 + 诺斯 | chivalry / castle_keepers / longbow_competitions / stand_and_fight | "
  "去掉英格兰的 hereditary_hierarchy，保留边境城堡与长弓，加诺斯的「坚守阵地」体现丹麦法区血统 |")
A("| `anjou` | 安茹 | 法兰西 + 诺曼 | chanson_de_geste / hereditary_hierarchy / chivalry / ruling_caste | "
  "以法兰西三项为底，取诺曼的「统治阶层」对应安茹帝国跨海而治的贵族结构 |")
A("| `gallo` | 加洛 | 法兰西 + 布列塔尼 | chanson_de_geste / hereditary_hierarchy / chivalry / storytellers | "
  "以法兰西三项为底，取布列塔尼的「说书人」体现布列塔尼边疆的奥依语口传传统 |")
A("| `transylvanian` | 特兰西瓦尼亚 | 罗马尼亚 + 匈牙利 | pastoralists / zealous_people / xenophilic / mountaineer_ruralism | "
  "瓦拉几亚四项去 hussar（轻骑兵是匈牙利特征），换「山地农田」贴合喀尔巴阡山内盆地 |")
A("")
A("#### 四、不建清单与原因（用户定）")
A("")
A("| 文化 | 原因 |")
A("|---|---|")
A("| 格里科 | 人数过少、无省份；意大利将在下个 DLC 更新，谨慎行事 |")
A("| 阿尔卑坦 | 意大利 DLC 原因 |")
A("| 那不勒斯 | 意大利 DLC 原因 |")
A("| 罗曼什 | 意大利 DLC 原因 |")
A("| 达尔马提亚 | 规模过小 |")
A("| 阿罗马尼亚 | 人数实在过少 |")
A("| 马耳他 | 只有一个岛，太小 |")
A("| 喀山 | 和其他草原民族一并处理，不算欧洲事务 |")
A("| 罗姆 | 流浪者文化，无地且难以设计 |")
A("| 安茹 / 加洛 / 特兰西瓦尼亚 / 西里西亚 / 诺森伯兰 | 列为备选，本轮不建 |")
A("")
A("#### 五、可行性检验结论")
A("")
A("1. **罗姆人无人物**：CK3 原版 `common/culture/cultures/` 无 `romani` 定义；"
  "`history/characters/` 全库 `culture = romani|roma|gypsy` 计数为 **0**"
  "（正则只误撞到伏尔加芬兰语的 `muroma`）。故 `romani_culture` 无落点，标 cat11 占位，0 男爵领。")
A("2. **罗马有定义无人物**：CK3 原版 `roman` 在 `00_latin.txt` 有定义，但 `history/characters/` 里 "
  "**0 个角色**使用、原版 **0 个省份**。`roman_culture → roman` 可以落，"
  "但游戏里不会有历史角色自带该文化，也不会自动出现在地图上。")
A("3. **本地化让位**：CK3 `pommeranian`（显示「波美拉尼亚」）实为 EU5 卡舒比，"
  "新融合文化 `pomeranian` 也要「波美拉尼亚」→ 原 `pommeranian` 本地化需改为「卡舒比」。"
  "`prussian` 显示「普鲁赛尼亚」——波罗的普鲁士人（pruthenian 普鲁赛尼亚 / sudovian 苏多维亚 / "
  "curonian 库罗尼亚）还在地图上，不能作古；德意志那一支另用 `teutonic`，显示「普鲁士」。")
A("4. **traditions 上限**：`DEFAULT_MAX_TRADITIONS = 5` 只是开局值，随时代解锁会继续增加，"
  "所以盎格鲁-爱尔兰 6 个、诺斯-盖尔 6 个都不需要砍。")
A("5. **沿海战士属 DLC 内容**：`tradition_fp1_coastal_warriors` 定义在 `01_fp1_traditions.txt`，"
  "为 Fate of Iberia 的内容。mod 假定全 DLC 可用；若需照顾无 DLC 环境，可换 `tradition_seafaring`（航海家）。")
A("")

io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("写出", OUT)
print("文化 %d / 男爵领 %d" % (len(rows), tot_b))
