"""1337 cardinals from EU5's authored seat comments, excluding the sitting pope.

Missing character records use an explicitly provisional birth date (age 50).
All overwritten inputs/products are snapshotted on F:.
"""
from pathlib import Path
import csv
import json
import re
import sys
import rebuild_geographical_regions_20261031 as g
import rebuild_ecclesiastical_titles_20261101 as h

M = Path(__file__).resolve().parents[1]
B = Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261101_061214_cardinals_1337')
O = M / 'gen_debug/cardinals_1337_20261101'
# EU5 support location, person, roman titular church, existing character key.
DATA = [
 ('rome','Giacomo Stefaneschi Caetani','贾科莫·斯泰法内斯基·卡埃塔尼','san_giorgio',''),
 ('tivoli','Napoleone Orsini','拿破仑·奥尔西尼','san_adriano','pap_napoleone_cardinale_orsini'),
 ('palestrina','Giovanni Colonna','乔万尼·科隆纳','san_angelo',''),
 ('velletri','Bertrand du Pouget','贝特朗·迪普热','ostia',''),
 ('toulouse','Jean-Raymond de Comminges','让－雷蒙·德·科曼日','porto','pap_jean_raymond_comminges'),
 ('bazas','Raymond Guilhem de Fargues','雷蒙·吉扬·德·法尔格','santa_maria_nuova',''),
 ('lyon','Bertrand de Montfavez','贝特朗·德·蒙法韦','santa_maria_in_aquiro',''),
 ('langres','Imbert Dupuis','安贝尔·迪皮','santi_apostoli',''),
 ('paris','Gauscelin de Jean','戈斯兰·德·让','albano',''),
 ('bourges',"Pierre Bertrand d'Annonay",'皮埃尔·贝特朗·达诺奈','san_clemente',''),
 ('narbonne','Gaillard de la Mothe','盖亚尔·德·拉莫特','santa_lucia',''),
 ('auxerre','Hélie de Talleyrand-Périgord','埃利·德·塔列朗－佩里戈尔','san_pietro','pap_helie_talleyrand_perigord'),
 ('manfredonia','Matteo Orsini','马泰奥·奥尔西尼','santi_giovanni_e_paolo',''),
 ('naples','Annibaldo di Ceccano','安尼巴尔多·迪·切卡诺','frascati',''),
 ('aix_en_provence','Pierre des Près','皮埃尔·德普雷','palestrina',''),
 ('cartagena','Pedro Gómez Barroso','佩德罗·戈麦斯·巴罗索','santa_prassede',''),
]


