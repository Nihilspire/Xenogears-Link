# ==== gear.py: gear-sized enemies (3D models) ====
import sys,struct,math,collections
import numpy as np
import spr2
from PIL import Image
def arch_safe(b):
    n=struct.unpack_from('<I',b,0)[0]
    if not 0<n<400: raise ValueError('arch n=%d'%n)
    o=struct.unpack_from('<%dI'%(n+1),b,4)
    return [b[o[i]:o[i+1]] if 0<o[i]<=o[i+1]<=len(b) else b'' for i in range(n)]
def load(d,a,b):
    A=arch_safe(d[a:]); anims=arch_safe(arch_safe(A[0])[0]); B=arch_safe(d[b:])
    return anims,B
def vram(texblk):
    V=np.zeros((512,1024),dtype=np.uint16)
    for e in arch_safe(texblk):
        if len(e)<16: continue
        fl,x,y,ox,oy,w,h=struct.unpack_from('<I6H',e,0)
        if w==0 or h==0 or 16+w*h*2>len(e)+1: continue
        X=x+ox;Y=y+oy
        if X+w>1024 or Y+h>512: continue
        V[Y:Y+h,X:X+w]=np.frombuffer(e[16:16+w*h*2],dtype='<u2').reshape(h,w)
    return V
def meshes(m):
    """parts: (vertices, [(type, faces)], status/primitive stream)"""
    n=struct.unpack_from('<I',m,0)[0]; out=[]
    for i in range(n):
        h=4+0x38*i
        nv,nf,ng=struct.unpack_from('<3H',m,h+0x0E); vo,no,fo,eo=struct.unpack_from('<4I',m,h+0x14)
        V=np.array([struct.unpack_from('<3h',m,vo+8*k) for k in range(nv)],dtype=float).reshape(-1,3)
        groups=[];p=fo
        for g in range(ng):
            typ,cnt=struct.unpack_from('<HH',m,p); p+=4
            groups.append((typ&0xFF,[struct.unpack_from('<4H',m,p+8*c) for c in range(cnt)])); p+=cnt*8
        out.append((V,groups,eo))
    ends=sorted(set(x[2] for x in out))+[len(m)]
    return [(V,groups,m[eo:ends[ends.index(eo)+1]]) for V,groups,eo in out]
def polys(groups,st):
    """walk the stream. Group type bits: 1 textured, 2 lit, 8 quad. Words with a top byte >= 0x80 are status words
    (0xC4 texture page, 0xC8 palette). Textured triangle: [uv of vertex 2 | command], [uv 0, uv 1]. Textured quad:
    [command], [uv 0, uv 1], [uv 2, uv 3]. Untextured: one colour word."""
    p=0;tp=0;cl=0;out=[];fi=0;nf=sum(len(f) for _,f in groups)
    for typ,faces in groups:
        quad=bool(typ&8);tex=bool(typ&1)
        for f in faces:
            while p+4<=len(st) and st[p+3]>=0x80:
                w=struct.unpack_from('<I',st,p)[0]
                if w>>24==0xC4: tp=w&0xFFFF
                elif w>>24==0xC8: cl=w&0xFFFF
                p+=4
            need=(12 if quad else 8) if tex else 4
            if p+need>len(st): return out,fi,p
            if tex:
                if quad:
                    b=st[p+4:p+12]; uv=[(b[0],b[1]),(b[2],b[3]),(b[4],b[5]),(b[6],b[7])]
                else:
                    b=st[p:p+8]; uv=[(b[4],b[5]),(b[6],b[7]),(b[0],b[1])]
                out.append((f[:4 if quad else 3],'t',(uv,tp,cl,st[p+3])))
            else:
                out.append((f[:4 if quad else 3],'c',struct.unpack_from('<I',st,p)[0]&0xFFFFFF))
            p+=need;fi+=1
    return out,fi,p
def rot(rx,ry,rz,order):
    def R(axis,a):
        a=a*math.pi/2048;c,s=math.cos(a),math.sin(a)
        if axis=='x': return np.array([[1,0,0],[0,c,-s],[0,s,c]])
        if axis=='y': return np.array([[c,0,s],[0,1,0],[-s,0,c]])
        return np.array([[c,-s,0],[s,c,0],[0,0,1]])
    M=np.eye(3)
    for ax in order: M=M@R(ax,{'x':rx,'y':ry,'z':rz}[ax])
    return M
