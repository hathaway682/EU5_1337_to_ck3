"""Restore Galloway to York and the Scottish Hebrides to Nidaros."""
from pathlib import Path
from collections import defaultdict
import json,sys
import rebuild_geographical_regions_20261031 as g
import rebuild_ecclesiastical_titles_20261101 as h

M=Path(__file__).resolve().parents[1]
B=Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261101_085931_scottish_isles')
O=M/'gen_debug/scottish_isles_20261101'

def main():
 O.mkdir(exist_ok=True);base=B/'mod'
 ts,bs,anc=g.titles(base/'common/landed_titles')
 pc={p:anc[b][-2] for b,p in bs.items()}
 old=json.loads((base/'gen_debug/european_church_audit_20261101/county_assignment.json').read_text());allocation=dict(old)
 changes={'c_galloway':'et_1178_york_region','c_inner_hebrides':'et_1178_nidaros_region','c_outer_hebrides':'et_1178_nidaros_region'}
 for county,region in changes.items():
  assert allocation[county]=='et_1178_roma_region';allocation[county]=region
 assert allocation['c_northern_isles']=='et_1178_nidaros_region'
 affected={'et_1178_roma_region','et_1178_york_region','et_1178_nidaros_region'}
 members=defaultdict(set)
 for county,region in allocation.items():members[region].update(ts[county])
 regions,files=h.load_regions(base/'map_data/geographical_regions')
 replacements=defaultdict(dict)
 for region in affected:
  rest=set(members[region]);props=[]
  for prefix,prop in [('d_','duchies'),('c_','counties')]:
   selected=[]
   for title,land in sorted(ts.items()):
    if title.startswith(prefix) and land and land<=rest:selected.append(title);rest-=land
   if selected:props.append((prop,([],selected)))
  assert not rest
  replacements[files[region]][region]='\n'.join(h.render(([(region,(props,[]))],[])))
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
 seen={};caps={}
 for title,state in histories.items():
  region=state.get('clerical_region','none')
  if region=='none':continue
  points=h.expand(region,final,ts,{})
  for county in {pc[p] for p in points}:
   assert county not in seen;assert ts[county]<=points;seen[county]=title
  capital=dict(titles[title][0])['capital'];assert capital not in caps and seen.get(capital)==title;caps[capital]=title
 assert seen['c_galloway']=='d_et_york'
 for c in ('c_inner_hebrides','c_outer_hebrides','c_northern_isles'):assert seen[c]=='d_et_nidaros'
 assert {c for c in old if old[c]!=allocation[c]}==set(changes)
 assert len(seen)==1000 and len(caps)==79
 for rel,text in products.items():
  p=O/'staged'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8-sig')
 if '--apply' in sys.argv:
  for rel in products:assert (M/rel).read_bytes()==(base/rel).read_bytes()
  for rel in products:(M/rel).write_bytes((O/'staged'/rel).read_bytes())
  for folder in ('history/titles/ce3','common/landed_titles'):
   for p in (base/folder).rglob('*.txt'):assert p.read_bytes()==(M/p.relative_to(base)).read_bytes()
 report={'backup':str(B),'changes':changes,'already_nidaros':['c_northern_isles'],
         'assigned_counties':len(seen),'active_regions':len(caps),'overlapping_counties':0,
         'overlapping_capitals':0,'in_game_test_performed':False,'validation':'passed'}
 (O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 (O/'county_assignment.json').write_text(json.dumps(allocation,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
 sys.stdout.reconfigure(encoding='utf-8');main()
