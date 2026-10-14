/* Disc builder: makes the room maps and room pictures from the player's own Xenogears disc 1, so none of the game's
   graphics ship with the app. Runs in the app's page (Android WebView, Electron) and under Node for the tests.

   Input: a reader for the disc image file, readAt(offset, length) -> Promise<Uint8Array>, and its size. A .bin (raw
   2352-byte sectors, MODE2), an .iso (2048-byte sectors) or a .chd (chd.js) of disc 1 works; .cue files only point at the .bin.
   Output: files handed to a writer, put(path, bytes|string) -> Promise:
     maps/<room>.js   the walkable area, same format as before (see "area names and mini map" in index.html)
     plan/<room>.webp the overhead picture of the room, trimmed to the walkable area
   The room pictures are drawn by a small software renderer that is a port of the Python tools used before
   (fld/rt.py, fld/export.py, fld/trim_plan.py; project doc xenogears_fieldtex_py.txt / xenogears_trim_plan_py.txt). */
(function(G){
'use strict';
var XB={VERSION:8};   /* VERSION: bump when the built files change, so the app offers a rebuild */

/* ---------------- disc ---------------- */
/* open(reader, size): works out the sector layout (.bin, .iso or .chd), checks it is Xenogears disc 1, reads the game's file table */
XB.open=async function(reader,size){
 var d={reader:reader,size:size,raw:false,off:0};
 var head=await reader(0,16);
 if(String.fromCharCode.apply(null,head.subarray(0,8))==='MComprHD'){   /* a .chd: read through chd.js */
  var C=G.CHD||(typeof require!=='undefined'?require('./chd.js'):null),c=await C.open(reader);d.raw=true;
  d.sec=async function(n,cnt){cnt=cnt||1;var out=new Uint8Array(cnt*2048);for(var k=0;k<cnt;k++)out.set((await c.sector(n+k)).subarray(24,2072),k*2048);return out}}
 else{
 if(String.fromCharCode.apply(null,head.subarray(0,4))==='FILE'||size<100000)throw new Error('That looks like a .cue file. Pick the .bin file next to it.');
 var sync=head[0]===0&&head[11]===0;for(var i=1;i<11;i++)if(head[i]!==0xFF)sync=false;
 if(sync&&size%2352===0){d.raw=true;d.off=24}   /* MODE2 form 1: 24 bytes of header before the 2048 bytes of data */
 else if(size%2048!==0)throw new Error('This file is not a disc image (.bin or .iso).');
 d.sec=async function(n,cnt){cnt=cnt||1;
  if(!d.raw)return reader(n*2048,cnt*2048);
  var all=await reader(n*2352,cnt*2352),out=new Uint8Array(cnt*2048);
  for(var k=0;k<cnt;k++)out.set(all.subarray(k*2352+24,k*2352+24+2048),k*2048);return out};}
 var pvd=await d.sec(16);
 if(String.fromCharCode.apply(null,pvd.subarray(1,6))!=='CD001')throw new Error('This file is not a PlayStation disc image.');
 var rootLba=pvd[158]|pvd[159]<<8|pvd[160]<<16|pvd[161]<<24,root=await d.sec(rootLba),names=[];
 for(var p=0;p<2048&&root[p];p+=root[p])names.push(String.fromCharCode.apply(null,root.subarray(p+33,p+33+root[p+32])));
 d.names=names;
 if(names.indexOf('SLUS_006.64;1')<0){
  if(names.indexOf('SLUS_006.69;1')>=0)throw new Error('This is disc 2. Choose disc 1 - it holds every room.');
  throw new Error('This is not Xenogears disc 1 (US).')}
 var t=await d.sec(24,16);d.table=[];
 for(i=0;i+7<=t.length;i+=7){var s=t[i]|t[i+1]<<8|t[i+2]<<16,z=t[i+3]|t[i+4]<<8|t[i+5]<<16|t[i+6]<<24;if(s===0xFFFFFF)break;d.table.push([s,z])}
 d.file=async function(i){var e=d.table[i];if(!e||e[1]<=0)return null;var b=await d.sec(e[0],Math.ceil(e[1]/2048));return b.subarray(0,e[1])};
 return d};
/* the game's LZSS: u32 size, then flag bytes (bit set = u16 back reference, 12-bit distance, 4-bit length + 3) */
XB.lzss=function(d){var n=d[0]|d[1]<<8|d[2]<<16|d[3]<<24,out=new Uint8Array(n),o=0,p=4;
 while(o<n&&p<d.length){var fl=d[p++];
  for(var b=0;b<8;b++){if(o>=n||p>=d.length)break;
   if(fl>>b&1){var v=d[p]|d[p+1]<<8;p+=2;var off=v&0xFFF,ln=(v>>12)+3;for(var k=0;k<ln&&o<n;k++){out[o]=off<=o?out[o-off]:0;o++}}
   else out[o++]=d[p++]}}
 return out};
function u16(b,p){return b[p]|b[p+1]<<8}
function s16(b,p){var v=b[p]|b[p+1]<<8;return v&0x8000?v-65536:v}
function u32(b,p){return (b[p]|b[p+1]<<8|b[p+2]<<16|b[p+3]<<24)>>>0}
/* block k of a room file (0 textures, 1 walkmesh, 2 models, 3 sprites, 4 palettes, 5 scripts, 6 line-ups, 7 dialogue, 8 triggers) */
function block(h,k){var a=u32(h,0x130+4*k),b=u32(h,0x134+4*k);if(!(a<b&&b<=h.length))return null;return XB.lzss(h.subarray(a,b))}

/* ---------------- walkable area (maps/<room>.js) ---------------- */
/* Layer 0 of the walkmesh: vertices merged on x/z (numbered in the order the triangles use them), triangles that collapse to a
   line dropped, tone per triangle (0 plain floor, 1 other surface, 2 blocked: surface flag 0x800000) and, on triangles that
   are not blocked, a bit for each edge that only one such triangle uses (the outline). Matches the files shipped up to v1.64. */
XB.walk=function(h){
 var w=block(h,1);if(!w)return null;
 var sz0=u32(w,4),so=u32(w,0x14),to=u32(w,0x18),vo=u32(w,0x1C),nt=Math.floor(sz0/14);
 var surf=new Uint32Array(256);for(var i=0;i<256&&so+4*i+4<=w.length;i++)surf[i]=u32(w,so+4*i);
 var T=[],nv=0;
 for(i=0;i<nt;i++){var q=to+14*i;var t=[u16(w,q),u16(w,q+2),u16(w,q+4),w[q+12]];T.push(t);nv=Math.max(nv,t[0]+1,t[1]+1,t[2]+1)}
 var VX=new Int16Array(nv),VY=new Int16Array(nv),VZ=new Int16Array(nv);
 for(i=0;i<nv;i++){VX[i]=s16(w,vo+8*i);VY[i]=s16(w,vo+8*i+2);VZ[i]=s16(w,vo+8*i+4)}
 return {T:T,VX:VX,VY:VY,VZ:VZ,surf:surf}};
/* every layer of the walkmesh: [{T:[[a,b,c,surface]], VX, VY, VZ}] and the surface flags */
XB.walkLayers=function(h){var w=block(h,1);if(!w)return null;var n=Math.min(4,u32(w,0)),so=u32(w,0x14),surf=new Uint32Array(256),L=[];
 for(var i=0;i<256&&so+4*i+4<=w.length;i++)surf[i]=u32(w,so+4*i);
 for(var l=0;l<n;l++){var nt=Math.floor(u32(w,4+4*l)/14),to=u32(w,0x18+8*l),vo=u32(w,0x1C+8*l),T=[],nv=0;
  for(i=0;i<nt&&to+14*i+14<=w.length;i++){var q=to+14*i,t=[u16(w,q),u16(w,q+2),u16(w,q+4),w[q+12]];T.push(t);nv=Math.max(nv,t[0]+1,t[1]+1,t[2]+1)}
  var VX=new Int16Array(nv),VY=new Int16Array(nv),VZ=new Int16Array(nv);
  for(i=0;i<nv&&vo+8*i+6<=w.length;i++){VX[i]=s16(w,vo+8*i);VY[i]=s16(w,vo+8*i+2);VZ[i]=s16(w,vo+8*i+4)}
  L.push({T:T,VX:VX,VY:VY,VZ:VZ})}
 return {L:L,surf:surf}};
/* The walkable area for the map (maps/<room>.js). Layer 0 is the main floor; a room can have more layers (a bridge over a path, a
   second level), and those are added when their triangles are floor-sized (a layer of a few huge triangles is a rough bounds
   mesh, not floor). Left out: triangles whose surface has flag bits 0x18 (door and exit stubs that stick out of the room, and
   large invisible trigger areas), blocked triangles of the extra layers, and on the extra layers any triangle far bigger than its
   neighbours. Vertices are merged on x/z, triangles that collapse to a line are dropped; per triangle: tone (0 floor, 1 other
   surface, 2 blocked: 0x800000), bits 2-4 the edges that lie on the outline of its own layer, bits 5-6 the layer. */
/* XB.MAPFIX (mapfix.js): rooms whose walkable area was redrawn by hand; XB.EXITS (exits.js): a door or exit stub triangle that holds
   an exit (or lies within 60 units of one) is kept, so the outline reaches the doors. */
XB.mapBytes=function(h,f){
 var fx=XB.MAPFIX&&f!=null&&XB.MAPFIX[f];if(fx)return fixBytes(fx);
 var ex=((XB.EXITS&&f!=null&&XB.EXITS[f])||[]).filter(function(e){return e[0]!==null});
 return mapCore(h,false,ex)};
function fixBytes(fx){var keep=fx.t.map(function(t){return [{VX:fx.v.map(function(v){return v[0]}),VZ:fx.v.map(function(v){return v[1]})},[t[0],t[1],t[2],-1],0]});return packMap(keep,function(){return 0})}
function nearTri(m,t,p,d){var A=[m.VX[t[0]],m.VZ[t[0]]],B=[m.VX[t[1]],m.VZ[t[1]]],C=[m.VX[t[2]],m.VZ[t[2]]];
 function cr(o,a,b){return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])}
 var s1=cr(A,B,p),s2=cr(B,C,p),s3=cr(C,A,p);if((s1>=0&&s2>=0&&s3>=0)||(s1<=0&&s2<=0&&s3<=0))return true;
 function sd(a,b){var dx=b[0]-a[0],dz=b[1]-a[1],l=dx*dx+dz*dz,u=l?Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dz)/l)):0,x=a[0]+u*dx-p[0],z=a[1]+u*dz-p[1];return Math.sqrt(x*x+z*z)}
 return Math.min(sd(A,B),sd(B,C),sd(C,A))<=d}
