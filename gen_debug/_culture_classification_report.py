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
_tbl("钦察语（15 个：伏尔加系→bolghar，黑海—里海系→cuman，其余→kipchak）", KIPCHAK_BLOCK)
_tbl("柏柏尔（12 个：马格里布/撒哈拉→butr，摩洛哥→baranis，加那利→guanches）", BERBER_BLOCK)
_tbl("罗斯 / 普鲁士（4 个：ilmenian 原版 0 省份不可用，诺夫哥罗德归罗斯；EU5 德意志普鲁士入萨克森）", RUS_BLOCK)
_tbl("苏丹-阿拉伯（1 个：入贝都因）", SUDAN_BLOCK)

# ============ 4.6 欧洲与融合文化落实方案 ============
A("### 4.6 文化落地（2026-10-22 定稿：CK3 原版地图内全部并入已有文化）")
A("")
A("**已落游戏（2026-10-22）**：范围是 **CK3 原版地图内的全部文化（cat1-cat9）**，"
  "共 781 个文化 / 14170 男爵领，其中 **686 条映射**把 EU5 文化并入 CK3 已有文化，"
  "省份改写 11728 行、人物层（角色 + 宗族 + 支系）16879 行。"
  "一个新建文化都没有，`zz_eu5_culture_merge.txt` 只剩 `prussian` 一个波罗的覆盖块。")
A("")
A("**范围**：cat1-cat9 = CK3 原版地图内，全部落地；"
  "cat10（图外可参考，351 个 / 1560 省）与 cat11（图外自创，956 个 / 5316 省）"
  "的 target 都是 `NEW:`，保持 EU5 key 不动，其定义本来就在 `00_generated_cultures.txt` 里。"
  "cat9 从 66 个降到 **35 个 / 154 省**，剩下的全在非洲（33 个），"
  "另有 2 个是 `domari` / `lomari`（罗姆两支，0 省，无地可落）。")
A("")
A("**方案为什么改**：CK3 新版官方将加入 `norse_gael`、`arpitan` 等文化，"
  "自建同名文化会与官方撞车。所以原计划的 5 个新文化全部取消，"
  "17 个 cat8 融合文化也一并改为并入已有文化。")
A("")
A("#### 一、取消的 5 个新文化及其落点")
A("")
A("| 原 key | 中文 | 类型 | 省份 | 落点 | 依据 |")
A("|---|---|---|---:|---|---|")
CANCELLED = [
    (["anglo_irish"], "盎格鲁-爱尔兰", "融合", "english", "爱尔兰的英格兰移民后裔；新版官方将加入同名文化"),
    (["norse_gael"], "诺斯-盖尔", "融合", "gaelic", "1337 群岛领主已盖尔化；新版官方将加入同名文化"),
    (["western_pomeranian", "eastern_pomeranian"], "波美拉尼亚", "融合", "saxon", "低地德语的德意志化人口，与卡舒比不同族"),
    (["walloon"], "瓦隆", "融合", "french", "瓦隆语属奥依语；新版官方将加入同名文化"),
    (["prussian"], "普鲁士（德意志）", "分离", "saxon", "低地德语，与波罗的普鲁士人同名异族"),
]
for _ks, _zh, _ty, _to, _why in CANCELLED:
    _b = sum(int(_ix[x]["baronies"]) for x in _ks if x in _ix)
    A("| `%s` | %s | %s | %d | `%s` | %s |" % (" / ".join(_ks), _zh, _ty, _b, _to, _why))
A("")
A("`prussian` 这个 key 本身保留，但只装波罗的普鲁士人"
  "（pruthenian 15 + sudovian 9 + curonian 6 = 30 省），"
  "定义在 `zz_eu5_culture_merge.txt` 里覆盖回 `heritage_baltic` / `language_baltic`。"
  "EU5 的德意志普鲁士（11 省）已并入 `saxon`。")
