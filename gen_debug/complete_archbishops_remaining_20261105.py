from pathlib import Path
import json, sys
import rebuild_geographical_regions_20261031 as g
import rebuild_ecclesiastical_titles_20261101 as h

M=Path(__file__).resolve().parents[1]
B=Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261105_173956_archbishops_remaining')
BASE=B/'mod'; OUT=M/'gen_debug/archbishops_remaining_20261105'
# Seat | name | Chinese | culture | religion | rite | source. Missing dates are provisional.
raw='''
antioch|Mark of Antioch|安条克的马尔科|greek|orthodox||https://stgeorgecleveland.com/about/antioch
cyprus|Élie de Nabinal|埃利·德纳比纳尔|french|catholic||https://en.wikipedia.org/wiki/Archdiocese_of_Nicosia
seleucia_ctesiphon|Denha II|登哈二世|assyrian|nestorian||https://en.wikipedia.org/wiki/List_of_patriarchs_of_the_Church_of_the_East
axum|Yaqob III|雅各布三世|egyptian|miaphysitism|ethiopian_rite|https://en.wikipedia.org/wiki/List_of_abunas_of_Ethiopia
monreale|Napoleone Orsini|拿破仑·奥尔西尼|italian|catholic||https://www.museodiocesanomonreale.it/index.php?Itemid=126&id=20&option=com_content&view=article
halych|Theodore of Halych|加利奇的狄奥多尔|russian|orthodox|slavic_rite|https://www.encyclopediaofukraine.com/display.asp?linkpath=pages%5CH%5CI%5CHistoryoftheUkrainianchurch.htm
'''

records=[]
for line in raw.strip().splitlines():
 seat,name,cn,culture,religion,rite,url=line.split('|');records.append(dict(seat=seat,name=name,cn=cn,culture=culture,religion=religion,rite=rite,source=url,existing=''))
records.append(dict(seat='tyre',name='Guido Cattaneo',cn='圭多·卡塔内奥',culture='italian',religion='catholic',rite='',source='https://en.wikipedia.org/wiki/Archdiocese_of_Oristano',existing='arb_guido_cattaneo'))
hist={}
for p in (BASE/'history/titles/ce3').glob('*.txt'):
 for k,n in g.parse(h.read(p))[0]:
  assert k not in hist;hist[k]=(p.relative_to(BASE),n)
chars={}
for p in (BASE/'history/characters').glob('*.txt'):
 for k,n in g.parse(h.read(p))[0]:chars.setdefault(k,[]).append(n)
changes={};persons=[];en=['l_english:'];zh=['l_simp_chinese:']
for row in records:
 seat=row['seat'];title='d_et_'+seat;rel,node=hist[title];state=h.state(node,(1337,4,1));assert state.get('holder')=='0',(title,state)
 ident=row['existing'] or 'eu5_archbishop_1337_'+seat;row['holder']=ident; row['title']=title
 if row['existing']:
  assert ident in chars
  assert any(h.state(n,(1337,4,1)).get('religion')==row['religion'] for n in chars[ident])
 else:
  assert ident not in chars
  key=ident+'_name';en.append(f' {key}:0 "{row["name"]}"');zh.append(f' {key}:0 "{row["cn"]}"')
  fields=[('name','"'+key+'"'),('culture',row['culture']),('religion',row['religion'])]
  if row['rite']:fields.append(('rite',row['rite']))
  fields.extend([('trait','celibate'),('trait','education_learning_3'),('1280.1.1',([('birth','yes')],[]))])
  persons.append('# Provisional birth date; source: '+row['source']+'\n'+'\n'.join(h.render(([(ident,(fields,[]))],[]))))
  row['birth_provisional']=True
 items=[]
 for k,v in node[0]:
  if k=='1337.4.1':
   fields=[(a,ident if a=='holder' else b) for a,b in v[0]]; assert sum(a=='holder' for a,b in fields)==1;v=(fields,v[1])
  items.append((k,v))
 changes.setdefault(rel,{})[title]='\n'.join(h.render(([(title,(items,node[1]))],[])))
products={rel:h.replace_blocks(h.read(BASE/rel),blocks) for rel,blocks in changes.items()}
products[Path('history/characters/zz_verified_archbishops_batch3_1337.txt')]='# Historically attested incumbents; all 1280 births are placeholders.\n\n'+'\n\n'.join(persons)+'\n'
products[Path('localization/english/verified_archbishops_batch3_l_english.yml')]='\n'.join(en)+'\n'
products[Path('localization/simp_chinese/verified_archbishops_batch3_l_simp_chinese.yml')]='\n'.join(zh)+'\n'
for rel,text in products.items():
 if rel.suffix=='.txt':g.parse(text)
 p=OUT/'staged'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8-sig')
(OUT/'research.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8')
if '--apply' in sys.argv:
 for rel in products:
  if (BASE/rel).exists():assert (BASE/rel).read_bytes()==(M/rel).read_bytes(),rel
  else:assert not (M/rel).exists(),rel
 for rel in products:
  (M/rel).parent.mkdir(parents=True,exist_ok=True);(M/rel).write_bytes((OUT/'staged'/rel).read_bytes())
for row in records:
 rel,_=hist[row['title']]; node=dict(g.parse(h.read(M/rel))[0])[row['title']]
 assert h.state(node,(1337,4,1))['holder']==row['holder']
print('Applied and validated',len(records),'incumbents; reused',sum(bool(r['existing']) for r in records))
