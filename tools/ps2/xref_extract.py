# Part of the PS2 symbol name-map pipeline; see docs/ps2-symbols.md.
"""Extract string/float references per function from the PS2 ELF and the PC exe.
Usage: xref_extract.py <ps2_elf> <pc_exe> <function-inventory.csv> <out.json>"""
import sys,struct,csv,json,subprocess,re
import capstone
from capstone import mips as cm, x86 as cx
elf,pcexe,invcsv,out=sys.argv[1:5]

def cstr(get,a,maxlen=512):
    s=bytearray()
    for k in range(maxlen):
        c=get(a+k,1)
        if c is None: return None
        if c==b'\0': break
        s+=c
    else: return None
    if len(s)<4: return None
    if not all(32<=b<127 or b in (9,10,13) for b in s): return None
    if sum(chr(b).isalpha() for b in s)<3: return None
    return s.decode('latin1')

# ---------- PS2 ----------
E=open(elf,'rb').read()
BASE,OFF,SIZE=0x200000,0x100,0x1a2a80
def pget(a,n):
    o=a-BASE
    return E[OFF+o:OFF+o+n] if 0<=o and o+n<=SIZE else None
syms=subprocess.run(['readelf','-s','-W',elf],capture_output=True,text=True).stdout.split('\n')
pfuncs=[]
for l in syms:
    p=l.split()
    if len(p)>=8 and p[3]=='FUNC' and p[7]!='DEFAULT':
        a=int(p[1],16); n=int(p[2]) if not p[2].startswith('0x') else int(p[2],16)
        if n>0: pfuncs.append((a,n,p[7]))
ps2={}
LOADSTORE={0x20,0x21,0x23,0x24,0x25,0x27,0x37,0x1e,0x28,0x29,0x2b,0x3f,0x1f,0x31,0x39}  # lb lh lw lbu lhu lwu ld lq sb sh sw sd sq lwc1 swc1
for a,n,name in pfuncs:
    code=pget(a,n)
    if code is None: continue
    hi={}; strs=[]; flts=[]; calls=[]
    for k in range(0,len(code)-3,4):
        w=struct.unpack_from('<I',code,k)[0]; op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31; imm=w&0xffff; simm=imm-0x10000 if imm&0x8000 else imm
        if op==0x0f: hi[rt]=imm<<16; continue                      # lui
        if op==0x03: calls.append(((a+k)&0xf0000000)|((w&0x3ffffff)<<2)); continue  # jal
        tgt=None
        if op in (0x09,0x19) and rs in hi:                          # addiu/daddiu
            tgt=(hi[rs]+simm)&0xffffffff; hi[rt]=tgt
        elif op==0x0d and rs in hi:                                 # ori
            tgt=hi[rs]|imm; hi[rt]=tgt
        elif op in LOADSTORE and rs in hi:
            tgt=(hi[rs]+simm)&0xffffffff
            if op==0x31:                                            # lwc1 -> float constant
                v=pget(tgt,4)
                if v: flts.append(v.hex())
                if rt in hi and op in (0x23,0x37): hi.pop(rt,None)
                continue
            if op in (0x23,0x37,0x20,0x21,0x24,0x25,0x27,0x1e): hi.pop(rt,None)
        elif op==0x11 and rs==4 and rt in hi:                       # mtc1: float built in a register
            flts.append(struct.pack('<I',hi[rt]).hex()); continue
        else:
            # any other write to a tracked register invalidates it (R-type rd, I-type rt)
            if op==0 : hi.pop((w>>11)&31,None)
            elif op not in (0x04,0x05,0x01,0x02,0x2b,0x28,0x29,0x3f,0x1f,0x39,0x14,0x15,0x06,0x07,0x16,0x17): hi.pop(rt,None)
        if tgt is not None:
            s_=cstr(pget,tgt)
            if s_: strs.append(s_)
    ps2['%08x'%a]={'name':name,'size':n,'strings':strs,'floats':flts,'calls':['%08x'%c for c in calls]}

# ---------- PC ----------
P=open(pcexe,'rb').read()
pe=struct.unpack_from('<I',P,0x3c)[0]; opt=pe+24; base=struct.unpack_from('<I',P,opt+28)[0]
ns=struct.unpack_from('<H',P,pe+6)[0]; so=opt+struct.unpack_from('<H',P,pe+20)[0]
secs=[struct.unpack_from('<8sIIII',P,so+40*i) for i in range(ns)]
def xget(a,n):
    for nm,vs,va,rs,ro in secs:
        if base+va<=a<base+va+rs:
            o=ro+a-base-va; return P[o:o+n] if a-base-va+n<=rs else None
    return None
inv=sorted((int(r['address'],16),r['thunk']=='true') for r in csv.DictReader(open(invcsv)))
TEXT_END=0x52ea08
xd=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); xd.detail=True
pc={}
for i,(a,th) in enumerate(inv):
    if th or a>=0x519e00: continue
    end=inv[i+1][0] if i+1<len(inv) else TEXT_END
    code=xget(a,end-a)
    if not code: continue
    strs=[];flts=[];calls=[]
    for ins in xd.disasm(code,a):
        for op in ins.operands:
            v=None
            if op.type==cx.X86_OP_MEM and op.mem.base==0 and op.mem.index==0:
                v=op.mem.disp&0xffffffff
                if ins.mnemonic.startswith('f') and op.size in (4,):
                    b=xget(v,4)
                    if b: flts.append(b.hex()); continue
            elif op.type==cx.X86_OP_IMM:
                v=op.imm&0xffffffff
                if ins.mnemonic=='call': calls.append(v); continue
                if ins.mnemonic in ('mov','push') and (0x3a000000<=v<0x4f000000 or 0xba000000<=v<0xcf000000) and (v&0xfff)==0:
                    flts.append(struct.pack('<I',v).hex()); continue
                if ins.mnemonic=='mov' and op.size==4 and ins.op_str.startswith('dword ptr') :
                    pass
            if v and 0x52f000<=v<0x700000:
                s=cstr(xget,v)
                if s: strs.append(s)
    pc['%08x'%a]={'size':end-a,'strings':strs,'floats':flts,'calls':['%08x'%c for c in calls]}
json.dump({'ps2':ps2,'pc':pc},open(out,'w'))
print('ps2 funcs',len(ps2),'with strings',sum(1 for v in ps2.values() if v['strings']),'with floats',sum(1 for v in ps2.values() if v['floats']))
print('pc funcs',len(pc),'with strings',sum(1 for v in pc.values() if v['strings']),'with floats',sum(1 for v in pc.values() if v['floats']))
