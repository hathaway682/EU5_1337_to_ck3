# -*- coding: utf-8 -*-
import io, re, os
EU5 = r"D:\Program Files (x86)\Steam\steamapps\common\Europa Universalis V\game"
locdir = os.path.join(EU5, "main_menu", "localization", "simp_chinese")
rx = re.compile(r'^\s*([A-Za-z0-9_.]+):\s*"([^"]*)"\s*$')
d = {}
for root, _, fs in os.walk(locdir):
    for fn in fs:
        if fn.endswith(".yml"):
            for line in io.open(os.path.join(root, fn), encoding="utf-8-sig", errors="replace"):
                m = rx.match(line)
                if m and m.group(1) not in d:
                    d[m.group(1)] = m.group(2)
print("总 key", len(d))
for k in ["andalusi_culture", "bambara_culture", "bhil_culture", "algerian_culture",
          "angevin_culture", "arpitan_culture", "amhara_culture", "bemba_culture",
          "turkmen_culture", "greek_culture", "han_culture"]:
    print("%-26s %s" % (k, d.get(k, "缺")))
# 有多少 key 以 _culture 结尾
print("_culture 结尾", sum(1 for k in d if k.endswith("_culture")))
