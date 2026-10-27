# -*- coding: utf-8 -*-
"""按人工知识映射（异名同地）修圣地位置：只改圣地块的 county= / barony= 指向。

映射来源：2026-10-23 盘点，用户确认「迦太基=突尼斯、汴梁=开封」这类异名同地也算。
默认 dry-run，--apply 才写（先备份，保 BOM + 纯 CRLF）。
"""
import io, os, re, shutil, sys, time

MOD = r"D:\Documents\Paradox Interactive\Crusader Kings III\mod\EU5_Modern_Borders_noshape"
SRC = os.path.join(MOD, "common", "religion", "holy_site_types", "00_holy_site_types.txt")
LT = os.path.join(MOD, "common", "landed_titles", "00_landed_titles.txt")
APPLY = "--apply" in sys.argv
BLOCK = re.compile(r"([A-Za-z0-9_\-]+)\s*=\s*\{")

# 圣地 key -> 目标男爵领
MAP = {
    "sinai": "b_saint_katrine",
    "bahrein": "b_manama",
    "lalish": "b_sinjar",
    "sufed": "b_safed",
    "ctesiphon": "b_baghdad",
    "mount_damavand": "b_damavand",
    "xingqing": "b_ningxia",
    "jorvik": "b_york",
    "poszony": "b_bratislava",
    "harar": "b_harar",
    "mogadishu": "b_mogadishu",
    "mount_qiyung": "b_xiuning",
    "dali": "b_taihe_dali",
    "bianliang": "b_kaifeng",
    "sonba_i": "b_sombai",
    "nanning": "b_xuanhua_nanning",
    "zunyi": "b_bozhou",
    "vaishali": "b_weithali",
    "tiantai": "b_tiantai",
    "kathmandu": "b_kathmandu",
    "kanchipuram": "b_kanchipuram",
    "ujjayini": "b_ujjain",
    "angkor": "b_angkor",
    "bayon": "b_angkor",
    "bantey_srei": "b_angkor",
    "kochi": "b_kochi",
    "manipur": "b_imphal",
    "sanchi": "b_bhopal",
    "udabhanda": "b_attock",
    "chang_an": "b_jingzhao",
    # 点状地物（山/寺/城址）：按元代县、日本郡判定落点
    "mount_tai": "b_fengfu",          # 泰山 → 泰安州奉符县
    "mount_heng": "b_hunyuan",        # 北岳恒山 → 浑源州
    "dunhuang": "b_shazhou",          # 敦煌 → 沙州路
    "mount_qiyung": "b_xiuning",      # 齐云山 → 徽州路休宁县
    "sikong": "b_qianshan",           # 司空山 → 安庆路潜山县
    "ise_jingu": "b_watarai",         # 伊势神宫 → 伊势国度会郡
    # 异名同地（别名/古称/外语名）
    "ragusa": "b_dubrovnik",          # 拉古萨 = 杜布罗夫尼克
    "palitana": "b_palitana",         # 波利多拿 = 巴利塔纳
    "zhaotong": "b_wumeng",           # 昭通 = 乌蒙
    "bupaya": "b_pagan",              # 卜帕耶佛塔 → 蒲甘
    "atamasthana": "b_anuradhapura",  # 阿吒摩萨傥那（八圣地）→ 阿努拉德普勒
    "itil": "b_astrakhan",            # 阿得（Itil）→ 阿斯特拉罕
    "rebgong": "b_tongren",           # 捏工（热贡）→ 同仁
    "muze": "b_mengzi",               # 目则 → 蒙自
    "kutai": "b_kutai_lama",          # 库泰 → 库泰喇嘛（东加里曼丹）
    "iona": "b_mull",                 # 艾奥纳 → b_mull（CK 原版名「艾奥纳」，内赫布里底）
    # 河流：照 CK 原版 b_changjiang(c_yuezhou_1) / b_ob(c_ob) 的落点
    "yangtze": "b_baling",            # 长江 → 岳州巴陵
    "ob": "b_ob",                     # 鄂毕 → b_ob（c_obdorsk）
    "taebaek": "b_samcheok",          # 太白山主峰在太白市（原三陟郡）→ c_gangneung/b_samcheok
    # 全量对照 CK3 原版圣地表后采纳的 3 条（原版目标在 mod 存在且判定更贴）
    "adur_farnbag": "b_kariyan",      # 阿杜尔·法伦巴格圣火 → 卡里扬（县本已是 c_kariyan，男爵领从洪杰换回卡里扬）
    "badd": "b_ahar",                 # 巴德（巴巴克城堡，阿拉斯巴兰）→ 阿哈尔，县随之 c_tabriz→c_ardabil
    "hitakami": "b_isawa",            # 日高见/北上川 → 胆泽（奥州胆泽郡，县同为 c_rikuchuu）
    # 行尾注释盘点后采纳的 2 条
    "emei": "b_emei",                 # 峨眉山 → 嘉定府峨眉（原 c_rongzhou 融州，广西融水；本块原无 barony 行，需插入）
    "bumiayu": "b_bumi_ayu",          # 南苏门答腊 Candi Bumiayu → 布米阿尤（c_ogan 奥甘，原 b_musi 上穆西）
    # 无中文本地化那批（原版 simp_chinese 缺 holy_site_<key>_name，名字匹配从没覆盖过）
    "armagh": "b_armagh",             # 阿马 → 阿马（原 b_dundalk 邓多克，同县 c_oriel）
    "yamama": "b_al_yamamah",         # 耶马迈 → 耶马迈（原 b_ad_dilam 迪勒姆，同县 c_yamama）
    "badrinath": "b_badrinath",       # 伯德里纳特 → 伯德里纳特（原 b_uttarkashi 北加希，同县 c_garhwal）
    "shringeri": "b_sringeri",        # 斯灵盖里 → 斯灵盖里（原 b_basavapattana，同县 c_banavasi）
    "sparta": "b_mystras",            # 斯巴达 → 米斯特拉斯（原 b_kythira 基西拉岛，同县 c_laconia）
    "suzhou": "b_wuxian",             # 苏州 → 吴县（苏州城；原 b_changshu 常熟。注意 b_suzhou 是四川黎州）
    "hangzhou": "b_hangzhou",         # 杭州 → 杭州（原 b_fuyang_hangzhou 富阳，同县 c_hangzhou）
    "jiuhua": "b_qingyang",           # 九华山 → 池州青阳（mod 译作「庆阳」；原 b_dongliu 东流，同县 c_chizhou）
    "bulguksa": "b_gyeongju",         # 佛国寺 → 庆州（原 b_boseongbu 宝城府，同县 c_gyeongju）
    "putuo": "b_changguo",            # 普陀山 → 昌国州（舟山，元属庆元路；原 b_baling 巴陵，岳阳，完全错）
    "nanhua": "b_qujiang",            # 南华寺 → 韶州曲江（c_shaozhou 中文名误作「邵州」；原 b_jiyin 济阴，山东，完全错）
    "tate": "b_niikawa",              # 立山 → 越中新川郡（原 b_tsukama 筑摩，信浓，错）
    "jianchang": "b_nancheng",        # 建昌府 → 南城（原 b_jingchuan 泾川，甘肃，完全错）
    "zhuolu": "b_baoan_baoan",        # 涿鹿 → 保安州（元涿鹿属保安州；原 b_baideng 白登，大同，错）
    "quzhou": "b_xian_quzhou",        # 衢州 → 衢州西安县（原 b_liujiang 流江，四川广安，完全错）
    "dongting": "b_baling",           # 洞庭湖 → 岳州巴陵（原 b_langzhong 阆中，四川，完全错）
    "mogao": "b_shazhou",             # 莫高窟 → 沙州敦煌（原 b_anding_suzhou 安定，同县 c_shazhou）
    "heiankyo": "b_kyoto",            # 平安京 → 京都（原 b_kuse 久世，同县 c_yamashiro）
    "mount_kunyu": "b_wendeng",       # 昆嵛山 → 宁海州文登（原 b_penglai 蓬莱，登州，隔了一座山）
    # 用户拍板（2026-10-23）：取最近的可用男爵领
    "hiei": "b_kurita",               # 比叡山 → 近江栗太郡（草津，紧邻滋贺郡；原 b_takashima 高岛在近江最北）
    "linzi": "b_zichuan",             # 临淄 → 青州淄川（淄博；原 b_yidu_qingzhou 益都偏东）
}


