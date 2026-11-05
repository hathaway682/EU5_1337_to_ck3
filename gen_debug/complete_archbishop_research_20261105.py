from pathlib import Path
import json, sys
import rebuild_geographical_regions_20261031 as g
import rebuild_ecclesiastical_titles_20261101 as h

M=Path(__file__).resolve().parents[1]
B=Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261105_172958_archbishops_full')
BASE=B/'mod'; OUT=M/'gen_debug/archbishops_batch2_20261105'
# Seat | name | Chinese | culture | religion | rite | source. Missing dates are provisional.
raw='''
sevilla|Juan Sánchez|胡安·桑切斯|castilian|catholic||https://en.wikipedia.org/wiki/Archdiocese_of_Seville
cashel|Eóin Ó Grada|欧因·奥格拉达|irish|catholic||https://en.wikipedia.org/wiki/Archbishop_of_Cashel
tuam|Máel Sechlain Mac Áeda|梅尔·谢赫兰·马克埃达|irish|catholic||https://en.wikipedia.org/wiki/Archbishop_of_Tuam
sens|Guillaume de Brosse|纪尧姆·德布罗斯|french|catholic||https://en.wikipedia.org/wiki/Archdiocese_of_Sens
bourges|Foucaud de Rochechouart|富科·德罗什舒阿尔|french|catholic||https://en.wikipedia.org/wiki/Archdiocese_of_Bourges
bordeaux|Pierre de Luc|皮埃尔·德吕克|occitan|catholic||https://en.wikipedia.org/wiki/Archdiocese_of_Bordeaux
lyon|Guillaume de Sure|纪尧姆·德叙尔|french|catholic||https://en.wikipedia.org/wiki/Archdiocese_of_Lyon
tarentaise|Jacques de Salins|雅克·德萨兰|french|catholic||https://www.catholic-hierarchy.org/bishop/bsalinsj.html
vienne|Bertrand de La Chapelle|贝尔特朗·德拉沙佩勒|french|catholic||https://en.wikipedia.org/wiki/Archdiocese_of_Vienne
auch|Guillaume de Flavacourt|纪尧姆·德弗拉瓦库尔|occitan|catholic||https://en.wikipedia.org/wiki/Archdiocese_of_Auch
besancon|Hugues de Vienne|于格·德维埃纳|french|catholic||https://en.wikipedia.org/wiki/Archdiocese_of_Besan%C3%A7on
aix|Armand de Narcès|阿尔芒·德纳尔塞|occitan|catholic||https://en.wikipedia.org/wiki/Archdiocese_of_Aix
embrun|Bertrand de Déaulx|贝尔特朗·德多|occitan|catholic||https://en.wikipedia.org/wiki/Archdiocese_of_Embrun
genoa|Dino de' Tusci|迪诺·德图斯奇|italian|catholic||https://en.wikipedia.org/wiki/Archdiocese_of_Genoa
cagliari|Gundisalvus Bonihominis|贡迪萨尔武斯·博尼奥米尼斯|sardinian|catholic||https://en.wikipedia.org/wiki/Archdiocese_of_Cagliari
torres|Pietro de Portillo|彼得罗·德波蒂略|sardinian|catholic||https://en.wikipedia.org/wiki/Archdiocese_of_Sassari
reggio_calabria|Pietro de Galganis|彼得罗·德加尔加尼斯|italian|catholic||https://en.wikipedia.org/wiki/Archdiocese_of_Reggio_Calabria-Bova
cosenza|Francesco della Marra|弗朗切斯科·德拉马拉|italian|catholic||https://en.wikipedia.org/wiki/Archdiocese_of_Cosenza-Bisignano
palermo|Theobaldus|特奥巴尔杜斯|sicilian|catholic||https://en.wikipedia.org/wiki/Archdiocese_of_Palermo
ravenna|Francesco Michiel|弗朗切斯科·米凯尔|italian|catholic||https://www.catholic-hierarchy.org/diocese/drace
pisa|Simone Saltarelli|西莫内·萨尔塔雷利|italian|catholic||https://en.wikipedia.org/wiki/Archdiocese_of_Pisa
napoli|Giovanni Orsini|乔万尼·奥尔西尼|italian|catholic||https://escholarship.org/content/qt7d49p517/qt7d49p517.pdf
salerno|Benedictus|本笃|italian|catholic||https://en.wikipedia.org/wiki/Archdiocese_of_Salerno-Campagna-Acerno
benevento|Arnaldo de Brusacco|阿纳尔多·德布鲁萨科|italian|catholic||https://en.wikipedia.org/wiki/Archdiocese_of_Benevento
bari|Rogerius de Sanseverino|罗杰里乌斯·德圣塞韦里诺|italian|catholic||https://catholic-hierarchy.org/diocese/dbabi.html
trani|Bartolomeo Brancaccio|巴尔托洛梅奥·布兰卡乔|italian|catholic||https://en.wikipedia.org/wiki/Archdiocese_of_Trani-Barletta-Bisceglie
brindisi|Guglielmo Isnardi|古列尔莫·伊斯纳尔迪|italian|catholic||https://en.wikipedia.org/wiki/Archdiocese_of_Brindisi-Ostuni
esztergom|Csanád Telegdi|乔纳德·泰莱格迪|hungarian|catholic||https://en.wikipedia.org/wiki/Csan%C3%A1d_Telegdi
split|Domenico Luccari|多梅尼科·卢卡里|croatian|catholic||https://en.wikipedia.org/wiki/Archdiocese_of_Split-Makarska
ragusa|Tommaso|托马索|croatian|catholic||https://www.catholic-hierarchy.org/diocese/ddubr.html
lund|Peder Jensen|佩德·延森|danish|catholic||https://www.catholic-hierarchy.org/events/b1336.html
uppsala|Petrus Filipsson|彼得鲁斯·菲利普松|swedish|catholic||https://en.wikipedia.org/wiki/List_of_archbishops_of_Uppsala
nidaros|Pål Bårdsson|保尔·鲍德松|norwegian|catholic||https://nbl.snl.no/P%C3%A5l_B%C3%A5rdsson
jerusalem|Lazarus of Jerusalem|耶路撒冷的拉匝禄|greek|orthodox||https://en.wikipedia.org/wiki/Greek_Orthodox_Patriarch_of_Jerusalem
zaragoza|Pedro López de Luna|佩德罗·洛佩斯·德卢纳|aragonese|catholic||https://en.wikipedia.org/wiki/Archdiocese_of_Zaragoza
toulouse|Guillaume de Laudun|纪尧姆·德洛丹|occitan|catholic||https://en.wikipedia.org/wiki/Archdiocese_of_Toulouse
pec|Danilo II|达尼洛二世|serbian|orthodox|slavic_rite|https://doiserbia.nb.rs/img/doi/0584-9888/2016/0584-98881653237M.pdf
'''
records=[]
for line in raw.strip().splitlines():
 seat,name,cn,culture,religion,rite,url=line.split('|');records.append(dict(seat=seat,name=name,cn=cn,culture=culture,religion=religion,rite=rite,source=url,existing=''))
records.append(dict(seat='riga',name='Friedrich von Pernstein',cn='弗里德里希·冯佩恩施泰因',culture='saxon',religion='catholic',rite='',source='https://en.wikipedia.org/wiki/Archdiocese_of_Riga',existing='rig_friedrich_von_pernstein'))
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
products[Path('history/characters/zz_verified_archbishops_batch2_1337.txt')]='# Historically attested incumbents; all 1280 births are placeholders.\n\n'+'\n\n'.join(persons)+'\n'
products[Path('localization/english/verified_archbishops_batch2_l_english.yml')]='\n'.join(en)+'\n'
products[Path('localization/simp_chinese/verified_archbishops_batch2_l_simp_chinese.yml')]='\n'.join(zh)+'\n'
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
