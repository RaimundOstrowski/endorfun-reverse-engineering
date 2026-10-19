import sys,struct
b=open(sys.argv[1],'rb').read()
pe=struct.unpack('<I',b[0x3c:0x40])[0]
nsec=struct.unpack('<H',b[pe+6:pe+8])[0]; optsz=struct.unpack('<H',b[pe+20:pe+22])[0]
opt=pe+24
entry,=struct.unpack('<I',b[opt+16:opt+20]); imgbase,=struct.unpack('<I',b[opt+28:opt+32])
subsys,=struct.unpack('<H',b[opt+68:opt+70]); linkmaj,linkmin=b[opt+2],b[opt+3]
osmaj,osmin,imgmaj,imgmin,ssmaj,ssmin=struct.unpack('<HHHHHH',b[opt+40:opt+52])
print('linker %d.%d  os %d.%d subsys-ver %d.%d subsystem %d entry 0x%x imagebase 0x%x timestamp %d'%(linkmaj,linkmin,osmaj,osmin,ssmaj,ssmin,subsys,entry,imgbase,struct.unpack('<I',b[pe+8:pe+12])[0]))
secs=[]
st=opt+optsz
for k in range(nsec):
    s=b[st+40*k:st+40*(k+1)]
    name=s[:8].rstrip(b'\0').decode(); vs,va,rs,ro=struct.unpack('<IIII',s[8:24]); ch,=struct.unpack('<I',s[36:40])
    secs.append((name,va,vs,ro,rs,ch)); print('section %-8s va 0x%06x vsize %6d raw 0x%06x rsize %6d chars 0x%08x'%(name,va,vs,ro,rs,ch))
def rva2off(r):
    for n,va,vs,ro,rs,ch in secs:
        if va<=r<va+max(vs,rs): return r-va+ro
    raise ValueError(hex(r))
rsrc_rva=struct.unpack('<I',b[opt+96+2*8:opt+96+2*8+4])[0]
base=rva2off(rsrc_rva)
def rd_dir(off):
    n_named,n_id=struct.unpack('<HH',b[off+12:off+16]); out=[]
    for k in range(n_named+n_id):
        e=off+16+8*k; name,data=struct.unpack('<II',b[e:e+8])
        if name&0x80000000:
            so=base+(name&0x7fffffff); ln,=struct.unpack('<H',b[so:so+2]); nm=b[so+2:so+2+2*ln].decode('utf-16le')
        else: nm=name
        out.append((nm,data))
    return out
res={}
for t,d1 in rd_dir(base):
    for n,d2 in rd_dir(base+(d1&0x7fffffff)):
        for lang,d3 in rd_dir(base+(d2&0x7fffffff)):
            rva,sz=struct.unpack('<II',b[base+d3:base+d3+8]); res[(t,n,lang)]=b[rva2off(rva):rva2off(rva)+sz]
def wstr(d,i):
    s=''
    while True:
        c,=struct.unpack('<H',d[i:i+2]); i+=2
        if c==0: return s,i
        s+=chr(c)
for (t,n,l),d in sorted(res.items(),key=lambda x:(str(x[0][0]),str(x[0][1]))):
    if t==6:
        i=0; print('--- STRINGTABLE block',n,'(ids %d..%d)'%((n-1)*16,(n-1)*16+15))
        for k in range(16):
            ln,=struct.unpack('<H',d[i:i+2]); i+=2
            if ln: print('  %4d: %s'%((n-1)*16+k, d[i:i+2*ln].decode('utf-16le'))); i+=2*ln
    elif t==9:
        print('--- ACCELERATORS',n)
        for k in range(len(d)//8):
            fl,key,cmd,_=struct.unpack('<HHHH',d[8*k:8*k+8]); print('  flags 0x%02x key 0x%02x (%s) cmd %d'%(fl,key,chr(key) if 32<=key<127 else 'VK',cmd))
    elif t==16:
        s=d.decode('utf-16le','replace'); import re
        print('--- VERSIONINFO:', ' | '.join(x for x in re.findall(r'[\x20-\x7e]{3,}',s)))
    elif t==5:
        i=0
        style,ext,cnt,x,y,cx,cy=struct.unpack('<IIHHHHH',d[0:18]); i=18
        menu,i=(wstr(d,i+2)[0],wstr(d,i+2)[1]) if struct.unpack('<H',d[i:i+2])[0]==0xffff else wstr(d,i)
        cls,i=wstr(d,i); title,i=wstr(d,i)
        font=''
        if style&0x40: pt,=struct.unpack('<H',d[i:i+2]); font,i=wstr(d,i+2); font='%s %dpt'%(font,pt)
        print('--- DIALOG %s: "%s" %dx%d at (%d,%d) style 0x%08x %s controls=%d'%(n,title,cx,cy,x,y,style,font,cnt))
        for k in range(cnt):
            i=(i+3)&~3
            st,ex,cx_,cy_,cw,ch,cid=struct.unpack('<IIHHHHH',d[i:i+18]); i+=18
            if struct.unpack('<H',d[i:i+2])[0]==0xffff:
                cls={0x80:'BUTTON',0x81:'EDIT',0x82:'STATIC',0x83:'LISTBOX',0x84:'SCROLLBAR',0x85:'COMBOBOX'}.get(struct.unpack('<H',d[i+2:i+4])[0],'?'); i+=4
            else: cls,i=wstr(d,i)
            if struct.unpack('<H',d[i:i+2])[0]==0xffff: txt='#%d'%struct.unpack('<H',d[i+2:i+4])[0]; i+=4
            else: txt,i=wstr(d,i)
            ex_,=struct.unpack('<H',d[i:i+2]); i+=2+ex_
            print('    id %5d %-9s %3d,%3d %3dx%-3d style 0x%08x "%s"'%(cid,cls,cx_,cy_,cw,ch,st,txt))
    elif t==32:
        print('--- type 32 "#LINE" payload %d bytes: %s'%(len(d), d[:200]))
    elif t not in (3,4,14):
        print('--- type',t,'name',n,'bytes',len(d))