def pose(anim0,hier,order='zyx'):
    nb=struct.unpack_from('<H',anim0,0)[0]
    nodes=[struct.unpack_from('<hh',hier,i*4) for i in range(nb)]
    W=[]
    for i,(mesh,par) in enumerate(nodes):
        rx,ry,rz,tx,ty,tz=struct.unpack_from('<6h',anim0,0x18+12*i)
        L=np.eye(4);L[:3,:3]=rot(rx,ry,rz,order);L[:3,3]=(tx,ty,tz)
        W.append(L if par<0 or par>=i else W[par]@L)
    return nodes,W
def build(d,a,b,order='zyx'):
    anims,B=load(d,a,b)
    M=meshes(B[1]);V=vram(B[0]);nodes,W=pose(anims[0],B[2],order)
    tris=[];stat=collections.Counter()
    for i,(mesh,par) in enumerate(nodes):
        if mesh<0 or mesh>=len(M): continue
        Vt,groups,st=M[mesh]
        P=(W[i][:3,:3]@Vt.T).T+W[i][:3,3]
        pl,fi,p=polys(groups,st); stat['faces']+=sum(len(f) for _,f in groups);stat['parsed']+=fi;stat['left']+=max(0,len(st)-p-3)
        for idx,kind,data in pl:
            if max(idx)>=len(P): continue
            order_=[(0,1,2),(1,3,2)] if len(idx)==4 else [(0,1,2)]
            for tr in order_:
                pts=[P[idx[j]] for j in tr]
                if kind=='t':
                    uv,tp,cl,c=data; tris.append((pts,'t',([uv[j] for j in tr],tp,cl)))
                elif kind=='g': tris.append((pts,'g',[data[j] for j in tr]))
                else: tris.append((pts,'c',data))
    return tris,V,stat
def texel(V,tp,cl,u,v):
    bx=(tp&0xF)*64;by=((tp>>4)&1)*256;mode=(tp>>7)&3
    cx=(cl&0x3F)*16;cy=(cl>>6)&0x1FF
    if mode==0:
        w=V[(by+v)&511,(bx+(u>>2))&1023];i=(w>>((u&3)*4))&15
    elif mode==1:
        w=V[(by+v)&511,(bx+(u>>1))&1023];i=(w>>((u&1)*8))&255
    else: return V[(by+v)&511,(bx+u)&1023]
    return V[cy,(cx+i)&1023]
def trim_thin(tris,V,view='-x',yaw=40,frac=0.12,size=400):
    """drop thin strands that stick out above or below a model (Brigandier's two hanging cables, Oct 2026): render it once, and
    from the top and the bottom drop image rows with fewer opaque pixels than frac of the fullest row; then keep the triangles that
    reach the rows left (yaw only turns the model about the vertical axis, so a row is a height)"""
    im=render(tris,V,view,size=size,yaw=yaw)
    A=np.array(im)[:,:,3]>0;cnt=A.sum(1);mx=cnt.max();rows=np.nonzero(cnt>=frac*mx)[0]
    if not len(rows): return tris
    P=np.array([p for t in tris for p in t[0]])
    if yaw:
        a=math.radians(yaw);c,s_=math.cos(a),math.sin(a);H=np.concatenate([P[:,0]*c+P[:,2]*s_]);H2=-P[:,0]*s_+P[:,2]*c
    Y=P[:,1];Hh=(-(-P[:,0]*math.sin(math.radians(yaw))+P[:,2]*math.cos(math.radians(yaw))))
    span=max(np.ptp(Hh),np.ptp(Y),1);sc=(size-2)/span
    y0=Y.min()+(rows[0]-1)/sc;y1=Y.min()+(rows[-1]+1)/sc
    return [t for t in tris if any(y0<=p[1]<=y1 for p in t[0])]
