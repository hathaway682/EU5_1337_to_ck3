"""1337 ecclesiastical districts. No new rites, faiths, or county boundaries.

Sources and county-resolution compromises are documented in the output report.
The user explicitly approved c_noto as Monreale's proxy capital.
"""
from pathlib import Path
from collections import defaultdict
import json
import csv
import sys
import re
import rebuild_geographical_regions_20261031 as g
import rebuild_ecclesiastical_titles_20261101 as h

M=Path(__file__).resolve().parents[1]
B=Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261101_073204_church_1337')
O=M/'gen_debug/church_regions_1337_20261101'
SOURCES={
 'Monreale':'https://www.diocesimonreale.it/diocesi/storia-2/',
 'Toulouse':'https://toulouse.catholique.fr/diocese/histoire/',
 'Zaragoza':'https://www.iglesiaenaragon.com/los-obispos-de-aragon-acompanan-al-arzobispo-carlos-en-la-imposicion-del-palio',
 'Riga':'https://old.historia.lv/alfabets/R/ri/rigas_arhbisk/rigas_arhbisk.htm',
 'Halych':'https://www.encyclopediaofukraine.com/display.asp?linkpath=pages%5CH%5CA%5CHalychmetropoly.htm',
 'Pec':'https://srpskaenciklopedija.rs/books/slovo-d/page/danilo-ii/revisions/24827/changes',
 'Tarnovo':'https://bg-patriarshia.bg/tarnovo-patriarchs',
 'Scotland':'https://www.scottishcatholicarchives.org.uk/Portals/0/Scottish-Catholic-Directory/1980-1989/1982.pdf',
 'Moscow':'https://www.oca.org/saints/lives/2017/12/21/103604-repose-of-saint-peter-metropolitan-of-moscow-wonderworker-of-all',
}


