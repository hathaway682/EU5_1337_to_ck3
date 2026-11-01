"""Apply audited medieval Catholic province corrections at county granularity.

Uses the Stanford Corpus Synodalium 1350 atlas (CC BY 3.0), with 1337 and
user-specified exceptions. All overwritten inputs are snapshotted on F:.
"""
from pathlib import Path
from collections import defaultdict,Counter
import csv,importlib.util,json,sys
import numpy as np
from PIL import Image
import rebuild_geographical_regions_20261031 as g
import rebuild_ecclesiastical_titles_20261101 as h

M=Path(__file__).resolve().parents[1]
B=Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261101_082521_europe_church_audit')
O=M/'gen_debug/european_church_audit_20261101'

def adjacency(ts,bs,anc):
 cache=O/'county_adjacency.json'
 if cache.exists():return {k:set(v) for k,v in json.loads(cache.read_text()).items()}
 spec=importlib.util.spec_from_file_location('eurogeoref',B/'inputs/_georef.py');geo=importlib.util.module_from_spec(spec);spec.loader.exec_module(geo)
 keys=sorted(k for k in ts if k.startswith('c_'));ix={c:i+1 for i,c in enumerate(keys)}
 pc={p:anc[b][-2] for b,p in bs.items()};lut=g.definitions(B/'mod/map_data/definition.csv');cm=np.zeros(int(lut.max())+1,dtype=np.uint16)
 for p,c in pc.items():cm[p]=ix[c]
 a=geo.lonlat_to_eu5_px(-25,73);b=geo.lonlat_to_eu5_px(48,30)
 x0=max(0,int(min(a[0],b[0]))-10);x1=min(16384,int(max(a[0],b[0]))+11)
 y0=max(0,int(min(a[1],b[1]))-10);y1=min(8192,int(max(a[1],b[1]))+11)
 Image.MAX_IMAGE_PIXELS=None;im=Image.open(B/'inputs/our_provinces.png');pairs=set();prior=None;n=len(keys)+1
 for y in range(y0,y1,128):
  rgb=np.asarray(im.crop((x0,y,x1,min(y+128,y1))).convert('RGB'),dtype=np.uint32)
  v=cm[lut[(rgb[:,:,0]<<16)|(rgb[:,:,1]<<8)|rgb[:,:,2]]]
  combos=[(v[:,:-1],v[:,1:]),(v[:-1,:],v[1:,:])]
  if prior is not None:combos.append((prior,v[0,:]))
  for left,right in combos:
   mask=(left!=right)&(left!=0)&(right!=0)
   lo=np.minimum(left[mask],right[mask]).astype(np.int64);hi=np.maximum(left[mask],right[mask])
   pairs.update(map(int,np.unique(lo*n+hi)))
  prior=v[-1,:].copy()
 graph=defaultdict(set)
 for code in pairs:
  p,q=divmod(code,n);graph[keys[p-1]].add(keys[q-1]);graph[keys[q-1]].add(keys[p-1])
 with (B/'inputs/adjacencies.csv').open(encoding='utf-8-sig',newline='') as f:
  for row in csv.reader(f,delimiter=';'):
   if len(row)<2 or not row[0].isdigit() or not row[1].isdigit():continue
   c1,c2=pc.get(int(row[0])),pc.get(int(row[1]))
   if c1 and c2 and c1!=c2:graph[c1].add(c2);graph[c2].add(c1)
 cache.write_text(json.dumps({k:sorted(v) for k,v in graph.items()},ensure_ascii=False),encoding='utf-8')
 return graph