A("")
A("#### 二、17 个融合文化（cat8）改为并入")
A("")
A("| 文化 | 男爵领 | 洲 | 落点 | 依据 |")
A("|---|---:|---|---|---|")
MERGED = ["anglo_irish", "norse_gael", "western_pomeranian", "eastern_pomeranian", "walloon",
          "kazani", "mishar", "crimean", "astrakhani", "nogai",
          "turkish_culture", "azeri_culture", "gyalrong_culture",
          "algerian", "moroccan", "tunisian", "sudanese_arab"]
for _k in MERGED:
    _x = _ix.get(_k)
    if _x:
        A("| %s | %s | %s | %s | %s |" % (nm(_x), _x["baronies"], _x["continent"], tg(_x), _x["note"][:52]))
A("")
A("草原按 EU5 的草原族群文化组（`steppe_group`）分东西支（用户 2026-10-22 定）："
  "**带 `steppe_group` 的 → `cuman`（库曼，西支）** —— 阿斯特拉罕 70 / 克里米亚 108 / 诺盖 73；"
  "**不带的 → `kipchak`（钦察，东支）** —— 乌兹别克 122 / 库梅克 5 / 巴尔卡尔 3 / 卡拉恰伊 3 / "
  "帖良古惕 11 / 铁列乌特 9 / 叶尔喀勒 38。"
  "`kipchak_language` 里带草原组的只有这 5 个（另有喀山 41、米萨 32）。")
A("")
A("**能独立的一律保留**（用户：「能自己独立的还是保留」）—— CK3 `00_turkic.txt` 里已有独立文化的，"
  "不并入上面两支：`bashkir` 25 省、`bolghar` 110 省（喀山 + 米萨，伏尔加保加尔）、"
  "`chuvash` 8 省、`uyghur` 32 省、`kirghiz` 26 省（黠戛斯，原版有，原先错并进 kipchak 已改回）、"
  "`cuman` 3 省（库曼本体，匈牙利）。不落 `kazakh`：1337 年还没有哈萨克汗国，那是 15 世纪的事。")
A("")
A("马札尔另有一条：`chiyalik_culture`（奇亚利克，马札尔文化组仅存文化，40 省）→ `mogyer`（马扎尔），"
  "不是 `hungarian`。CK3 里 `mogyer` 是 `hungarian` 的父文化（`00_magyar.txt`："
  "`hungarian.created = 1000.1.1`、`parents = { mogyer }`），比匈牙利更早。")
A("")
A("三条按本地化改名：`turkish_culture`（土耳其）→ `turkmen`（土库曼）、"
  "`azeri_culture`（阿塞拜疆）→ `turkish`（乌古斯）、`gyalrong_culture`（嘉绒）→ `qiang`（羌）。"
  "CK3 的 `turkish` 显示名是「乌古斯」不是「土耳其」，判名一律以本地化为准。")
A("")
A("#### 三、亚洲按语族并入（2026-10-22 用户定：按 eu5_language 语族整体落）")
A("")
A("口径：CK3 原版地图内的亚洲 cat9 文化，一律按 EU5 的 `eu5_language`（语族）"
  "整体并入 CK3 已有文化，不建新文化。落点全部取自 CK3 原版 `00_*.txt`，多数是 0 省的空文化。"
  "**37 个 / 306 省，现已全部落地。**")
A("")
A("| 语族（eu5_language） | 个数 | 省份 | 落点 | 依据 |")
A("|---|---:|---:|---|---|")
ASIA = [
    ("`evenk_language`（通古斯）", 2, 72, "`jurchen`", "鄂温克 / 鄂伦春主体在满洲，属女真组（用户定）"),
    ("`evenk_language`（通古斯）", 11, 99, "`mohe`", "西西伯利亚通古斯诸族，非女真组（用户定）"),
    ("`meitei_language`（藏缅）", 6, 46, "`lhomon`", "CK3 lhomon 原版注释直接含 Lhoba / Mishmi，正对珞巴与僜"),
    ("`turkic_language`（突厥）", 6, 37, "`uriankhai`", "CK3 uriankhai 原版注释点名 Khakas 与 Tuvans"),
    ("`circassian_language`（西北高加索）", 3, 20, "`alan`", "CK3 缺西北高加索文化，按地理贴北高加索（用户定）"),
    ("`dagestanian_language`（东北高加索）", 5, 19, "`alan`", "同上（用户定）"),
    ("`georgian_language`（卡特维尔）", 3, 12, "`georgian`", "拉兹 / 斯万 / 明格列尔同属卡特维尔语系"),
    ("`shan_dialect`（掸语支）", 1, 1, "`tai`", "傣隆，入 CK3 tai（傣）"),
]
for _lang, _n, _b, _to, _why in ASIA:
    A("| %s | %d | %d | %s | %s |" % (_lang, _n, _b, _to, _why))
