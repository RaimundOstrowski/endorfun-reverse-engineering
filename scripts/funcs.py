import re,sys,struct,collections
dis=open('work/dis95.txt').read().splitlines()
# IAT map from .idata: parse PE import directory
b=open('endorfun-src/ENDORF95.EXE','rb').read()
pe=struct.unpack('<I',b[0x3c:0x40])[0]; opt=pe+24; nsec=struct.unpack('<H',b[pe+6:pe+8])[0]; optsz=struct.unpack('<H',b[pe+20:pe+22])[0]
secs=[]
for k in range(nsec):
    s=b[opt+optsz+40*k:opt+optsz+40*(k+1)]; secs.append((struct.unpack('<I',s[12:16])[0],struct.unpack('<I',s[8:12])[0],struct.unpack('<I',s[20:24])[0]))
def r2o(r):
    for va,vs,ro in secs:
        if va<=r<va+max(vs,0x1000): return r-va+ro
imp_rva=struct.unpack('<I',b[opt+96+8:opt+96+12])[0]; o=r2o(imp_rva); iat={}
while True:
    ilt,ts,fc,name,ft=struct.unpack('<IIIII',b[o:o+20]); o+=20
    if name==0: break
    dll=b[r2o(name):].split(b'\0')[0].decode()
    p=r2o(ilt or ft); slot=ft
    while True:
        e=struct.unpack('<I',b[p:p+4])[0]
        if e==0: break
        nm=('#%d'%(e&0xffff)) if e&0x80000000 else b[r2o(e)+2:].split(b'\0')[0].decode()
        iat[0x400000+slot]=dll.split('.')[0]+'!'+nm; p+=4; slot+=4
# function boundaries: 'push ebp; mov ebp,esp' prologues, or targets of call
addr_re=re.compile(r'^\s*([0-9a-f]+):\s+(.*)$')
ins=[]
for l in dis:
    m=addr_re.match(l)
    if m: ins.append((int(m.group(1),16),m.group(2).strip()))
calls=collections.Counter()
for a,t in ins:
    m=re.match(r'call\s+(0x[0-9a-f]+)',t)
    if m: calls[int(m.group(1),16)]+=1
starts=set(calls)
for i,(a,t) in enumerate(ins[:-1]):
    if t.startswith('push') and 'ebp' in t and ins[i+1][1].replace(' ','') in ('movebp,esp',): starts.add(a)
starts=sorted(starts)
print('functions (call targets + prologues):',len(starts),'; distinct call targets:',len(calls))
# per function import usage
fi=0; cur=None; usage=collections.defaultdict(collections.Counter); size={}
for a,t in ins:
    while fi<len(starts) and starts[fi]<=a: cur=starts[fi]; fi+=1
    if cur is None: continue
    size[cur]=a-cur
    for m in re.finditer(r'\[(0x[0-9a-f]+)\]',t):
        v=int(m.group(1),16)
        if v in iat: usage[cur][iat[v]]+=1
print('IAT entries:',len(iat))
# summarise: which functions use which API families
fam=lambda n: n.split('!')[0]
print()
print('=== functions using multimedia / timing / palette APIs ===')
keys=['WINMM','GDI32!AnimatePalette','GDI32!StretchDIBits','GDI32!CreatePalette','KERNEL32!GetPrivateProfileStringA','KERNEL32!WritePrivateProfileStringA','KERNEL32!GetPrivateProfileIntA','USER32!WinHelpA','comdlg32','USER32!RegisterClassA','USER32!CreateWindowExA','USER32!PeekMessageA','USER32!GetCursorPos','USER32!SetCursorPos','USER32!GetKeyState','KERNEL32!OpenFile','KERNEL32!FindResourceA','USER32!LoadStringA','USER32!DialogBoxParamA','USER32!CreateDialogIndirectParamA']
for k in keys:
    fs=[(f,sum(c for n,c in u.items() if n.startswith(k))) for f,u in usage.items() if any(n.startswith(k) for n in u)]
    print('%-40s %s'%(k,' '.join('%x(%d)'%(f,c) for f,c in sorted(fs))))
print()
print('=== top 25 functions by size with their API mix ===')
for f in sorted(size,key=lambda x:-size[x])[:25]:
    u=usage[f]; print('%x size %5d  %s'%(f,size[f],', '.join('%s x%d'%(n.split('!')[1],c) for n,c in u.most_common(8))))
# exported names
print()
print('=== exports (.edata) ===')
exp_rva=struct.unpack('<I',b[opt+96:opt+96+4])[0]; o=r2o(exp_rva)
nf,nn=struct.unpack('<II',b[o+20:o+28]); af,an,ao=struct.unpack('<III',b[o+28:o+40])
for k in range(nn):
    nmr=struct.unpack('<I',b[r2o(an)+4*k:r2o(an)+4*k+4])[0]; ordv=struct.unpack('<H',b[r2o(ao)+2*k:r2o(ao)+2*k+2])[0]
    fa=struct.unpack('<I',b[r2o(af)+4*ordv:r2o(af)+4*ordv+4])[0]
    print('  %s @ 0x%x'%(b[r2o(nmr):].split(b'\0')[0].decode(),0x400000+fa))
import json; json.dump({'%x'%f:{'size':size.get(f,0),'apis':dict(u)} for f,u in usage.items()},open('work/func_api.json','w'))