def main():
 O.mkdir(exist_ok=True);base=B/'mod'
 ts,bs,anc=g.titles(base/'common/landed_titles')
 pc={bs[b]:next(c for c in chain if c.startswith('c_')) for b,chain in anc.items()}
 def counties(duchy):return {ch[-2] for ch in anc.values() if duchy in ch}
 allocation=json.loads((base/'gen_debug/split_trani_seats_20261101/county_assignment.json').read_text())
 original=dict(allocation)
 # name, EN, ZH, capital, counties, existing holder, political liege (optional).
 specs=[
 ('riga','Riga','里加','c_south_livonia',
  (counties('d_baltic')-{'c_estonia'})|(counties('d_prussia')-{'c_danzig','c_tuchola'}),'rig_friedrich_von_pernstein',''),
 ('zaragoza','Zaragoza','萨拉戈萨','c_zaragoza',counties('d_aragon')|counties('d_navarre'),'',''),
 ('monreale','Monreale','蒙雷阿莱','c_noto',{'c_noto'},'',''),
 ('toulouse','Toulouse','图卢兹','c_toulousain',{'c_toulousain','c_foix'},'',''),
 ('halych','Halych','加利奇','c_halych',counties('d_red_ruthenia')|counties('d_volhynia')|{'c_turov'},'',''),
 ('pec','Autocephalous Archbishopric of Pec','佩奇自主大主教区','c_kosovo',counties('d_serbia'),'',''),
 ('tarnovo','Patriarchate of Tarnovo','特尔诺沃牧首区','c_tarnovo',
  (counties('d_bulgaria')-{'c_north_dobruja'})|{'c_sliven','c_zagore'},'bul_theodosius',''),
 ('st_andrews','St Andrews (exempt diocese)','圣安德鲁斯直属教区','c_fife',{'c_fife','c_lothian'},'','k_papal_state'),
 ('glasgow','Glasgow (exempt diocese)','格拉斯哥直属教区','c_strathclyde',{'c_strathclyde','c_teviotdale'},'','k_papal_state'),
 ('dunkeld_dunblane','Dunkeld and Dunblane (exempt dioceses)','邓凯尔德与邓布莱恩直属教区','c_perthshire',{'c_perthshire'},'','k_papal_state'),
 ('brechin','Brechin (exempt diocese)','布里金直属教区','c_angus',{'c_angus'},'','k_papal_state'),
 ('aberdeen','Aberdeen (exempt diocese)','阿伯丁直属教区','c_aberdeenshire',{'c_aberdeenshire'},'','k_papal_state'),
 ('moray','Moray (exempt diocese)','马里直属教区','c_moray',{'c_moray'},'','k_papal_state'),
 ('ross','Ross (exempt diocese)','罗斯直属教区','c_ross',{'c_ross'},'','k_papal_state'),
 ('caithness','Caithness (exempt diocese)','凯思内斯直属教区','c_sutherland',{'c_sutherland'},'','k_papal_state'),
 ('argyll','Argyll (exempt diocese)','阿盖尔直属教区','c_argyll',{'c_argyll'},'','k_papal_state'),
 ]
 assigned=set();new_regions={};new_titles={};new_history={};labels=[];changes=[]
 for index,(name,en,zh,cap,cc,holder,liege) in enumerate(specs):
  title='d_et_'+name;region='eu5_et_1337_'+name+'_region'
  assert cap in cc and cc and cc<=ts.keys();assert not assigned&cc;assigned|=cc
  for c in cc:
   changes.append({'county':c,'previous_region':allocation.get(c,''),'region':region})
   allocation[c]=region
  new_regions[region]=cc
  color=(70+(index*47)%170,55+(index*71)%180,65+(index*31)%170)
  new_titles[title]=([('color',([],list(map(str,color)))),('capital',cap),('landless','yes'),
   ('always_follows_primary_heir','yes'),('no_automatic_claims','yes'),('ai_primary_priority',([('add','-1000')],[]))],[])
  fields=[('government','ecclesiastical_government'),('holder',holder or '0'),('clerical_region',region)]
  dated=[]
  if liege:dated.append(('1337.1.1',([('liege',liege)],[])))
  dated.append(('1337.4.1',(fields,[])))
  new_history[title]=(dated,[]);labels.append((title,en,zh))
 # Tallinn/Reval was a Lund suffragan; Prussian Polish dioceses stay Gniezno.
 for c,r in [('c_estonia','et_1178_lund_region'),('c_north_dobruja','et_1178_constantinople_region')]:
  changes.append({'county':c,'previous_region':allocation.get(c,''),'region':r});allocation[c]=r
 affected={r for c in changes for r in (c['previous_region'],c['region']) if r}
 members=defaultdict(set)
 for c,r in allocation.items():members[r].update(ts[c])
 def region_node(ps):
  rest=set(ps);props=[]
  for prefix,prop in [('d_','duchies'),('c_','counties')]:
   selected=[]
   for key,land in sorted(ts.items()):
    if key.startswith(prefix) and land and land<=rest:selected.append(key);rest-=land
   if selected:props.append((prop,([],selected)))
  assert not rest
  return props,[]
 geo_rel=Path('map_data/geographical_regions/geographical_region.txt')
 original_geo=dict(g.parse(h.read(base/geo_rel))[0])
 geo_changes={r:'\n'.join(h.render(([(r,region_node(members[r]))],[]))) for r in affected if r in original_geo}
 products={geo_rel:h.replace_blocks(h.read(base/geo_rel),geo_changes)}
 newgeo=Path('map_data/geographical_regions/30_eu5_church_1337.txt')
 products[newgeo]='# 1337 church districts. Complete counties only; no new rites.\n'+'\n'.join(h.render(([(r,region_node(members[r])) for r in new_regions],[])))+'\n'
 declarations=Path('common/landed_titles/zzz_eu5_church_1337.txt')
 products[declarations]='# 1337 ecclesiastical districts; Scottish districts are not metropolitan provinces.\n'+'\n'.join(h.render((list(new_titles.items()),[])))+'\n'
 history_rel=Path('history/titles/ce3/03_eu5_church_1337.txt')
 products[history_rel]='# 1337 institutional layout. No new rites; original Slavic-rite histories are preserved.\n'+'\n'.join(h.render((list(new_history.items()),[])))+'\n'
 # Keep Kyiv's historic title/key and canonical dependency, change only residence.
 title_rel=Path('common/landed_titles/07_pam_ecclesiastical_titles.txt')
 original_titles=dict(g.parse(h.read(base/title_rel))[0]);kyiv=original_titles['d_et_kyiv']
 revised=([(k,'c_moscow' if k=='capital' else v) for k,v in kyiv[0]],kyiv[1])
 products[title_rel]=h.replace_blocks(h.read(base/title_rel),{'d_et_kyiv':'\n'.join(h.render(([('d_et_kyiv',revised)],[])))})
 labels.append(('d_et_kyiv','Kyiv and All Rus (Moscow seat)','基辅及全罗斯都主教区（驻莫斯科）'))
 for lang,col in [('english',1),('simp_chinese',2)]:
  rel=Path(f'localization/replace/{lang}/eu5_church_1337_l_{lang}.yml')
  products[rel]='l_'+lang+':\n'+'\n'.join(f' {row[0]}:0 "{row[col]}"' for row in labels)+'\n'
 # Validate actual staged geographical/title/history trees.
 finalgeo=dict(original_geo);finalgeo.update(dict(g.parse(products[geo_rel])[0]));finalgeo.update(dict(g.parse(products[newgeo])[0]))
 finalhist={};finaltitles={}
 for p in (base/'history/titles/ce3').glob('*.txt'):
  for k,n in g.parse(h.read(p))[0]:assert k not in finalhist;finalhist[k]=n
 for k,n in new_history.items():assert k not in finalhist;finalhist[k]=n
 for p in (base/'common/landed_titles').glob('*.txt'):
  for k,n in g.parse(products.get(p.relative_to(base),h.read(p)))[0]:finaltitles[k]=n
 for k,n in new_titles.items():assert k not in finaltitles;finaltitles[k]=n
 chars={}
 for p in (base/'history/characters').glob('*.txt'):
  for k,n in g.parse(h.read(p))[0]:
   prev=chars.get(k,([],[]));chars[k]=(prev[0]+n[0],[])
 seen={};capitals={};active=0
 for k,n in finalhist.items():
  state=h.state(n,(1337,4,1));r=state.get('clerical_region','none')
  if r=='none':continue
  active+=1;ps=h.expand(r,finalgeo,ts,{})
  assert ps,('Empty active church district',k)
  for c in {pc[p] for p in ps}:
   assert c not in seen,(c,k,seen.get(c));assert ts[c]<=ps;seen[c]=k
  cap=dict(finaltitles[k][0])['capital'];assert cap not in capitals,(cap,k,capitals.get(cap));capitals[cap]=k
  assert seen.get(cap)==k,(k,cap)
  holder=state.get('holder','0')
  if holder!='0':assert holder in chars
 assert active==88
 for c,r in original.items():
  if c not in {ch['county'] for ch in changes}:assert allocation[c]==r
 assert allocation['c_galloway']=='et_1178_york_region'
 assert allocation['c_inner_hebrides']==allocation['c_outer_hebrides']=='et_1178_nidaros_region'
 assert h.state(chars['bul_theodosius'],(1337,4,1))['rite']=='slavic_rite'
 for rel,text in products.items():
  if rel.suffix=='.txt':g.parse(text)
  target=O/'staged'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text,encoding='utf-8-sig')
 report={'backup':str(B),'active_districts':active,'counties':len(seen),'overlapping_counties':0,'overlapping_capitals':0,
  'new_districts':16,'new_rites':0,'faith_and_rite_histories_unchanged':True,
  'russian_metropolitan_seat':'c_moscow','moscow_autocephaly_added':False,'serbian_patriarchate_prematurely_added':False,
  'monreale_proxy_capital':'c_noto','sources':SOURCES,'county_changes':changes,
  'approximations':['Dunkeld and Dunblane share c_perthshire; represented together without creating a metropolitan province.',
   'Monreale uses approved c_noto proxy; Catania shares c_demena with Messina and is not separated.',
   'Toulouse covers c_toulousain and c_foix; Montauban shares c_quercy with Cahors and is not separated.',
   'Calahorra shares c_soria with Osma; this boundary county remains in its existing district.',
   'Halych metropolitan status was contested in the 1330s; it is represented separately as requested.'],
  'validation':'passed','in_game_test_performed':False}
 (O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 (O/'county_assignment.json').write_text(json.dumps(allocation,ensure_ascii=False,indent=2),encoding='utf-8')
 with (O/'church_districts.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f);w.writerow(['title','name','capital','counties','holder','liege'])
  for name,en,zh,cap,cc,holder,liege in specs:w.writerow(['d_et_'+name,zh,cap,' '.join(sorted(cc)),holder or '0',liege])
 if '--apply' in sys.argv:
  for rel in products:
   old=(base/rel).read_bytes() if (base/rel).exists() else None
   live=(M/rel).read_bytes() if (M/rel).exists() else None
   assert live in (old,(O/'staged'/rel).read_bytes()),rel
  for rel in products:
   target=M/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((O/'staged'/rel).read_bytes())
  # No changes to rites, religions, populations, characters, or cardinal rosters.
  for folder in ['common/religion','history/characters','history/provinces','history/faiths','history/titles/ce3']:
   for p in (base/folder).rglob('*.txt'):
    assert p.read_bytes()==(M/p.relative_to(base)).read_bytes()
 print(json.dumps({k:v for k,v in report.items() if k not in ('county_changes','sources')},ensure_ascii=False,indent=2))

if __name__=='__main__':
 sys.stdout.reconfigure(encoding='utf-8');main()
