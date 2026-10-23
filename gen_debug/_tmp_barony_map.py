import re, glob, json, os
MOD="D:/Documents/Paradox Interactive/Crusader Kings III/mod/EU5_Modern_Borders_noshape"
# 1. baronies that have a holder in zz_eu5_titles.txt
baronies=set()
inblock=None
with open(f"{MOD}/history/titles/zz_eu5_titles.txt",encoding="utf-8-sig") as f:
    for line in f:
        m=re.match(r'^([bcdekh])_([a-z0-9_]+)\s*=\s*\{',line)
        if m:
            inblock=f"{m.group(1)}_{m.group(2)}"
        elif re.match(r'^\s*\}\s*$',line):
            inblock=None
        elif inblock and re.match(r'\s*holder\s*=',line) and inblock.startswith('b_'):
            baronies.add(inblock)
print("added barony lords (b_ with holder):",len(baronies))

# 2. parse landed_titles: b_ -> province, enclosing c_, enclosing k_, enclosing e_
stack=[]
b_info={}  # b_ -> {prov, c, k, e}
cur={}
for fn in glob.glob(f"{MOD}/common/landed_titles/*.txt"):
    if fn.endswith(".bak"): continue
    with open(fn,encoding="utf-8-sig") as f:
        for line in f:
            s=line.strip()
            m=re.match(r'^([bcdekh])_([a-z0-9_]+)\s*=\s*\{',s)
            if m:
                tid=f"{m.group(1)}_{m.group(2)}"
                stack.append(tid)
                cur={'prov':None,'c':None,'k':None,'e':None}
                for t in reversed(stack):
                    if t.startswith('c_') and cur['c'] is None: cur['c']=t
                    if t.startswith('k_') and cur['k'] is None: cur['k']=t
                    if t.startswith('e_') and cur['e'] is None: cur['e']=t
                if tid.startswith('b_'):
                    b_info[tid]=cur
                continue
            mp=re.match(r'^province\s*=\s*(\d+)',s)
            if mp and stack and stack[-1].startswith('b_'):
                b_info[stack[-1]]['prov']=int(mp.group(1))
                continue
            if s=='}':
                if stack: stack.pop()
print("baronies parsed in landed_titles:",len(b_info))

# 3. join
matched=[b for b in baronies if b in b_info]
print("matched to province:",len(matched))
missing=[b for b in baronies if b not in b_info]
print("missing province mapping:",len(missing))
from collections import Counter
kc=Counter(b_info[b]['k'] for b in matched)
ec=Counter(b_info[b]['e'] for b in matched)
print("distinct de-jure kingdoms:",len(kc))
print("distinct de-jure empires:",len(ec))
print("top kingdoms:",kc.most_common(10))
print("top empires:",ec.most_common(15))
# save matched info
out={b:{'prov':b_info[b]['prov'],'k':b_info[b]['k'],'e':b_info[b]['e']} for b in matched}
with open(f"{MOD}/gen_debug/_tmp_barony_matched.json","w",encoding="utf-8") as f:
    json.dump(out,f)