def main():
 O.mkdir(exist_ok=True);base=B/'mod'
 ts,bs,anc=g.titles(base/'common/landed_titles');pc={p:anc[b][-2] for b,p in bs.items()}
 old=json.loads((base/'gen_debug/church_control_cleanup_20261101/county_assignment.json').read_text());alloc=dict(old)
 audit=json.loads((O/'atlas_audit.json').read_text(encoding='utf-8'));graph=adjacency(ts,bs,anc)
 # Source uncertainty/contrary primary evidence and recently agreed control rules.
 keep={'c_zamora':'Zamora was a Santiago suffragan, despite competing Braga claims.',
       'c_benavente':'Benavente city was an Oviedo enclave; county straddles dioceses.',
       'c_punente':'County capital Albenga was a Genoa suffragan; Savona belonged to Milan.',
       'c_bosnia':'Bosnian Catholic bishopric was suffragan to Kalocsa.',
       'c_usora_and_soli':'Hungarian-control and Bosnian/Kalocsa decision retained.'}
 protected=set(keep)
 proposals={}
 for row in audit:
  c=row['county'];src=row['current_region'];dst=row['atlas_region'];n=row['atlas_samples']
  if src==dst or row['capital_locked'] or row['user_protected'] or row['controlled_church'] or c in protected:continue
  if n<2 or n/len(ts[c])<.6 or row['confidence']<.7:continue
  proposals[c]=dst
 # Newly mapped Finnish counties are one historically documented maritime
 # cluster under Turku/Uppsala; preserve the expressly requested Rome/Scotland.
 new_finland={c:r for c,r in proposals.items() if not old.get(c)}
 assert all(r=='et_1178_uppsala_region' for r in new_finland.values())
 for c,r in new_finland.items():alloc[c]=r
 # Geography gate: accept an atlas correction only when it touches the target
 # region and removing it does not split the connected source land component.
 def reachable(start,allowed):
  seen={start};todo=[start]
  while todo:
   for nxt in graph.get(todo.pop(),set())&allowed-seen:seen.add(nxt);todo.append(nxt)
  return seen
 pending={c:r for c,r in proposals.items() if old.get(c)};accepted={};skipped={}
 while pending:
  progress=False
  for c,dst in list(pending.items()):
   src=alloc[c];target={k for k,v in alloc.items() if v==dst}
   if not graph.get(c,set())&target:continue
   source={k for k,v in alloc.items() if v==src};neighbors=graph.get(c,set())&source
   if len(neighbors)>1 and not neighbors<=reachable(next(iter(neighbors)),source-{c}):continue
   alloc[c]=dst;accepted[c]=dst;del pending[c];progress=True
  if not progress:break
 # These eight are independently documented historical suffragan sees, or
 # Gotland's natural island. Do not misclassify an authentic cross-border or
 # maritime jurisdiction as an error solely because the county graph splits.
 historical_noncontiguous={
  'c_astorga':'et_1178_braga_region','c_lugo':'et_1178_braga_region',
  'c_ourense':'et_1178_braga_region','c_tras_os_montes':'et_1178_braga_region',
  'c_bjelovar':'et_1178_kalocsa_region','c_zagreb':'et_1178_kalocsa_region',
  'c_gotland':'et_1178_uppsala_region','c_valtellina':'et_867_aquileia_region',
 }
 for c,dst in historical_noncontiguous.items():
  assert proposals.get(c)==dst
  if c in pending:alloc[c]=dst;accepted[c]=dst;del pending[c]
 for c,dst in pending.items():skipped[c]={'atlas':dst,'reason':'geographical connectivity or ambiguous boundary'}
 assert old['c_jawf']=='et_1178_antioch_region' and old['c_sharat']=='et_1178_jerusalem_region'
 del alloc['c_jawf'];alloc['c_sharat']='et_1178_antioch_region'
 changed={c for c in old.keys()|alloc.keys() if old.get(c)!=alloc.get(c)}
 affected={r for c in changed for r in (old.get(c),alloc.get(c)) if r}
 regions,files=h.load_regions(base/'map_data/geographical_regions');members=defaultdict(set)
 for c,r in alloc.items():members[r].update(ts[c])
 def compress(ps):
  rest=set(ps);props=[]
  for prefix,prop in [('d_','duchies'),('c_','counties')]:
   selected=[]
   for key,land in sorted(ts.items()):
    if key.startswith(prefix) and land and land<=rest:selected.append(key);rest-=land
   if selected:props.append((prop,([],selected)))
  assert not rest
  return props,[]
 replacements=defaultdict(dict)
 for r in affected:
  assert r in regions and members[r]
  replacements[files[r]][r]='\n'.join(h.render(([(r,compress(members[r]))],[])))
 products={}
 for filename,change in replacements.items():
  rel=Path('map_data/geographical_regions')/filename;products[rel]=h.replace_blocks(h.read(base/rel),change)
 final=dict(regions)
 for rel,text in products.items():final.update(dict(g.parse(text)[0]))
 for r in regions:
  if r not in affected:assert final[r]==regions[r]
 histories={};titles={}
 for p in (base/'history/titles/ce3').glob('*.txt'):
  for k,v in g.parse(h.read(p))[0]:assert k not in histories;histories[k]=h.state(v,(1337,4,1))
 for p in (base/'common/landed_titles').glob('*.txt'):
  for k,v in g.parse(h.read(p))[0]:titles[k]=v
 seen={};caps={}
 for title,n in histories.items():
  reg=n.get('clerical_region','none')
  if reg=='none':continue
  points=h.expand(reg,final,ts,{})
  for c in {pc[p] for p in points}:
   assert c not in seen,(c,title,seen.get(c));assert ts[c]<=points;seen[c]=title
  cap=dict(titles[title][0])['capital'];assert cap not in caps and seen.get(cap)==title;caps[cap]=title
 assert seen.get('c_jawf') is None and seen['c_sharat']=='d_et_antioch'
 assert seen['c_prilep']=='d_et_ohrid' and seen['c_soria']==seen['c_montana']=='d_et_toledo'
 for c,r in old.items():
  if c not in changed:assert alloc[c]==r
 for c in ('c_bosnia','c_usora_and_soli'):assert alloc[c]==old[c]
 for rel,text in products.items():
  p=O/'staged'/rel;p.parent.mkdir(exist_ok=True,parents=True);p.write_text(text,encoding='utf-8-sig')
 report={'atlas':'https://doi.org/10.25740/rh195hm5975','atlas_attribution':'Rowan Dorin, Clara Romani, Lauren Schlansky, Claire Womack (2021), CC BY 3.0; adapted to CK3 county geometry and 1337 exceptions.',
  'atlas_license':'https://creativecommons.org/licenses/by/3.0/','baseline_map':'province1350.json (approximate 1350, Prague 1344 corrected to Mainz)',
  'atlas_counties_examined':len(audit),'existing_counties_corrected':len(accepted),'new_finland_counties':len(new_finland),
  'historical_noncontiguous_or_island_exceptions':historical_noncontiguous,
  'specified_changes':{'c_jawf':'unassigned','c_sharat':'et_1178_antioch_region'},'kept_ambiguous':keep,
  'skipped_for_geography_or_uncertainty':skipped,'changed_counties':{c:{'from':old.get(c,''),'to':alloc.get(c,'')} for c in sorted(changed)},
  'user_exceptions_preserved':['Scotland directly in Rome','c_prilep remains Ohrid','c_north_dalmatia Split proxy','c_capitanata Trani proxy','c_noto Monreale proxy','Pec/Tarnovo/Halych follow 1337 political control'],
  'active_church_regions':len(caps),'assigned_counties':len(seen),'overlap_counties':0,'overlap_capitals':0,'backup':str(B),'validation':'passed','in_game_test_performed':False}
 (O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 (O/'county_assignment.json').write_text(json.dumps(alloc,ensure_ascii=False,indent=2),encoding='utf-8')
 if '--apply' in sys.argv:
  for rel in products:assert (M/rel).read_bytes()==(base/rel).read_bytes()
  for rel in products:(M/rel).write_bytes((O/'staged'/rel).read_bytes())
 print(json.dumps({k:v for k,v in report.items() if k not in ('changed_counties','skipped_for_geography_or_uncertainty')},ensure_ascii=False,indent=2))
 print('Skipped for connectivity:',json.dumps(skipped,ensure_ascii=False))

if __name__=='__main__':
 sys.stdout.reconfigure(encoding='utf-8');main()
