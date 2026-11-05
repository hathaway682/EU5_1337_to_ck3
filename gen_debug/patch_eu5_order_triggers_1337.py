"""Allow the reviewed 1337 startup roster while preserving normal order triggers."""
from pathlib import Path
import re,json,hashlib,sys
M=Path(__file__).resolve().parents[1]; B=Path(r'F:/备份/EU5_Modern_Borders_noshape/_backup_20261105_101859_order_startup_and_coa');sys.path.insert(0,str(M/'gen_debug'));import rebuild_geographical_regions_20261031 as parser
rows=json.loads((M/'gen_debug/historical_orders_1337_20261105/inputs/orders.json').read_text(encoding='utf8'))['orders'];expected={r['type_key'] for r in rows if not r['type_key'].startswith('ho_eu5_')}
files=[('mod/common/holy_orders/00_christian_holy_orders.txt','common/holy_orders/00_christian_holy_orders.txt'),('game/common/holy_orders/00_muslim_holy_orders.txt','common/holy_orders/00_muslim_holy_orders.txt')]
outputs={};found=set()
def mask(s):
 return re.sub(r'#[^\n]*|"(?:\\.|[^"\\])*"',lambda m:' '*len(m.group()),s)
def endbrace(s,start):
 depth=0
 for i in range(start,len(s)):
  if s[i]=='{':depth+=1
  if s[i]=='}':
   depth-=1
   if depth==0:return i
 raise ValueError('unclosed brace')
for src,dst in files:
 text=(B/src).read_text(encoding='utf-8-sig');m=mask(text);changes=[]
 for match in re.finditer(r'^([A-Za-z0-9_]+)\s*=\s*\{',m,re.M):
  key=match.group(1)
  if key not in expected:continue
  end=endbrace(m,match.end()-1);body=m[match.end():end];trig=list(re.finditer(r'^\s*\ttrigger\s*=\s*\{',body,re.M));assert len(trig)==1,(key,len(trig))
  op=match.end()+trig[0].end()-1;cl=endbrace(m,op);original=text[op+1:cl].rstrip(' \t')
  wrapped='\n\t\ttrigger_if = {\n\t\t\tlimit = { scope:founder = { has_character_flag = eu5_1337_historical_order_setup } }\n\t\t\talways = yes\n\t\t}\n\t\ttrigger_else = {'+original+'\n\t\t}\n\t'
  changes.append((op+1,cl,wrapped));found.add(key)
 for a,b,new in reversed(changes):text=text[:a]+new+text[b:]
 if dst.endswith('00_christian_holy_orders.txt'):
  old='scope:new_holy_order = { set_order_tenet = tenet:tenet_simony }'
  assert text.count(old)==1
  new='if = {\n\t\t\t\tlimit = { scope:founder = { has_character_flag = eu5_1337_historical_order_setup } }\n\t\t\t\tscope:new_holy_order = { set_order_tenet = tenet:tenet_scholasticism }\n\t\t\t}\n\t\t\telse = { scope:new_holy_order = { set_order_tenet = tenet:tenet_simony } }'
  text=text.replace(old,new)
 parser.parse(text);outputs[dst]=text
assert found==expected,('missing',sorted(expected-found),'extra',sorted(found-expected))
for dst,text in outputs.items():
 target=M/dst;src=B/'mod'/dst
 if target.exists():assert src.exists() and hashlib.sha256(target.read_bytes()).digest()==hashlib.sha256(src.read_bytes()).digest(),('modified input',dst)
 target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b'\xef\xbb\xbf'+text.replace('\r\n','\n').replace('\n','\r\n').encode('utf8'))
print('Patched types:',len(found),'files:',list(outputs))