function mapCore(h,noStubCut,ex){
 var W=XB.walkLayers(h);if(!W||!W.L.length)return null;var surf=W.surf,keep=[],STUB=noStubCut?0x10000000:0x80;   /* 0x80 = Fei on foot cannot walk here (Noah decompilation: 0x20 NPCs, 0x40 gears, 0x80 people; 0x08/0x10 only stop jumping) */
 function longest(m,t){var b=0;for(var k=0;k<3;k++){var p=t[k],q=t[(k+1)%3],dx=m.VX[p]-m.VX[q],dz=m.VZ[p]-m.VZ[q];b=Math.max(b,Math.sqrt(dx*dx+dz*dz))}return b}
 function med(a){if(!a.length)return 0;a=a.slice().sort(function(x,y){return x-y});return a[a.length>>1]}
 var base=0;
 W.L.forEach(function(m,l){var walk=m.T.filter(function(t){var f=surf[t[3]];return !(f&0x800000)&&!(f&STUB)}),sz=walk.map(function(t){return longest(m,t)}),md=med(sz);
  if(l>0&&l===W.L.length-1)return;   /* the last layer is the camera-bounds mesh, never walked on */
  if(l===0)base=md;
  else if(!walk.length||md>Math.max(600,3*base))return;   /* a rough bounds layer */
  m.T.forEach(function(t){var f=surf[t[3]];if((f&STUB)&&!(ex.length&&!(f&0x800000)&&longest(m,t)<=Math.max(300,2.5*(base||md))&&ex.some(function(e){return nearTri(m,t,e,60)})))return;if(l>0&&(f&0x800000))return;var lg=longest(m,t);if(l>0&&lg>Math.max(1500,10*md))return;keep.push([m,t,l])})});
  if(!noStubCut&&!keep.some(function(e){return !(surf[e[1][3]]&0x800000)}))return mapCore(h,true,ex);   /* nothing left but stubs: keep them */
 return packMap(keep,function(e){var f=surf[e[1][3]];return f&0x800000?2:(f===0?0:1)})};
