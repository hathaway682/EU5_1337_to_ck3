"""Expand the Kyiv-and-all-Rus ecclesiastical region to uncovered Slavic-rite
counties in EU5's Russian, Ruthenian and adjacent steppe regions. Existing
Halych and other ecclesiastical regions are preserved. No rites are changed.
"""
from pathlib import Path
from collections import defaultdict,Counter
import csv,json,sys
import rebuild_geographical_regions_20261031 as g
import rebuild_ecclesiastical_titles_20261101 as h

M=Path(__file__).resolve().parents[1]
B=Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261101_090532_rus_slavic_church')
O=M/'gen_debug/rus_slavic_church_20261101'
TARGET='et_1178_kyiv_region'

def main():
 O.mkdir(exist_ok=True);base=B/'mod'
 ts,bs,anc=g.titles(base/'common/landed_titles')
 pc={p:anc[b][-2] for b,p in bs.items()}
 old=json.loads((base/'gen_debug/scottish_isles_20261101/county_assignment.json').read_text());allocation=dict(old)
 root=g.parse(h.read(B/'inputs/definitions.txt'));locations={}
 def walk(node,chain=()):
  for k,v in node[0]:
   if isinstance(v,tuple):
    path=chain+(k,)
    if len(path)==5:
     for loc in v[1]:
      assert loc.casefold() not in locations
      locations[loc.casefold()]=path[2]
    else:walk(v,path)
 walk(root)
 ph=dict(g.parse(h.read(base/'history/provinces/00_generated_provinces.txt'))[0])
 county_data=defaultdict(lambda:{'total':0,'slavic':[],'region_counts':Counter(),'rite_counts':Counter()})
 source_regions={'russian_region','ruthenia_region','steppes_region'}
 for barony,pid in bs.items():
  c=anc[barony][-2];st=h.state(ph[str(pid)],(1337,4,1));loc_region=locations.get(barony[2:].casefold())
  assert loc_region is not None,barony
  row=county_data[c];row['total']+=1;row['rite_counts'][st.get('rite','(not explicit)')]+=1
  if st.get('rite')=='slavic_rite' and loc_region in source_regions:
   row['slavic'].append(barony);row['region_counts'][loc_region]+=1
 changes={};protected={}
 for county,row in county_data.items():
  if not row['slavic']:continue
  current=allocation.get(county,'')
  if current==TARGET:continue
  if current:
   protected[county]=current;continue
  allocation[county]=TARGET;changes[county]=row
 assert len(changes)>0
 # Explicitly retained independent Halych province.
 assert all(allocation[c]==r for c,r in old.items() if r=='eu5_et_1337_halych_region')
 regions,files=h.load_regions(base/'map_data/geographical_regions');assert TARGET in regions
 desired=set().union(*(ts[c] for c,r in allocation.items() if r==TARGET));remaining=set(desired);props=[]
 for prefix,prop in [('d_','duchies'),('c_','counties')]:
  selected=[]
  for key,land in sorted(ts.items()):
   if key.startswith(prefix) and land and land<=remaining:selected.append(key);remaining-=land
  if selected:props.append((prop,([],selected)))
 assert not remaining
 rel=Path('map_data/geographical_regions')/files[TARGET];before=h.read(base/rel)
 block='\n'.join(h.render(([(TARGET,(props,[]))],[])))
 after=h.replace_blocks(before,{TARGET:block})
 original_nodes=dict(g.parse(before)[0]);final_nodes=dict(g.parse(after)[0]);assert original_nodes.keys()==final_nodes.keys()
 assert all(original_nodes[k]==final_nodes[k] for k in original_nodes if k!=TARGET)
 regions[TARGET]=final_nodes[TARGET]
 histories={};titles={}
 for p in (base/'history/titles/ce3').glob('*.txt'):
  for k,n in g.parse(h.read(p))[0]:assert k not in histories;histories[k]=h.state(n,(1337,4,1))
 for p in (base/'common/landed_titles').glob('*.txt'):
  for k,n in g.parse(h.read(p))[0]:titles[k]=n
 seen={};capitals={}
 for title,state in histories.items():
  r=state.get('clerical_region','none')
  if r=='none':continue
  points=h.expand(r,regions,ts,{})
  for c in {pc[p] for p in points}:
   assert c not in seen,(c,title);assert ts[c]<=points;seen[c]=title
  cap=dict(titles[title][0])['capital'];assert cap not in capitals and seen.get(cap)==title;capitals[cap]=title
 assert all(seen[c]=='d_et_kyiv' for c in changes)
 assert len(capitals)==79 and len(seen)==len(old)+len(changes)
 assert dict(titles['d_et_kyiv'][0])['capital']=='c_moscow'
 staged=O/'staged'/rel;staged.parent.mkdir(parents=True,exist_ok=True);staged.write_text(after,encoding='utf-8-sig')
 fields=['county','slavic_baronies','all_baronies','source_regions','mixed_or_unset_rites','slavic_barony_keys']
 with (O/'added_counties.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for c,row in sorted(changes.items()):
   w.writerow({'county':c,'slavic_baronies':len(row['slavic']),'all_baronies':row['total'],
    'source_regions':' '.join(sorted(row['region_counts'])),'mixed_or_unset_rites':len(row['slavic'])!=row['total'],
    'slavic_barony_keys':' '.join(row['slavic'])})
 mixed=[c for c,row in changes.items() if len(row['slavic'])!=row['total']]
 report={'backup':str(B),'source_eu5_regions':sorted(source_regions),'added_counties':len(changes),
  'mixed_or_unset_rite_counties':sorted(mixed),'protected_existing_regions':protected,
  'kyiv_total_counties':sum(r==TARGET for r in allocation.values()),'assigned_counties':len(seen),
  'active_regions':len(capitals),'overlapping_counties':0,'overlapping_capitals':0,
  'capital':'c_moscow','rite_histories_changed':False,'in_game_test_performed':False,'validation':'passed'}
 (O/'county_assignment.json').write_text(json.dumps(allocation,ensure_ascii=False,indent=2),encoding='utf-8')
 (O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 if '--apply' in sys.argv:
  assert (M/rel).read_bytes()==(base/rel).read_bytes()
  (M/rel).write_bytes(staged.read_bytes())
  assert (M/'history/provinces/00_generated_provinces.txt').read_bytes()==(base/'history/provinces/00_generated_provinces.txt').read_bytes()
  for folder in ('history/titles/ce3','common/landed_titles'):
   for p in (base/folder).glob('*.txt'):assert p.read_bytes()==(M/p.relative_to(base)).read_bytes()
 print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
 sys.stdout.reconfigure(encoding='utf-8');main()
