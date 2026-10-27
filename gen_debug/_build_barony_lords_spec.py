import json, re, glob, os
MOD="D:/Documents/Paradox Interactive/Crusader Kings III/mod/EU5_Modern_Borders_noshape"
matched=json.load(open(f"{MOD}/gen_debug/_tmp_barony_matched.json",encoding="utf-8"))

emp=dict()
for b,info in matched.items():
    e=info['e'] or 'e_NONE'
    emp.setdefault(e,set()).add(info['prov'])

LABELS={
 'e_western_europe':'西欧','e_north_america':'北美','e_east_asia':'东亚',
 'e_south_asia':'南亚','e_south_east_asia':'东南亚','e_eastern_europe':'东欧',
 'e_middle_east':'中东','e_south_america':'南美','e_west_africa':'西非',
 'e_east_africa':'东非','e_pacific_islands':'太平洋诸岛','e_central_asia':'中亚',
 'e_central_africa':'中非洲','e_NONE':'无帝国归属'}
# 13 distinct, readable colors
PALETTE=["#E03A3A","#3A7BE0","#3AB55A","#E0A93A","#9B3AE0","#3AE0D5","#E03A8C",
         "#7A8A2A","#2A5A8A","#C25A1E","#1E8A5A","#8A1E5A","#5A5A5A"]
groups=[]
for i,(eid,provs) in enumerate(sorted(emp.items(),key=lambda kv:-len(kv[1]))):
    groups.append({"name":LABELS.get(eid,eid),"provs":sorted(provs),"color":PALETTE[i%len(PALETTE)]})

spec={
  "mod_root": MOD,
  "out": f"{MOD}/gen_debug/barony_lords_world",
  "title": u"已添加的男爵领领主 · 全球分布",
  "subtitle": f"{len(matched)} 个有领主的男爵领，按 de jure 帝国着色",
  "groups": groups,
  "color": {"mode":"direct"},
  "base": {"unassigned":"#F2F2F2","sea":"#3C78C8","lake":"#3C78C8","impassable_sea":"#3C78C8","waste":"#808080","orphan":"#D9D9D9"},
  "legend": {"enabled":True,"unit":"男爵领","show_counts":True,"width":420}
}
json.dump(spec,open(f"{MOD}/gen_debug/barony_lords_spec.json","w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("groups:",len(groups))