function packMap(keep,toneOf){
 function key(m,j){return m.VX[j]+','+m.VZ[j]}
 keep=keep.filter(function(e){var m=e[0],t=e[1],a=key(m,t[0]),b=key(m,t[1]),c=key(m,t[2]);return a!==b&&b!==c&&a!==c});
 var idx={},vs=[],ri=[];
 keep.forEach(function(e){var m=e[0],t=e[1],r=[];for(var k=0;k<3;k++){var kk=key(m,t[k]);if(!(kk in idx)){idx[kk]=vs.length;vs.push([m.VX[t[k]],m.VZ[t[k]]])}r.push(idx[kk])}ri.push(r)});
 var tone=keep.map(toneOf),cnt={};
 function ek(l,a,b){return l+':'+(a<b?a+'_'+b:b+'_'+a)}
 keep.forEach(function(e,i){if(tone[i]===2)return;for(var k=0;k<3;k++){var q=ek(e[2],ri[i][k],ri[i][(k+1)%3]);cnt[q]=(cnt[q]||0)+1}});
 var out=new Uint8Array(4+vs.length*4+keep.length*7),dv=new DataView(out.buffer);
 dv.setUint16(0,vs.length,true);dv.setUint16(2,keep.length,true);var o=4;
 vs.forEach(function(v){dv.setInt16(o,v[0],true);dv.setInt16(o+2,v[1],true);o+=4});
 keep.forEach(function(e,i){var fl=tone[i]|(e[2]&3)<<5;
  if(tone[i]!==2)for(var k=0;k<3;k++)if(cnt[ek(e[2],ri[i][k],ri[i][(k+1)%3])]===1)fl|=4<<k;
  dv.setUint16(o,ri[i][0],true);dv.setUint16(o+2,ri[i][1],true);dv.setUint16(o+4,ri[i][2],true);out[o+6]=fl;o+=7});
 return out};
function b64(u8){var s='',CH=8192;for(var i=0;i<u8.length;i+=CH)s+=String.fromCharCode.apply(null,u8.subarray(i,i+CH));return (typeof btoa!=='undefined'?btoa(s):Buffer.from(s,'binary').toString('base64'))}
XB.mapJs=function(f,bytes){return 'MAPDATA['+f+']="'+(bytes?b64(bytes):'')+'";\n'};
XB.b64=b64;

/* ---------------- room geometry ---------------- */
/* VRAM image the room's texture file builds (1024 x 512 16-bit words) */
XB.vram=function(t){var V=new Uint16Array(1024*512),p=0;
 while(t&&p+0x1C<=t.length){var typ=u16(t,p),x=u16(t,p+4),y=u16(t,p+6),mx=u16(t,p+8),my=u16(t,p+10),w=u16(t,p+12),cnt=u16(t,p+18);
  if((typ!==0x1200&&typ!==0x1201)||cnt===0||cnt>600)break;
  var q=p+0x800,X=x+mx,Y=y+my;
  for(var c=0;c<cnt;c++){var hh=u16(t,p+0x1C+2*c);
   if(hh&&q+w*hh*2<=t.length&&X+w<=1024){var r=Math.min(hh,512-Y);for(var j=0;j<r;j++)for(var i=0;i<w;i++)V[(Y+j)*1024+X+i]=u16(t,q+2*(j*w+i))}
   Y+=hh;q+=0x800}
  p=q}
 return V};
/* model id -> parts [{V:[x,y,z...], polys:[[idx], kind, data]}] (block 2 of the room file) */
XB.models=function(h){var md=block(h,2),out={};if(!md)return out;var n=u32(md,0);if(n<1||n>4000)return out;
 var offs=[];for(var i=0;i<n;i++)offs.push(u32(md,4+4*i));offs.push(md.length);
 for(i=0;i<n;i++){var m=md.subarray(offs[i],offs[i+1]);if(m.length<0x3C)continue;var np=u32(m,0);if(np<1||np>64||4+0x38*np>m.length)continue;
  var parts=[];
  for(var k=0;k<np;k++){var hh=4+0x38*k,nv=u16(m,hh+0x0E),ng=u16(m,hh+0x12),vo=u32(m,hh+0x14),fo=u32(m,hh+0x1C),eo=u32(m,hh+0x20);
   if(nv===0||!(vo<=fo&&fo<=eo&&eo<=m.length)||vo+nv*8>m.length)continue;
   var V=new Float64Array(nv*3);for(var j=0;j<nv;j++){V[3*j]=s16(m,vo+8*j);V[3*j+1]=s16(m,vo+8*j+2);V[3*j+2]=s16(m,vo+8*j+4)}
   var groups=[],p=fo,ok=true;
   for(var g=0;g<ng;g++){if(p+4>eo){ok=false;break}var typ=u16(m,p),cnt=u16(m,p+2);p+=4;if(p+cnt*8>eo){ok=false;break}
    var fs=[];for(var c=0;c<cnt;c++)fs.push([u16(m,p+8*c),u16(m,p+8*c+2),u16(m,p+8*c+4),u16(m,p+8*c+6)]);groups.push([typ&0xFF,fs]);p+=cnt*8}
   if(ok)parts.push([V,groups,eo])}
  var ends=parts.map(function(x){return x[2]}).filter(function(v,i,a){return a.indexOf(v)===i}).sort(function(a,b){return a-b});ends.push(m.length);
  out[i]=parts.map(function(x){return {V:x[0],polys:polys(x[1],m.subarray(x[2],ends[ends.indexOf(x[2])+1]))}})}
 return out};
/* the drawing commands that go with a part's faces: texture page and palette words, then per face uv (textured) or colour */
function polys(groups,st){var p=0,tp=0,cl=0,out=[];
 for(var gi=0;gi<groups.length;gi++){var typ=groups[gi][0],faces=groups[gi][1],quad=!!(typ&8),tex=!!(typ&1);
  for(var fi=0;fi<faces.length;fi++){var f=faces[fi];
   while(p+4<=st.length&&st[p+3]>=0x80){var w=u32(st,p);if(w>>>24===0xC4)tp=w&0xFFFF;else if(w>>>24===0xC8)cl=w&0xFFFF;p+=4}
   var need=tex?(quad?12:8):4;if(p+need>st.length)return out;
   var idx=quad?f.slice(0,4):f.slice(0,3);
   if(tex){var uv,c;if(quad){uv=[[st[p+4],st[p+5]],[st[p+6],st[p+7]],[st[p+8],st[p+9]],[st[p+10],st[p+11]]];c=st[p+3]}
           else{uv=[[st[p+4],st[p+5]],[st[p+6],st[p+7]],[st[p],st[p+1]]];c=st[p+3]}
    out.push([idx,'t',[uv,tp,cl,c]])}
   else out.push([idx,'c',[u32(st,p)&0xFFFFFF,tp,st[p+3]]]);
   p+=need}}
 return out}
/* object placement table in the room header: flags, rotation x, y, z (4096 a turn), position x, y, z, model id */
function entities(h){var n=u32(h,0x18C),out=[];for(var i=0;i<Math.min(n,2000);i++){var o=0x190+16*i,r=[];for(var k=0;k<8;k++)r.push(s16(h,o+2*k));out.push(r)}return out}