def read(p):
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


def walk(s, path=()):
    i, n = 0, len(s)
    while i < n:
        m = BLOCK.search(s, i)
        if not m:
            return
        j, d = m.end(), 1
        while j < n and d:
            if s[j] == "{":
                d += 1
            elif s[j] == "}":
                d -= 1
            j += 1
        body = s[m.end():j - 1]
        yield path, m.group(1), body
        yield from walk(body, path + (m.group(1),))
        i = j


def main():
    lt = read(LT)
    bar2c = {}
    for path, key, body in walk(lt):
        if not key.startswith("b_"):
            continue
        c = next((x for x in reversed(path) if x.startswith("c_")), None)
        if c:
            bar2c[key] = c

    raw = io.open(SRC, "rb").read()
    lines = raw.decode("utf-8-sig").split("\r\n")

    # 定位每个顶层块的行号
    idx, depth, cur = {}, 0, None
    for i, ln in enumerate(lines):
        m = re.match(r"^([A-Za-z0-9_\-]+)\s*=\s*\{", ln)
        if depth == 0 and m:
            cur = m.group(1)
            idx[cur] = {"c": None, "b": None}
        if depth == 1 and cur:
            mc = re.match(r"^\s*county\s*=\s*(\S+)", ln)
            mb = re.match(r"^\s*barony\s*=\s*(\S+)", ln)
            if mc:
                idx[cur]["c"] = (i, mc.group(1))
            if mb:
                idx[cur]["b"] = (i, mb.group(1))
        depth += ln.count("{") - ln.count("}")

    plan, miss = [], []
    for key, tb in MAP.items():
        if key not in idx:
            miss.append((key, "圣地块不存在"))
            continue
        if tb not in bar2c:
            miss.append((key, "目标 barony 不存在: " + tb))
            continue
        blk = idx[key]
        if not blk["b"]:
            # 本块没有 barony 行（如 emei 只有 county）：在 county 行后插入一行
            if not blk["c"]:
                miss.append((key, "无 county/barony 行"))
                continue
            plan.append({"key": key, "li_b": None, "old_b": None,
                         "new_b": tb, "li_c": blk["c"][0],
                         "old_c": blk["c"][1], "new_c": bar2c[tb],
                         "ins_after": blk["c"][0]})
            continue
        plan.append({"key": key, "li_b": blk["b"][0], "old_b": blk["b"][1],
                     "new_b": tb, "li_c": blk["c"][0] if blk["c"] else None,
                     "old_c": blk["c"][1] if blk["c"] else None, "new_c": bar2c[tb],
                     "ins_after": None})

    print("计划 %d 处（其中插入 barony 行 %d 处）；异常 %d"
          % (len(plan), sum(1 for p in plan if p["ins_after"] is not None), len(miss)))
    for p in plan:
        tag = " +插入barony行" if p["ins_after"] is not None else ""
        print("  %-22s %s(%s) -> %s(%s)%s"
              % (p["key"], p["old_b"], p["old_c"], p["new_b"], p["new_c"], tag))
    for k, r in miss:
        print("  !! %-22s %s" % (k, r))

    if not APPLY:
        print("\n[dry-run] 未写文件。")
        return
    if not plan:
        print("无改动。")
        return

    for p in plan:
        if p["li_c"] is not None:
            lines[p["li_c"]] = re.sub(r"(county\s*=\s*)\S+", r"\g<1>" + p["new_c"], lines[p["li_c"]])
        if p["li_b"] is not None:
            lines[p["li_b"]] = re.sub(r"(barony\s*=\s*)\S+", r"\g<1>" + p["new_b"], lines[p["li_b"]])
    # 插入行必须倒序，否则前面的插入会让后面的行号错位
    for p in sorted([x for x in plan if x["ins_after"] is not None],
                    key=lambda x: -x["ins_after"]):
        lines.insert(p["ins_after"] + 1, "\tbarony = " + p["new_b"])

    new = "\r\n".join(lines)
    ts = time.strftime("%Y%m%d_%H%M%S")
    bak = SRC + ".bak_holysite_knowledge_" + ts
    shutil.copy2(SRC, bak)
    io.open(SRC, "wb").write(b"\xef\xbb\xbf" + new.encode("utf-8"))
    print("\nAPPLIED %d 处。备份：%s" % (len(plan), bak))
    print("braces: %d %d" % (new.count("{"), new.count("}")))


if __name__ == "__main__":
    main()
