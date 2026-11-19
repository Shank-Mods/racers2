import re,sys
# Minimal CodeWarrior/GCC2-style demangler for Name__<n>ClassF<args>
def parse_class(s,i):
    if s[i]=='Q':  # qualified: Q<count><n>Name<n>Name
        cnt=int(s[i+1]); i+=2; parts=[]
        for _ in range(cnt):
            m=re.match(r'\d+',s[i:]); n=int(m.group()); i+=len(m.group()); parts.append(s[i:i+n]); i+=n
        return '::'.join(parts),i
    m=re.match(r'\d+',s[i:])
    if not m: return None,i
    n=int(m.group()); i+=len(m.group()); return s[i:i+n],i+n
def split(sym):
    k=sym.find('__',1)
    while k!=-1:
        name=sym[:k]; rest=sym[k+2:]
        if rest and (rest[0].isdigit() or rest[0]=='Q'):
            cls,j=parse_class(rest,0)
            if cls: return cls,name,rest[j:]
        if rest.startswith('F'): return None,name,rest
        k=sym.find('__',k+1)
    return None,sym,''
if __name__=='__main__':
    for l in sys.stdin:
        c,n,a=split(l.strip()); print(c or '',n,a,sep='\t')
