# Part of the PS2 symbol name-map pipeline; see docs/ps2-symbols.md.
"""Match PS2 functions to PC functions.
Pass 1: anchors from shared rare strings (and rare float constants as support).
Pass 2: propagate through call graphs from confident pairs.
Usage: namematch.py xrefs.json pc_thunks.csv out.json"""
import json,math,sys,collections,csv
X=json.load(open(sys.argv[1])); ps2=X['ps2']; pc=X['pc']
# resolve PC thunks (jmp stubs) to their targets via inventory names thunk_FUN_xxxxxxxx
thunk={}
for r in csv.DictReader(open(sys.argv[2])):
    if r['thunk']=='true' and r['name'].startswith('thunk_FUN_'):
        thunk[r['address'].lower()]=r['name'][10:].lower()
def pcalls(a): return [thunk.get(c,c) for c in pc[a]['calls'] if thunk.get(c,c) in pc]
def scalls(a): return [c for c in ps2[a]['calls'] if c in ps2]
LIB=lambda n: n.startswith(('sce','_','Sce')) or (n.islower() and '__' not in n)  # C/SDK library-style names
pset=[a for a in ps2 if not LIB(ps2[a]['name'])]
# ---- feature weights
def feats(v):
    return {('s',s) for s in v['strings']} | {('f',f) for f in v['floats'] if f not in ('00000000','0000803f','000080bf','0000003f')}
F_ps={a:feats(ps2[a]) for a in pset}; F_pc={a:feats(pc[a]) for a in pc}
df_ps=collections.Counter(f for fs in F_ps.values() for f in fs); df_pc=collections.Counter(f for fs in F_pc.values() for f in fs)
def w(f):
    d=max(df_ps[f],df_pc[f])
    if d>4: return 0
    base=3.0 if f[0]=='s' else 1.0
    return base*math.log(1+5/d)
idx=collections.defaultdict(set)
for a,fs in F_ps.items():
    for f in fs:
        if w(f)>0 and df_pc[f]: idx[f].add(a)
score=collections.defaultdict(float)
for b,fs in F_pc.items():
    for f in fs:
        ww=w(f)
        if ww<=0: continue
        for a in idx.get(f,()): score[(a,b)]+=ww
def strong(a,b):
    shared=F_ps[a]&F_pc[b]
    return any(f[0]=='s' for f in shared) or sum(1 for f in shared if w(f)>0)>=3
best_ps=collections.defaultdict(list); best_pc=collections.defaultdict(list)
for (a,b),s in score.items(): best_ps[a].append((s,b)); best_pc[b].append((s,a))
pairs={}; evidence={}
for a,l in best_ps.items():
    l.sort(reverse=True); s,b=l[0]
    second=l[1][0] if len(l)>1 else 0
    l2=sorted(best_pc[b],reverse=True); 
    if l2[0][1]!=a: continue
    second2=l2[1][0] if len(l2)>1 else 0
    if s>=3.0 and s>=1.5*max(second,second2) and strong(a,b):
        pairs[a]=b; evidence[a]={'method':'shared-constants','score':round(s,2),
            'shared':sorted(f[1] for f in F_ps[a]&F_pc[b] if w(f)>0)[:4]}
print('anchors',len(pairs))
# ---- pass 2: call-graph propagation (callees and callers), iterate
rev_pc=collections.defaultdict(set); rev_ps=collections.defaultdict(set)
for b in pc:
    for c in pcalls(b): rev_pc[c].add(b)
for a in pset:
    for c in scalls(a): rev_ps[c].add(a)
def uniq(seq):
    out=[]
    for x in seq:
        if x not in out: out.append(x)
    return out
for it in range(25):
    used=set(pairs.values()); votes=collections.defaultdict(lambda: collections.Counter())
    for a,b in list(pairs.items()):
        cs=[c for c in uniq(scalls(a)) if not LIB(ps2[c]['name'])]; cp=uniq(pcalls(b))
        # drop already-matched on both sides, then align positionally if counts agree
        ms=[c for c in cs if c not in pairs]; mp=[c for c in cp if c not in used]
        known_ok=all((pairs[c] in cp) for c in cs if c in pairs)
        if known_ok and ms and len(ms)==len(mp):
            for x,y in zip(ms,mp): votes[x][y]+=1
        # callers: if both have exactly one unmatched caller
        ps_callers=[c for c in rev_ps.get(a,()) if c not in pairs and c in F_ps]
        pc_callers=[c for c in rev_pc.get(b,()) if c not in used]
        if len(ps_callers)==1 and len(pc_callers)==1: votes[ps_callers[0]][pc_callers[0]]+=1
    added=0; claimed=collections.Counter()
    for x,c in votes.items():
        y,n=c.most_common(1)[0]
        if len(c)==1 or n>=2*c.most_common(2)[1][1]: claimed[y]+=1
    for x,c in votes.items():
        y,n=c.most_common(1)[0]
        if x in pairs or y in used or claimed[y]>1: continue
        if len(c)>1 and n<2*c.most_common(2)[1][1]: continue
        # sanity: size ratio within a broad band (different ISAs)
        r=pc[y]['size']/max(ps2[x]['size'],1)
        if not (0.2<=r<=3.0): continue
        pairs[x]=y; used.add(y); evidence[x]={'method':'call-graph','votes':n,'round':it+1}; added+=1
    print('iteration',it,'added',added,'total',len(pairs))
    if not added: break
json.dump({a:{'pc':b,'ps2_name':ps2[a]['name'],**evidence[a]} for a,b in pairs.items()},open(sys.argv[3],'w'),indent=0)
