"""Adjust Carthage, Alexandria and Axum using 1337 titles and control."""
from pathlib import Path
from collections import defaultdict
import json,sys
import rebuild_geographical_regions_20261031 as g
import rebuild_ecclesiastical_titles_20261101 as h

M=Path(__file__).resolve().parents[1]
B=Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261101_092712_africa_church_regions')
O=M/'gen_debug/africa_church_regions_20261101'

def main():
 O.mkdir(exist_ok=True);base=B/'mod'
 ts,bs,anc=g.titles(base/'common/landed_titles');pc={p:anc[b][-2] for b,p in bs.items()}
 old=json.loads((base/'gen_debug/rus_slavic_church_20261101/county_assignment.json').read_text());allocation=dict(old)
 def duchy_counties(d):return {ch[-2] for ch in anc.values() if d in ch}
 desert=duchy_counties('d_desert')
 ethiopia_duchies={'d_central_ethiopia','d_northern_ethiopia','d_southern_ethiopia'}
 de_jure=set().union(*(duchy_counties(d) for d in ethiopia_duchies))
 assert len(desert)==8 and len(de_jure)==25
 states={}
 for p in (base/'history/titles').glob('*.txt'):
  for title,node in g.parse(h.read(p))[0]:
   assert title not in states;states[title]=h.state(node,(1337,4,1))
 ranks={'b':1,'c':2,'d':3,'k':4,'e':5,'h':6};options=defaultdict(list)
 for title,state in states.items():
  holder=state.get('holder','0');liege=state.get('liege','0');lord=states.get(liege,{}).get('holder','0')
  if holder!='0' and lord not in ('0',holder):options[holder].append((ranks.get(title[0],0),lord,title,liege))
 parent={holder:max(v)[1] for holder,v in options.items()}
 def control(holder):
  seen=set()
  while holder in parent:
   assert holder not in seen;seen.add(holder);holder=parent[holder]
  return holder
 eth_root=control(states['c_tigray']['holder'])
 controlled={c for c in ts if c.startswith('c_') and c in states and states[c].get('holder','0')!='0' and control(states[c]['holder'])==eth_root}
 assert len(controlled)==14
 target=de_jure|controlled
 carthage='et_867_africa_region';alexandria='et_1178_alexandria_region';axum='et_867_axum_region'
 removed_desert={c for c in desert if allocation.get(c)==carthage}
 for c in removed_desert:del allocation[c]
 assert len(removed_desert)==4
 removed_alex={'c_kordofan','c_bahr_al_jabal'}
 for c in removed_alex:
  assert allocation.get(c)==alexandria
  del allocation[c]
 assert not removed_alex&target
 for c in target:allocation[c]=axum
 changed={c for c in old.keys()|allocation.keys() if old.get(c)!=allocation.get(c)}
 affected={r for c in changed for r in (old.get(c),allocation.get(c)) if r}
 assert affected<={carthage,alexandria,axum}
 members=defaultdict(set)
 for c,r in allocation.items():members[r].update(ts[c])
 regions,files=h.load_regions(base/'map_data/geographical_regions')
 def compress(ps):
  rest=set(ps);props=[]
  for prefix,prop in [('d_','duchies'),('c_','counties')]:
   selected=[]
   for t,land in sorted(ts.items()):
    if t.startswith(prefix) and land and land<=rest:selected.append(t);rest-=land
   if selected:props.append((prop,([],selected)))
  assert not rest
  return props,[]
 replacements=defaultdict(dict)
 for r in affected:
  assert members[r]
  replacements[files[r]][r]='\n'.join(h.render(([(r,compress(members[r]))],[])))
 products={}
 for filename,blocks in replacements.items():
  rel=Path('map_data/geographical_regions')/filename
  products[rel]=h.replace_blocks(h.read(base/rel),blocks)
 final=dict(regions)
 for rel,text in products.items():final.update(dict(g.parse(text)[0]))
 assert all(final[k]==v for k,v in regions.items() if k not in affected)
 titles={};histories={}
 for p in (base/'common/landed_titles').glob('*.txt'):
  for k,n in g.parse(h.read(p))[0]:titles[k]=n
 for p in (base/'history/titles/ce3').glob('*.txt'):
  for k,n in g.parse(h.read(p))[0]:assert k not in histories;histories[k]=h.state(n,(1337,4,1))
 seen={};capitals={}
 for title,state in histories.items():
  region=state.get('clerical_region','none')
  if region=='none':continue
  points=h.expand(region,final,ts,{})
  for c in {pc[p] for p in points}:
   assert c not in seen,(c,title);assert ts[c]<=points;seen[c]=title
  cap=dict(titles[title][0])['capital'];assert cap not in capitals and seen.get(cap)==title;capitals[cap]=title
 assert not (desert&{c for c,r in allocation.items() if r==carthage})
 assert not (removed_alex&{c for c,r in allocation.items() if r==alexandria})
 assert all(allocation[c]==axum for c in target)
 assert all(allocation.get(c)==old.get(c) for c in old.keys()|allocation.keys() if c not in changed)
 assert len(capitals)==79
 for rel,text in products.items():
  p=O/'staged'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8-sig')
 report={'backup':str(B),'ethiopian_controller':eth_root,'ethiopian_de_jure_duchies':sorted(ethiopia_duchies),
  'de_jure_counties':len(de_jure),'controlled_counties':len(controlled),'required_axum_counties':len(target),
  'controlled_outside_three_duchies':sorted(controlled-de_jure),'removed_carthage_desert':sorted(removed_desert),
  'removed_from_alexandria':sorted(removed_alex),'county_changes':{c:{'from':old.get(c,''),'to':allocation.get(c,'')} for c in sorted(changed)},
  'active_regions':len(capitals),'assigned_counties':len(seen),'overlap_counties':0,'overlap_capitals':0,
  'in_game_test_performed':False,'validation':'passed'}
 (O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 (O/'county_assignment.json').write_text(json.dumps(allocation,ensure_ascii=False,indent=2),encoding='utf-8')
 if '--apply' in sys.argv:
  for rel in products:assert (M/rel).read_bytes()==(base/rel).read_bytes()
  for rel in products:(M/rel).write_bytes((O/'staged'/rel).read_bytes())
  for folder in ('history/titles/ce3','common/landed_titles'):
   for p in (base/folder).glob('*.txt'):assert p.read_bytes()==(M/p.relative_to(base)).read_bytes()
 print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
 sys.stdout.reconfigure(encoding='utf-8');main()