function placed(h){var M=XB.models(h),out=[];
 entities(h).forEach(function(e){var fl=e[0],mid=e[7];if(fl&0x40||!M[mid])return;
  var a=e[2]*Math.PI/2048,c=Math.cos(a),s=Math.sin(a),ax=e[1]*Math.PI/2048,cx=Math.cos(ax),sx=Math.sin(ax),az=e[3]*Math.PI/2048,cz=Math.cos(az),sz=Math.sin(az);
  out.push(M[mid].map(function(part){var V=part.V,n=V.length/3,P=new Float64Array(n*3);
   for(var j=0;j<n;j++){var x=V[3*j],y=V[3*j+1],z=V[3*j+2],t;
    t=y*cx-z*sx;z=y*sx+z*cx;y=t; t=x*c+z*s;z=-x*s+z*c;x=t; t=x*cz-y*sz;y=x*sz+y*cz;x=t;
    P[3*j]=x+e[4];P[3*j+1]=y+e[5];P[3*j+2]=z+e[6]}
   return {P:P,polys:part.polys}}))});
 return out}

/* ---------------- distance transforms and blur (for the floor fill and the trim) ---------------- */
/* squared distance from every pixel to the nearest pixel where feat is set, and that pixel's index (Felzenszwalb) */
function edt(feat,W,H){var INF=1e20,D=new Float64Array(W*H),I=new Int32Array(W*H).fill(-1),f=new Float64Array(Math.max(W,H)),fi=new Int32Array(Math.max(W,H)),
 v=new Int32Array(Math.max(W,H)),z=new Float64Array(Math.max(W,H)+1),d=new Float64Array(Math.max(W,H)),di=new Int32Array(Math.max(W,H));
 function pass(n){var k=0;v[0]=0;z[0]=-INF;z[1]=INF;
  for(var q=1;q<n;q++){var s=((f[q]+q*q)-(f[v[k]]+v[k]*v[k]))/(2*q-2*v[k]);
   while(s<=z[k]){k--;s=((f[q]+q*q)-(f[v[k]]+v[k]*v[k]))/(2*q-2*v[k])}
   k++;v[k]=q;z[k]=s;z[k+1]=INF}
  k=0;for(q=0;q<n;q++){while(z[k+1]<q)k++;d[q]=(q-v[k])*(q-v[k])+f[v[k]];di[q]=fi[v[k]]}}
 for(var x=0;x<W;x++){for(var y=0;y<H;y++){var on=feat[y*W+x];f[y]=on?0:INF;fi[y]=on?y*W+x:-1}pass(H);for(y=0;y<H;y++){D[y*W+x]=d[y];I[y*W+x]=di[y]}}
 for(y=0;y<H;y++){for(x=0;x<W;x++){f[x]=D[y*W+x];fi[x]=I[y*W+x]}pass(W);for(x=0;x<W;x++){D[y*W+x]=d[x];I[y*W+x]=di[x]}}
 return {D:D,I:I}}
function blur(A,W,H,sig){var r=Math.ceil(sig*3),k=new Float64Array(2*r+1),s=0;for(var i=-r;i<=r;i++){k[i+r]=Math.exp(-i*i/(2*sig*sig));s+=k[i+r]}for(i=0;i<k.length;i++)k[i]/=s;
 var T=new Float32Array(W*H),O=new Float32Array(W*H);
 for(var y=0;y<H;y++)for(var x=0;x<W;x++){var a=0;for(i=-r;i<=r;i++){var xx=Math.min(W-1,Math.max(0,x+i));a+=A[y*W+xx]*k[i+r]}T[y*W+x]=a}
 for(y=0;y<H;y++)for(x=0;x<W;x++){a=0;for(i=-r;i<=r;i++){var yy=Math.min(H-1,Math.max(0,y+i));a+=T[yy*W+x]*k[i+r]}O[y*W+x]=a}
 return O}

/* ---------------- room picture ---------------- */
/* height of the walkable floor under each pixel (the topmost, smallest y), 1e9 where there is none; grow: fill from the nearest floor */
/* floor height per pixel (the topmost floor); with extra floor layers (T[i][4] > 0) layer 0 wins wherever it reaches, the others
   fill in where it does not (a street below bridges), so a flat sheet over a whole room does not hide the main floor */
function floormap(wk,W,cx,cz,sc,grow){var fl=new Float32Array(W*W).fill(1e9),flx=null,T=wk.T,X=wk.VX,Y=wk.VY,Z=wk.VZ;
 for(var t=0;t<T.length;t++){var a=T[t][0],b=T[t][1],c=T[t][2],dst=fl;if(T[t][4]){if(!flx)flx=new Float32Array(W*W).fill(1e9);dst=flx}
  var x0=W/2+(X[a]-cx)*sc,x1=W/2+(X[b]-cx)*sc,x2=W/2+(X[c]-cx)*sc,y0=W/2+(Z[a]-cz)*sc,y1=W/2+(Z[b]-cz)*sc,y2=W/2+(Z[c]-cz)*sc;
  var bx0=Math.max(Math.floor(Math.min(x0,x1,x2))-1,0),bx1=Math.min(Math.floor(Math.max(x0,x1,x2))+1,W-1),by0=Math.max(Math.floor(Math.min(y0,y1,y2))-1,0),by1=Math.min(Math.floor(Math.max(y0,y1,y2))+1,W-1);
  if(bx1<bx0||by1<by0)continue;var den=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2);if(Math.abs(den)<1e-6)continue;var e=0.5/Math.max(Math.sqrt(Math.abs(den)),1);
  for(var py=by0;py<=by1;py++)for(var px=bx0;px<=bx1;px++){var gx=px+0.5,gy=py+0.5,A=((y1-y2)*(gx-x2)+(x2-x1)*(gy-y2))/den,B=((y2-y0)*(gx-x2)+(x0-x2)*(gy-y2))/den,C=1-A-B;
   if(A>=-e&&B>=-e&&C>=-e){var zz=A*Y[a]+B*Y[b]+C*Y[c],k=py*W+px;if(zz<dst[k])dst[k]=zz}}}
 if(flx)for(var q=0;q<W*W;q++)if(fl[q]>1e8&&flx[q]<1e8)fl[q]=flx[q];
 if(grow){var have=new Uint8Array(W*W),any=false;for(var i=0;i<W*W;i++)if(fl[i]<1e8){have[i]=1;any=true}
  if(any){var r=edt(have,W,W),g2=grow*grow,o=new Float32Array(fl);for(i=0;i<W*W;i++)if(!have[i]&&r.D[i]<=g2)o[i]=fl[r.I[i]];fl=o}}
 return fl}
