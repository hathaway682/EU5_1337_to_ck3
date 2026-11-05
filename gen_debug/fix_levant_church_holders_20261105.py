from pathlib import Path
import hashlib, json, sys
import rebuild_geographical_regions_20261031 as g
import rebuild_ecclesiastical_titles_20261101 as h

M=Path(__file__).resolve().parents[1]
B=Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261105_180211_levant_church_holders/mod')
O=M/'gen_debug/levant_church_holders_20261105'
rel=Path('history/titles/ce3/00_ecclesiastical_titles.txt')
text=h.read(B/rel);nodes=dict(g.parse(text)[0]);changes={}
holder='eu5_antiochian_patriarch_michael_yeshu'
expected={'d_et_antioch':'eu5_archbishop_1337_antioch','d_et_jerusalem':'eu5_archbishop_1337_jerusalem','d_et_tyre':'arb_guido_cattaneo'}
for title,old in expected.items():
 node=nodes[title];state=h.state(node,(1337,4,1));assert state['holder']==old and state['clerical_region']!='none'
 fields=[]
 for key,value in node[0]:
  if key=='1337.4.1':
   value=([(k,(holder if title=='d_et_antioch' else '0') if k=='holder' else v) for k,v in value[0]],value[1])
  fields.append((key,value))
 changes[title]='\n'.join(h.render(([(title,(fields,node[1]))],[])))
title_text=h.replace_blocks(text,changes)
character='''# Michael Yeshu, Syriac Orthodox patriarch of Antioch, 1313–1349.
# Birth date is an explicit gameplay approximation; historical birth is not known.
eu5_antiochian_patriarch_michael_yeshu = {
 name = "eu5_antiochian_patriarch_michael_yeshu_name"
 culture = assyrian
 religion = miaphysitism
 rite = antiochian_rite
 trait = celibate
 trait = education_learning_3
 1280.1.1 = { birth = yes }
}
'''
products={rel:title_text,
 Path('history/characters/zz_antiochian_patriarch_1337.txt'):character,
 Path('localization/english/antiochian_patriarch_1337_l_english.yml'):'l_english:\n eu5_antiochian_patriarch_michael_yeshu_name:0 "Michael Yeshu"\n',
 Path('localization/simp_chinese/antiochian_patriarch_1337_l_simp_chinese.yml'):'l_simp_chinese:\n eu5_antiochian_patriarch_michael_yeshu_name:0 "米海尔·耶稣"\n'}
for p in (B/'history/characters').glob('*.txt'):
 assert holder not in dict(g.parse(h.read(p))[0]),p
oldnodes=dict(g.parse(text)[0]);newnodes=dict(g.parse(title_text)[0])
assert all(oldnodes[k]==newnodes[k] for k in oldnodes if k not in expected)
for k in expected:
 before=h.state(oldnodes[k],(1337,4,1));after=h.state(newnodes[k],(1337,4,1))
 assert before['clerical_region']==after['clerical_region']
 assert all(before.get(f)==after.get(f) for f in before if f!='holder')
 assert after['holder']==(holder if k=='d_et_antioch' else '0')
person=h.state(dict(g.parse(character)[0])[holder],(1337,4,1))
assert person['religion']=='miaphysitism' and person['rite']=='antiochian_rite'
O.mkdir(parents=True,exist_ok=True)
for path,content in products.items():
 if path.suffix=='.txt':g.parse(content)
 p=O/'staged'/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content,encoding='utf-8-sig')
if '--apply' in sys.argv:
 for path in products:
  if (B/path).exists():assert (M/path).read_bytes()==(B/path).read_bytes(),path
  else:assert not (M/path).exists(),path
 for path in products:
  (M/path).parent.mkdir(parents=True,exist_ok=True);(M/path).write_bytes((O/'staged'/path).read_bytes())
 for path in products:assert (M/path).read_bytes()==(O/'staged'/path).read_bytes()
report={'antioch_holder':holder,'antioch_faith':'miaphysitism','antioch_rite':'antiochian_rite','vacant':['d_et_jerusalem','d_et_tyre'],'regions_changed':False,'birth_date_provisional':True,'in_game_test_performed':False,'source':'https://en.wikipedia.org/wiki/List_of_Syriac_Orthodox_patriarchs_of_Antioch'}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=True,indent=2))
