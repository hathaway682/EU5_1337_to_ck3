"""User correction: direct Roman jurisdiction in Scotland; political control
defines Serbia, Bulgaria and Galicia-Volhynia's independent church districts.
"""
from pathlib import Path
from collections import defaultdict,Counter
import json
import re
import sys
import rebuild_geographical_regions_20261031 as g
import rebuild_ecclesiastical_titles_20261101 as h

M=Path(__file__).resolve().parents[1]
B=Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261101_075202_church_control_cleanup')
O=M/'gen_debug/church_control_cleanup_20261101'
SCOTTISH={'st_andrews','glasgow','dunkeld_dunblane','brechin','aberdeen','moray','ross','caithness','argyll'}


def main():
 O.mkdir(exist_ok=True);base=B/'mod'
 previous_staged={p.relative_to(O/'staged'):p.read_bytes() for p in (O/'staged').rglob('*') if p.is_file()}
 ts,bs,anc=g.titles(base/'common/landed_titles')
 pc={bs[b]:next(c for c in ch if c.startswith('c_')) for b,ch in anc.items()}
 allocation=json.loads((base/'gen_debug/church_regions_1337_20261101/county_assignment.json').read_text())
 previous=dict(allocation)
 old_report=json.loads((base/'gen_debug/church_regions_1337_20261101/report.json').read_text(encoding='utf-8'))
 states={}
 for p in sorted((base/'history/titles').glob('*.txt')):
  for title,node in g.parse(h.read(p))[0]:
   assert title not in states;states[title]=h.state(node,(1337,4,1))
 rank={'b':1,'c':2,'d':3,'k':4,'e':5,'h':6};options=defaultdict(list)
 for title,n in states.items():
  holder=n.get('holder','0');liege=n.get('liege','0');lord=states.get(liege,{}).get('holder','0')
  if holder!='0' and lord not in ('0',holder):options[holder].append((rank.get(title[0],0),lord,title,liege))
 parent={holder:max(v)[1] for holder,v in options.items()}
 def control(holder):
  seen=set()
  while holder in parent:
   assert holder not in seen,('Cyclic political control',holder)
   seen.add(holder);holder=parent[holder]
  return holder
 controls={c:control(states.get(c,{}).get('holder','0')) for c in ts if c.startswith('c_')}
 targets={'pec':('c_kosovo',12),'tarnovo':('c_tarnovo',9),'halych':('c_halych',17)}
 church_members={}
 for name,(capital,count) in targets.items():
  owner=controls[capital];cc={c for c,root in controls.items() if root==owner}
  assert len(cc)==count,(name,len(cc));church_members[name]=cc
 # Explicit user exception: retain Ohrid's own capital despite Serbian control.
 church_members['pec'].remove('c_prilep')
 # Undo the obsolete de-jure-based assignments before assigning controlled land.
 target_regions={'eu5_et_1337_'+name+'_region' for name in targets}
 prior={row['county']:row['previous_region'] for row in old_report['county_changes'] if row['region'] in target_regions}
 for c,r in list(allocation.items()):
  if r in target_regions:
   assert prior.get(c),('Missing pre-adjustment church jurisdiction',c)
   allocation[c]=prior[c]
 for name,cc in church_members.items():
  for c in cc:allocation[c]='eu5_et_1337_'+name+'_region'
 # Counties of the two competing Scottish royal holders go directly to Rome.
 scottish_roots={controls['c_fife'],controls['c_lothian']}
 scottish_counties={c for c,owner in controls.items() if owner in scottish_roots}
 assert len(scottish_counties)==14
 for c in scottish_counties:allocation[c]='et_1178_roma_region'
 # Castilian enclaves cannot remain in Tarragona after the Zaragoza split.
 castile=controls['c_soria']
 castilian_corrections=[]
 for c,r in list(allocation.items()):
  if r=='et_867_tarragona_region' and controls[c]==castile:
   allocation[c]='et_1178_toledo_region';castilian_corrections.append(c)
 assert {'c_montana','c_soria'}<=set(castilian_corrections)
 # Former Serbian territory controlled by Hungary belongs to its neighboring
 # Kalocsa province, rather than remaining detached islands of Ohrid.
 assert controls['c_macva']==controls['c_sumadija']==control(states['k_hungary']['holder'])
 for c in ('c_macva','c_sumadija'):allocation[c]='et_1178_kalocsa_region'
 # User correction: retain Ohrid's capital; Romanian counties go to
 # Constantinople. Hungarian Bosnia goes to Kalocsa.
 ohrid_detached_hungary={'c_bosnia','c_usora_and_soli'}
 ohrid_detached_danubian={'c_bacau','c_barlad','c_basarabia','c_east_muntenia','c_iasi',
  'c_north_muntenia','c_north_oltenia','c_south_muntenia','c_south_oltenia','c_west_muntenia'}
 for c in ohrid_detached_hungary:
  assert allocation[c]=='et_1066_ohrid_region'
  assert controls[c]==control(states['k_hungary']['holder'])
  allocation[c]='et_1178_kalocsa_region'
 for c in ohrid_detached_danubian:
  assert allocation[c]=='et_1066_ohrid_region'
  allocation[c]='et_1178_constantinople_region'
 assert {c for c,r in allocation.items() if r=='et_1066_ohrid_region'}=={
  'c_albania','c_north_epirus','c_prilep','c_south_epirus','c_upper_macedonia'}
 removed_titles={'d_et_'+name for name in SCOTTISH}
 removed_regions={'eu5_et_1337_'+name+'_region' for name in SCOTTISH}
 assert not (set(allocation.values())&removed_regions)
 members=defaultdict(set)
 for c,r in allocation.items():members[r].update(ts[c])
 affected={r for c in allocation if allocation[c]!=previous.get(c) for r in (allocation[c],previous.get(c)) if r}
 allregions,files=h.load_regions(base/'map_data/geographical_regions')
 def compress(ps):
  rest=set(ps);props=[]
  for prefix,prop in [('d_','duchies'),('c_','counties')]:
   selected=[]
   for key,land in sorted(ts.items()):
    if key.startswith(prefix) and land and land<=rest:selected.append(key);rest-=land
   if selected:props.append((prop,([],selected)))
  assert not rest
  return props,[]
 blocks=defaultdict(dict)
 for r in affected:
  if r in removed_regions:blocks[files[r]][r]=''
  else:blocks[files[r]][r]='\n'.join(h.render(([(r,compress(members[r]))],[])))
 products={}
 for file,updates in blocks.items():
  rel=Path('map_data/geographical_regions')/file
  products[rel]=h.replace_blocks(h.read(base/rel),updates)
 decl_rel=Path('common/landed_titles/zzz_eu5_church_1337.txt')
 hist_rel=Path('history/titles/ce3/03_eu5_church_1337.txt')
 for rel in (decl_rel,hist_rel):
  text=h.read(base/rel)
  products[rel]=h.replace_blocks(text,{k:'' for k in removed_titles})
  products[rel]=products[rel].replace('Scottish districts are not metropolitan provinces.','Scottish counties are directly in the Roman ecclesiastical region.')
 for lang in ('english','simp_chinese'):
  rel=Path(f'localization/replace/{lang}/eu5_church_1337_l_{lang}.yml')
  products[rel]='\n'.join(line for line in h.read(base/rel).splitlines()
   if not any(re.match(r'\s*'+re.escape(k)+r':',line) for k in removed_titles))+'\n'
 finalregions=dict(allregions)
 for rel,text in products.items():
  if str(rel).replace('\\','/').startswith('map_data/'):
   oldkeys=set(dict(g.parse(h.read(base/rel))[0]));new=dict(g.parse(text)[0])
   for k in oldkeys-new.keys():finalregions.pop(k)
   finalregions.update(new)
 for r in allregions:
  if r not in affected:assert finalregions[r]==allregions[r]
 for node in finalregions.values():
  for k,v in node[0]:
   if k=='regions':assert not (set(v[1])&removed_regions)
 titledefs={}
 for p in (base/'common/landed_titles').glob('*.txt'):
  for k,v in g.parse(products.get(p.relative_to(base),h.read(p)))[0]:titledefs[k]=v
 histories={}
 for p in (base/'history/titles/ce3').glob('*.txt'):
  for k,v in g.parse(products.get(p.relative_to(base),h.read(p)))[0]:
   assert k not in histories;histories[k]=v
 assert not removed_titles&titledefs.keys() and not removed_titles&histories.keys()
 seen={};caps={};active=0
 for title,node in histories.items():
  state=h.state(node,(1337,4,1));r=state.get('clerical_region','none')
  if r=='none':continue
  active+=1;ps=h.expand(r,finalregions,ts,{})
  assert ps
  for c in {pc[p] for p in ps}:
   assert c not in seen,(c,title,seen.get(c));assert ts[c]<=ps;seen[c]=title
  cap=dict(titledefs[title][0])['capital'];assert cap not in caps;caps[cap]=title
  assert seen.get(cap)==title
 assert active==79 and len(seen)==len(allocation)==995
 for name,cc in church_members.items():
  r='eu5_et_1337_'+name+'_region'
  assert {c for c,x in allocation.items() if x==r}==cc
 for c in scottish_counties:assert seen[c]=='d_et_roma'
 assert seen['c_montana']==seen['c_soria']=='d_et_toledo'
 assert seen['c_turov']=='d_et_kyiv'
 for rel,text in products.items():
  if rel.suffix=='.txt':g.parse(text)
  p=O/'staged'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8-sig')
 changes=[{'county':c,'previous':previous[c],'region':r,'controller':controls[c]} for c,r in allocation.items() if r!=previous[c]]
 report={'backup':str(B),'active_church_regions':active,'counties':len(seen),
  'overlapping_counties':0,'overlapping_active_capitals':0,'scottish_fragment_titles_removed':sorted(removed_titles),
  'scottish_counties_directly_under_rome':sorted(scottish_counties),'castilian_corrections':sorted(castilian_corrections),
  'autonomous_church_controlled_counties':{k:sorted(v) for k,v in church_members.items()},
  'county_changes':changes,'faiths_rites_characters_and_cardinals_unchanged':True,
  'political_control_exception':{'c_prilep':'d_et_ohrid'},
  'ohrid_detached_hungarian_counties_to_kalocsa':sorted(ohrid_detached_hungary),
  'danubian_counties_under_constantinople':sorted(ohrid_detached_danubian),
  'validation':'passed','in_game_test_performed':False}
 (O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 (O/'county_assignment.json').write_text(json.dumps(allocation,ensure_ascii=False,indent=2),encoding='utf-8')
 (O/'county_controllers.json').write_text(json.dumps(controls,ensure_ascii=False,indent=2),encoding='utf-8')
 if '--apply' in sys.argv:
  for rel in products:
   assert (M/rel).read_bytes() in ((base/rel).read_bytes(),(O/'staged'/rel).read_bytes(),previous_staged.get(rel)),rel
  for rel in products:(M/rel).write_bytes((O/'staged'/rel).read_bytes())
  for folder in ('common/landed_titles','history/titles','map_data/geographical_regions'):
   for p in (base/folder).rglob('*.txt'):
    rel=p.relative_to(base)
    if rel not in products:assert p.read_bytes()==(M/rel).read_bytes()
 print(json.dumps({k:v for k,v in report.items() if k!='county_changes'},ensure_ascii=False,indent=2))

if __name__=='__main__':
 sys.stdout.reconfigure(encoding='utf-8');main()