/* one textured top-down render, W x W, as in fld/rt.py room1 (y is negative upwards; a smaller y is nearer the viewer) */
function render1(h,VR,wk,plan,W,cut){var clipAbove=1500,shade=0.35,head=130,cx=plan[0],cz=plan[1],sc=W/plan[2];
 var T=wk.T,miny=1e9,maxy=-1e9,wx0=1e9,wx1=-1e9,wz0=1e9,wz1=-1e9;
 for(var j=0;j<wk.VX.length;j++){var y=wk.VY[j],x=wk.VX[j],z=wk.VZ[j];miny=Math.min(miny,y);maxy=Math.max(maxy,y);wx0=Math.min(wx0,x);wx1=Math.max(wx1,x);wz0=Math.min(wz0,z);wz1=Math.max(wz1,z)}
 var top=miny-clipAbove,wh=maxy-miny;
 var FL0=floormap(wk,W,cx,cz,sc,0),FL=floormap(wk,W,cx,cz,sc,1e9);for(var i=0;i<FL.length;i++)FL[i]-=head;
 var zb=new Float32Array(W*W).fill(1e9),col=new Float32Array(W*W*3),seen=new Uint8Array(W*W),und=new Float32Array(W*W).fill(-1),uz=new Float32Array(W*W).fill(1e9),tris=[],allT=[];
 placed(h).forEach(function(obj){var a0=1e9,a1=-1e9,b0=1e9,b1=-1e9,c0=1e9,c1=-1e9;
  obj.forEach(function(o){var P=o.P;for(var j=0;j<P.length;j+=3){a0=Math.min(a0,P[j]);a1=Math.max(a1,P[j]);b0=Math.min(b0,P[j+1]);b1=Math.max(b1,P[j+1]);c0=Math.min(c0,P[j+2]);c1=Math.max(c1,P[j+2])}});
  if(a0<wx0-400&&a1>wx1+400&&c0<wz0-400&&c1>wz1+400&&(((b1-b0)>Math.max(2.5*wh,300)&&b0<miny-200)||b0>maxy+300))return;
  /* an object that encloses the whole walkable area is dropped when it is a shell rising well above the floor (sky domes, walls
     round an arena) or lies wholly and well under the floor (cloud planes far below; a sea just under a deck stays); low ground round a flat room (room 67's passage,
     Nortune 194) is kept */
  obj.forEach(function(o){var P=o.P,nP=P.length/3;
   o.polys.forEach(function(pl){var idx=pl[0],kind=pl[1],data=pl[2];if(Math.max.apply(null,idx)>=nP)return;
    (idx.length===4?[[0,1,2],[1,3,2]]:[[0,1,2]]).forEach(function(tr){
     var p=tr.map(function(j){var q=idx[j]*3;return [P[q],P[q+1],P[q+2]]});
     var my=(p[0][1]+p[1][1]+p[2][1])/3;if(my<top)return;
     var d,cmd;
     if(kind==='t'){cmd=data[3];d=[tr.map(function(j){return data[0][j]}),data[1],data[2]]}
     else{var c0_=data[0];cmd=data[2];d=c0_;if((c0_&255)+((c0_>>8)&255)+((c0_>>16)&255)<30&&!(cmd&2))return}   /* black filler planes hide the floor (and are left out of the grey shading too: they are not ground) */
     allT.push(p);
     tris.push([!!(cmd&2),p,kind,d,(data[1]>>5)&3])})})})});
 /* plain shading of the topmost geometry everywhere (the old untextured picture), shown dimmed under the textured one */
 allT.forEach(function(p){var x0=W/2+(p[0][0]-cx)*sc,x1=W/2+(p[1][0]-cx)*sc,x2=W/2+(p[2][0]-cx)*sc,y0=W/2+(p[0][2]-cz)*sc,y1=W/2+(p[1][2]-cz)*sc,y2=W/2+(p[2][2]-cz)*sc;
  var bx0=Math.max(Math.floor(Math.min(x0,x1,x2)),0),bx1=Math.min(Math.floor(Math.max(x0,x1,x2))+1,W-1),by0=Math.max(Math.floor(Math.min(y0,y1,y2)),0),by1=Math.min(Math.floor(Math.max(y0,y1,y2))+1,W-1);
  if(bx1<bx0||by1<by0)return;var den=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2);if(Math.abs(den)<1e-6)return;
  var ux=p[1][0]-p[0][0],uy=p[1][1]-p[0][1],uz2=p[1][2]-p[0][2],vx=p[2][0]-p[0][0],vy=p[2][1]-p[0][1],vz=p[2][2]-p[0][2];
  var nx=uy*vz-uz2*vy,ny=uz2*vx-ux*vz,nz=ux*vy-uy*vx,up=Math.abs(ny)/(Math.sqrt(nx*nx+ny*ny+nz*nz)||1),lum=100+116*up;
  for(var py=by0;py<=by1;py++)for(var px=bx0;px<=bx1;px++){var gx=px+0.5,gy=py+0.5,A=((y1-y2)*(gx-x2)+(x2-x1)*(gy-y2))/den,B=((y2-y0)*(gx-x2)+(x0-x2)*(gy-y2))/den,C=1-A-B;
   if(A<0||B<0||C<0)continue;var k=py*W+px,zz=A*p[0][1]+B*p[1][1]+C*p[2][1];if(zz<uz[k]){uz[k]=zz;und[k]=lum}}});
 var opaque=tris.filter(function(t){return !t[0]}),semi=tris.filter(function(t){return t[0]});
 semi.sort(function(a,b){return (b[1][0][1]+b[1][1][1]+b[1][2][1])-(a[1][0][1]+a[1][1][1]+a[1][2][1])});
 opaque.concat(semi).forEach(function(tt){var sm=tt[0],p=tt[1],kind=tt[2],data=tt[3],abr=tt[4];
  var x0=W/2+(p[0][0]-cx)*sc,x1=W/2+(p[1][0]-cx)*sc,x2=W/2+(p[2][0]-cx)*sc,y0=W/2+(p[0][2]-cz)*sc,y1=W/2+(p[1][2]-cz)*sc,y2=W/2+(p[2][2]-cz)*sc,z0=p[0][1],z1=p[1][1],z2=p[2][1];
  var bx0=Math.max(Math.floor(Math.min(x0,x1,x2)),0),bx1=Math.min(Math.floor(Math.max(x0,x1,x2))+1,W-1),by0=Math.max(Math.floor(Math.min(y0,y1,y2)),0),by1=Math.min(Math.floor(Math.max(y0,y1,y2))+1,W-1);
  if(bx1<bx0||by1<by0)return;var den=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2);if(Math.abs(den)<1e-6)return;
  var ux=p[1][0]-p[0][0],uy=p[1][1]-p[0][1],uz=p[1][2]-p[0][2],vx=p[2][0]-p[0][0],vy=p[2][1]-p[0][1],vz=p[2][2]-p[0][2];
  var nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx,nl=Math.sqrt(nx*nx+ny*ny+nz*nz)||1,up=Math.abs(ny)/nl,down=ny<0||cut==='all';
  var sh=sm?1:(1-shade)+shade*up,uv,bx,by,mode,qx,qy,cr,cg,cb;
  if(kind==='t'){uv=data[0];var tp=data[1],cl=data[2];bx=(tp&0xF)*64;by=((tp>>4)&1)*256;mode=(tp>>7)&3;qx=(cl&0x3F)*16;qy=(cl>>6)&0x1FF}
  else{cr=data&255;cg=(data>>8)&255;cb=(data>>16)&255}
  for(var py=by0;py<=by1;py++)for(var px=bx0;px<=bx1;px++){var gx=px+0.5,gy=py+0.5,A=((y1-y2)*(gx-x2)+(x2-x1)*(gy-y2))/den,B=((y2-y0)*(gx-x2)+(x0-x2)*(gy-y2))/den,C=1-A-B;
   if(A<0||B<0||C<0)continue;var k=py*W+px,zz=A*z0+B*z1+C*z2;
   if(sm?!(zz<zb[k]+12):!(zz<zb[k]))continue;
   if(down){var f=FL[k];if(!(f>1e8||zz>=f))continue}   /* undersides above head height are ceilings: from above they only hide the room */
   var r,g,b,stp=null;
   if(kind==='t'){var uu=Math.min(255,Math.max(0,Math.floor(A*uv[0][0]+B*uv[1][0]+C*uv[2][0]+0.5))),vv=Math.min(255,Math.max(0,Math.floor(A*uv[0][1]+B*uv[1][1]+C*uv[2][1]+0.5))),px16;
    if(mode===0){var wd=VR[((by+vv)&511)*1024+((bx+(uu>>2))&1023)],ix=(wd>>((uu&3)*4))&15;px16=VR[qy*1024+((qx+ix)&1023)]}
    else if(mode===1){wd=VR[((by+vv)&511)*1024+((bx+(uu>>1))&1023)];ix=(wd>>((uu&1)*8))&255;px16=VR[qy*1024+((qx+ix)&1023)]}
    else px16=VR[((by+vv)&511)*1024+((bx+uu)&1023)];
    if(px16===0)continue;r=(px16&31)*255/31;g=((px16>>5)&31)*255/31;b=((px16>>10)&31)*255/31;stp=(px16&0x8000)!==0}
   else{r=cr;g=cg;b=cb}
   var o3=k*3;
   if(!sm){zb[k]=zz;col[o3]=r*sh;col[o3+1]=g*sh;col[o3+2]=b*sh}
   else{if(stp===null||stp){var dr=col[o3],dg=col[o3+1],db=col[o3+2];
     if(abr===0){dr=(dr+r)/2;dg=(dg+g)/2;db=(db+b)/2}else if(abr===1){dr+=r;dg+=g;db+=b}else if(abr===2){dr-=r;dg-=g;db-=b}else{dr+=r/4;dg+=g/4;db+=b/4}
     col[o3]=Math.min(255,Math.max(0,dr));col[o3+1]=Math.min(255,Math.max(0,dg));col[o3+2]=Math.min(255,Math.max(0,db))}
    else{col[o3]=r;col[o3+1]=g;col[o3+2]=b}
    if(zb[k]>1e8)seen[k]=1}}});
 var out=new Uint8ClampedArray(W*W*4),foot=0,hit=0;
 for(i=0;i<W*W;i++){var valid=zb[i]<1e8||(seen[i]&&col[3*i]+col[3*i+1]+col[3*i+2]>24);
  out[4*i]=col[3*i];out[4*i+1]=col[3*i+1];out[4*i+2]=col[3*i+2];out[4*i+3]=valid?255:0;
  if(FL0[i]<1e8){foot++;if(zb[i]<FL0[i]-2*head)hit++}}
 return {img:out,cov:hit/Math.max(foot,1),und:und}}