def render(tris,V,view='x',size=160,flip=False,yaw=0,pitch=0):
    if not tris: return None
    pts=np.array([p for t in tris for p in t[0]])
    if yaw or pitch:
        a=math.radians(yaw);c,s_=math.cos(a),math.sin(a)
        x=pts[:,0]*c+pts[:,2]*s_;z=-pts[:,0]*s_+pts[:,2]*c;pts=np.stack([x,pts[:,1],z],1)
        b=math.radians(pitch);c,s_=math.cos(b),math.sin(b)
        x=pts[:,0]*c-pts[:,1]*s_;y=pts[:,0]*s_+pts[:,1]*c;pts=np.stack([x,y,pts[:,2]],1)
    # view axes: horizontal h, vertical y (down positive), depth
    ax={'x':(2,1,0),'z':(0,1,2),'-x':(2,1,0),'-z':(0,1,2)}[view]
    H=pts[:,ax[0]].copy();Y=pts[:,ax[1]];D=pts[:,ax[2]].copy()
    if view in('-x',): H=-H;D=-D
    if view=='-z': H=-H;D=-D
    if flip: H=-H
    span=max(H.max()-H.min(),Y.max()-Y.min(),1);sc=(size-2)/span
    w=int((H.max()-H.min())*sc)+3;h=int((Y.max()-Y.min())*sc)+3
    col=np.zeros((h,w,4),dtype=np.uint8);zb=np.full((h,w),-1e18)
    X2=(H-H.min())*sc+1;Y2=(Y-Y.min())*sc+1
    L=np.array([0.3,-0.6,0.74]) # light in view space (h, y, depth toward viewer)
    for ti,(p3,kind,data) in enumerate(tris):
        i0=ti*3
        x=X2[i0:i0+3];y=Y2[i0:i0+3];z=D[i0:i0+3]
        x0=max(int(math.floor(x.min())),0);x1=min(int(math.ceil(x.max())),w-1);y0=max(int(math.floor(y.min())),0);y1=min(int(math.ceil(y.max())),h-1)
        if x1<x0 or y1<y0: continue
        den=(y[1]-y[2])*(x[0]-x[2])+(x[2]-x[1])*(y[0]-y[2])
        if abs(den)<1e-9: continue
        gx,gy=np.meshgrid(np.arange(x0,x1+1)+0.5,np.arange(y0,y1+1)+0.5)
        a=((y[1]-y[2])*(gx-x[2])+(x[2]-x[1])*(gy-y[2]))/den
        b=((y[2]-y[0])*(gx-x[2])+(x[0]-x[2])*(gy-y[2]))/den
        c=1-a-b
        m=(a>=-0.01)&(b>=-0.01)&(c>=-0.01)
        if not m.any(): continue
        zz=a*z[0]+b*z[1]+c*z[2]
        # normal shading in view space
        v0=np.array([x[0],y[0],z[0]*sc]);v1=np.array([x[1],y[1],z[1]*sc]);v2=np.array([x[2],y[2],z[2]*sc])
        nrm=np.cross(v1-v0,v2-v0);nl=np.linalg.norm(nrm)
        sh=0.62+0.48*abs(float(nrm@L)/nl) if nl>0 else 1
        sub=zb[y0:y1+1,x0:x1+1];m&=zz>sub
        if not m.any(): continue
        if kind=='t':
            uv,tp,cl=data
            uu=np.clip(np.rint(a*uv[0][0]+b*uv[1][0]+c*uv[2][0]-0.0),0,255).astype(int);vv=np.clip(np.rint(a*uv[0][1]+b*uv[1][1]+c*uv[2][1]),0,255).astype(int)
            bx=(tp&0xF)*64;by=((tp>>4)&1)*256;mode=(tp>>7)&3;cx=(cl&0x3F)*16;cy=(cl>>6)&0x1FF
            if mode==0:
                wv=V[(by+vv)&511,(bx+(uu>>2))&1023];ix=(wv>>((uu&3)*4))&15;px=V[cy,(cx+ix)&1023]
            elif mode==1:
                wv=V[(by+vv)&511,(bx+(uu>>1))&1023];ix=(wv>>((uu&1)*8))&255;px=V[cy,(cx+ix)&1023]
            else: px=V[(by+vv)&511,(bx+uu)&1023]
            m&=px!=0
            r=(px&31)*8.2;g=((px>>5)&31)*8.2;bl=((px>>10)&31)*8.2
        else:
            if kind=='g':
                cs=[((q&255),(q>>8)&255,(q>>16)&255) for q in data]
                r=a*cs[0][0]+b*cs[1][0]+c*cs[2][0];g=a*cs[0][1]+b*cs[1][1]+c*cs[2][1];bl=a*cs[0][2]+b*cs[1][2]+c*cs[2][2]
            else:
                r=np.full(a.shape,float(data&255));g=np.full(a.shape,float((data>>8)&255));bl=np.full(a.shape,float((data>>16)&255))
        if not m.any(): continue
        sc_=col[y0:y1+1,x0:x1+1]
        sc_[m,0]=np.clip(r*sh,0,255)[m];sc_[m,1]=np.clip(g*sh,0,255)[m];sc_[m,2]=np.clip(bl*sh,0,255)[m];sc_[m,3]=255
        sub[m]=zz[m]
    return Image.fromarray(col,'RGBA')
