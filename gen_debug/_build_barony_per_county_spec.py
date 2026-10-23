import re, glob, json, os
MOD="D:/Documents/Paradox Interactive/Crusader Kings III/mod/EU5_Modern_Borders_noshape"

# 1. added barony lords (b_ with holder) in zz_eu5_titles.txt
added=set()
cur=None
with open(f"{MOD}/history/titles/zz_eu5_titles.txt",encoding="utf-8-sig") as f:
    for line in f:
        m=re.match(r'^([bcdekh])_([a-z0-9_]+)\s*=\s*\{',line)
        if m: cur=f"{m.group(1)}_{m.group(2)}"
        elif re.match(r'^\s*\}\s*$',line): cur=None
        elif cur and cur.startswith('b_') and re.match(r'\s*holder\s*=',line): added.add(cur)

# 2. parse landed_titles: b_ -> province, enclosing c_
stack=[]
b2c={}; b2prov={}
for fn in glob.glob(f"{MOD}/common/landed_titles/*.txt"):
    if fn.endswith(".bak"): continue
    with open(fn,encoding="utf-8-sig") as f:
        for line in f:
            s=line.strip()
            m=re.match(r'^([bcdekh])_([a-z0-9_]+)\s*=\s*\{',s)
            if m:
                tid=f"{m.group(1)}_{m.group(2)}"; stack.append(tid)
                for t in reversed(stack):
                    if t.startswith('c_'):
                        if tid.startswith('b_'): b2c[tid]=t
                        break
                continue
            mp=re.match(r'^province\s*=\s*(\d+)',s)
            if mp and stack and stack[-1].startswith('b_'):
                b2prov[stack[-1]]=int(mp.group(1)); continue
            if s=='}':
                if stack: stack.pop()

# 3. per-county: total barony provinces, added count
from collections import defaultdict
c_total=defaultdict(set)     # c_ -> set(prov)
c_added=defaultdict(int)     # c_ -> added barony count
for b,prov in b2prov.items():
    c=b2c.get(b)
    if not c: continue
    c_total[c].add(prov)
    if b in added: c_added[c]+=1

# 4. prov_values: shade the WHOLE county (all its barony provinces) by its added count
prov_values={}
for c,provs in c_total.items():
    n=c_added.get(c,0)
    if n>=1:
        for p in provs: prov_values[p]=n

print("added baronies total:",len(added))
print("counties with >=1 added barony:",sum(1 for c in c_total if c_added.get(c,0)>=1))
print("counties total:",len(c_total))
from collections import Counter
dist=Counter(c_added[c] for c in c_total if c_added.get(c,0)>=1)
print("added-count distribution (count->#counties):",dict(sorted(dist.items())))

spec={
  "mod_root": MOD,
  "out": f"{MOD}/gen_debug/barony_per_county",
  "title": u"每伯爵领添加的男爵领数（深浅）",
  "subtitle": u"颜色越深 = 该伯爵领内被添加的男爵领越多",
  "layer": "county",
  "prov_values": {str(k):v for k,v in prov_values.items()},
  "color": {"mode":"sequential","hue":0.60,"rarity":"value","gamma":1.0},
  "base": {"unassigned":"#F2F2F2","sea":"#3C78C8","lake":"#3C78C8","impassable_sea":"#3C78C8","waste":"#808080","orphan":"#D9D9D9"},
  "legend": {"enabled":True,"unit":"男爵领/伯爵领","show_counts":True,"width":420}
}
json.dump(spec,open(f"{MOD}/gen_debug/barony_per_county_spec.json","w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("provinces painted:",len(prov_values))