/* the room picture at W x W before finishing: re-drawn without any overhead geometry when it covers most of the floor */
/* layer 0 plus the extra floor layers the map keeps (floor-sized, not blocked, not door stubs), as one mesh: rooms with a lower
   level (a street under bridges, a deck under a gangway) need every floor for the height tests, not only layer 0 */
/* the floors of a room, one entry per walk layer kept: [{l, m (the layer), T (its triangles to draw from)}]. Layer 0 whole; the
   other layers only when floor-sized, not the camera-bounds mesh (the last layer) and not a flat sheet over the whole room. */
XB.floorList=function(h){var W=XB.walkLayers(h);if(!W||!W.L.length)return null;var surf=W.surf,base=0,out=[];
 function longest(m,t){var b=0;for(var k=0;k<3;k++){var p=t[k],q=t[(k+1)%3],dx=m.VX[p]-m.VX[q],dz=m.VZ[p]-m.VZ[q];b=Math.max(b,Math.sqrt(dx*dx+dz*dz))}return b}
 W.L.forEach(function(m,l){var walk=m.T.filter(function(t){var f=surf[t[3]];return !(f&0x800000)&&!(f&0x80)}),sz=walk.map(function(t){return longest(m,t)}).sort(function(a,b){return a-b}),md=sz.length?sz[sz.length>>1]:0;
  if(l===0)base=md;else if(!walk.length||md>Math.max(600,3*base))return;
  if(l>0&&l===W.L.length-1)return;   /* camera-bounds mesh */
  if(l>0){var y0=1e9,y1=-1e9,a0=1e9,a1=-1e9,b0=1e9,b1=-1e9;walk.forEach(function(t){for(var k=0;k<3;k++){var j=t[k];y0=Math.min(y0,m.VY[j]);y1=Math.max(y1,m.VY[j]);a0=Math.min(a0,m.VX[j]);a1=Math.max(a1,m.VX[j]);b0=Math.min(b0,m.VZ[j]);b1=Math.max(b1,m.VZ[j])}});
   var L0=W.L[0],c0=1e9,c1=-1e9,d0=1e9,d1=-1e9;for(var j=0;j<L0.VX.length;j++){c0=Math.min(c0,L0.VX[j]);c1=Math.max(c1,L0.VX[j]);d0=Math.min(d0,L0.VZ[j]);d1=Math.max(d1,L0.VZ[j])}
   var ov=Math.max(0,Math.min(a1,c1)-Math.max(a0,c0))*Math.max(0,Math.min(b1,d1)-Math.max(b0,d0)),ar=Math.max(1,(c1-c0)*(d1-d0));
   if(y1-y0<=8&&ov>=0.7*ar)return}   /* a flat sheet over the whole room (room 95's at -776): not a floor to draw from */
  out.push({l:l,m:m,T:(l===0?m.T:walk).filter(function(t){return !(l>0&&longest(m,t)>Math.max(1500,10*md))}),walk:walk})});
 return {list:out,surf:surf}};
/* those floors merged into one mesh (several layers: rooms with a lower level need every floor for the height tests) */
function mergeFloors(F,pick){var VX=[],VY=[],VZ=[],T=[];
 F.list.forEach(function(e){if(pick&&!pick(e))return;var m=e.m,off=VX.length;for(var j=0;j<m.VX.length;j++){VX.push(m.VX[j]);VY.push(m.VY[j]);VZ.push(m.VZ[j])}
  e.T.forEach(function(t){T.push([t[0]+off,t[1]+off,t[2]+off,t[3]])})});
 return {T:T,VX:Int16Array.from(VX),VY:Int16Array.from(VY),VZ:Int16Array.from(VZ),surf:F.surf}}
