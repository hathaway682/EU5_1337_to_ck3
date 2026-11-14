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
BAKDIR = r"F:\EU5_Modern_Borders_bak\20261114_holysite_word"

# 圣地 key -> 目标男爵领
MAP = {
    "sinai": "b_saint_katrine",
    "bahrein": "b_manama",
    "lalish": "b_sinjar",
    "sufed": "b_safed",
    "ctesiphon": "b_dayr_aqul",       # 泰西封 → 代尔阿库勒（原版泰西封/王宫遗址在 b_an-nahrawan，mod 无该男爵领；避让巴格达智慧谷建筑，用户定 2026-11-14）
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
    "kathmandu": "b_kathmandu",
    "kanchipuram": "b_kanchipuram",
    "ujjayini": "b_ujjain",
    "angkor": "b_angkor",
    "bayon": "b_angkor",
    "bantey_srei": "b_angkor",
    "kochi": "b_kochi",
    "manipur": "b_imphal",
    "sanchi": "b_bhilsa",             # 桑吉大塔 → 比尔沙（Bhilsa 即 Vidisha 旧称，紧邻桑吉；用户手改 2026-11-14，原 b_bhopal 博帕尔）
    "udabhanda": "b_udabhanda",       # 乌达班达=洪德（印度沙希故都）；mod 有同名男爵领 b_udabhanda（c_kashmir），同一个词。2026-11-14 改（原 b_attock）
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
    # 河流：照 CK 原版 b_changjiang(c_yuezhou_1) / b_ob(c_ob) 的落点
    "yangtze": "b_baling",            # 长江 → 岳州巴陵
    "ob": "b_ob",                     # 鄂毕 → b_ob（c_obdorsk）
    "taebaek": "b_gapsan",            # 太白山 → 甲山（用户查 EU5 地图定，2026-11-14；原 c_gangneung/b_samcheok 三陟）
    "mani": "b_inju",                 # 摩尼山 → 仁州（江华岛旧称仁州，c_kaesong 同县；原 b_kaesong 开城）
    "dvin": "b_khor_virap",           # 德温 → 霍尔维拉普（用户查 EU5，2026-11-14；原 b_yerevan 埃里温）
    "shikharj": "b_katrasgarh",       # 尸佉罗时（Shikharji 耆那教圣地）→ 卡特拉斯加尔（EU5 shikharji location=katrasgarh；原 c_pandua/b_baragram 潘杜阿）
    # 全量对照 CK3 原版圣地表后采纳的 3 条（原版目标在 mod 存在且判定更贴）
    "adur_farnbag": "b_kariyan",      # 阿杜尔·法伦巴格圣火 → 卡里扬（县本已是 c_kariyan，男爵领从洪杰换回卡里扬）
    "badd": "b_ahar",                 # 巴德（巴巴克城堡，阿拉斯巴兰）→ 阿哈尔，县随之 c_tabriz→c_ardabil
    "hitakami": "b_isawa",            # 日高见/北上川 → 胆泽（奥州胆泽郡，县同为 c_rikuchuu）
    # 行尾注释盘点后采纳的 2 条
    # 无中文本地化那批（原版 simp_chinese 缺 holy_site_<key>_name，名字匹配从没覆盖过）
    # 用户拍板（2026-10-23）：取最近的可用男爵领
    # EU5 圣地 location 核对（2026-11-14）：EU5 common/holy_sites/ 直接标了 location，可精确到地块
    "wutai": "b_jianzhou_daizhou",    # 五台山 → 代州坚州（EU5 mount_wutai location=jianzhou_daizhou；原 b_daizhou 代州治）
    "haridwar": "b_gangadvara",       # 哈立德瓦尔 → 恒河门（EU5 haridwar_kumbh_mela location=gangadvara，Haridwar=恒河之门；原 c_puadh/b_thanesar 坦内萨尔）
    # 2026-11-14 第二轮「同一个词 / 一城异名」普查（用户批准 10 条一起改）
    "ellora": "b_daulatabad",         # 埃洛拉石窟 → 道拉塔巴德（=德瓦吉里）。原版 c_devagiri 下即 b_elapura+b_jalna，mod 的 b_jalna 在 c_upper_marathwada，两县对应；原 c_lower_vidarbha/b_mahagaon 在 Vidarbha，错 250 km
    "khao_khlang_nai": "b_sri_thep",  # 考克朗奈是西贴古城内的建筑，原版就在 b_sri_thep；mod 有 b_sri_thep（西贴）自成一县
    "ranakpur": "b_pali",             # 罗拿迦补罗在帕利县境内（原版挂 c_naddula=纳多尔，同在帕利县）；原 b_kurki
    "ranaheim": "b_nidaros",          # 拉纳海姆=Ranheim，特隆赫姆东郊；尼达罗斯=特隆赫姆旧称（一城异名）；原 b_orkdal 奥克达尔
    "mizdahqan": "b_xojeli",          # 米兹达赫甘粟特墓地在火者里（Xojeli）城边 4 km；原 b_shimbay 希姆拜
    "takht-e_soleyman": "b_takht_e_soleyman",  # 同一个词：mod 有 b_takht_e_soleyman（所罗门王座，c_barza，含布坎/米扬多阿布）；原 c_urmia/b_urmia
    "gyaitang": "b_dadandang",        # 建塘=中甸（香格里拉）藏语名，元代汉文作旦当/大旦当；mod 同县有 b_dadandang（大旦当）；原 b_nixi 泥西
    "kilimanjaro": "b_moshi",         # 莫希在乞力马扎罗南麓；原版 c_kilimanjaro 另一 barony 是 b_kwa_mgogo（莫希乡下），即该县落莫希一带；原 c_upper_pangani/b_usangi
    "gangganegara": "b_beruas",       # 刚迦尼国遗址一般定在木威（Beruas）；原 b_manjung 曼绒（曼绒是县、木威是镇）
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
    # 备份按约定放归档盘（项目目录内不得残留 bak）
    bakdir = os.path.join(BAKDIR, "common", "religion", "holy_site_types")
    if not os.path.isdir(bakdir):
        os.makedirs(bakdir)
    bak = os.path.join(bakdir, "00_holy_site_types.txt.bak_" + ts)
    shutil.copy2(SRC, bak)
    io.open(SRC, "wb").write(b"\xef\xbb\xbf" + new.encode("utf-8"))
    print("\nAPPLIED %d 处。备份：%s" % (len(plan), bak))
    print("braces: %d %d" % (new.count("{"), new.count("}")))


if __name__ == "__main__":
    main()
