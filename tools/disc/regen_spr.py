# Regenerate enemy pictures for table entries from the right monster bank (table index i -> bank i, i+1 from 52, i+2 from 67;
# banks 52 and 68 are not in the table). 2D sprites: idle frame, one pixel per game pixel. Gear-sized: three-quarter render of
# the 3D model (gear.py), stored at two image pixels per unit. Usage: regen_spr.py OUTDIR first last  -> prints JSON {i: [p0..p7]}
import sys,os,struct,json
sys.path[:0]=[__import__('os').path.dirname(__import__('os').path.abspath(__file__))]
import spr2,gear
from PIL import Image
OUT=sys.argv[1];LO,HI=int(sys.argv[2]),int(sys.argv[3])
s=open('/home/claude/xenogears-link/app/www/enemies.js').read();E=json.loads(s[s.index('window.ENEMIES=')+15:].rstrip().rstrip(';'))
bank=lambda i:i+2 if i>=67 else i+1 if i>=52 else i
def idle(d,a):
    s0=spr2.arch(d[a:])[0]; n=struct.unpack_from('<H',s0,0)[0]; offs=struct.unpack_from('<%dH'%n,s0,2)
    o=offs[0]; fl,a1,a2=struct.unpack_from('<HHH',s0,o); t1=o+2+a1
    for p in range(t1,min(t1+12,len(s0)-1)):
        if s0[p]==0xBE: return max(s0[p+1]-1,0)
    return 0
res={}
for i in range(LO,HI+1):
    f=2618+2*bank(i);d,ents=spr2.pack(f+1);hdr=8+12*len(ents);done={};row=[0]*8
    for k in range(min(8,len(ents))):
        n=E[i]['n'][k]
        if not n or n.startswith('Monster'): continue
        a,b,c=ents[k];t=c&0xFFFFFF;v=c>>24;hops=0
        while a<hdr and hops<4: a,b,c2=ents[a];hops+=1
        if a<hdr or b<hdr: continue
        key=(a,b,v,t)
        if key not in done:
            done[key]=0
            try:
                if t==1:
                    SS=4;tris,V,st=gear.build(d,a,b,'xyz');im=gear.render(tris,V,'-x',size=80*SS,yaw=40)
                    im=im.crop(im.getbbox());im=im.resize((max(1,round(im.width/SS)),max(1,round(im.height/SS))),Image.LANCZOS)
                    nm='g%d_%d'%(i,k);im.save(os.path.join(OUT,nm+'.png'),optimize=True);done[key]=[nm,round(im.width/2,1),round(im.height/2,1)]
                else:
                    fr=spr2.frames(spr2.arch(d[a:])[1]);fi=idle(d,a);im=None
                    for cc in [fi]+list(range(len(fr))):
                        if cc<len(fr) and fr[cc]:
                            r=spr2.render(d,a,b,cc,v)
                            if r and r[0].width>=8 and r[0].height>=8: im=r[0];break
                    if im: nm='%d_%d'%(i,k);im.save(os.path.join(OUT,nm+'.png'),optimize=True);done[key]=[nm,im.width,im.height]
            except Exception as ex: print('ERR',i,k,n,repr(ex)[:90],file=sys.stderr)
        row[k]=done[key]
    res[i]=row
print(json.dumps(res))
