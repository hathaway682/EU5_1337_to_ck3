from pathlib import Path
import json, sys
import rebuild_geographical_regions_20261031 as g
import rebuild_ecclesiastical_titles_20261101 as h

M = Path(__file__).resolve().parents[1]
B = Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261105_172232_archbishops_1337')
BASE = B / 'mod'
O = M / 'gen_debug/verified_archbishops_1337_20261105'
# Unknown birth dates are provisional, not claims of historical fact.
DATA = [
 ('toledo','Jimeno de Luna','希梅诺·德卢纳','castilian','catholic','',1262,'https://philobiblon.upf.edu/xtf/servlet/org.cdlib.xtf.dynaXML.DynaXML?gobk=&source=%2Funified%2FDisplay%2F5625BETA.Person.xml&style=Person.xsl'),
 ('santiago','Juan Fernández de Limia','胡安·费尔南德斯·德利米亚','galician','catholic','',1280,'https://www.catholic-hierarchy.org/diocese/dscom.html'),
 ('tarragona','Arnau Sescomes','阿尔瑙·塞斯科梅斯','catalan','catholic','',1280,'https://www.arquebisbattarragona.cat/arquebisbat/historia/'),
 ('braga','Gonçalo Pereira','贡萨洛·佩雷拉','portuguese','catholic','',1280,'https://www.magistricataloniae.org/en/indexmceng/codumentedart/item/mestre-pero.html'),
 ('york','William Melton','威廉·梅尔顿','english','catholic','',1280,'https://archbishopsregisters.york.ac.uk/search/simple?date_facet=1337&display_type=full+display&page=1&rows_per_page=10&search_term=Lands'),
 ('dublin','Alexander de Bicknor','亚历山大·德比克诺尔','english','catholic','',1280,'https://chaptersofdublin.ie/Handcock/tallaght1.htm'),
 ('reims','Jean de Vienne','让·德维埃纳','french','catholic','',1280,'https://en.wikipedia.org/wiki/Jean_de_Vienne_%28bishop%2C_died_1351%29'),
 ('tours','Pierre Frétaud','皮埃尔·弗雷托','french','catholic','',1280,'https://dokumen.pub/the-catholic-encyclopedia-15-tournon-to-zwirner-15.html'),
 ('narbonne','Bernard de Farges','贝尔纳·德法尔格','occitan','catholic','',1280,'https://amesfoundation.law.harvard.edu/papal_spoils/PapalSpoils_2dProofs.pdf'),
 ('milano','Aicardo Antimiani','艾卡尔多·安蒂米亚尼','cisalpine','catholic','ambrosian_rite',1280,'https://www.treccani.it/enciclopedia/aicardo-antimiani_%28Dizionario-Biografico%29/'),
 ('gniezno','Janisław','亚尼斯瓦夫','polish','catholic','',1280,'https://www.wbc.poznan.pl/Content/33588/20590.pdf'),
 ('kyiv','Theognostus of Kyiv','基辅的狄奥格诺斯托斯','greek','orthodox','slavic_rite',1280,'https://life-cheb.ru/en/hramy/perenos-rezidencii-mitropolita-v-moskvu.html'),
]
titles = {}
for p in (BASE/'history/titles/ce3').glob('*.txt'):
 for k,n in g.parse(h.read(p))[0]:
  assert k not in titles
  titles[k]=(p.relative_to(BASE),n)
existing = set()
for p in (BASE/'history/characters').glob('*.txt'):
 existing.update(k for k,n in g.parse(h.read(p))[0])
regions, files = h.load_regions(BASE/'map_data/geographical_regions') if (BASE/'map_data/geographical_regions').exists() else ({},{})
changes, people, en, zh, rows = {}, [], ['l_english:'], ['l_simp_chinese:'], []
for seat,name,cn,culture,religion,rite,birth,url in DATA:
 title='d_et_'+seat; ident='eu5_archbishop_1337_'+seat; namekey=ident+'_name'
 assert ident not in existing
 rel,node=titles[title]; state=h.state(node,(1337,4,1)); old=state['holder']
 assert old == ({'toledo':'pap_gil_alvarez_albornoz','milano':'mlo_giovanni_visconti'}.get(seat,'0'))
 new=[]
 for k,v in node[0]:
  if k=='1337.4.1':
   fields=[(key,ident if key=='holder' else val) for key,val in v[0]]
   assert sum(k=='holder' for k,v in fields)==1
   v=(fields,v[1])
  new.append((k,v))
 changes.setdefault(rel,{})[title]='\n'.join(h.render(([(title,(new,node[1]))],[])))
 fields=[('name','"'+namekey+'"'),('culture',culture),('religion',religion)]
 if rite: fields.append(('rite',rite))
 fields += [('trait','celibate'),('trait','education_learning_3'),(f'{birth}.1.1',([('birth','yes')],[]))]
 people.append('# Birth date is approximate/provisional. Source: '+url+'\n'+'\n'.join(h.render(([(ident,(fields,[]))],[]))))
 en.append(f' {namekey}:0 "{name}"');zh.append(f' {namekey}:0 "{cn}"')
 rows.append({'title':title,'name':name,'holder':ident,'previous_holder':old,'birth_year':birth,'birth_is_approximate':True,'source':url})
products={rel:h.replace_blocks(h.read(BASE/rel),blocks) for rel,blocks in changes.items()}
products[Path('history/characters/zz_verified_archbishops_1337.txt')]='# 1337-04-01 incumbents; provisional birth dates are noted for every person.\n\n'+'\n\n'.join(people)+'\n'
products[Path('localization/english/verified_archbishops_1337_l_english.yml')]='\n'.join(en)+'\n'
products[Path('localization/simp_chinese/verified_archbishops_1337_l_simp_chinese.yml')]='\n'.join(zh)+'\n'
for rel,txt in products.items():
 if rel.suffix=='.txt':g.parse(txt)
 p=O/'staged'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(txt,encoding='utf-8-sig')
O.mkdir(parents=True,exist_ok=True)
(O/'research.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
if '--apply' in sys.argv:
 for rel in products:
  if (BASE/rel).exists():assert (BASE/rel).read_bytes()==(M/rel).read_bytes()
  else:assert not (M/rel).exists()
 for rel in products:
  (M/rel).parent.mkdir(parents=True,exist_ok=True)
  (M/rel).write_bytes((O/'staged'/rel).read_bytes())
 for row in rows:
  rel,_=titles[row['title']];new=dict(g.parse(h.read(M/rel))[0])[row['title']]
  assert h.state(new,(1337,4,1))['holder']==row['holder']
print(json.dumps(rows,ensure_ascii=False,indent=2))
