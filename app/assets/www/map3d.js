/* 3D room view for the MAP tab (the 3D toggle). The room's own models are read from the player's disc when the room is entered
   (disc 1 file 606 + 2 x room and its texture file; the same reader the map builder uses) and drawn with three.js (three.min.js,
   r147, MIT). Nothing from the game ships with the app.
   Space: the game's (x, y down, z) is drawn as (x, -y, -z): flipping y alone would mirror the room, because the PlayStation camera is
   right-handed with y down. The camera starts looking the way the game camera looks (or north with MAP VIEW = NORTH), from above.
   It is a view taken from where the party stands when it is opened (or re-centred with a tap): everything more than CEIL units (about
   Fei's height) above the party's feet is clipped away, so ceilings, upper floors and roofs never hide the floor the party is on; on a
   lower level the floors above disappear on their own. Swipes turn the camera round that spot. Faces are drawn one-sided (the back faces, which are the room's
   inner faces after the axis flip), so walls between the camera and the room drop out like a cutaway.
   The page draws its icons on the 2D map canvas laid over this one, placed with M3.project(). */
(function(G){
'use strict';
var layers=null,fitBox=null;var M3={on:false,room:null,ready:false,err:'',busy:false},T=null,R=null,scene=null,cam=null,roomG=null,lineG=null,clip=null,disc=null,discKey='',cv=null,walk=null,box=null;
/* phones and handhelds (v1.82: the 3D map stopped the Android app answering): no logarithmic depth (it writes depth per pixel, slow on
   phone GPUs), at most MAXW pixels across, a frame at most every MINMS, and the room is put together in small steps that give the
   page time to breathe in between */
var MOBILE=/Android|iPhone|iPad/i.test(navigator.userAgent),MAXW=MOBILE?640:1600,MINMS=MOBILE?120:30;
function breathe(){return new Promise(function(r){setTimeout(r,0)})}
var CEIL=120,COVER2=150;   /* about the height of Fei's sprite: the view shows the room up to there */
function u16(b,p){return b[p]|b[p+1]<<8}function s16(b,p){var v=b[p]|b[p+1]<<8;return v&0x8000?v-65536:v}function u32(b,p){return (b[p]|b[p+1]<<8|b[p+2]<<16|b[p+3]<<24)>>>0}
/* one canvas for the life of the page (the map's HTML is rebuilt often; a WebGL context is not), moved into the map box */
var keep=null;M3.canvas=function(box){if(!keep){keep=document.createElement('canvas');keep.style.cssText='position:absolute;left:0;top:0;width:100%;height:100%;display:block'}if(keep.parentNode!==box)box.appendChild(keep);return keep};
M3.can=function(){return !!(G.THREE&&G.HOST&&HOST.discSize&&+HOST.discSize()>0)};
function init(canvas){if(R&&cv===canvas)return true;T=G.THREE;if(!T)return false;cv=canvas;
 try{R=new T.WebGLRenderer({canvas:canvas,antialias:false,alpha:true,preserveDrawingBuffer:false,logarithmicDepthBuffer:!MOBILE,powerPreference:'low-power'})}catch(e){M3.err='No WebGL here';return false}
 canvas.addEventListener('webglcontextlost',function(e){e.preventDefault();M3.ready=false;M3.err='3D stopped (the graphics chip gave up). Turn 3D off and on.';M3.room=null},false);
 R.localClippingEnabled=true;clip=new T.Plane(new T.Vector3(0,-1,0),1e6);R.clippingPlanes=[clip];
 scene=new T.Scene();cam=new T.PerspectiveCamera(40,1,10,60000);roomG=new T.Group();lineG=new T.Group();scene.add(roomG,lineG);return true}
/* the disc, opened once and kept while it is the same file */
async function openDisc(){var key=String(HOST.discName&&HOST.discName()||'')+'/'+HOST.discSize();if(disc&&discKey===key)return disc;
 var size=+HOST.discSize(),nr=0,reader=async function(o,n){if(++nr%4===0)await breathe();var r=HOST.discRead(o,n);if(typeof r!=='string')return r;if(r.slice(0,4)==='ERR:')throw new Error(r.slice(4));return G.b64u8(r)};
 disc=await XB.open(reader,size);discKey=key;return disc}
/* texture page + palette -> 256 x 256 RGBA (4-bit, 8-bit or 15-bit texels; colour 0 is see-through) */
function pageTex(VR,tp,cl,cache){var key=tp+'_'+cl;if(cache[key])return cache[key];
 var bx=(tp&15)*64,by=((tp>>4)&1)*256,mode=(tp>>7)&3,qx=(cl&0x3F)*16,qy=(cl>>6)&0x1FF,px=new Uint8Array(256*256*4),P32=new Uint32Array(px.buffer);
 function rgba(p16){return p16===0?0:((255<<24)|((((p16>>10)&31)*255/31|0)<<16)|((((p16>>5)&31)*255/31|0)<<8)|((p16&31)*255/31|0))>>>0}
 var pal=null;if(mode<2){var nc=mode===0?16:256;pal=new Uint32Array(nc);for(var c=0;c<nc;c++)pal[c]=rgba(VR[qy*1024+((qx+c)&1023)])}   /* the palette once, not per texel */
 for(var v=0;v<256;v++){var row=((by+v)&511)*1024,o=v*256;
  if(mode===0)for(var u=0;u<256;u++)P32[o+u]=pal[(VR[row+((bx+(u>>2))&1023)]>>((u&3)*4))&15];
  else if(mode===1)for(u=0;u<256;u++)P32[o+u]=pal[(VR[row+((bx+(u>>1))&1023)]>>((u&1)*8))&255];
  else for(u=0;u<256;u++)P32[o+u]=rgba(VR[row+((bx+u)&1023)])}
 var t=new T.DataTexture(px,256,256,T.RGBAFormat);t.magFilter=T.NearestFilter;t.minFilter=T.NearestFilter;t.flipY=false;t.needsUpdate=true;cache[key]=t;return t}
function clear(g){while(g.children.length){var o=g.children[0];g.remove(o);o.traverse(function(q){if(q.geometry)q.geometry.dispose();if(q.material){if(q.material.map)q.material.map.dispose();q.material.dispose()}})}}
/* the room: one group per placed model (header table at 0x190); sky domes and backdrops round the whole room are left out */
var covers=[],coverAt=null;
async function build(h,t){covers=[];coverAt=null;var VR=XB.vram(t),M=XB.models(h),n=u32(h,0x18C)&0xFFFF,texC={},matC={},gain=1;clear(roomG);clear(lineG);
 function mat(kind,tp,cl,semi,abr){var k=kind+tp+'_'+cl+'_'+semi+'_'+abr;if(matC[k])return matC[k];var o={side:T.BackSide,clippingPlanes:[clip]};
  if(kind==='t'){o.map=pageTex(VR,tp,cl,texC);o.alphaTest=0.5}else o.vertexColors=true;
  if(semi){o.transparent=true;o.depthWrite=false;o.blending=abr===1||abr===3?T.AdditiveBlending:abr===2?T.SubtractiveBlending:T.NormalBlending;o.opacity=abr===0?0.5:abr===3?0.3:1;if(o.alphaTest)o.alphaTest=0.01}
  return matC[k]=new T.MeshBasicMaterial(o)}
 var F=XB.walkFloors(h);box=new T.Box3();walk=F;layers=XB.walkLayers(h);fitBox=null;
 /* floor triangles far bigger than the rest are rough bounds sheets (room 288 has one under the hall): no outline, no framing */
 var big=1e9;if(F){var LE=F.T.map(function(t){var b=0;for(var k=0;k<3;k++){var p=t[k],q=t[(k+1)%3];b=Math.max(b,Math.hypot(F.VX[p]-F.VX[q],F.VZ[p]-F.VZ[q]))}return b}),so=LE.slice().sort(function(a,b){return a-b});
  big=Math.max(600,4*(so[Math.floor(so.length*0.9)]||150));F.big=LE.map(function(v){return v>big});
  F.T.forEach(function(t,i){if(F.big[i]||(F.surf[t[3]]||0)&0x800000)return;for(var k=0;k<3;k++){var v=t[k];box.expandByPoint(new T.Vector3(F.VX[v],-F.VY[v],-F.VZ[v]))}})}
 var wh=box.isEmpty()?0:box.max.y-box.min.y;
 /* Roofs and ceilings: a face whose lowest point is more than COVER units above a walkable floor straight under its middle covers
   that floor. Such faces are kept in their own meshes, labelled with the floor they cover, and hidden while the party stands on
   that floor (M3.draw); everything else is always drawn, whatever its height (v1.83: the fixed cut at Fei's height also cut the
   tops off towers and walls beside the party, leaving black holes). Floors are found through a 128-unit grid. */
 var GC=128,grid={};
 if(F)F.T.forEach(function(t,i){var fl=F.surf[t[3]]||0;if(F.big[i]||fl&0x800000||fl&0x80)return;var xs=[F.VX[t[0]],F.VX[t[1]],F.VX[t[2]]],zs=[F.VZ[t[0]],F.VZ[t[1]],F.VZ[t[2]]];
  for(var gx=Math.floor(Math.min.apply(null,xs)/GC);gx<=Math.floor(Math.max.apply(null,xs)/GC);gx++)for(var gz=Math.floor(Math.min.apply(null,zs)/GC);gz<=Math.floor(Math.max.apply(null,zs)/GC);gz++)(grid[gx+','+gz]||(grid[gx+','+gz]=[])).push(i)});
 function floorsAt(x,z){var L=grid[Math.floor(x/GC)+','+Math.floor(z/GC)],out=[];if(!L)return out;
  for(var q=0;q<L.length;q++){var t=F.T[L[q]],ax=F.VX[t[0]],az=F.VZ[t[0]],bx=F.VX[t[1]],bz=F.VZ[t[1]],cx=F.VX[t[2]],cz=F.VZ[t[2]];
   var den=(bz-cz)*(ax-cx)+(cx-bx)*(az-cz);if(!den)continue;var A=((bz-cz)*(x-cx)+(cx-bx)*(z-cz))/den,B=((cz-az)*(x-cx)+(ax-cx)*(z-cz))/den,C=1-A-B;
   if(A>=-0.01&&B>=-0.01&&C>=-0.01)out.push(A*F.VY[t[0]]+B*F.VY[t[1]]+C*F.VY[t[2]])}return out}
 var COVER=160;
 var t0=Date.now();
 for(var i=0;i<Math.min(n,2000);i++){if(Date.now()-t0>30){await breathe();t0=Date.now()}var o=0x190+16*i,fl=u16(h,o),mid=u16(h,o+14);if(fl&0x40||!M[mid])continue;
  var rx=s16(h,o+2),ry=s16(h,o+4),rz=s16(h,o+6),ex=s16(h,o+8),ey=s16(h,o+10),ez=s16(h,o+12),bk={},bb=new T.Box3();
  var a=ry*Math.PI/2048,c=Math.cos(a),s=Math.sin(a),ax=rx*Math.PI/2048,cx=Math.cos(ax),sx=Math.sin(ax),az=rz*Math.PI/2048,cz=Math.cos(az),sz=Math.sin(az);
  M[mid].forEach(function(part){var V=part.V,nv=V.length/3,P=new Float32Array(nv*3);
   for(var j=0;j<nv;j++){var x=V[3*j],y=V[3*j+1],z=V[3*j+2],q;q=y*cx-z*sx;z=y*sx+z*cx;y=q;q=x*c+z*s;z=-x*s+z*c;x=q;q=x*cz-y*sz;y=x*sz+y*cz;x=q;
    P[3*j]=x+ex;P[3*j+1]=-(y+ey);P[3*j+2]=-(z+ez);bb.expandByPoint(new T.Vector3(P[3*j],P[3*j+1],P[3*j+2]))}
   part.polys.forEach(function(pl){var idx=pl[0],kind=pl[1],d=pl[2];for(var k=0;k<idx.length;k++)if(idx[k]>=nv)return;
    var tris=idx.length===4?[[0,1,2],[1,3,2]]:[[0,1,2]],semi,abr,tp=0,cl=0,col=0,uv=null;
    if(kind==='t'){uv=d[0];tp=d[1];cl=d[2];semi=!!(d[3]&2);abr=(tp>>5)&3}
    else{col=d[0];semi=!!(d[2]&2);abr=(d[1]>>5)&3;if(!semi&&(col&255)+((col>>8)&255)+((col>>16)&255)<30)return}   /* black filler planes */
    tris.forEach(function(tr){var cv=null,lo=-1e9,mx=0,mz=0;tr.forEach(function(j){var q=idx[j]*3;lo=Math.max(lo,-P[q+1]);mx+=P[q]/3;mz-=P[q+2]/3});   /* lo: the face's lowest point (game y, down) */
     if(F)floorsAt(mx,mz).forEach(function(fy){if(fy>lo+COVER&&(cv==null||fy<cv))cv=fy});
     var key=kind+'|'+tp+'|'+cl+'|'+(semi?1:0)+'|'+abr+'|'+(cv==null?'-':Math.round(cv/20)),b=bk[key]||(bk[key]={kind:kind,tp:tp,cl:cl,semi:semi,abr:abr,cover:cv==null?null:Math.round(cv/20)*20,pos:[],uv:[],col:[]});
     tr.forEach(function(j){var q=idx[j]*3;b.pos.push(P[q],P[q+1],P[q+2]);
     if(kind==='t')b.uv.push((uv[j][0]+0.5)/256,(uv[j][1]+0.5)/256);else b.col.push((col&255)/255,((col>>8)&255)/255,((col>>16)&255)/255)})})})});
  if(!box.isEmpty()&&!bb.isEmpty()){var encl=bb.min.x<box.min.x-200&&bb.max.x>box.max.x+200&&bb.min.z<box.min.z-200&&bb.max.z>box.max.z+200;
   if(encl&&(((bb.max.y-bb.min.y)>Math.max(2.5*wh,300)&&bb.max.y>box.max.y+200)||bb.max.y<box.min.y-300))continue}
  var g=new T.Group();g.userData.ent=i;
  Object.keys(bk).forEach(function(k){var b=bk[k],geo=new T.BufferGeometry();geo.setAttribute('position',new T.Float32BufferAttribute(b.pos,3));
   if(b.kind==='t')geo.setAttribute('uv',new T.Float32BufferAttribute(b.uv,2));else geo.setAttribute('color',new T.Float32BufferAttribute(b.col,3));
   var me=new T.Mesh(geo,mat(b.kind,b.tp,b.cl,b.semi,b.abr));if(b.semi)me.renderOrder=2;me.userData.cover=b.cover;if(b.cover!=null)covers.push(me);g.add(me)});
  roomG.add(g)}
 /* dark rooms are brightened the way the room pictures are (95th percentile of texel brightness under 100: up to 3x) */
 var L=[];Object.keys(texC).forEach(function(k){var d=texC[k].image.data;for(var q=0;q<d.length;q+=4*97)if(d[q+3])L.push((d[q]+d[q+1]+d[q+2])/3)});
 if(L.length){L.sort(function(x,y){return x-y});var p95=L[Math.floor(L.length*0.95)];if(p95<100)gain=Math.min(3,100/Math.max(p95,1))}
 Object.keys(matC).forEach(function(k){matC[k].color.setScalar(gain)})}
/* load room f in the background; the map draws flat until it is ready */
M3.load=function(f,canvas){if(M3.room===f&&(M3.ready||M3.busy))return;if(!init(canvas))return;M3.room=f;M3.ready=false;M3.busy=true;M3.err='';
 (async function(){try{var d=await openDisc(),h=await d.file(606+2*f),t=await d.file(607+2*f);if(M3.room!==f)return;if(!h)throw new Error('No room data');await build(h,t);if(M3.room!==f)return;M3.ready=true}
  catch(e){M3.err=String(e&&e.message||e)}M3.busy=false;if(G.last)G.last={};if(G.drawMap)G.drawMap()})()};
/* floor heights under (x, z), lowest y first (y down: the highest floor first) */
M3.floors=function(x,z){var F=walk,out=[];if(!F)return out;
 for(var i=0;i<F.T.length;i++){var t=F.T[i],ax=F.VX[t[0]],az=F.VZ[t[0]],bx=F.VX[t[1]],bz=F.VZ[t[1]],cx=F.VX[t[2]],cz=F.VZ[t[2]];
  if(x<Math.min(ax,bx,cx)||x>Math.max(ax,bx,cx)||z<Math.min(az,bz,cz)||z>Math.max(az,bz,cz))continue;
  var den=(bz-cz)*(ax-cx)+(cx-bx)*(az-cz);if(!den)continue;var A=((bz-cz)*(x-cx)+(cx-bx)*(z-cz))/den,B=((cz-az)*(x-cx)+(ax-cx)*(z-cz))/den,C=1-A-B;
  if(A>=-0.02&&B>=-0.02&&C>=-0.02&&!(F.big&&F.big[i]))out.push(A*F.VY[t[0]]+B*F.VY[t[1]]+C*F.VY[t[2]])}
 return out.sort(function(a,b){return a-b})};
/* the floor under (x, z) nearest to height ref (game y), or ref when there is none */
M3.yAt=function(x,z,ref){var fl=M3.floors(x,z);if(!fl.length)return ref;var best=fl[0];fl.forEach(function(y){if(Math.abs(y-ref)<Math.abs(best-ref))best=y});return best};
/* The camera follows the party (v1.80, as in v1.78): it looks the way the game camera looks, from behind and above; swipes turn and
   tilt it (an offset kept until a tap or a new room), pinch or the wheel move it in and out. Everything more than CEIL units
   above the party's feet is cut away.
   First-person (EYE): the camera stands at Fei's eye height on the party and looks the way the game camera looks (turning as it
   turns), nothing is cut and both sides of every face are drawn, so walls and roofs show; swipes look around. */
var V={room:null,yawOff:0,pitch:0.95,dist:900,max:6000,look:-0.12},FP=false,EYE=95;
M3.follow=function(f){if(V.room===f)return;var c=box&&!box.isEmpty()?box.getSize(new T.Vector3()):null;
 V={room:f,yawOff:0,pitch:0.95,look:-0.12,dist:c?Math.max(700,Math.min(2500,0.9*Math.max(c.x,c.z))):900,max:c?Math.max(1500,2.2*Math.max(c.x,c.z)):6000};M3.key=Math.random()};
M3.recentre=function(){V.yawOff=0;V.pitch=0.95;V.look=-0.12;M3.key=Math.random()};
M3.orbit=function(dx,dy){V.yawOff-=dx*0.008;if(FP)V.look=Math.max(-1.3,Math.min(1.0,V.look-dy*0.006));else V.pitch=Math.max(0.12,Math.min(1.53,V.pitch+dy*0.006));M3.key=Math.random()};
M3.zoom=function(k){V.dist=Math.max(150,Math.min(V.max,V.dist*k));M3.key=Math.random()};
M3.firstPerson=function(on){on=!!on;if(on===FP)return;FP=on;roomG.traverse(function(o){if(o.material){o.material.side=FP?T.DoubleSide:T.BackSide;o.material.needsUpdate=true}});lineG.visible=!FP;M3.key=Math.random()};
M3.isFP=function(){return FP};
/* draw: W x H device pixels; at = the party {x, y, z} (game units); fw = [fx, fz] the game camera's way (game x, z) */
/* EYE draws at half the map's size in each direction (a quarter of the pixels) and the picture is stretched back up blocky, which
   suits the game's own look; the view from above keeps full size. (v1.81: EYE was slow on the handheld.) */
var EYE_RES=0.5;
var lastDraw=0,pend=null,curW=0,curH=0;
M3.draw=function(W,H,at,fw){if(!M3.ready||!R||!at)return false;
 var now=Date.now();if(now-lastDraw<MINMS){if(!pend)pend=setTimeout(function(){pend=null;lastDraw=0;if(G.drawMap){var c=document.getElementById('mapcv');if(c)c._sig=null;G.drawMap()}},MINMS-(now-lastDraw));return true}
 lastDraw=now;
 var k=Math.min(1,MAXW/Math.max(W,1))*(FP?EYE_RES:1),w=Math.max(1,Math.round(W*k)),hh=Math.max(1,Math.round(H*k));
 if(w!==curW||hh!==curH){R.setPixelRatio(1);R.setSize(w,hh,false);curW=w;curH=hh}   /* setting the same size again would clear and reallocate the canvas */
 cam.aspect=W/Math.max(H,1);
 if(keep){var ir=FP?'pixelated':'auto';if(keep.style.imageRendering!==ir)keep.style.imageRendering=ir}
 var yaw=Math.atan2(-fw[1],fw[0])+V.yawOff,fx=Math.cos(yaw),fz=Math.sin(yaw);
 if(FP){cam.fov=70;cam.position.set(at.x,-at.y+EYE,-at.z);var cl=Math.cos(V.look);cam.up.set(0,1,0);cam.lookAt(at.x+fx*cl*100,-at.y+EYE+Math.sin(V.look)*100,-at.z+fz*cl*100);cam.near=5;cam.far=V.max*2+6000;clip.constant=1e6}
 else{cam.fov=40;var tgt=new T.Vector3(at.x,-at.y+40,-at.z),hz=Math.cos(V.pitch)*V.dist;
  cam.position.set(tgt.x-fx*hz,tgt.y+Math.sin(V.pitch)*V.dist,tgt.z-fz*hz);cam.up.set(0,1,0);cam.lookAt(tgt);
  cam.near=Math.max(5,V.dist*0.03);cam.far=V.dist+V.max*2+4000;clip.constant=1e6}
 var ck=FP?'fp':Math.round(at.y/10);if(ck!==coverAt){coverAt=ck;for(var ci=0;ci<covers.length;ci++)covers[ci].visible=FP||Math.abs(covers[ci].userData.cover-at.y)>COVER2}   /* roofs over the floor the party is on are hidden */
 cam.updateProjectionMatrix();cam.updateMatrixWorld();R.render(scene,cam);return true};
/* game (x, y, z) -> device pixels on the canvas last drawn */
var pv=null,pc=null;M3.project=function(x,y,z,W,H){if(!pv){pv=new T.Vector3();pc=new T.Vector3()}pv.set(x,-y,-z);pc.copy(pv).applyMatrix4(cam.matrixWorldInverse);pv.project(cam);return [(pv.x+1)/2*W,(1-pv.y)/2*H,pc.z<0]};   /* third: in front of the camera */
/* a spot whose floor is in the clipped-away part above the party (an upper level seen from below) */
M3.above=function(y,ref){return y<ref-CEIL};
/* the floor of walk layer l under (x, z) nearest to ref (for the map's own outline, which keeps each triangle's layer) */
M3.yLayer=function(x,z,l,ref){var W=layers&&layers.L[l];if(!W)return M3.yAt(x,z,ref);var best=null;
 for(var i=0;i<W.T.length;i++){var t=W.T[i],ax=W.VX[t[0]],az=W.VZ[t[0]],bx=W.VX[t[1]],bz=W.VZ[t[1]],cx=W.VX[t[2]],cz=W.VZ[t[2]];
  if(x<Math.min(ax,bx,cx)-1||x>Math.max(ax,bx,cx)+1||z<Math.min(az,bz,cz)-1||z>Math.max(az,bz,cz)+1)continue;
  var den=(bz-cz)*(ax-cx)+(cx-bx)*(az-cz);if(!den)continue;var A=((bz-cz)*(x-cx)+(cx-bx)*(z-cz))/den,B=((cz-az)*(x-cx)+(ax-cx)*(z-cz))/den,C=1-A-B;
  if(A>=-0.05&&B>=-0.05&&C>=-0.05){var y=A*W.VY[t[0]]+B*W.VY[t[1]]+C*W.VY[t[2]];if(best==null||Math.abs(y-ref)<Math.abs(best-ref))best=y}}
 return best==null?M3.yAt(x,z,ref):best};
/* frame the whole-room view on these (x, z) points (the map's walkable vertices) */
M3.fit=function(xs,zs){fitBox=new T.Box3();for(var i=0;i<xs.length;i++){var fl=M3.floors(xs[i],zs[i]),y=fl.length?fl[fl.length-1]:0;fitBox.expandByPoint(new T.Vector3(xs[i],-y,-zs[i]))}};
M3.reset=function(){M3.room=null;M3.ready=false};
G.M3=M3;
})(window);
