from pathlib import Path
import json,re,sys
import rebuild_geographical_regions_20261031 as g
import rebuild_ecclesiastical_titles_20261101 as h
M=Path(__file__).resolve().parents[1]
B=Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261105_183807_noble_archbishops/mod')
O=M/'gen_debug/noble_archbishops_20261105'
# seat, family slug, family names, culture, given names; Luccari branch is provisional.
data=[
 ('besancon','vienne','Vienne','维埃纳','french','Hugues','于格'),
 ('sens','brosse','Brosse','布罗斯','french','Guillaume','纪尧姆'),
 ('narbonne','fargues','Fargues','法尔格','occitan','Bernard','贝尔纳'),
 ('auch','flavacourt','Flavacourt','弗拉瓦库尔','french','Guillaume','纪尧姆'),
 ('aix','narces','Narcès','纳尔塞','occitan','Armand','阿尔芒'),
 ('genoa','radicofani','Radicofani','拉迪科法尼','italian','Dino','迪诺'),
 ('esztergom','telegdi','Telegdi','泰莱格迪','hungarian','Csanád','乔纳德'),
 ('uppsala','rumby','Rumby','鲁姆比','swedish','Petrus Filipsson','佩德鲁斯·菲利普松'),
 ('lund','galen','Galen','加伦','danish','Peder Jensen','佩德·延森'),
 ('split','luccari','Luccari','卢卡里','croatian','Domenico','多梅尼科'),
]
archrel=Path('history/characters/zz_ecclesiastical_1337_characters.txt');cardrel=Path('history/characters/zz_eu5_cardinals_1337.txt')
products={}
def update_file(rel, mapping):
 text=h.read(B/rel);spans=h.top_spans(text);changes={};before=dict(g.parse(text)[0])
 for key,dynasty in mapping.items():
  node=before[key];assert 'dynasty' not in dict(node[0]) and 'dynasty_house' not in dict(node[0])
  block=text[slice(*spans[key])];m=re.search(r'(?m)^[ \t]*name[ \t]*=[^\n]*\n',block);assert m
  changes[key]=block[:m.end()]+' dynasty = '+dynasty+'\n'+block[m.end():]
 result=h.replace_blocks(text,changes);after=dict(g.parse(result)[0]);assert before.keys()==after.keys()
 for key in before:
  if key not in mapping:assert before[key]==after[key]
  else:
   assert [(k,v) for k,v in after[key][0] if k!='dynasty']==before[key][0]
   assert dict(after[key][0])['dynasty']==mapping[key]
 products[rel]=result
update_file(archrel,{'eu5_archbishop_1337_'+seat:'eu5_noble_'+slug+'_dynasty' for seat,slug,*_ in data})
update_file(cardrel,{'eu5_cardinal_bazas':'eu5_noble_fargues_dynasty'})
dynasty_ids=['eu5_noble_'+r[1]+'_dynasty' for r in data];existing=set()
for p in (B/'common/dynasties').glob('*.txt'):existing.update(dict(g.parse(h.read(p))[0]))
assert len(set(dynasty_ids))==10 and not set(dynasty_ids)&existing
dynasty_text='# Noble families for 1337 archbishops; Luccari branch remains unconfirmed.\n\n'
for seat,slug,en,zh,culture,given,givzh in data:
 key='eu5_noble_'+slug+'_dynasty'
 dynasty_text+=f'{key} = {{\n name = "{key}_name"\n culture = {culture}\n}}\n\n'
products[Path('common/dynasties/zz_ecclesiastical_noble_families_1337.txt')]=dynasty_text
for lang,index in [('english',5),('simp_chinese',6)]:
 path=Path('localization')/lang/('ecclesiastical_1337_l_'+lang+'.yml');text=h.read(B/path)
 for row in data:
  seat=row[0];pattern=r'(?m)^([ \t]*eu5_archbishop_1337_'+seat+r'_name:\d+[ \t]+)"[^"]+"[ \t]*$'
  text,n=re.subn(pattern,lambda m:m.group(1)+'"'+row[index]+'"',text);assert n==1,(lang,seat,n)
 products[path]=text
 path=Path('localization')/lang/('eu5_cardinals_1337_l_'+lang+'.yml');text=h.read(B/path)
 given='Raymond Guilhem' if lang=='english' else '雷蒙·吉扬'
 text,n=re.subn(r'(?m)^([ \t]*eu5_cardinal_bazas_name:\d+[ \t]+)"[^"]+"[ \t]*$',lambda m:m.group(1)+'"'+given+'"',text);assert n==1
 products[path]=text
 header='l_'+lang+':\n';nameidx=2 if lang=='english' else 3
 lines=[f' eu5_noble_{r[1]}_dynasty_name:0 "{r[nameidx]}"' for r in data]
 products[Path('localization')/lang/('ecclesiastical_noble_families_1337_l_'+lang+'.yml')]=header+'\n'.join(lines)+'\n'
for path,text in products.items():
 if path.suffix=='.txt':g.parse(text)
 if path.suffix=='.yml' and (B/path).exists():
  def keys(t):return re.findall(r'(?m)^[ \t]*(\w+):\d+[ \t]+"',t)
  assert keys(h.read(B/path))==keys(text),path
 p=O/'staged'/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8-sig')
if '--apply' in sys.argv:
 for path in products:
  if (B/path).exists():assert (B/path).read_bytes()==(M/path).read_bytes(),path
  else:assert not (M/path).exists(),path
 for path in products:
  (M/path).parent.mkdir(parents=True,exist_ok=True);(M/path).write_bytes((O/'staged'/path).read_bytes())
 for path in products:assert (M/path).read_bytes()==(O/'staged'/path).read_bytes()
report={'archbishops':len(data),'new_dynasties':len(dynasty_ids),'cardinal':'eu5_cardinal_bazas','luccari_branch':'unconfirmed','parent_relations_added':False}
(O/'report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report))