if __name__=='__main__':
    f=int(sys.argv[1]);ei=int(sys.argv[2])
    d,ents=spr2.pack(f);a,b,c=ents[ei]
    out=Image.new('RGBA',(4*170,3*170),(40,40,60,255))
    for r,order in enumerate(('xyz','zyx','yxz')):
        tris,V,stat=build(d,a,b,order)
        if r==0: print(stat,len(tris))
        for cidx,view in enumerate(('x','-x','z','-z')):
            im=render(tris,V,view)
            if im: out.alpha_composite(im,(cidx*170+2,r*170+2))
    out.resize((out.width*2,out.height*2),Image.NEAREST).save(sys.argv[3])

# ==== mkgear2.py: render every gear model into www/spr ====
#M # render a three-quarter view of every gear-sized enemy's 3D model into www/spr and record it in enemies.js
#M import os,sys,json,pickle,collections
#M import gear,spr2
#M from PIL import Image
#M R=pickle.load(open('recs.pkl','rb'));files=[]
#M for f,k,n,r in R:
#M     if f not in files: files.append(f)
#M OUT='/home/claude/xg/v/www/spr'
#M p='/home/claude/xg/v/www/enemies.js';s=open(p).read()
#M i=s.index('window.ENEMIES=');head=s[:i];E=json.loads(s[i+15:].rstrip().rstrip(';'))
#M for x in os.listdir(OUT):
#M     if x.startswith('g'): os.remove(os.path.join(OUT,x))
#M done={};st=collections.Counter();SS=4;SIZE=80
#M for bi,f in enumerate(files):
#M     d,ents=spr2.pack(f+1);hdr=8+12*len(ents)
#M     for k in range(min(8,len(ents))):
#M         if not E[bi]['n'][k] or E[bi]['n'][k].startswith('Monster'): continue
#M         a,b,c=ents[k]
#M         if (c&0xFFFFFF)!=1: continue
#M         hops=0
#M         while a<hdr and hops<4: a,b,c2=ents[a];hops+=1
#M         if a<hdr or b<hdr: st['unresolved']+=1;continue
#M         key=(f,a,b)
#M         if key not in done:
#M             try:
#M                 tris,V,stat=gear.build(d,a,b,'xyz');im=gear.render(tris,V,'-x',size=SIZE*SS,yaw=40)
#M                 im=im.crop(im.getbbox());im=im.resize((max(1,round(im.width/SS)),max(1,round(im.height/SS))),Image.LANCZOS)
#M                 name='g%d_%d'%(bi,k);im.save(os.path.join(OUT,name+'.png'),optimize=True);done[key]=[name,round(im.width/2,1),round(im.height/2,1)];st['ok']+=1
#M             except Exception as ex: done[key]=0;st['err']+=1;print('ERR',f,k,E[bi]['n'][k],repr(ex)[:80])
#M         E[bi]['p'][k]=done[key];st['records']+=1
#M head=head.replace("0 for gear-sized enemies, which are 3D models","sprites are the idle frame at one game pixel per unit; names starting g are three-quarter renders of a gear-sized enemy's 3D model at two image pixels per unit")
#M open(p,'w').write(head.rstrip()+'\nwindow.ENEMIES='+json.dumps(E,separators=(',',':'))+';\n')
#M print(st, sum(os.path.getsize(os.path.join(OUT,x)) for x in os.listdir(OUT)), len(os.listdir(OUT)))
#M nop=[(e['n'][k]) for e in E for k in range(8) if e['n'][k] and not e['n'][k].startswith('Monster') and (e['h'][k][0] or e['h'][k][1]) and not e['p'][k]]
#M print('named enemies still without a picture:',nop)

