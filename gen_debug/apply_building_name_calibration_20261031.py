"""Stage named monument positions, preserving vanilla neighboring-barony roles."""
from pathlib import Path
from collections import defaultdict,Counter
import importlib.util,json,re,csv,sys
sys.stdout.reconfigure(encoding='utf-8')
MOD=Path(__file__).resolve().parents[1]
B=Path('F:/备份/EU5_Modern_Borders_noshape/_backup_20261031_220020_building_name_calibration')
OUT=MOD/'gen_debug/building_name_calibration_20261031/calibrated';OUT.mkdir(parents=True,exist_ok=True)
s=importlib.util.spec_from_file_location('g',B/'inputs/rebuild_geographical_regions_20261031.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
def read(p):return p.read_text(encoding='utf-8-sig',errors='replace')
rows=json.loads(read(MOD/'gen_debug/building_name_calibration_20261031/name_audit.json'))
defs={};prev={}
for folder in (B/'inputs/vanilla_buildings',B/'mod/common/buildings'):
 for p in sorted(folder.glob('*.txt')):
  for key,node in g.parse(read(p))[0]:
   if isinstance(node,tuple):defs[key]=node
for key,node in defs.items():
 nxt=dict(node[0]).get('next_building')
 if isinstance(nxt,str):prev[nxt]=key
def family(key):
 seen=set()
 while key in prev:
  assert key not in seen;seen.add(key);key=prev[key]
 return key
_,bs,anc=g.titles(B/'mod/common/landed_titles');rev={p:b for b,p in bs.items()}
extra={'hanging_temple_01':'b_hunyuan','wartburg_01':'b_eisenach','hosios_loukas':'b_livadeia',
       'dazaifu_01':'b_mikasa','wilwatikta_palace_01':'b_trowulan','hpakant_mines_01':'b_phakant',
       'palace_of_ctesiphon_01':'b_dayr_aqul','the_colosseum_01':'b_rome','pam_lateran_basilica_01':'b_velletri'}
# Vanilla deliberately uses an adjacent barony, or a linear wall has multiple sites.
retain={'london_bridge_01','great_wall_of_gorgan_01','liuhe_pagoda_01','dengfeng_observatory_01','phnom_dek_mines_01'}
for row in rows:
 f=row['building_family']
 if f in retain:
  row['named_province']=row['old_province'];row['calibration_rule']='vanilla_neighboring_barony_or_linear_landmark'
 if f in extra:
  row['named_province']=bs[extra[f]];row['calibration_rule']='reviewed_historical_place_name'
 if f=='generic_university' and row['source_barony']=='b_uppsala':
  row['named_province']=bs['b_enkoping'];row['calibration_rule']='nearby_same_county_slot_for_uppsala_temple'
# Preserve original DLC alternatives at their common site.
by_group={(x['source_province'],x['building_family']):x for x in rows}
for row in rows:
 if row['rule'].startswith('shared_original_site_with_'):
  primary=row['rule'].removeprefix('shared_original_site_with_')
  row['named_province']=by_group[(row['source_province'],primary)]['named_province']
  row['calibration_rule']='preserved_vanilla_dlc_alternative'
for row in rows:row['named_barony']=rev[row['named_province']]
slots=defaultdict(list)
for row in rows:
 slot='ducal' if dict(defs[row['building_family']][0]).get('type')=='duchy_capital' else 'special'
 slots[(row['named_province'],slot)].append(row)
for key,items in slots.items():
 if len(items)>1:
  # Same vanilla province: DLC-specific alternatives or replacement at that site.
  assert len({x['source_province'] for x in items})==1,('Unresolved unrelated slot collision',key,[(x['building_family'],x['source_barony']) for x in items])
changes=[x for x in rows if x['old_province']!=x['named_province']]
move={(x['old_province'],x['building_family']):x['named_province'] for x in changes}
COMMANDS={'special_building','special_building_slot','add_special_building','add_special_building_slot','remove_building','duchy_capital_building'}
def walk(node,path=()):
 for k,v in node[0]:
  yield path,k,v
  if isinstance(v,tuple):yield from walk(v,path+(k,))
def belongs(k,v,f):return k in COMMANDS and isinstance(v,str) and v in defs and family(v)==f
def extract(node,f):
 out=[]
 for k,v in node[0]:
  if belongs(k,v,f):out.append((k,v))
  elif isinstance(v,tuple) and k!='limit':
   child=extract(v,f)
   if child[0]:out.append((k,child))
 if out:out=[(k,v) for k,v in node[0] if k=='limit']+out
 if any(k in ('else','else_if') for k,v in out):
  rebuilt=[]
  for k,v in node[0]:
   if isinstance(v,tuple) and k in ('if','else_if','else'):
    child=extract(v,f)
    if not child[0]:child=([(a,b) for a,b in v[0] if a=='limit'],[])
    rebuilt.append((k,child))
   elif k=='limit' or belongs(k,v,f):rebuilt.append((k,v))
   elif isinstance(v,tuple):
    child=extract(v,f)
    if child[0]:rebuilt.append((k,child))
  out=rebuilt
 return out,[]
def remove(node,f):
 return [(k,remove(v,f) if isinstance(v,tuple) else v) for k,v in node[0] if not belongs(k,v,f)],list(node[1])
def render(node,depth=0):
 lines=[]
 for k,v in node[0]:
  if isinstance(v,tuple):lines+=['\t'*depth+k+' = {']+render(v,depth+1)+['\t'*depth+'}']
  else:lines.append('\t'*depth+k+' = '+v)
 if node[1]:lines.append('\t'*depth+' '.join(node[1]))
 return lines
histrel=Path('history/provinces/00_generated_provinces.txt');oldtree=g.parse(read(B/'mod'/histrel));before=dict(oldtree[0]);after={k:(list(v[0]),list(v[1])) for k,v in oldtree[0]}
fragments=defaultdict(list)
for (old,f),new in move.items():
 fragment=extract(before[str(old)],f)
 if fragment[0]:fragments[new].append(fragment)
 after[str(old)]=remove(after[str(old)],f)
for pid,parts in fragments.items():
 for part in parts:after[str(pid)][0].extend(part[0])
holding_changes=[]
for row in changes:
 old,new=row['old_province'],row['named_province'];newprops=dict(after[str(new)][0]);oldprops=dict(before[str(old)][0])
 if newprops.get('holding') in ('none','wilderness_holding') and oldprops.get('holding') not in ('none','wilderness_holding'):
  # Only historical buildings need an inhabited carrier; pure future slots do not.
  built=any(k in ('special_building','add_special_building','duchy_capital_building') for _,k,v in walk(extract(before[str(old)],row['building_family'])))
  built|='on_start' in row['sources'] and row['building_family']!='generic_university'
  if built:
   newholding=oldprops['holding'];after[str(new)]=([(k,newholding if k=='holding' else v) for k,v in after[str(new)][0]],after[str(new)][1]);holding_changes.append({'barony':rev[new],'from':newprops['holding'],'to':newholding})
def counts(tree):return Counter((k,v) for _,k,v in walk(tree) if k in COMMANDS and isinstance(v,str))
newtree=([(k,after[k]) for k,v in oldtree[0]],oldtree[1]);assert counts(oldtree)==counts(newtree)
def nonbuilding(node):
 out=[]
 for k,v in node[0]:
  if k in COMMANDS:continue
  if isinstance(v,tuple):
   v=nonbuilding(v)
   if not v[0] and not v[1]:continue
  out.append((k,v))
 if all(k=='limit' for k,v in out):out=[]
 return out,node[1]
newhold={bs[x['barony']]:x['to'] for x in holding_changes}
for pid,node in before.items():
 expected=nonbuilding(node)
 if int(pid) in newhold:expected=([(k,newhold[int(pid)] if k=='holding' else v) for k,v in expected[0]],expected[1])
 assert expected==nonbuilding(after[pid]),('Unrelated province data changed',pid)

def blocks(text):
 toks=[m for m in g.TOKEN.finditer(text) if not m.group().startswith('#')];stack=[];out=[]
 for i,t in enumerate(toks):
  if t.group()=='{':stack.append((toks[i-2] if i>=2 and toks[i-1].group()=='=' else None,t))
  elif t.group()=='}':
   k,o=stack.pop()
   if k:out.append((k.group(),k.start(),k.end(),o.end(),t.start(),t.end()))
 assert not stack;return out
def edits(text,items):
 for start,end,new in sorted(items,reverse=True):text=text[:start]+new+text[end:]
 return text
startrel=Path('common/on_action/game_start.txt');startup=read(B/'mod'/startrel);replace=[]
for key,start,end,inside,close,_ in blocks(startup):
 match=re.fullmatch(r'title:(b_[\w-]+)\.title_province',key)
 if not match or match[1] not in bs:continue
 roots={family(v) for _,k,v in walk(g.parse(startup[inside:close])) if k in COMMANDS and isinstance(v,str) and v in defs}
 if not roots:continue
 old=bs[match[1]];targets={move.get((old,f),old) for f in roots};assert len(targets)==1,(key,roots,targets)
 new=targets.pop()
 if new!=old:replace.append((start,end,'title:'+rev[new]+'.title_province'))
startup=edits(startup,replace)
assert counts(g.parse(startup))==counts(g.parse(read(B/'mod'/startrel)))
outputs={histrel:'# Historical buildings calibrated by named places; vanilla neighboring-barony arrangements retained.\n'+'\n'.join(render(newtree))+'\n',startrel:startup}
univmap={x['old_barony']:x['named_barony'] for x in changes if x['building_family'] in ('generic_university','siena_university','sankore_university','al_azhar_university')}
for rel,key in [('events/decisions_events/major_decisions_events.txt','major_decisions.2001'),('common/decisions/80_major_decisions.txt','found_university_decision')]:
 text=read(B/'mod'/rel);span=next(x for x in blocks(text) if x[0]==key);body=text[span[3]:span[4]];body=re.sub(r'title:(b_[\w-]+)\b',lambda m:'title:'+univmap.get(m[1],m[1]),body);outputs[Path(rel)]=edits(text,[(span[3],span[4],body)])
for rel,text in outputs.items():
 g.parse(text);p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8-sig')
outrows=[]
for x in rows:
 new=dict(x);new['target_province']=x['named_province'];new['target_barony']=x['named_barony'];new['county']=next(k for k in anc[x['named_barony']] if k.startswith('c_'));outrows.append(new)
with (OUT/'building_locations.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(outrows[0]));w.writeheader();w.writerows(outrows)
summary={'backup':str(B),'audited_arrangements':len(rows),'moved_arrangements':len(changes),'changed_files':list(map(str,outputs)),
 'holding_changes':holding_changes,'changes':[{k:x[k] for k in ('building_family','source_barony','old_barony','named_barony','calibration_rule')} for x in changes],
 'preserved_vanilla_neighboring_cases':sorted(retain),'building_types_unchanged':True,'province_building_command_counts_preserved':True,'startup_building_command_counts_preserved':True,
 'sources':['https://whc.unesco.org/en/list/250','https://whc.unesco.org/en/list/897','https://whc.unesco.org/en/list/537/'], 'tested_in_game':False}
(OUT/'report.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS: audited',len(rows),'arrangements; moved',len(changes),'; startup scopes moved:',len(replace),'; carrier holdings:',len(holding_changes))
print('User examples:',[(x['building_family'],x['named_barony']) for x in rows if x['building_family'] in ('holy_site_basilica_santiago_01','falun_mines_01','temple_of_uppsala_01','citadel_of_aleppo_01')])
if '--apply' in sys.argv:
 for rel in outputs:assert (MOD/rel).read_bytes()==(B/'mod'/rel).read_bytes(),('Changed since backup',rel)
 for rel in outputs:(MOD/rel).write_bytes((OUT/rel).read_bytes())
 print('Applied',len(outputs),'files.')
