# Cut an enemy out of a battle frame: find the VRAM texture pages whose removal changes the frame (per page), then compare the frame
# with and without the chosen pages; the pixels that change are the enemy.
import sys,struct,json; sys.path[:0]=['/home/claude/emu/rcdata/tools','/home/claude/emu/run']
import lr,h,numpy as np
from lr import *
from PIL import Image
rec=bytes.fromhex(sys.argv[1]); tag=sys.argv[2]; wait=int(sys.argv[3]) if len(sys.argv)>3 else 400
VO=2724993
e=h.fresh('/home/claude/emu/run/st23_0.bin','/home/claude/emu/run/r23_0.srm'); e.run(5)
if len(sys.argv)>4 and sys.argv[4]=='gear':
    for i in range(3): e.w8(0x8006F8E5+i,1)
for i in range(16):
    for j,b in enumerate(rec): e.w8(0x800658DC+i*0x20+j,b)
dirs=[UP,LEFT,DOWN,RIGHT]
for f in range(3000):
    e.run(1,[dirs[(f//40)%4]])
    if e.u32(0x8006FAF0)==6: break
e.run(wait)
st=bytearray(e.save())
V0=np.frombuffer(bytes(st[VO:VO+1024*512*2]),dtype='<u2').reshape(512,1024).copy()
def frame(V):
    s=bytearray(st); s[VO:VO+1024*512*2]=V.tobytes(); e.load(bytes(s)); e.run(2)
    d,w,hh,p=e.frame
    a=np.frombuffer(d,dtype=np.uint16).reshape(hh,p//2)[:,:w]
    return np.dstack([((a>>11)&31)*255//31,((a>>5)&63)*255//63,(a&31)*255//31]).astype(np.uint8)
base=frame(V0)
Image.fromarray(base).save('/home/claude/emu/rc3/%s_base.png'%tag)
res=[]
for py in range(2):
    for px in range(16):
        V=V0.copy(); V[py*256:(py+1)*256,px*64:(px+1)*64]=0
        im=frame(V); m=(np.abs(im.astype(int)-base.astype(int)).sum(2)>30)
        if m.sum()>20:
            ys,xs=np.nonzero(m); res.append((px,py,int(m.sum()),int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())))
for r in res: print('page',r)
json.dump(res,open('/home/claude/emu/rc3/%s_pages.json'%tag,'w'))
# cut: zero the chosen pages, diff, save RGBA crop
if len(sys.argv)>5:
    pages=[tuple(map(int,p.split(','))) for p in sys.argv[5].split(';')]
    V=V0.copy()
    for px,py in pages: V[py*256:(py+1)*256,px*64:(px+1)*64]=0
    im=frame(V); m=(np.abs(im.astype(int)-base.astype(int)).sum(2)>24)
    ys,xs=np.nonzero(m); x0,y0,x1,y1=xs.min(),ys.min(),xs.max()+1,ys.max()+1
    rgba=np.dstack([base,(m*255).astype(np.uint8)])[y0:y1,x0:x1]
    Image.fromarray(rgba,'RGBA').save('/home/claude/emu/rc3/%s_cut.png'%tag); print('cut',x0,y0,x1,y1)
# keep-models mode: zero the given background pages and save the whole frame with black as transparent
if len(sys.argv)>6 and sys.argv[6]=='models':
    V=V0.copy()
    for px,py in pages: V[py*256:(py+1)*256,px*64:(px+1)*64]=0
    im=frame(V); m=im.astype(int).sum(2)>12
    Image.fromarray(np.dstack([im,(m*255).astype(np.uint8)]),'RGBA').save('/home/claude/emu/rc3/%s_models.png'%tag)