# ==== pbr.py: the party's battle sprites (disc files 2988-2998; tiles carry their own pixels) ====
#P import sys,struct
#P import spr2
#P from PIL import Image
#P def load(f):
#P     d=spr2.getf(f); A=spr2.arch(d); return A
#P def frames(s1):
#P     n=s1[0]; offs=struct.unpack_from('<%dH'%n,s1,2); out=[]
#P     for o in offs:
#P         nt=s1[o]&0x3f; hdr=s1[o:o+6]
#P         prs=[struct.unpack_from('<HH',s1,o+6+4*k) for k in range(nt)]
#P         p=o+6+4*nt; pl=[]
#P         for a,b in prs:
#P             ctl=[]
#P             while s1[p]>=0xC0:
#P                 if s1[p]>=0xE0: ctl.append(s1[p:p+3]); p+=3
#P                 else: ctl.append(s1[p:p+1]); p+=1
#P             fl=s1[p]; x,y=struct.unpack_from('<bb',s1,p+1); p+=3
#P             pl.append((a,b,fl,x,y,ctl))
#P         out.append((hdr,pl))
#P     return out
#P def render(A,fi,flip=(0x10,0x20),order=-1):
#P     s1=A[1]; a,P=spr2.pals(A[2]); hdr,pl=frames(s1)[fi]; px={}
#P     for t,b,fl,x,y,ctl in pl[::order]:
#P         w,h=s1[t*4],s1[t*4+1]; data=s1[t*4+4:]; pal=P[min(fl&0x0F,len(P)-1)]; rw=(w+1)//2
#P         rw=(rw+3)&~3 if False else rw
#P         for yy in range(h):
#P             for xx in range(w):
#P                 byte=data[yy*rw+(xx>>1)]; c=(byte>>4) if xx&1 else (byte&15)
#P                 if c==0: continue
#P                 dx=(w-1-xx) if fl&flip[0] else xx; dy=(h-1-yy) if fl&flip[1] else yy
#P                 px[(x+dx,y+dy)]=pal[c][:3]+(255,)
#P     if not px: return None
#P     xs=[p[0] for p in px];ys=[p[1] for p in px]
#P     x0,y0=min(xs),min(ys); im=Image.new('RGBA',(max(xs)-x0+1,max(ys)-y0+1))
#P     for (x,y),c in px.items(): im.putpixel((x-x0,y-y0),c)
#P     return im,(x0,y0)
#P if __name__=='__main__':
#P     f=int(sys.argv[1]); A=load(f); fr=frames(A[1]); n=len(fr)
#P     cols=16; cell=96; sheet=Image.new('RGBA',(cols*cell,((n+cols-1)//cols)*cell),(40,40,60,255))
#P     for i in range(n):
#P         try: r=render(A,i)
#P         except Exception as e: print(i,e); r=None
#P         if r: 
#P             im=r[0]; sheet.alpha_composite(im.crop((0,0,min(im.width,cell),min(im.height,cell))),((i%cols)*cell+2,(i//cols)*cell+2))
#P     sheet.save('pb_%d.png'%f); print(n,sheet.size)
# ---- mkpb.py: idle frame of each party member into www/img/pb/<character id>.png ----
#Q # party battle sprites: disc files 2988-2998 (idle frame 0) -> www/img/pb/<character id>.png
#Q import pbr,os,json
#Q OUT='/home/claude/xg/v/www/img/pb'; os.makedirs(OUT,exist_ok=True)
#Q FILE={0:2988,1:2989,2:2991,3:2990,4:2992,5:2993,6:2994,7:2995,8:2996,9:2997,10:2998}
#Q sz=[]
#Q for i in range(11):
#Q     im=pbr.render(pbr.load(FILE[i]),0)[0]; im.save('%s/%d.png'%(OUT,i),optimize=True); sz.append([im.width,im.height])
#Q print(json.dumps(sz).replace(' ',''), sum(os.path.getsize(OUT+'/'+x) for x in os.listdir(OUT)))
