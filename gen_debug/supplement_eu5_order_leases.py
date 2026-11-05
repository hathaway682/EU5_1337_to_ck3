from pathlib import Path
import json,sys,math,copy
M=Path.cwd();B=Path(r'F:/备份/EU5_Modern_Borders_noshape/_backup_20261105_105332_eu5_order_leases');sys.path.insert(0,str(M/'gen_debug'));import rebuild_geographical_regions_20261031 as g
p=M/'gen_debug/historical_orders_1337_20261105/inputs';d=json.loads((B/'mod/gen_debug/historical_orders_1337_20261105/inputs/orders.json').read_text(encoding='utf8'));meta=json.loads((p/'map_metadata.json').read_text(encoding='utf8'));coords=json.loads((p/'barony_coordinates.json').read_text(encoding='utf8'));eu=dict(g.parse(g.read(B/'eu5/04_religious_orders.txt'))[0])['religious_order_manager'][0];used={b:r['id'] for r in d['orders'] for b in [r['capital']]+r['branches']};targets={0,11,39,40,41};source={k:dict(n[0])['locations'][1] for k,n in eu};out=[];assigned=set()
def distance(a,b):
 x,y=map(math.radians,a);u,v=map(math.radians,b);return 12742*math.asin(min(1,math.sqrt(math.sin((y-v)/2)**2+math.cos(y)*math.cos(v)*math.sin((x-u)/2)**2)))
def valid(b,kind):
 h=meta[b]['state'].get('holding','none');return not meta[b]['capital'] and b in coords and 'connector' not in b and h in (('none','church_holding','temple_citadel_holding') if kind=='monastic' else ('none','castle_holding','city_holding','temple_citadel_holding'))
# Reserve free exact named sites before using proxies.
reserved={('b_'+loc) for r in d['orders'] if r['id'] in targets for loc in source[r['eu5_source_key']] if 'b_'+loc in meta and 'b_'+loc not in used and valid('b_'+loc,r['ORDER_TYPE'])}
for r in d['orders']:
 if r['id'] not in targets:continue
 sites=[r['capital']]+r['branches'];locs=source[r['eu5_source_key']]
 for loc in locs:
  b='b_'+loc;assert b in meta,b
  if b in sites and b not in assigned:dest=b;status='existing exact'
  elif b in reserved and b not in used:dest=b;status='added exact';r['branches'].append(dest);used[dest]=r['id']
  else:
   options=[x for x in sites if x not in assigned and meta[x]['county']==meta[b]['county']]
   if options:dest=min(options,key=lambda x:distance(coords[b],coords[x]));status='existing proxy'
   else:
    options=[x for x in meta if x not in used and x not in reserved and meta[x]['county']==meta[b]['county'] and valid(x,r['ORDER_TYPE'])]
    if not options:out.append({'order':r['id'],'source':loc,'status':'no available compatible non-capital barony'});continue
    dest=min(options,key=lambda x:distance(coords[b],coords[x]));status='added proxy';r['branches'].append(dest);used[dest]=r['id']
  assigned.add(dest);out.append({'order':r['id'],'source':loc,'barony':dest,'status':status,'county':meta[dest]['county'],'distance_km':round(distance(coords[b],coords[dest]),2)})
# Cistercians retain exactly the ten EU5-mapped locations.
r=next(x for x in d['orders'] if x['id']==11);sites=[x['barony'] for x in out if x['order']==11];assert len(sites)==10 and r['capital'] in sites;r['branches']=[b for b in sites if b!=r['capital']]
# Distribute broad EU5 Benedictine locations to existing branches and reuse their established sites.
by={r['id']:r for r in d['orders']}
reuse={'salzburg':('b_berchtesgaden',17,'b_hallein'),'mainz':('b_offenbach',17,'b_oppenheim'),'sto_domingo_silos':('b_castrojeriz',10,'b_sto_domingo_silos')}
moves={'regensburg':('b_kelheim',8),'bamberg':('b_bamberg',17),'rome':('b_velletri',4),'sahagun':('b_sahagun',10),'jaca':('b_jaca',10)}
for x in out:
 if x['order']!=0:continue
 loc=x['source']
 if loc in reuse:
  old,newid,new=reuse[loc];assert old in by[0]['branches'] and new in [by[newid]['capital']]+by[newid]['branches'];by[0]['branches'].remove(old);used.pop(old);x.update(barony=new,assigned_order_id=newid,status='reused existing monastic lease',county=meta[new]['county'],previous_barony=old,distance_km=round(distance(coords['b_'+loc],coords[new]),2))
 elif loc in moves:
  b,newid=moves[loc];assert b in by[0]['branches'];by[0]['branches'].remove(b);by[newid]['branches'].append(b);used[b]=newid;x.update(assigned_order_id=newid,status='reassigned to Benedictine branch')
 else:x['assigned_order_id']=0
# Keep the other prior headquarters and branches.
old=json.loads((B/'mod/gen_debug/historical_orders_1337_20261105/inputs/orders.json').read_text(encoding='utf8'))
for a,b in zip(old['orders'],d['orders']):
 assert a['id']==b['id'] and a['capital']==b['capital'];assert a['id']==11 or b['branches'][:len(a['branches'])]==a['branches']
 if a['id'] not in targets | {4,8,10,17}:assert a==b
print('added',sum(x['status'].startswith('added') for x in out),'existing',sum(x['status'].startswith('existing') for x in out),'unmapped',[x for x in out if 'barony' not in x]);print('total',len(used))
for row in d['orders']:
 if row['id'] in (1,6):row['rite']='roman_rite'
(p/'orders.json').write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding='utf8');(p/'eu5_lease_supplement_mapping.json').write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
