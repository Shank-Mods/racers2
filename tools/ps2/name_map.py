"""Grade PS2->PC matches and write the name map CSV.
Usage: name_map.py matches.json <source-root> unused <function-inventory.csv> <out.csv>"""
import json,sys,re,collections,statistics,csv
import os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from mwdemangle import split
M=json.load(open(sys.argv[1])); SRC=sys.argv[2]
pcname={}
for dp,_,fs in os.walk(SRC):
    for fn in fs:
        L=open(os.path.join(dp,fn),errors='ignore').read().split('\n')
        for i,l in enumerate(L):
            m=re.match(r'\s*// (FUNCTION|STUB|LIBRARY): LEGORACERS2 (0x[0-9a-f]+)',l)
            if m:
                n=re.search(r'([A-Za-z_][\w:~]*)\s*\(',' '.join(L[i+1:i+4]))
                if n: pcname[int(m.group(2),16)]=n.group(1)
inv={int(r['address'],16):r['name'] for r in csv.DictReader(open(sys.argv[4]))}
norm=lambda c: re.sub(r'^[cs](?=[A-Z])','',c or '')
# class clustering outliers
byc=collections.defaultdict(list)
for a,v in M.items():
    c,m,_=split(v['ps2_name'])
    if c: byc[c].append(int(v['pc'],16))
med={c:statistics.median(l) for c,l in byc.items() if len(l)>=3}
def tier(a,v):
    c,m,_=split(v['ps2_name']); b=int(v['pc'],16)
    if c in med and abs(b-med[c])>0x8000: return 'low'
    if v['method']=='shared-constants':
        sh=v.get('shared',[])
        strs=[s for s in sh if not re.fullmatch(r'[0-9a-f]{8}',s)]
        return 'high' if strs or len(sh)>=3 else 'medium'
    if v.get('votes',1)>=2: return 'medium'
    return 'medium' if v.get('round',99)<=3 else 'low'
SYN={'initialise':'initialize','init':'initialize','shutdown':'release','free':'release','destroy':'release','deinit':'release','dt':'release','ct':'construct','colour':'color','render':'draw'}
def words(s):
    s=re.sub(r'([a-z0-9])([A-Z])',r'\1 \2',s); return {SYN.get(w,w) for w in re.findall(r'[a-z]+',s.lower()) if len(w)>2 and w not in ('fun','the','and','for','object','manager')}
stats=collections.defaultdict(lambda: collections.Counter()); rows=[]
for a,v in M.items():
    t=tier(a,v); c,m,args=split(v['ps2_name']); b=int(v['pc'],16)
    n=pcname.get(b) or inv.get(b,'')
    stats[t]['total']+=1
    if n and not n.startswith('FUN_'):
        stats[t]['named']+=1
        if (words(m)|words(norm(c)))&words(n): stats[t]['shareword']+=1
    ev=v['method']+(': '+'; '.join(v.get('shared',[])) if v['method']=='shared-constants' else ' (round %d, %d vote%s)'%(v['round'],v['votes'],'s' if v['votes']>1 else ''))
    ev=ev.replace('\r','\\r').replace('\n','\\n')
    rows.append(('0x%08x'%b,n,'0x'+a,v['ps2_name'],(norm(c)+'::' if c else '')+m,t,ev))
for t in ('high','medium','low'):
    s=stats[t]; print('%-6s %4d pairs | PC side already named: %3d | of those, share a word with the PS2 name: %3d (%.0f%%)'%(t,s['total'],s['named'],s['shareword'],100*s['shareword']/max(s['named'],1)))
rows.sort()
with open(sys.argv[5],'w',newline='') as f:
    w=csv.writer(f); w.writerow(['pc_address','pc_current_name','ps2_address','ps2_symbol','ps2_name','confidence','evidence']); w.writerows(rows)
print('wrote',len(rows))
