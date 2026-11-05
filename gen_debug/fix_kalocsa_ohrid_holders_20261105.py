from pathlib import Path
import json,sys
import rebuild_geographical_regions_20261031 as g
import rebuild_ecclesiastical_titles_20261101 as h
M=Path(__file__).resolve().parents[1]
B=Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261105_181125_kalocsa_ohrid/mod')
O=M/'gen_debug/kalocsa_ohrid_holders_20261105'
rel=Path('history/titles/ce3/00_ecclesiastical_titles.txt')
source=h.read(B/rel);nodes=dict(g.parse(source)[0]);changes={}
targets={'d_et_kalocsa':'eu5_archbishop_1337_harkacsi','d_et_ohrid':'eu5_archbishop_1337_nicholas_ohrid'}
for title,holder in targets.items():
 node=nodes[title];state=h.state(node,(1337,4,1));assert state['holder']=='0' and state['clerical_region']!='none'
 fields=[]
 for key,value in node[0]:
  if key=='1337.4.1':value=([(k,holder if k=='holder' else v) for k,v in value[0]],value[1])
  fields.append((key,value))
 changes[title]='\n'.join(h.render(([(title,(fields,node[1]))],[])))
out=h.replace_blocks(source,changes);newnodes=dict(g.parse(out)[0])
assert all(nodes[k]==newnodes[k] for k in nodes if k not in targets)
for k,holder in targets.items():
 old=h.state(nodes[k],(1337,4,1));new=h.state(newnodes[k],(1337,4,1))
 assert new['holder']==holder and all(old[x]==new[x] for x in old if x!='holder')
for p in (B/'history/characters').glob('*.txt'):
 assert not (set(targets.values()) & dict(g.parse(h.read(p))[0]).keys())
people='''# Explicitly selected 1337 holders; birth dates are provisional.
eu5_archbishop_1337_harkacsi = {
 name = "eu5_archbishop_1337_harkacsi_name"
 culture = hungarian
 religion = catholic
 trait = celibate
 trait = education_learning_3
 1280.1.1 = { birth = yes }
}

eu5_archbishop_1337_nicholas_ohrid = {
 name = "eu5_archbishop_1337_nicholas_ohrid_name"
 culture = greek
 religion = orthodox
 rite = slavic_rite
 trait = celibate
 trait = education_learning_3
 1280.1.1 = { birth = yes }
}
'''
products={rel:out,Path('history/characters/zz_kalocsa_ohrid_archbishops_1337.txt'):people,
 Path('localization/english/kalocsa_ohrid_archbishops_1337_l_english.yml'):'l_english:\n eu5_archbishop_1337_harkacsi_name:0 "Stephen Harkácsi"\n eu5_archbishop_1337_nicholas_ohrid_name:0 "Nicholas"\n',
 Path('localization/simp_chinese/kalocsa_ohrid_archbishops_1337_l_simp_chinese.yml'):'l_simp_chinese:\n eu5_archbishop_1337_harkacsi_name:0 "伊什特万·哈尔卡奇"\n eu5_archbishop_1337_nicholas_ohrid_name:0 "尼古拉"\n'}
O.mkdir(parents=True,exist_ok=True)
for rel,text in products.items():
 if rel.suffix=='.txt':g.parse(text)
 p=O/'staged'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8-sig')
if '--apply' in sys.argv:
 for rel in products:
  if (B/rel).exists():assert (B/rel).read_bytes()==(M/rel).read_bytes()
  else:assert not (M/rel).exists()
 for rel in products:
  (M/rel).parent.mkdir(parents=True,exist_ok=True);(M/rel).write_bytes((O/'staged'/rel).read_bytes())
 for rel in products:assert (M/rel).read_bytes()==(O/'staged'/rel).read_bytes()
print(json.dumps({'holders':targets,'birth_dates_provisional':True,'in_game_test_performed':False},ensure_ascii=True))
