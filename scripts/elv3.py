import sys,os,struct,glob,collections,json
d=sys.argv[1]
def cstr(b,o,n): return b[o:o+n].split(b'\x00')[0].decode('latin-1')
REC=463
exps=[]; allrecs=[]
for p in sorted(glob.glob(os.path.join(d,'*.ELV'))):
    b=open(p,'rb').read(); fn=os.path.basename(p)
    assert b[:4]==b'ELVD' and b[8:12]==b'LVTL'
    ng,nb=b[6],b[7]; lvtl_len=struct.unpack('<H',b[12:14])[0]
    assert lvtl_len==257, (fn,lvtl_len)
    e={'file':fn,'n_game':ng,'n_bonus':nb,'title':cstr(b,14,30),'win':cstr(b,0x2c,13),'lose':cstr(b,0x39,13),'win_wav':cstr(b,0x46,13),'lose_wav':cstr(b,0x53,13),'textures':cstr(b,0x60,13),'b6d':b[0x6d],'b6e':b[0x6e],'desc':cstr(b,0x6f,0x10f-0x6f)}
    i=0x10f; assert b[i:i+4]==b'LVDS'; ln=struct.unpack('<H',b[i+4:i+6])[0]; assert ln==ng*REC,(fn,ln,ng)
    recs=[b[i+6+k*REC:i+6+(k+1)*REC] for k in range(ng)]
    j=i+6+ng*REC; assert b[j:j+4]==b'LVBN',(fn,hex(j)); ln2=struct.unpack('<H',b[j+4:j+6])[0]; assert ln2==nb*REC,(fn,ln2,nb)
    brecs=[b[j+6+k*REC:j+6+(k+1)*REC] for k in range(nb)]
    assert j+6+nb*REC==len(b),(fn,len(b)-(j+6+nb*REC))
    e['levels']=recs; e['bonus']=brecs; exps.append(e)
    for k,r in enumerate(recs): allrecs.append((fn,'G',k,r))
    for k,r in enumerate(brecs): allrecs.append((fn,'B',k,r))
print('parsed',len(exps),'experiences; game levels',sum(e['n_game'] for e in exps),'bonus levels',sum(e['n_bonus'] for e in exps),'; all chunk/size assertions hold')
print()
print('=== LVTL bytes 0x6d/0x6e per experience ===')
for e in exps: print('%-13s %2d %2d  ng=%3d nb=%2d  %-28s win=%-12s lose=%-12s tex=%-12s wavs=%s/%s'%(e['file'],e['b6d'],e['b6e'],e['n_game'],e['n_bonus'],e['title'],e['win'],e['lose'],e['textures'],e['win_wav'],e['lose_wav']))
print('b6d dist',collections.Counter(e['b6d'] for e in exps),'b6e dist',collections.Counter(e['b6e'] for e in exps))
G=[r for _,k,_,r in allrecs if k=='G']; B=[r for _,k,_,r in allrecs if k=='B']
def stats(rs,label):
    print('=== u16 n0..n32 stats, %s (%d) ==='%(label,len(rs)))
    for k in range(33):
        off=2*k; vals=collections.Counter(struct.unpack('<H',r[off:off+2])[0] for r in rs)
        print('n%-2d +0x%02x: n=%3d min=%5d max=%5d top=%s'%(k,off,len(vals),min(vals),max(vals),sorted(vals.items(),key=lambda x:-x[1])[:8]))
stats(G,'GAME'); stats(B,'BONUS')
print()
print('=== raw string region +0x42..+0xa0 for diverse records ===')
seen=set()
for fn,k,idx,r in allrecs:
    key=(cstr(r,0x42,16)[:6],k)
    if key in seen: continue
    seen.add(key)
    if len(seen)>14: break
    print(fn,k,idx,r[0x42:0x78]); print('    msg:',r[0x78:0xa0])
print()
print('=== NUL map new offsets 0x42..0xdc ===')
print(' '.join('%02x:%.2f'%(o,sum(1 for r in G if r[o]==0)/len(G)) for o in range(0x42,0xdd)))
print()
print('=== message first-byte analysis ===')
msgs=collections.Counter((r[0x78], cstr(r,0x79,39)) for r in G+B if r[0x79])
print('first byte present (nonzero) in',sum(c for (fb,m),c in msgs.items() if fb),'records; zero in',sum(c for (fb,m),c in msgs.items() if not fb))
print('examples with first byte:',[(chr(fb)+m) for (fb,m),c in msgs.items() if fb][:12])
print('examples without:',[m for (fb,m),c in msgs.items() if not fb][:12])
print('region 0xa0..0xdb nonzero in',sum(1 for r in G+B if any(r[0xa0:0xdb])),'of',len(G+B),'records')
print()
print('=== Life Force table: count @0xdb, entries @0xdd (8B x30), trailing 2B @0x1cd ===')
cnt=collections.Counter(); f=[collections.Counter() for _ in range(4)]; perkind=collections.defaultdict(collections.Counter)
for fn,k,idx,r in allrecs:
    n=struct.unpack('<H',r[0xdd:0xdf])[0]; cnt[(k,n)]+=1
    for e_ in range(min(n,30)):
        v=struct.unpack('<HHHH',r[0xdf+8*e_:0xdf+8*e_+8])
        for q in range(4): f[q][v[q]]+=1
print('count dist:',sorted(cnt.items()))
for q in range(4): print(' field%d: n=%d'%(q,len(f[q])),sorted(f[q].items(),key=lambda x:-x[1])[:30])
print('trailing:',collections.Counter(r[0x1cd:0x1cf] for _,_,_,r in allrecs).most_common(6))
print('bytes beyond count nonzero:',sum(1 for _,_,_,r in allrecs if any(r[0xdf+8*min(30,struct.unpack('<H',r[0xdd:0xdf])[0]):0x1cd])))
# per-record f3 pairs
pairs=collections.Counter()
for fn,k,idx,r in allrecs:
    n=struct.unpack('<H',r[0xdd:0xdf])[0]
    for e_ in range(min(n,30)):
        v=struct.unpack('<HHHH',r[0xdf+8*e_:0xdf+8*e_+8]); pairs[(v[3]&0xff,v[3]>>8)]+=1
print('field3 as (lo,hi):',sorted(pairs.items(),key=lambda x:-x[1])[:20])
# dump JSON for reuse
out=[]
for e in exps:
    def rec(r):
        u=list(struct.unpack('<33H',r[:66]))
        n=struct.unpack('<H',r[0xdd:0xdf])[0]
        return {'u16':u,'bg':cstr(r,0x42,16),'pal':cstr(r,0x4d,15),'tex':cstr(r,0x5c,13),'rloop':cstr(r,0x69,15),'msg':cstr(r,0x78,40),'lf_count':n,'lf':[list(struct.unpack('<HHHH',r[0xdf+8*q:0xdf+8*q+8])) for q in range(min(n,30))],'trail':list(r[0x1cd:0x1cf])}
    out.append({k:v for k,v in e.items() if k not in ('levels','bonus')}|{'levels':[rec(r) for r in e['levels']],'bonus':[rec(r) for r in e['bonus']]})
json.dump(out,open('work/elv_dump.json','w'),indent=0)
print('wrote work/elv_dump.json')