A("")
A("两条是 CK3 原版注释直接点名的，不必猜：")
A("")
A("- **`uriankhai`（兀良孩）** 的定义里写着「these are western \"Uriankhai\", in this case "
  "**specifically the Khakas and the Tuvans**」—— 原版设计来装的就是哈卡斯与图瓦，"
  "正好覆盖 `turkic_language` 那 6 个南西伯利亚突厥（哈卡斯 16 / 图瓦 10 / 切尔坎 5 / "
  "图巴拉尔 3 / 绍尔 2 / 库曼丁 1）。这个文化此前 0 省。")
A("- **`lhomon`（珞门）** 的定义里写着「Lhomon (**Monpa; Lhoba; Kho-Bwa; Mishmi**; Memba; etc.)」"
  "—— 直接含珞巴（`tani`）与僜（`mishmi`）；佐 / 那加 / 米基尔 / 梅泰同属东北印度藏缅山地，"
  "CK3 无更细落点，一并入珞门。")
A("")
A("**通古斯为什么拆两支**：CK3 通古斯只有 `jurchen` 与 `mohe` 两个文化。"
  "鄂温克（65 省，38 省在满洲）、鄂伦春（7 省全在满洲）是女真组，落 `jurchen`（并入后 228 省）；"
  "其余 11 个西西伯利亚通古斯小族（瑟姆、奥布金茨、希利亚吉尔、瓦尔加盖茨、谢洛贡、"
  "切姆达尔、纳纳吉尔、乌恰米、锡尼格尔、纽里尔茨、孔多吉尔）落 `mohe`（并入后 99 省）。"
  "`mohe` 并入前是 0 省的空文化。")
A("")
A("**高加索为什么都进 `alan`**：CK3 的 `heritage_caucasian` 只有 `georgian` 与 `armenian` 两个文化，"
  "西北高加索（切尔克斯 / 阿布哈兹 / 阿巴扎）与东北高加索（列兹金 / 纳赫 / 阿瓦尔 / 达尔金 / 拉克）"
  "在原版没有任何对应文化。用户定：这两组按地理贴北高加索的 `alan`（阿兰，并入 39 省后共 43 省），"
  "只有卡特维尔语系的拉兹 / 斯万 / 明格列尔按语族入 `georgian`。")
A("")
A("注意 `avar_culture`（高加索阿瓦尔，东北高加索语）与 CK3 的 `avar`（潘诺尼亚阿瓦尔，突厥/乌古尔语）"
  "是**同名异族**，`SAME_NAME_DIFF` 里已拦住自动同名，本轮显式落 `alan`。")
A("")
A("落地结果：省份 306 行 / 37 组，人物层（角色 + 宗族 + 支系）421 行。"
  "落点省份数：`jurchen` 228、`mohe` 99、`tai` 80、`lhomon` 64、`georgian` 52、`alan` 43、`uriankhai` 37。"
  "37 个旧 key 在省份层残留为 0。")
