from pathlib import Path
from collections import defaultdict, Counter
import json, sys
import rebuild_geographical_regions_20261031 as g
import rebuild_ecclesiastical_titles_20261101 as h

M=Path(__file__).resolve().parents[1]
B=Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261105_174425_merge_tyre_oristano')
BASE=B/'mod';OUT=M/'gen_debug/merged_tyre_oristano_20261105'
ts,bs,anc=g.titles(BASE/'common/landed_titles')
pc={p:anc[b][-2] for b,p in bs.items()}
regions,files=h.load_regions(BASE/'map_data/geographical_regions')
old={}
for p in (BASE/'history/titles/ce3').glob('*.txt'):
 for title,node in g.parse(h.read(p))[0]:
  region=h.state(node,(1337,4,1)).get('clerical_region','none')
  if region=='none':continue
  points=h.expand(region,regions,ts,{})
  for c in {pc[point] for point in points}:
   assert c not in old and ts[c]<=points,(title,c)
   old[c]=region
allocation=dict(old);source='et_1178_tyre_region';target='et_1178_oristano_region'
moved={c for c,r in old.items() if r==source}
assert moved=={'c_lebanon'}
for c in moved:allocation[c]=target
members=set().union(*(ts[c] for c,r in allocation.items() if r==target))
rest=set(members);props=[]
for prefix,prop in [('d_','duchies'),('c_','counties')]:
 selected=[]
 for title,land in sorted(ts.items()):
  if title.startswith(prefix) and land and land<=rest:selected.append(title);rest-=land
 if selected:props.append((prop,([],selected)))
assert not rest
rrel=Path('map_data/geographical_regions')/files[target]
replacement='\n'.join(h.render(([(target,(props,[]))],[])))
rtext=h.replace_blocks(h.read(BASE/rrel),{target:replacement})
final=dict(regions);final.update(dict(g.parse(rtext)[0]))
assert all(final[k]==v for k,v in regions.items() if k!=target)
hrel=Path('history/titles/ce3/00_ecclesiastical_titles.txt')
hist_text=h.read(BASE/hrel);nodes=dict(g.parse(hist_text)[0]);node=nodes['d_et_tyre'];state=h.state(node,(1337,4,1))
assert state['holder']=='arb_guido_cattaneo' and state['clerical_region']==source
new=[]
for key,value in node[0]:
 if key=='1337.4.1':
  value=([(k,'0' if k=='holder' else 'none' if k=='clerical_region' else v) for k,v in value[0]],value[1])
 new.append((key,value))
title_text=h.replace_blocks(hist_text,{'d_et_tyre':'\n'.join(h.render(([('d_et_tyre',(new,node[1]))],[])))})
products={rrel:rtext,hrel:title_text}
titles={}
for p in (BASE/'common/landed_titles').glob('*.txt'):titles.update(dict(g.parse(h.read(p))[0]))
histories={}
for p in (BASE/'history/titles/ce3').glob('*.txt'):
 text=products.get(p.relative_to(BASE),h.read(p))
 for k,n in g.parse(text)[0]:assert k not in histories;histories[k]=h.state(n,(1337,4,1))
seen={};caps={};holders=[]
for title,state in histories.items():
 region=state.get('clerical_region','none')
 if region=='none':continue
 points=h.expand(region,final,ts,{})
 for c in {pc[p] for p in points}:
  assert c not in seen and ts[c]<=points,(title,c)
  assert allocation.get(c)==region,(title,c,allocation.get(c))
  seen[c]=title
 cap=dict(titles[title][0])['capital'];assert cap not in caps and seen.get(cap)==title;caps[cap]=title
 holder=state.get('holder','0')
 if holder!='0':holders.append(holder)
assert len(caps)==78 and len(seen)==len(allocation)
assert not [x for x,n in Counter(holders).items() if n>1]
assert histories['d_et_tyre']['holder']=='0' and histories['d_et_tyre']['clerical_region']=='none'
assert histories['d_et_oristano']['holder']=='arb_guido_cattaneo'
assert set(old)^set(allocation)==set() and all(old[c]==allocation[c] for c in old if c not in moved)
OUT.mkdir(parents=True,exist_ok=True)
for rel,text in products.items():
 p=OUT/'staged'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8-sig')
(OUT/'county_assignment.json').write_text(json.dumps(allocation,ensure_ascii=False,indent=2),encoding='utf8')
report={'moved_counties':sorted(moved),'merged_into':'d_et_oristano','deactivated':'d_et_tyre','active_regions':len(caps),'assigned_counties':len(seen),'duplicate_holders':0,'in_game_test_performed':False}
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
if '--apply' in sys.argv:
 for rel in products:assert (M/rel).read_bytes()==(BASE/rel).read_bytes(),rel
 for rel in products:(M/rel).write_bytes((OUT/'staged'/rel).read_bytes())
 for rel in products:assert (M/rel).read_bytes()==(OUT/'staged'/rel).read_bytes()
print(json.dumps(report,ensure_ascii=False,indent=2))