XB.walkFloors=function(h){var F=XB.floorList(h);return F?mergeFloors(F):null};
/* Rooms on two or more levels (a street under bridges, a hold under a deck): the walk layers whose floor has another floor more
   than 150 units above it over at least 40 cells of 32 x 32 units. Each gets its own picture (plan/<room>_<layer>.webp) drawn from
   that layer alone with everything above head height over it taken away, and the app shows it while the party is on that layer. */
XB.levels=function(h){var F=XB.floorList(h);if(!F||F.list.length<2&&!F.list.length)return [];var C=32;
 function cells(e){var m=e.m,M={};e.walk.forEach(function(t){var P=[0,1,2].map(function(k){return [m.VX[t[k]],m.VY[t[k]],m.VZ[t[k]]]});
   var den=(P[1][2]-P[2][2])*(P[0][0]-P[2][0])+(P[2][0]-P[1][0])*(P[0][2]-P[2][2]);if(!den)return;
   var x0=Math.floor(Math.min(P[0][0],P[1][0],P[2][0])/C),x1=Math.floor(Math.max(P[0][0],P[1][0],P[2][0])/C),z0=Math.floor(Math.min(P[0][2],P[1][2],P[2][2])/C),z1=Math.floor(Math.max(P[0][2],P[1][2],P[2][2])/C);
   for(var x=x0;x<=x1;x++)for(var z=z0;z<=z1;z++){var gx=(x+0.5)*C,gz=(z+0.5)*C,A=((P[1][2]-P[2][2])*(gx-P[2][0])+(P[2][0]-P[1][0])*(gz-P[2][2]))/den,B=((P[2][2]-P[0][2])*(gx-P[2][0])+(P[0][0]-P[2][0])*(gz-P[2][2]))/den,c=1-A-B;
    if(A<0||B<0||c<0)continue;var k=x+','+z;(M[k]||(M[k]=[])).push(A*P[0][1]+B*P[1][1]+c*P[2][1])}});return M}
 var cs=F.list.map(cells),out=[];
 F.list.forEach(function(e,i){var n=0,under=0;for(var k in cs[i]){n++;var y=Math.max.apply(null,cs[i][k]),up=false;   /* y down: the lowest floor in the cell */
   for(var j=0;j<cs.length&&!up;j++){var v=cs[j][k];if(v)for(var q=0;q<v.length;q++)if(v[q]<y-150){up=true;break}}if(up)under++}
  if(under>=40&&under>=0.03*n)out.push(e.l)});
 return out};
XB.levelPicture=async function(d,f,plan,l){var h=await d.file(606+2*f),t=await d.file(607+2*f);if(!h)return null;var F=XB.floorList(h);if(!F)return null;
 var wk=mergeFloors(F,function(e){return e.l===l});if(!wk.T.length)return null;
 var W=1024,VR=XB.vram(t),r=render1(h,VR,wk,plan,W,'all'),r0=XB.renderRoom(h,t,plan,W);if(!r0)return XB.finish(r,W);
 /* the level's own render where its floor is (and a margin round it), the room's usual picture dimmed everywhere else */
 var fl=floormap(wk,W,plan[0],plan[1],W/plan[2],0),feat=new Uint8Array(W*W);for(var i=0;i<W*W;i++)if(fl[i]<1e8)feat[i]=1;
 var D=edt(feat,W,W).D,R=20,F=16,img=new Uint8ClampedArray(W*W*4),und=new Float32Array(W*W);
 /* where the level's own render has nothing (a walk layer with no drawn floor under it, room 288's under the hall) the usual picture stays */
 var cov=new Float32Array(W*W);for(i=0;i<W*W;i++)cov[i]=r.img[4*i+3]>0?1:0;cov=blur(cov,W,W,8);
 for(i=0;i<W*W;i++){var d=Math.sqrt(D[i]),m=(d<=R?1:d>=R+F?0:1-(d-R)/F)*Math.min(1,Math.max(0,(cov[i]-0.35)*3)),q=4*i;
  var a1=r.img[q+3]/255,a0=r0.img[q+3]/255,dim=0.55,A=m*a1+(1-m)*a0;
  if(A>0){img[q]=(m*a1*r.img[q]+(1-m)*a0*r0.img[q]*dim)/A;img[q+1]=(m*a1*r.img[q+1]+(1-m)*a0*r0.img[q+1]*dim)/A;img[q+2]=(m*a1*r.img[q+2]+(1-m)*a0*r0.img[q+2]*dim)/A;img[q+3]=A*255}
  und[i]=m>=0.5?r.und[i]:(r0.und[i]>=0?r0.und[i]*dim:-1)}
 return XB.finish({img:img,und:und},W)};
XB.renderRoom=function(h,tex,plan,W,mode){var VR=XB.vram(tex),wk=mode==='layer0'?XB.walk(h):XB.walkFloors(h);if(!wk||!wk.T.length)return null;
 var r=render1(h,VR,wk,plan,W,'down');if(r.cov>0.5)r=render1(h,VR,wk,plan,W,'all');return r};
/* finish as fld/export.py: brighten dark rooms, halve the size (premultiplied), and put a dim grey-blue shading of the bare
   geometry under it where the texture has nothing, so no part of the room is lost */
XB.finish=function(r,W){var a=r.img,n=W*W,i;
 var hist=new Float64Array(766),cnt=0;for(i=0;i<n;i++)if(a[4*i+3]){hist[a[4*i]+a[4*i+1]+a[4*i+2]]++;cnt++}   /* 95th percentile of brightness, from a histogram */
 var g=1;if(cnt){var want=0.95*(cnt-1),acc=0,s3=0;for(s3=0;s3<766;s3++){acc+=hist[s3];if(acc>want)break}var p95=s3/3;if(p95<100)g=Math.min(3,100/Math.max(p95,1))}
 var S=W/2,o=new Uint8ClampedArray(S*S*4);
 for(var y=0;y<S;y++)for(var x=0;x<S;x++){var R=0,G=0,B=0,A=0,U=0,un=0;
  for(var dy=0;dy<2;dy++)for(var dx=0;dx<2;dx++){var k=(2*y+dy)*W+2*x+dx,al=a[4*k+3]/255;R+=Math.min(255,a[4*k]*g)*al;G+=Math.min(255,a[4*k+1]*g)*al;B+=Math.min(255,a[4*k+2]*g)*al;A+=al;
   if(r.und[k]>=0){U+=r.und[k]*0.30;un++}}
  var q=4*(y*S+x),ua=un/4,ul=un?U/un:0,fa=A/4;
  var nr=fa?R/A:0,ng=fa?G/A:0,nb=fa?B/A:0,oa=fa+ua*(1-fa);
  if(oa>0){o[q]=(nr*fa+ul*0.92*ua*(1-fa))/oa;o[q+1]=(ng*fa+ul*0.96*ua*(1-fa))/oa;o[q+2]=(nb*fa+ul*1.12*ua*(1-fa))/oa;o[q+3]=oa*255}}
 return o};
