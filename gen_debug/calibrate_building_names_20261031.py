"""Audit fixed monuments against nearby EU5 place names; stage before deployment."""
from pathlib import Path
import importlib.util,json,re,unicodedata,csv
from collections import defaultdict,Counter
MOD=Path(__file__).resolve().parents[1]
B=Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261031_220020_building_name_calibration')
OUT=MOD/'gen_debug/building_name_calibration_20261031';OUT.mkdir(exist_ok=True)
s=importlib.util.spec_from_file_location('g',B/'inputs/rebuild_geographical_regions_20261031.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
def read(p):return p.read_text(encoding='utf-8-sig',errors='replace')
def norm(x):return ''.join(c for c in unicodedata.normalize('NFKD',x.casefold()) if c.isalnum())
def labels(paths):
 d={}
 for p in paths:
  d.update(re.findall(r'^\s*([^\s:#]+):(?:\d+)?\s*"(.*)"\s*$',read(p),re.M))
 def resolve(v,seen=()):
  return re.sub(r'\$([^$]+)\$',lambda m:resolve(d.get(m[1],m[1]),seen+(m[1],)) if m[1] not in seen else m[1],v)
 return {k:resolve(v) for k,v in d.items()}
loc={lang:labels([B/f'mod/localization/{lang}/eu5_titles_l_{lang}.yml']) for lang in ('english','simp_chinese')}
bl={lang:labels((B/f'inputs/vanilla_localization/{lang}').glob('*.yml')) for lang in loc}
ts,bs,anc=g.titles(B/'mod/common/landed_titles');rev={v:k for k,v in bs.items()}
t=read(B/'mod/gfx/map/map_object_data/building_locators.txt')
xy={int(p):(float(x),8191-float(z)) for p,x,_,z in re.findall(r'\bid\s*=\s*(\d+)\s+position\s*=\s*\{\s*([\d.-]+)\s+([\d.-]+)\s+([\d.-]+)',t)}
r=json.loads(read(B/'inputs/all_special_buildings_20261031/report.json'));rows=r['placements']
def dist(a,b):return sum((x-y)**2 for x,y in zip(xy[a],xy[b]))**.5
manual={'holy_site_basilica_santiago_01':'b_santiago_compostela','falun_mines_01':'b_falun','temple_of_uppsala_01':'b_uppsala','citadel_of_aleppo_01':'b_aleppo',
 'alhambra_01':'b_granada','kyz_kala_01':'b_merv','beta_giyorgis_01':'b_lalibela','citadel_linan_01':'b_hangzhou','quanzhou_seaport_01':'b_jinjiang','wulingyuan_01':'b_dayong','ha_long_bay_01':'b_van_don','hanxing_mines_01':'b_handan'}
manual.update({'heddal_stave_church_01':'b_skien','somapura_university_01':'b_naogaon','brihadeeswarar_temple_01':'b_thanjavur',
 'tower_of_hercules_01':'b_coruna','cluny_abbey_01':'b_macon','sanchi_stupa_01':'b_bhilsa','trepca_mines_01':'b_mitrovica',
 'imam_reza_shrine_01':'b_mashhad','buddhas_of_bamian_01':'b_bamyan','confucius_temple_01':'b_qufu',
 'nanhua_temple_01':'b_qujiang','yungang_grottoes_01':'b_datong_datong','pagoda_of_fogong_temple_01':'b_jincheng',
 'leshan_giant_buddha_01':'b_longyou_jiading','lize_academy_01':'b_jinhua','maoshan_academy_01':'b_jurong',
 'liuhe_pagoda_01':'b_hangzhou','itoigawa_mines_01':'b_nishikubiki','koganeyama_mines_01':'b_oshika',
 'plain_of_jars_01':'b_muang_phuan','fairy_chimneys':'b_urgup'})
generic={'generic','university','holy','site','temple','market','bazaar','mines','castle','cathedral','citadel','palace','walls','great','church','of','the','and','for','type','building','grand','duchy','statue','shrine','ancient','roman','stone','tower','mosque','basilica'}
decisions=[]
for row in rows:
 fam=row['building_family'];old=row['target_province'];names=[bl[l].get('building_type_'+fam,bl[l].get('building_'+fam,'')) for l in bl]
 tokens=[w for w in re.sub(r'_\d+$','',fam).split('_') if len(w)>=4 and w not in generic]
 candidates=[]
 for bar,pid in bs.items():
  distance=dist(old,pid)
  if distance>150:continue
  stem=bar[2:];words=stem.split('_');score=0;reason=''
  for tok in tokens:
   if tok==stem:score=max(score,100);reason='building_key_exact_place'
   elif tok in words and len(tokens)==1:score=max(score,80);reason='building_key_place_component'
  for lang,name in zip(bl,names):
   place=loc[lang].get(bar,'');pn=norm(place);bn=norm(name)
   match = re.search(r'(?<!\w)'+re.escape(place.casefold())+r'(?!\w)',name.casefold()) if lang=='english' else len(pn)>=3 and pn in bn
   if len(pn)>=3 and match and '$' not in place:score=max(score,110);reason='localized_building_place_name'
  if score:candidates.append((score,-distance,bar,reason))
 chosen=max(candidates,default=None)
 target=old;rule='retained_geographic_site'
 if chosen:target=bs[chosen[2]];rule=chosen[3]
 if fam in manual:target=bs[manual[fam]];rule='user_identified_named_site'
 if row['rule']=='preserved_silk_road' or fam in ('theodosian_walls_01','aurelian_walls_01'):target=old;rule='preserved_audited_site'
 decisions.append({**row,'old_province':old,'old_barony':rev[old],'named_province':target,'named_barony':rev[target],'calibration_rule':rule,'building_english':names[0],'building_chinese':names[1],'move_distance':round(dist(old,target),2)})
(OUT/'name_audit.json').write_text(json.dumps(decisions,ensure_ascii=False,indent=2),encoding='utf-8')
for d in decisions:
 if d['named_province']!=d['old_province']:print(d['building_family'],d['building_english'],d['old_barony'],'=>',d['named_barony'],d['move_distance'])
print('AUDITED',len(decisions),'CHANGES',sum(d['named_province']!=d['old_province'] for d in decisions))
