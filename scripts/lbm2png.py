import sys,os,struct,zlib
def png(path,w,h,rgb):
    raw=b''.join(b'\x00'+bytes(rgb[y*w*3:(y+1)*w*3]) for y in range(h))
    def chunk(t,d): return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
    open(path,'wb').write(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b''))
def load(p):
    b=open(p,'rb').read(); i=12; w=h=0; cmap=None; body=None; comp=0; chunks={}
    while i+8<=len(b):
        tag=b[i:i+4]; ln=struct.unpack('>I',b[i+4:i+8])[0]; d=b[i+8:i+8+ln]
        if tag==b'BMHD': w,h,_,_,pl,mask,comp=struct.unpack('>HHhhBBB',d[:11])
        elif tag==b'CMAP': cmap=d
        elif tag==b'BODY': body=d
        elif tag==b'CRNG': chunks.setdefault('CRNG',[]).append(struct.unpack('>hhhBB',d[:8]))
        i+=8+ln+(ln&1)
    if comp==1:
        out=bytearray(); j=0
        while j<len(body) and len(out)<w*h:
            n=body[j]; j+=1
            if n<128: out+=body[j:j+n+1]; j+=n+1
            elif n>128: out+=bytes([body[j]])*(257-n); j+=1
        pix=bytes(out)
    else: pix=body
    return w,h,cmap,pix,chunks
if __name__=='__main__':
    out=sys.argv[1]
    for p in sys.argv[2:]:
        w,h,cmap,pix,ch=load(p)
        scale=1 if w>64 else 16
        W,H=w*scale,h*scale
        rgb=bytearray(W*H*3)
        for y in range(H):
            for x in range(W):
                c=pix[(y//scale)*w+(x//scale)] if (y//scale)*w+(x//scale)<len(pix) else 0
                rgb[(y*W+x)*3:(y*W+x)*3+3]=cmap[c*3:c*3+3]
        name=os.path.splitext(os.path.basename(p))[0]+'.png'
        png(os.path.join(out,name),W,H,rgb)
        print('%-14s %4dx%-4d pixels=%6d cmap=%3d colours used=%3d CRNG active=%s'%(os.path.basename(p),w,h,len(pix),len(cmap)//3,len(set(pix)),[(r[2],r[3],r[4]) for r in ch.get('CRNG',[]) if r[1]&1]))
