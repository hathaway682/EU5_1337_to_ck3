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

# —— 4.5 藏区 / 喜马拉雅 与 突厥语支 的细分 ——
# 这两块原先都是「一个语言规则吞掉整片」：藏语一律→bodpa、突厥语一律→cuman。
# 依据 CK3 原版 history/provinces/k_*.txt 里各王国的 culture 分布重新落点。
TIBET_BLOCK = ["utsang_culture", "khampa_culture", "changpa_culture", "amdowa_culture",
               "tebbu_culture", "ladakh_culture", "balti_culture", "ngalop_culture",
               "sikkim_culture", "monpa_culture", "newar_culture", "magar_culture",
               "gurung_culture", "tamang_culture", "limbu_culture", "sherpa_culture"]
TURKIC_BLOCK = ["kyrgyz_culture", "kazani", "uzbek_culture", "nogai", "astrakhani", "mishar"]
A("### 4.5 按 CK3 原版王国文化分布细分的两处（藏区 / 突厥语支）")
A("")
A("原先「藏语→bodpa」「突厥语→cuman」两条语言规则把整片语族并成一个文化。"
  "按 CK3 原版 `history/provinces/k_{u,tsang,kham,amdo,guge,gyalrong,lhomon,himalaya,maryul}.txt`"
  " 的实际 culture 分布重新落点：")
A("")
A("**藏区 / 喜马拉雅（16 个）**")
A("")
A("| 文化 | 男爵领 | 类别 | 目标 | 依据 |")
A("|---|---:|---:|---|---|")
_ix = {x["culture"]: x for x in rows}
for k in TIBET_BLOCK:
    x = _ix.get(k)
    if x:
        A("| %s | %s | %s | %s | %s |" % (nm(x), x["baronies"], x["category"], tg(x), x["note"][:60]))
A("")
A("**突厥语支（6 个，其余无 CK3 对应者仍留 cuman）**")
A("")
A("| 文化 | 男爵领 | 类别 | 目标 | 依据 |")
A("|---|---:|---:|---|---|")
for k in TURKIC_BLOCK:
    x = _ix.get(k)
    if x:
        A("| %s | %s | %s | %s | %s |" % (nm(x), x["baronies"], x["category"], tg(x), x["note"][:60]))
A("")

io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("写出", OUT)
print("文化 %d / 男爵领 %d" % (len(rows), tot_b))
