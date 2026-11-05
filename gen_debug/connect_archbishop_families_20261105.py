from pathlib import Path
import json,sys,re
import rebuild_geographical_regions_20261031 as g
import rebuild_ecclesiastical_titles_20261101 as h
M=Path(__file__).resolve().parents[1]
B=Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261105_182856_archbishop_families/mod')
O=M/'gen_debug/archbishop_families_20261105'
assign={'toledo':'martinez_luna_dynasty','zaragoza':'luna_dynasty','bourges':'de_rochechouart_dynasty','napoli':'orsini_dynasty','monreale':'orsini_dynasty','ravenna':'michiel_dynasty','braga':'eu5_pereira_dynasty','trani':'eu5_brancaccio_dynasty'}
rel=Path('history/characters/zz_ecclesiastical_1337_characters.txt');s=h.read(B/rel);spans=h.top_spans(s);blocks={}
for seat,dynasty in assign.items():
 key='eu5_archbishop_1337_'+seat;block=s[slice(*spans[key])]
 assert not re.search(r'\b(?:dynasty|dynasty_house)\s*=',block)
 match=re.search(r'(?m)^[ \t]*name[ \t]*=[^\n]*\n',block);assert match
 pos=match.end()
 blocks[key]=block[:pos]+' dynasty = '+dynasty+'\n'+block[pos:]
chartext=h.replace_blocks(s,blocks)
before=dict(g.parse(s)[0]);after=dict(g.parse(chartext)[0]);assert before.keys()==after.keys()
for k in before:
 if k not in blocks:assert before[k]==after[k]
 else:
  props=after[k][0];assert [(a,b) for a,b in props if a!='dynasty']==before[k][0]
  assert dict(props)['dynasty']==assign[k.removeprefix('eu5_archbishop_1337_')]
dyntext='''# New families for historically attested archbishops, not found in existing EU5 family definitions.
eu5_pereira_dynasty = {
 name = "eu5_pereira_dynasty_name"
 culture = portuguese
}

eu5_brancaccio_dynasty = {
 name = "eu5_brancaccio_dynasty_name"
 culture = italian
}
'''
existing=set()
for p in (B/'common/dynasties').glob('*.txt'):existing.update(dict(g.parse(h.read(p))[0]))
assert set(assign.values())-{'eu5_pereira_dynasty','eu5_brancaccio_dynasty'}<=existing
assert not ({'eu5_pereira_dynasty','eu5_brancaccio_dynasty'}&existing)
en={'toledo':'Jimeno','zaragoza':'Pedro López','bourges':'Foucaud','napoli':'Giovanni','monreale':'Napoleone','ravenna':'Francesco','braga':'Gonçalo','trani':'Bartolomeo'}
zh={'toledo':'希梅诺','zaragoza':'佩德罗·洛佩斯','bourges':'富科','napoli':'乔万尼','monreale':'拿破仑','ravenna':'弗朗切斯科','braga':'贡萨洛','trani':'巴尔托洛梅奥'}
products={rel:chartext,Path('common/dynasties/zz_ecclesiastical_1337_families.txt'):dyntext,
 Path('localization/english/ecclesiastical_1337_families_l_english.yml'):'l_english:\n eu5_pereira_dynasty_name:0 "Pereira"\n eu5_brancaccio_dynasty_name:0 "Brancaccio"\n',
 Path('localization/simp_chinese/ecclesiastical_1337_families_l_simp_chinese.yml'):'l_simp_chinese:\n eu5_pereira_dynasty_name:0 "佩雷拉"\n eu5_brancaccio_dynasty_name:0 "布兰卡乔"\n'}
for lang,table in [('english',en),('simp_chinese',zh)]:
 path=Path('localization')/lang/('ecclesiastical_1337_l_'+lang+'.yml');txt=h.read(B/path)
 for seat,name in table.items():
  pattern=r'(?m)^(\s*eu5_archbishop_1337_'+seat+r'_name:\d+[ \t]+)"[^"]+"[ \t]*$'
  txt,n=re.subn(pattern,lambda m:m.group(1)+'"'+name+'"',txt);assert n==1,(seat,lang,n)
 products[path]=txt
O.mkdir(parents=True,exist_ok=True)
for path,txt in products.items():
 if path.suffix=='.txt':g.parse(txt)
 p=O/'staged'/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(txt,encoding='utf-8-sig')
if '--apply' in sys.argv:
 for path in products:
  if (B/path).exists():assert (B/path).read_bytes()==(M/path).read_bytes(),path
  else:assert not (M/path).exists(),path
 for path in products:
  (M/path).parent.mkdir(parents=True,exist_ok=True);(M/path).write_bytes((O/'staged'/path).read_bytes())
 for path in products:assert (M/path).read_bytes()==(O/'staged'/path).read_bytes()
(O/'report.json').write_text(json.dumps({'assignments':assign,'new_families':['eu5_pereira_dynasty','eu5_brancaccio_dynasty'],'parent_relations_added':False},indent=2),encoding='utf8')
print('Validated',len(assign),'assignments and two new families')
