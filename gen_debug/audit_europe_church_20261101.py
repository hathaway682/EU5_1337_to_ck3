"""Read-only county audit using Stanford Corpus Synodalium atlas (CC BY 3.0).

Atlas: Dorin, Romani, Schlansky and Womack, 2021,
https://doi.org/10.25740/rh195hm5975. Atlas 1350 polygons are adapted via
the project's Gall/Miller georeference and 1337 title/region definitions.
The source is an approximation, not a map of exactly 1337.
"""
from pathlib import Path
from collections import Counter,defaultdict
import importlib.util,json,zipfile,sys,re
from shapely.geometry import shape,Point
from shapely.strtree import STRtree
import rebuild_geographical_regions_20261031 as g
import rebuild_ecclesiastical_titles_20261101 as h

M=Path(__file__).resolve().parents[1]
B=Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261101_082521_europe_church_audit')
O=M/'gen_debug/european_church_audit_20261101'

def main():
 O.mkdir(exist_ok=True);base=B/'mod'
 spec=importlib.util.spec_from_file_location('geo',B/'inputs/_georef.py');geo=importlib.util.module_from_spec(spec);spec.loader.exec_module(geo)
 ts,bs,anc=g.titles(base/'common/landed_titles')
 alloc=json.loads((base/'gen_debug/church_control_cleanup_20261101/county_assignment.json').read_text())
 history={}
 for p in (base/'history/titles/ce3').glob('*.txt'):
  for k,n in g.parse(h.read(p))[0]:history[k]=h.state(n,(1337,4,1))
 bytitle={k:n['clerical_region'] for k,n in history.items() if n.get('clerical_region','none')!='none'}
 titledefs={}
 for p in (base/'common/landed_titles').glob('*.txt'):
  for k,n in g.parse(h.read(p))[0]:titledefs[k]=n
 capmap={dict(titledefs[t][0])['capital']:r for t,r in bytitle.items()}
 protected=set(json.loads((base/'gen_debug/church_control_cleanup_20261101/report.json').read_text())['scottish_counties_directly_under_rome'])
 protected|={'c_prilep','c_noto','c_north_dalmatia','c_capitanata','c_montana','c_soria'}
 controlled={r for r in alloc.values() if r in ('eu5_et_1337_pec_region','eu5_et_1337_tarnovo_region','eu5_et_1337_halych_region')}
 aliases={'Bremen':'hamburg','Prague':'mainz','Seville':'sevilla','Nicosia':'cyprus','Reggio-Calabria':'reggio_calabria',
          'Santiago':'santiago','Zaragoza':'zaragoza','Monreale':'monreale','Toulouse':'toulouse','Riga':'riga',
          'Gniezno':'gniezno','Santa Severina':'santa_severina'}
 unknown={'Exempt Diocese','Scotland','Halyč','Zadar','Bar','Grado','Manfredonia','Sorrento','Amalfi','Conza','Acerenza','Taranto','Otranto','Candia'}
 z=zipfile.ZipFile(B/'inputs/GeoJSONs-Feb2021.zip')
 features=json.loads(z.read('GeoJSONs-Feb2021/province1350.json'))['features']
 shapes=[];targets=[];feature_info=[];skipped=[]
 for f in features:
  p=f['properties'];name=p['Dioc_Prov_'];start=p.get('StartDate1') or 0;end=p.get('EndDate1') or 9999
  if name in unknown:skipped.append(name);continue
  if name!='Prague' and not (start<=1337<=end):
   if name!='Mainz':continue
  key='d_et_'+aliases.get(name,name.casefold().replace('-','_').replace(' ','_'))
  if key not in bytitle:skipped.append(name+':'+key);continue
  shapes.append(shape(f['geometry']));targets.append(bytitle[key]);feature_info.append((name,key))
 tree=STRtree(shapes)
 loc=h.read(base/'gfx/map/map_object_data/building_locators.txt')
 coords={int(p):(float(x),8191-float(z)) for p,x,_,z in re.findall(r'\bid\s*=\s*(\d+)\s+position\s*=\s*\{\s*([\d.-]+)\s+([\d.-]+)\s+([\d.-]+)',loc)}
 votes=defaultdict(Counter);names=defaultdict(Counter);samples=defaultdict(list)
 for bar,pid in bs.items():
  if pid not in coords:continue
  county=anc[bar][-2];lon,lat=geo.eu5_px_to_lonlat(*coords[pid])
  if not (-25<=lon<=42 and 34<=lat<=72):continue
  hits=tree.query(Point(lon,lat),predicate='within')
  found={targets[int(i)] for i in hits}
  if len(found)==1:
   reg=next(iter(found));votes[county][reg]+=1
   names[county][feature_info[int(hits[0])][0]]+=1
   samples[county].append((bar,reg))
  elif len(found)>1:samples[county].append((bar,'OVERLAP:'+','.join(sorted(found))))
 result=[]
 for c,cnt in sorted(votes.items()):
  top,count=cnt.most_common(1)[0];total=sum(cnt.values());old=alloc.get(c,'')
  result.append({'county':c,'current_region':old,'atlas_region':top,'atlas_votes':count,'atlas_samples':total,
   'confidence':round(count/total,3),'capital_locked':c in capmap,'user_protected':c in protected,
   'controlled_church':old in controlled or top in controlled,'atlas_names':dict(names[c]),'sample_baronies':samples[c]})
 (O/'atlas_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 (O/'atlas_sources.json').write_text(json.dumps({'source':'https://doi.org/10.25740/rh195hm5975','license':'https://creativecommons.org/licenses/by/3.0/',
  'source_file':'GeoJSONs-Feb2021/province1350.json','notes':'Adapted to 1337 county geometry; map represents around 1350. Prague attributed to Mainz before 1344. Exempt dioceses and unsupported sees are not force-mapped.',
  'mapped_features':len(shapes),'skipped_features':skipped},ensure_ascii=False,indent=2),encoding='utf-8')
 mismatches=[x for x in result if x['current_region'] and x['current_region']!=x['atlas_region'] and not x['capital_locked'] and not x['user_protected'] and not x['controlled_church'] and x['confidence']>=0.7 and x['atlas_samples']>=2]
 print('audited counties',len(result),'high-confidence existing mismatches',len(mismatches),'unmapped names',sorted(set(skipped)))
 for x in mismatches:print(x['county'],x['current_region'],'->',x['atlas_region'],x['atlas_votes'],'/',x['atlas_samples'])

if __name__=='__main__':
 sys.stdout.reconfigure(encoding='utf-8');main()
