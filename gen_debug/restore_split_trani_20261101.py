"""Restore Split/Trani within their merged territory, with user-selected seats."""
from pathlib import Path
from collections import Counter
import json
import sys
import rebuild_geographical_regions_20261031 as g
import rebuild_ecclesiastical_titles_20261101 as h

M = Path(__file__).resolve().parents[1]
B = Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261101_072316_split_trani_seats')
O = M / 'gen_debug/split_trani_seats_20261101'


def main():
 O.mkdir(exist_ok=True)
 base=B/'mod'
 ts,bs,anc=g.titles(base/'common/landed_titles')
 pc={bs[b]:next(c for c in chain if c.startswith('c_')) for b,chain in anc.items()}
 old=json.loads((base/'gen_debug/ecclesiastical_1178_20261101/region_provinces.json').read_text())
 allocation=json.loads((base/'gen_debug/clerical_overlap_20261101/county_assignment.json').read_text())
 original=dict(allocation)
 changespec=[('d_et_split','et_1178_split_region','et_1178_ragusa_region','c_north_dalmatia','c_south_dalmatia'),
             ('d_et_trani','et_1066_trani_region','et_1066_bari_region','c_capitanata','c_bari')]
 transfers={}
 for title,target,merged,newseat,retainedseat in changespec:
  assert allocation[newseat]==allocation[retainedseat]==merged
  votes=Counter(pc[p] for p in old[target])
  other=Counter(pc[p] for p in old[merged])
  moved=[]
  for county,owner in list(allocation.items()):
   if owner==merged and county!=retainedseat and (county==newseat or votes[county]>other[county]):
    allocation[county]=target;moved.append(county)
  assert newseat in moved
  transfers[title]=sorted(moved)
 members={r:set() for r in set(allocation.values())}
 for county,r in allocation.items():members[r].update(ts[county])
 affected={r for _,target,merged,_,_ in changespec for r in (target,merged)}
 geo_rel=Path('map_data/geographical_regions/geographical_region.txt')
 title_rel=Path('common/landed_titles/07_pam_ecclesiastical_titles.txt')
 hist_rel=Path('history/titles/ce3/00_ecclesiastical_titles.txt')
 before={rel:h.read(base/rel) for rel in (geo_rel,title_rel,hist_rel)}
 geo_changes={}
 for r in affected:
  rest=set(members[r]);props=[]
  for prefix,prop in [('d_','duchies'),('c_','counties')]:
   selected=[]
   for t,ps in sorted(ts.items()):
    if t.startswith(prefix) and ps and ps<=rest:selected.append(t);rest-=ps
   if selected:props.append((prop,([],selected)))
  assert not rest
  geo_changes[r]='\n'.join(h.render(([(r,(props,[]))],[])))
 titles=dict(g.parse(before[title_rel])[0]);hist=dict(g.parse(before[hist_rel])[0])
 title_changes={};hist_changes={}
 for title,target,_,newseat,_ in changespec:
  title_changes[title]='\n'.join(h.render(([(title,([(k,newseat if k=='capital' else v) for k,v in titles[title][0]],titles[title][1]))],[])))
  fields=dict(hist[title][0]);node=fields['1337.4.1']
  updated=([(k,target if k=='clerical_region' else v) for k,v in node[0]],node[1])
  hist_changes[title]='\n'.join(h.render(([(title,([('1337.4.1',updated)],[]))],[])))
 products={geo_rel:h.replace_blocks(before[geo_rel],geo_changes),
           title_rel:h.replace_blocks(before[title_rel],title_changes),hist_rel:h.replace_blocks(before[hist_rel],hist_changes)}
 for rel,changed in [(geo_rel,affected),(title_rel,set(title_changes)),(hist_rel,set(hist_changes))]:
  a=dict(g.parse(before[rel])[0]);z=dict(g.parse(products[rel])[0]);assert set(a)==set(z)
  assert all(a[k]==z[k] for k in a if k not in changed)
 finalgeo=dict(g.parse(products[geo_rel])[0]);finalhist=dict(g.parse(products[hist_rel])[0]);finaltitles=dict(g.parse(products[title_rel])[0])
 owned={};capital_owners={};active=0
 for title,n in finalhist.items():
  state=h.state(n,(1337,4,1));r=state.get('clerical_region','none')
  if r=='none':continue
  active+=1;ps=h.expand(r,finalgeo,ts,{})
  counties={pc[p] for p in ps}
  for c in counties:
   assert c not in owned,('Overlapping county',c,title,owned.get(c))
   assert ts[c]<=ps;owned[c]=title
  capital=dict(finaltitles[title][0])['capital']
  assert capital in counties
  assert capital not in capital_owners,('Overlapping capital',capital)
  capital_owners[capital]=title
 assert active==72 and len(owned)==980
 for c,r in original.items():
  if r not in affected:assert allocation[c]==r
 for rel,text in products.items():
  p=O/'staged'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8-sig')
 if '--apply' in sys.argv:
  for rel in products:assert (M/rel).read_bytes()==(base/rel).read_bytes()
  for rel in products:(M/rel).write_bytes((O/'staged'/rel).read_bytes())
  for folder in ('common/landed_titles','history/titles/ce3','map_data/geographical_regions'):
   for p in (base/folder).glob('*.txt'):
    rel=p.relative_to(base)
    if rel not in products:assert p.read_bytes()==(M/rel).read_bytes()
 report={'backup':str(B),'active_regions':active,'counties':len(owned),'overlapping_counties':0,'overlapping_active_capitals':0,
         'restored_titles':{title:{'capital':seat,'counties':transfers[title]} for title,_,_,seat,_ in changespec},
         'other_regions_and_capitals_unchanged':True,'cardinal_histories_unchanged':True,'validation':'passed','in_game_test_performed':False}
 (O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 (O/'county_assignment.json').write_text(json.dumps(allocation,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
 sys.stdout.reconfigure(encoding='utf-8');main()