def main():
 O.mkdir(exist_ok=True)
 source = h.read(B/'inputs/13_religion.txt')
 locations = re.findall(r'seat_of_cardinal\s*=\s*\{[^}]*location\s*=\s*(\w+)',source)
 assert len(locations)==17 and set(locations)-{'avignon'}=={r[0] for r in DATA}
 ts,bs,anc=g.titles(B/'mod/common/landed_titles')
 chars={}
 for p in (B/'mod/history/characters').glob('*.txt'):
  for k,n in g.parse(h.read(p))[0]:
   prev=chars.get(k,([],[]));chars[k]=(prev[0]+n[0],[])
 ph=dict(g.parse(h.read(M/'history/provinces/00_generated_provinces.txt'))[0])
 declaration_keys=set()
 for p in (B/'mod/common/landed_titles').glob('*.txt'):
  declaration_keys.update(k for k,n in g.parse(h.read(p))[0])
 status_rel=Path('history/titles/ce3/01_cardinalate_status.txt')
 status=h.read(B/'mod'/status_rel)
 status_nodes=dict(g.parse(status)[0]);status_changes={}
 new_history=[];new_chars=[];rows=[];en=[];zh=[]
 for location,name,name_zh,church,existing in DATA:
  title='d_cd_'+church;holder=existing or 'eu5_cardinal_'+location
  barony='b_'+('rome' if location=='rome' else location)
  assert barony in bs
  if existing:
   assert holder in chars and h.state(chars[holder],(1337,4,1))['religion']=='catholic'
  else:
   assert holder not in chars
   province=h.state(ph[str(bs[barony])],(1337,4,1))
   culture=province['culture']
   namekey=holder+'_name'
   en.append(f' {namekey}:0 "{name}"');zh.append(f' {namekey}:0 "{name_zh}"')
   new_chars.append(f'# EU5 seat comment: {name}. Birth is provisional, not historical.\n'+
    '\n'.join(h.render(([(holder,([('name','"'+namekey+'"'),('religion','catholic'),('culture',culture),
      ('trait','celibate'),('trait','education_learning_3'),('1287.1.1',([('birth','yes')],[]))],[]))],[]))))
  effect=[]
  if title in status_nodes:
   old=h.state(status_nodes[title],(1337,4,1));effect+=old.get('effect',([],[]))[0]
  effect += [('add_clerical_elector','faith:catholic'),('set_variable',([('name','named_after'),('value','title:'+barony)],[]))]
  if church=='santa_maria_in_aquiro':
   effect.append(('add_to_global_variable_list',([('name','roma_cardinalates'),('target','title:'+title)],[])))
  fields=[('government','ecclesiastical_government'),('holder',holder),('liege','k_papal_state'),('effect',(effect,[]))]
  text='# '+name+'; EU5 support location: '+location+'\n'+'\n'.join(h.render(([(title,([('1337.4.1',(fields,[]))],[]))],[])))
  if title in status_nodes:status_changes[title]=text
  else:new_history.append(text)
  rows.append({'person':name,'holder':holder,'title':title,'eu5_location':location,'existing_character':bool(existing),
               'birth_date_provisional':not bool(existing),'provisional_birth_date':'' if existing else '1287.1.1'})
 assert len({r['title'] for r in rows})==16 and len({r['holder'] for r in rows})==16
 assert 'pap_benedetto_xii' not in {r['holder'] for r in rows}
 newtitle='d_cd_santa_maria_in_aquiro'
 assert {r['title'] for r in rows}-declaration_keys=={newtitle}
 titletext=f'''# Santa Maria in Aquiro: EU5's Bertrand de Montfavez cardinalate.
{newtitle} = {{
 capital = c_marittima
 landless = yes
 allow_domicile = no
 destroy_on_succession = yes
 no_automatic_claims = yes
 can_be_named_after_dynasty = yes
}}
'''
 en += [' d_cd_santa_maria_in_aquiro:0 "Santa Maria in Aquiro"']
 zh += [' d_cd_santa_maria_in_aquiro:0 "阿奎罗圣母堂"']
 products={status_rel:h.replace_blocks(status,status_changes),
  Path('history/titles/ce3/02_eu5_cardinals_1337.txt'):'# EU5 1337 cardinal roster. The sitting Pope is excluded.\n\n'+'\n\n'.join(new_history)+'\n',
  Path('history/characters/zz_eu5_cardinals_1337.txt'):'# People named only in EU5 seat comments; missing births are explicitly provisional (age 50).\n\n'+'\n\n'.join(new_chars)+'\n',
  Path('common/landed_titles/zzz_eu5_cardinalates_1337.txt'):titletext,
  Path('localization/english/eu5_cardinals_1337_l_english.yml'):'l_english:\n'+'\n'.join(en)+'\n',
  Path('localization/simp_chinese/eu5_cardinals_1337_l_simp_chinese.yml'):'l_simp_chinese:\n'+'\n'.join(zh)+'\n'}
 for rel,text in products.items():
  if rel.suffix=='.txt':g.parse(text)
  target=O/'staged'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text,encoding='utf-8-sig')
 allhist={}
 for p in (B/'mod/history/titles/ce3').glob('*.txt'):
  allhist.update(dict(g.parse(products.get(p.relative_to(B/'mod'),h.read(p)))[0]))
 for k,n in g.parse(products[Path('history/titles/ce3/02_eu5_cardinals_1337.txt')])[0]:
  assert k not in allhist;allhist[k]=n
 for row in rows:
  n=h.state(allhist[row['title']],(1337,4,1));assert n['holder']==row['holder']
  assert ('add_clerical_elector','faith:catholic') in n['effect'][0]
 for title in ('d_cd_velletri','d_cd_santa_rufina'):
  assert h.state(allhist[title],(1337,4,1))==h.state(status_nodes[title],(1337,4,1))
 with (O/'cardinals.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 if '--apply' in sys.argv:
  for rel in products:
   before=(B/'mod'/rel).read_bytes() if (B/'mod'/rel).exists() else None
   live=(M/rel).read_bytes() if (M/rel).exists() else None
   assert live in (before,(O/'staged'/rel).read_bytes()),rel
  for rel in products:
   (M/rel).write_bytes((O/'staged'/rel).read_bytes())
  for p in (B/'mod/history/titles/ce3').glob('*.txt'):
   if p.relative_to(B/'mod') not in products:assert p.read_bytes()==(M/p.relative_to(B/'mod')).read_bytes()
 reused=sum(bool(row[4]) for row in DATA)
 report={'cardinals':16,'existing_characters':reused,'new_characters':16-reused,'new_titular_churches':1,
         'provisional_births':16-reused,'pope_excluded':True,'bishop_histories_unchanged':True,
         'backup':str(B),'validation':'passed','in_game_test_performed':False}
 (O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
 sys.stdout.reconfigure(encoding='utf-8');main()