/* trim to the walkable area plus a margin, as fld/trim_plan.py (10 %, closing 14 %) */
XB.trim=function(px,S,mapBytes,plan){if(!mapBytes)return px;var dv=new DataView(mapBytes.buffer,mapBytes.byteOffset,mapBytes.byteLength),nv=dv.getUint16(0,true),nt=dv.getUint16(2,true);if(!nt)return px;
 var vx=new Float64Array(nv),vz=new Float64Array(nv);for(var i=0;i<nv;i++){vx[i]=((dv.getInt16(4+4*i,true)-plan[0])/plan[2]+0.5)*S;vz[i]=((dv.getInt16(6+4*i,true)-plan[1])/plan[2]+0.5)*S}
 var tri=[],o=4+nv*4;for(i=0;i<nt;i++,o+=7)tri.push([dv.getUint16(o,true),dv.getUint16(o+2,true),dv.getUint16(o+4,true),mapBytes[o+6]]);
 var walk=tri.filter(function(t){return (t[3]&3)!==2});if(!walk.length)walk=tri;
 /* extra layers count only where their triangles are floor-sized (a long sliver would open a stripe of picture) */
 function lg(t){var b=0;for(var k=0;k<3;k++){var p=t[k],q=t[(k+1)%3];b=Math.max(b,Math.hypot(vx[p]-vx[q],vz[p]-vz[q]))}return b}
 var md={};[1,2,3].forEach(function(l){var a=walk.filter(function(t){return (t[3]>>5&3)===l}).map(lg).sort(function(x,y){return x-y});if(a.length)md[l]=a[a.length>>1]});
 walk=walk.filter(function(t){var l=t[3]>>5&3;return !l||lg(t)<=4*md[l]});
 var core=new Uint8Array(S*S),x0=1e9,x1=-1e9,z0=1e9,z1=-1e9;
 walk.forEach(function(t){var P=[[vx[t[0]],vz[t[0]]],[vx[t[1]],vz[t[1]]],[vx[t[2]],vz[t[2]]]];P.forEach(function(q){x0=Math.min(x0,q[0]);x1=Math.max(x1,q[0]);z0=Math.min(z0,q[1]);z1=Math.max(z1,q[1])});fillTri(core,S,P)});
 var ext=Math.max(x1-x0,z1-z0),mg=Math.floor(Math.max(11,Math.min(67,ext*10/100))),R=ext*14/100;
 if(R>=2){var pad=Math.floor(R)+2,B=S+2*pad,big=new Uint8Array(B*B);for(var y=0;y<S;y++)for(var x=0;x<S;x++)big[(y+pad)*B+x+pad]=core[y*S+x];
  var d1=edt(big,B,B).D,grown=new Uint8Array(B*B),R2=R*R;for(i=0;i<B*B;i++)grown[i]=d1[i]<=R2?1:0;
  var out=new Uint8Array(B*B);for(i=0;i<B*B;i++)out[i]=grown[i]?0:1;var d2=edt(out,B,B).D;
  for(y=0;y<S;y++)for(x=0;x<S;x++)if(d2[(y+pad)*B+x+pad]>R2)core[y*S+x]=1}
 var dist=edt(core,S,S).D,m2=mg*mg,gm=new Float32Array(S*S);for(i=0;i<S*S;i++)gm[i]=dist[i]<=m2?255:0;
 var m=blur(gm,S,S,Math.max(2,mg/4)),A0=0,hit=0;
 for(i=0;i<S*S;i++)if(px[4*i+3]>40){A0++;if(m[i]*1.6>128)hit++}
 if(hit<0.05*Math.max(A0,1))return px;   /* the mask misses the picture: left untrimmed */
 var o2=new Uint8ClampedArray(px);for(i=0;i<S*S;i++){var al=Math.min(px[4*i+3],Math.min(255,m[i]*1.6));o2[4*i+3]=al;if(al<1){o2[4*i]=o2[4*i+1]=o2[4*i+2]=0}}
 return o2};
/* filled triangle with its outline (as PIL's polygon fill + outline) */
function fillTri(M,S,P){var x0=Math.max(0,Math.floor(Math.min(P[0][0],P[1][0],P[2][0]))),x1=Math.min(S-1,Math.ceil(Math.max(P[0][0],P[1][0],P[2][0]))),
 y0=Math.max(0,Math.floor(Math.min(P[0][1],P[1][1],P[2][1]))),y1=Math.min(S-1,Math.ceil(Math.max(P[0][1],P[1][1],P[2][1])));
 var den=(P[1][1]-P[2][1])*(P[0][0]-P[2][0])+(P[2][0]-P[1][0])*(P[0][1]-P[2][1]);
 for(var y=y0;y<=y1;y++)for(var x=x0;x<=x1;x++){var gx=x+0.5,gy=y+0.5,ok;
  if(Math.abs(den)<1e-9)ok=false;else{var a=((P[1][1]-P[2][1])*(gx-P[2][0])+(P[2][0]-P[1][0])*(gy-P[2][1]))/den,b=((P[2][1]-P[0][1])*(gx-P[2][0])+(P[0][0]-P[2][0])*(gy-P[2][1]))/den,c=1-a-b,e=0.7/Math.sqrt(Math.abs(den));ok=a>=-e&&b>=-e&&c>=-e}
  if(ok)M[y*S+x]=1}
 for(var k=0;k<3;k++){var A=P[k],Bq=P[(k+1)%3],n=Math.ceil(Math.max(Math.abs(Bq[0]-A[0]),Math.abs(Bq[1]-A[1])))+1;
  for(var s=0;s<=n;s++){var xx=Math.floor(A[0]+(Bq[0]-A[0])*s/n),yy=Math.floor(A[1]+(Bq[1]-A[1])*s/n);if(xx>=0&&yy>=0&&xx<S&&yy<S)M[yy*S+xx]=1}}}
/* one room, start to finish: 512 x 512 RGBA (or null when the room has no geometry) */
XB.roomPicture=async function(d,f,plan,mapBytes){var h=await d.file(606+2*f),t=await d.file(607+2*f);if(!h)return null;
 var r=XB.renderRoom(h,t,plan,1024);if(!r)return null;return XB.finish(r,1024)};   /* untrimmed from v3: the whole picture is kept */

G.XB=XB;
if(typeof module!=='undefined')module.exports=XB;
})(typeof window!=='undefined'?window:globalThis);