A("")
A("#### 四、欧洲其他落点（2026-10-21 决定，本轮未变）")
A("")
A("| 文化 | 男爵领 | 原落点 | 现落点 | 依据 |")
A("|---|---:|---|---|---|")
EU_CHANGES = [
    ("gallo", "4 法兰西", "7 布列塔尼"),
    ("angevin", "4 法兰西", "4 法兰西"),
    ("arpitan", "4 奥克", "4 奥克"),
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
    ("ingrian", "4 芬兰", "4 卡累利阿"),
    ("besermyan", "4 芬兰", "6 彼尔姆"),
    ("romani_culture", "9 罗姆", "11 罗姆（不建）"),
]
for _k, _old, _new in EU_CHANGES:
    _x = _ix.get(_k)
    if _x:
        A("| %s | %s | %s | %s | %s |" % (nm(_x), _x["baronies"], _old, tg(_x), _x["note"][:54]))
A("")
A("语言规则层同步修正：`francique_dialect` 由法兰克尼亚改为法兰西"
  "（EU5 的 francique 实为奥依语支，语言柱误挂 `language_high_german`）；"
  "`lombard_dialect` 由伦巴第改为山南；`maltese_dialect` 由马耳他改为西西里。")
A("")
A("#### 五、不建清单（用户定）")
A("")
A("| 文化 | 原因 |")
A("|---|---|")
A("| 盎格鲁-爱尔兰 / 诺斯-盖尔 / 瓦隆 | **新版官方将加入，自建会撞车** |")
A("| 格里科 | 人数过少、无省份；意大利将在下个 DLC 更新，谨慎行事 |")
A("| 阿尔卑坦 / 那不勒斯 / 罗曼什 | 意大利 DLC 原因（本轮并入奥克 / 西西里 / 山南） |")
A("| 达尔马提亚 | 规模过小 |")
A("| 阿罗马尼亚 | 人数实在过少 |")
A("| 马耳他 | 只有一个岛，太小 |")
A("| 罗姆 | 流浪者文化，无地且难以设计 |")
A("| 安茹 / 西里西亚 / 诺森伯兰 / 特兰西瓦尼亚 | 列为备选，本轮不建 |")
A("")
A("#### 六、落地结果与检验")
A("")
A("| 层 | 引用总数 | 不同 key |")
A("|---|---:|---:|")
A("| 省份 `history/provinces/00_generated_provinces.txt` | 21046 | 1508 |")
A("| 角色 `history/characters/*.txt` | 29766 | 925 |")
A("| 宗族 `common/dynasties/*.txt` | 4118 | 799 |")
A("| 支系 `common/dynasty_houses/*.txt` | 168 | 21 |")
A("")
A("1. **死 key 0**：四层合计 55098 处引用（不含注释行），并集（mod 1920 个定义 + CK3 原版 244 个）"
  "2140 个文化，全部有定义。cat1-cat7 里除了刻意保留的 `prussian` 30 省，"
  "没有任何一条 `target != 自身` 的映射被漏掉。")
A("2. **旧新文化清零**：`anglo_irish` / `norse_gael` / `walloon` / `pomeranian` / "
  "`teutonic` / `anatolian_turkish` / `kazakh` / `sudanese_arab` / `gyalrong` "
  "在四层里引用全部为 0；对应 `history/cultures/*.txt` 三个孤儿文件已删。")
A("3. **本地化**：`pommeranian` 改「卡舒比」（原版这个 key 装的就是 EU5 卡舒比人，"
  "名字仍对得上）；`prussian` 显示「普鲁赛尼亚」（波罗的普鲁士人还在地图上，不能作古）。")
A("4. **罗马皇帝**：EU5 `roman_culture`（中文「拉丁」）→ CK3 `roman`（罗马）。"
  "CK3 原版 `roman` 有定义但 0 个原生角色，mod 里那 62 个 `byz_*` 罗马皇帝"
  "（卡利古拉、尼禄、图拉真…）就是 `roman_culture` 改过来的。")
A("5. **`kazani` 定义成了孤儿**：`00_generated_cultures.txt` 里还留着 1 个块，"
  "但引用已归零（全部并入 `bolghar`）。留着无害，删不删待定。")
A("")

io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("写出", OUT)
print("文化 %d / 男爵领 %d" % (len(rows), tot_b))
