# -*- coding: utf-8 -*-
"""
修摄政周期（2026-10-23）。

问题：`history/characters/zz_eu5_diarchy_regencies.txt` 的 22 个块只有开始
（`try_start_diarchy = regency`），没有结束。CK3 的 regency 类型在
`common/diarchies/diarchy_types/00_regencies.txt` 里写的是

    start = { always = yes }
    end   = { always = no }

即**不会自动结束**，所以摄政会一直挂到游戏结束。EU5 侧每个国家都有
`start_regency_date` / `end_regency_date`，本脚本按它对齐：

  1. 起始日期改成 EU5 的 start_regency_date（原来 7 个与 EU5 不符：
     CHZ/COM/ETA/GOR/MGM/OKI/SCO）；
  2. 每个块末尾补一个 end_regency_date 块，`effect = { end_diarchy = yes }`。

默认 dry run，--apply 落盘。保持 BOM + CRLF。
"""
import os
import re
import sys

MOD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(MOD, "history", "characters", "zz_eu5_diarchy_regencies.txt")
APPLY = "--apply" in sys.argv

# holder -> (EU5 start_regency_date, EU5 end_regency_date)
DATA = {
    "alb_charles_durazzo": ("1336.4.5", "1341.1.1"),
    "ast_centule_iv_astarac": ("1331.1.1", "1339.1.1"),
    "auv_jeanne_auvergne": ("1332.8.6", "1344.5.8"),
    "chz_seii": ("1336.1.1", "1346.1.1"),
    "com_jean_comminges": ("1336.1.1", "1354.5.1"),
    "eta_louis_evreux": ("1336.9.5", "1354.1.1"),
    "gor_john_henry_iv_gorizia": ("1325.1.1", "1339.1.1"),
    "hhb_rudolf_iii_hohenberg_rotenburg": ("1336.1.11", "1348.1.1"),
    "jap_ashina_naomori": ("1335.9.4", "1341.1.1"),
    "jap_koumyou_tenno": ("1336.9.20", "1341.1.11"),
    "jap_mogami_kaneyori": ("1329.1.1", "1347.1.1"),
    "jap_mori_motoharu": ("1337.1.1", "1341.1.1"),
    "jap_oosaki_tadamochi": ("1327.1.1", "1345.1.1"),
    "jap_oyama_tomosato": ("1335.8.2", "1343.1.1"),
    "jap_suwa_yoritsugu": ("1335.9.6", "1346.1.1"),
    "jap_yuuki_naotomo": ("1336.5.30", "1343.1.1"),
    "ksh_haidar_khan_lohara": ("1323.1.1", "1338.1.1"),
    "leu_ulrich_ii_leuchtenberg": ("1334.1.1", "1346.1.1"),
    "rso_andrei_fedorovich_rostovsky_rurikovich": ("1331.1.1", "1346.1.1"),
    "sco_david_ii": ("1333.5.14", "1340.3.5"),
    "dan_valdemar_atterdag": ("1332.8.2", "1400.1.1"),
}

TOP = re.compile(r"^([a-z0-9_]+) = \{$")
DATE_LINE = re.compile(r"^\t(\d+\.\d+\.\d+) = \{$")


def main():
    with open(P, "rb") as f:
        text = f.read().decode("utf-8-sig")
    lines = text.split("\r\n")

    out = []
    i = 0
    stats = []
    while i < len(lines):
        m = TOP.match(lines[i])
        if not m or m.group(1) not in DATA:
            out.append(lines[i])
            i += 1
            continue

        holder = m.group(1)
        start, end = DATA[holder]
        # 收集整块到顶层的 "}"
        j = i + 1
        while j < len(lines) and lines[j] != "}":
            j += 1
        block = lines[i:j + 1]

        old = None
        for k, ln in enumerate(block):
            dm = DATE_LINE.match(ln)
            if dm:
                old = dm.group(1)
                block[k] = "\t%s = {" % start
                break

        # 已有结束块就不重复加
        has_end = any("end_diarchy" in ln for ln in block)
        if not has_end:
            block = block[:-1] + [
                "\t%s = {" % end,
                "\t\teffect = {",
                "\t\t\tend_diarchy = yes",
                "\t\t}",
                "\t}",
                "}",
            ]

        out.extend(block)
        stats.append((holder, old, start, end, has_end))
        i = j + 1

    for holder, old, start, end, had in stats:
        flag = "  (已有 end)" if had else ""
        mark = "" if old == start else "  <- start 改"
        print(f"{holder:44} {old} -> {start}   end={end}{mark}{flag}")

    print()
    print(f"块数 {len(stats)}，start 改动 {sum(1 for s in stats if s[1] != s[2])}，补 end {sum(1 for s in stats if not s[4])}")

    if APPLY:
        with open(P, "wb") as f:
            f.write(b"\xef\xbb\xbf" + "\r\n".join(out).encode("utf-8"))
        print("written:", P)


if __name__ == "__main__":
    main()
