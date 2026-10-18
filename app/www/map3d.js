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
var layers=null,fitBox=null;var M3={on:false,room:null,ready:false,err:'',busy:false},T=null,R=null,scene=null,cam=null,roomG=null,lineG=null,skyG=null,routeG=null,clip=null,disc=null,discKey='',cv=null,walk=null,box=null;
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
 scene=new T.Scene();cam=new T.PerspectiveCamera(40,1,10,60000);roomG=new T.Group();lineG=new T.Group();skyG=new T.Group();routeG=new T.Group();scene.add(roomG,lineG,skyG,routeG);return true}
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
/* the room: one group per placed model (header table at 0x190); sky domes and backdrops round the whole room go in skyG, drawn
   only in EYE when SETTINGS > EXPERIMENTAL > SKY is on (from above, a dome would hide the room) */
var covers=[],coverAt=null;
async function build(h,t){covers=[];coverAt=null;var VR=XB.vram(t),M=XB.models(h),n=u32(h,0x18C)&0xFFFF,texC={},matC={},gain=1;clear(roomG);clear(lineG);clear(skyG);clear(routeG);RM=null;RMP=null;RT.key='';RT.corr=null;RT.mesh=null;SM3=null;
 peopleRoom(h,VR);
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
  var isSky=false;if(!box.isEmpty()&&!bb.isEmpty()){var encl=bb.min.x<box.min.x-200&&bb.max.x>box.max.x+200&&bb.min.z<box.min.z-200&&bb.max.z>box.max.z+200;
   if(encl&&(((bb.max.y-bb.min.y)>Math.max(2.5*wh,300)&&bb.max.y>box.max.y+200)||bb.max.y<box.min.y-300))isSky=true}
  var g=new T.Group();g.userData.ent=i;
  Object.keys(bk).forEach(function(k){var b=bk[k],geo=new T.BufferGeometry();geo.setAttribute('position',new T.Float32BufferAttribute(b.pos,3));
   if(b.kind==='t')geo.setAttribute('uv',new T.Float32BufferAttribute(b.uv,2));else geo.setAttribute('color',new T.Float32BufferAttribute(b.col,3));
   var me=new T.Mesh(geo,mat(b.kind,b.tp,b.cl,b.semi,b.abr));if(b.semi)me.renderOrder=2;me.userData.cover=isSky?null:b.cover;if(b.cover!=null&&!isSky)covers.push(me);g.add(me)});
  (isSky?skyG:roomG).add(g)}
 /* dark rooms are brightened the way the room pictures are (95th percentile of texel brightness under 100: up to 3x) */
 var L=[];Object.keys(texC).forEach(function(k){var d=texC[k].image.data;for(var q=0;q<d.length;q+=4*97)if(d[q+3])L.push((d[q]+d[q+1]+d[q+2])/3)});
 if(L.length){L.sort(function(x,y){return x-y});var p95=L[Math.floor(L.length*0.95)];if(p95<100)gain=Math.min(3,100/Math.max(p95,1))}
 Object.keys(matC).forEach(function(k){matC[k].color.setScalar(gain)});P.gain=gain}
/* ---------- people in EYE (v1.94) ----------
   The room's NPCs as flat sprites standing in the room, always facing the camera, showing the frame the game would show from where
   the camera looks (npc.js XN.dirFrame: front, side, back, mirrored). Where they stand, which way they face and whether they are
   shown comes live from the game's actor list (the page passes it in, M3.people); which sprite each actor wears comes from running
   the room's set-up scripts at the current story step with the live script variables (XN.run, as the room viewer does). The
   sprites are read from the room file and drawn with the room's VRAM plus the room's own sprite sheets, from the player's disc. */
var P={spr:[],sc:null,head:null,VR:null,run:null,runKey:'',tex:{},objs:{},gain:1};
var K=2;   /* world units per sprite pixel (Fei is about 48 pixels and 95 units tall) */
function peopleRoom(h,VR){clearPeople();P.run=null;P.runKey='';P.spr=[];P.sc=null;P.head=null;P.VR=null;if(!G.XN)return;
 try{P.VR=VR.slice();XN.uploadSheets(h,P.VR,XB);P.spr=XN.sprites(h,XB);P.sc=XN.script(h,XB);P.head=XN.head(h)}catch(e){P.spr=[];P.sc=null}}
function clearPeople(){Object.keys(P.objs).forEach(function(k){var o=P.objs[k];if(o.parent)o.parent.remove(o);o.material.dispose()});P.objs={};
 Object.keys(P.tex).forEach(function(k){if(P.tex[k])P.tex[k].tex.dispose()});P.tex={};if(peopleG)clear(peopleG)}
var peopleG=null;
function frameTex(si,variant,fi){var k=si+'_'+variant+'_'+fi;if(P.tex[k]!==undefined)return P.tex[k];
 var fr=null;try{fr=XN.frame(P.spr[si],P.VR,fi,variant)}catch(e){}if(!fr){P.tex[k]=null;return null}
 var px=new Uint8Array(fr.w*fr.h*4);for(var y=0;y<fr.h;y++)px.set(fr.rgba.subarray(y*fr.w*4,(y+1)*fr.w*4),(fr.h-1-y)*fr.w*4);   /* bottom row first, as WebGL wants */
 var t=new T.DataTexture(px,fr.w,fr.h,T.RGBAFormat);t.magFilter=T.NearestFilter;t.minFilter=T.NearestFilter;t.flipY=false;t.needsUpdate=true;
 return P.tex[k]={tex:t,fr:fr}}
/* which sprite each actor wears: the set-up scripts run again when the story step or the script variables they read change */
M3.peopleSetup=function(step,vars){if(!P.sc)return;var key=step+'/'+(P.run?Object.keys(P.run.reads).map(function(v){return v+'='+(vars&&vars[v]|0)}).join(','):'-');if(P.run&&key===P.runKey)return;
 try{P.run=XN.run(P.sc,{step:step|0,vars:vars||{},head:P.head,entry:vars&&vars[2]|0,party:[0]})}catch(e){P.run=null}
 P.runKey=step+'/'+(P.run?Object.keys(P.run.reads).map(function(v){return v+'='+(vars&&vars[v]|0)}).join(','):'-')};
/* the actors the page read: [{i, x, y, z, rot, show}], i = actor (script entity) number; the player's own actor is left out by the page */
var live=[];M3.people=function(list){live=list||[]};
/* the actors worth reading positions for (those that wear a sprite), or null before the scripts have run (read them all) */
M3.peopleWanted=function(){if(!P.run)return null;var w={};P.run.E.forEach(function(e){if(e.kind==='npc'&&P.spr[e.sprite])w[e.i]=1});return w};
M3.peopleCount=function(){var n=0;Object.keys(P.objs).forEach(function(k){if(P.objs[k].visible)n++});return n};
function placePeople(camA){if(!peopleG){peopleG=new T.Group();scene.add(peopleG)}var seen={};
 peopleG.visible=FP;if(!FP||!P.run)return;
 live.forEach(function(a){var e=P.run.E[a.i];if(!e||e.kind!=='npc'||!P.spr[e.sprite]||!a.show)return;
  var o=P.objs[a.i];if(!o){o=new T.Sprite(new T.SpriteMaterial({transparent:true,alphaTest:0.5,depthWrite:true}));o.userData.last='';P.objs[a.i]=o;peopleG.add(o)}
  var df=XN.dirFrame(P.spr[e.sprite],((a.rot|0)-camA+0xC00)&0xFFF),key=e.sprite+'_'+(e.variant|0)+'_'+df[0]+(df[1]?'m':'');
  if(key!==o.userData.last){var ft=frameTex(e.sprite,e.variant|0,df[0]);if(!ft)return;o.material.map=ft.tex;o.material.color.setScalar(P.gain||1);o.material.needsUpdate=true;
   var fr=ft.fr,w=fr.w*K,hh=fr.h*K;o.scale.set(df[1]?-w:w,hh,1);o.center.set(df[1]?1+fr.x0/fr.w:-fr.x0/fr.w,1+fr.y0/fr.h);o.userData.last=key}
  o.position.set(a.x,-a.y,-a.z);o.visible=true;seen[a.i]=1});
 Object.keys(P.objs).forEach(function(k){if(!seen[k])P.objs[k].visible=false})}
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
M3.firstPerson=function(on){on=!!on;if(on===FP)return;FP=on;[roomG,skyG].forEach(function(G2){G2.traverse(function(o){if(o.material){o.material.side=FP?T.DoubleSide:T.BackSide;o.material.needsUpdate=true}})});lineG.visible=!FP;M3.key=Math.random()};
M3.isFP=function(){return FP};
/* draw: W x H device pixels; at = the party {x, y, z} (game units); fw = [fx, fz] the game camera's way (game x, z) */
/* EYE draws at half the map's size in each direction (a quarter of the pixels) and the picture is stretched back up blocky, which
   suits the game's own look; the view from above keeps full size. (v1.81: EYE was slow on the handheld.) */
var EYE_RES=0.5;
var lastDraw=0,pend=null,curW=0,curH=0;
/* SMOOTH 3D (SETTINGS > EXPERIMENTAL): the camera eases towards the party's live place, height and the camera's turn each frame
   (about 110 ms to close most of a gap) instead of jumping once a read, and frames come up to every SMMS while it is still moving.
   A jump of 500 units or a new room snaps. */
var SM3=null,smRaf=false,SMMS=MOBILE?40:16;M3.smooth=false;M3.sky=false;
function redrawSoon(){if(smRaf)return;smRaf=true;requestAnimationFrame(function(){smRaf=false;if(G.drawMap){var c=document.getElementById('mapcv');if(c)c._sig=null;G.drawMap()}})}
M3.draw=function(W,H,at,fw){if(!M3.ready||!R||!at)return false;
 var now=Date.now(),gap=M3.smooth?SMMS:MINMS;if(now-lastDraw<gap){if(!pend)pend=setTimeout(function(){pend=null;lastDraw=0;if(G.drawMap){var c=document.getElementById('mapcv');if(c)c._sig=null;G.drawMap()}},gap-(now-lastDraw));return true}
 lastDraw=now;
 var tYaw=Math.atan2(-fw[1],fw[0]);
 if(M3.smooth&&SM3&&SM3.room===M3.room&&Math.hypot(at.x-SM3.x,at.z-SM3.z)<500){var dt=Math.min(250,now-SM3.t),kk=1-Math.exp(-dt/110),dyw=Math.atan2(Math.sin(tYaw-SM3.yaw),Math.cos(tYaw-SM3.yaw));
  SM3.x+=(at.x-SM3.x)*kk;SM3.y+=(at.y-SM3.y)*kk;SM3.z+=(at.z-SM3.z)*kk;SM3.yaw+=dyw*kk;SM3.t=now}
 else SM3={room:M3.room,x:at.x,y:at.y,z:at.z,yaw:tYaw,t:now};
 if(M3.smooth){var left=Math.abs(at.x-SM3.x)+Math.abs(at.z-SM3.z)+Math.abs(at.y-SM3.y),lyaw=Math.abs(Math.atan2(Math.sin(tYaw-SM3.yaw),Math.cos(tYaw-SM3.yaw)));
  at={x:SM3.x,y:SM3.y,z:SM3.z};fw=[Math.cos(SM3.yaw),-Math.sin(SM3.yaw)];if(left>1.5||lyaw>0.003)redrawSoon()}
 skyG.visible=FP&&M3.sky;
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
 cam.updateProjectionMatrix();cam.updateMatrixWorld();
 /* the camera's way as a game angle (4096 a turn), the same reckoning as the room viewer: picks each sprite's front, side or back */
 placePeople(Math.round(-Math.atan2(-fz,fx)*2048/Math.PI));
 R.render(scene,cam);return true};
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
/* ---------- the way to go (SETTINGS > EXPERIMENTAL > ROUTE, v1.99.0.5; made light for the handheld in v1.99.0.6) ----------
   A green line on the floor from the party to a target the page gives (the next hint's spot in this room, or the door towards the
   hint's room, or a door the player tapped). The way is found with A* over the walkable triangles of the walk mesh (blocked
   0x800000, party-blocking 0x80 and the huge bounds sheets left out) and pulled straight through the shared edges with the funnel
   method, then laid on the floor every RSTEP units.
   - The floor graph is built a few milliseconds at a time after the room appears (prepRoute), so entering a room never stalls.
     Triangles join where they share an edge (same corners by x, y and z: the merged floor list repeats corners per layer), and an
     edge with no neighbour is probed 3 units outside its middle for a floor within 24 units of height (walk layers meet at stairs
     without shared corners).
   - While the party stays on the found corridor of triangles only the straightening is redone, from the triangle it is on; A* runs
     again only for a new target or once the party leaves the corridor.
   - The line's buffers are kept and refilled; the beam on the target is moved, not rebuilt. */
var RM=null,RMP=null,RT={key:'',t:0,fx:0,fz:0,corr:null,idx:null,portal:null,to:null,mesh:null,beam:null};
var RSTEP=MOBILE?40:24,RMAX=700;
function prepRoute(){if(RM||RMP||!walk)return;var F=walk,gen=F,nT=F.T.length,nV=F.VX.length,GC=128;RMP=gen;
 var ok=new Uint8Array(nT),cx=new Float32Array(nT),cy=new Float32Array(nT),cz=new Float32Array(nT),grid={},vid=new Int32Array(nV),vm={},nid=0,edges=new Map(),adj=[],ph=0,i=0;
 var M={F:F,ok:ok,cx:cx,cy:cy,cz:cz,grid:grid,GC:GC,adj:adj,n:nT};
 function hasE(i,a,b){var A=adj[i];for(var q=0;q<A.length;q+=3)if(A[q+1]===a&&A[q+2]===b||A[q+1]===b&&A[q+2]===a)return true;return false}
 function hasN(i,j){var A=adj[i];for(var q=0;q<A.length;q+=3)if(A[q]===j)return true;return false}
 function work(){var t=F.T[i];
  if(ph===0){var k=F.VX[i]+','+F.VY[i]+','+F.VZ[i],v=vm[k];if(v==null)v=vm[k]=nid++;vid[i]=v;if(++i>=nV){ph=1;i=0}return}
  if(ph===1){var fl=F.surf[t[3]]||0;adj[i]=[];ok[i]=!(F.big&&F.big[i])&&!(fl&0x800000)&&!(fl&0x80)?1:0;
   if(ok[i]){cx[i]=(F.VX[t[0]]+F.VX[t[1]]+F.VX[t[2]])/3;cy[i]=(F.VY[t[0]]+F.VY[t[1]]+F.VY[t[2]])/3;cz[i]=(F.VZ[t[0]]+F.VZ[t[1]]+F.VZ[t[2]])/3;
    var x0=Math.min(F.VX[t[0]],F.VX[t[1]],F.VX[t[2]]),x1=Math.max(F.VX[t[0]],F.VX[t[1]],F.VX[t[2]]),z0=Math.min(F.VZ[t[0]],F.VZ[t[1]],F.VZ[t[2]]),z1=Math.max(F.VZ[t[0]],F.VZ[t[1]],F.VZ[t[2]]);
    for(var gx=Math.floor(x0/GC);gx<=Math.floor(x1/GC);gx++)for(var gz=Math.floor(z0/GC);gz<=Math.floor(z1/GC);gz++)(grid[gx+','+gz]||(grid[gx+','+gz]=[])).push(i);
    for(var k2=0;k2<3;k2++){var a=t[k2],b=t[(k2+1)%3],va=vid[a],vb=vid[b],key=va<vb?va*1048576+vb:vb*1048576+va,o=edges.get(key);
     if(o==null)edges.set(key,[i,a,b]);else for(var q=0;q<o.length;q+=3){var j=o[q];adj[i].push(j,a,b);adj[j].push(i,a,b)}if(o!=null)o.push(i,a,b)}}
   if(++i>=nT){ph=2;i=0}return}
  if(ph===2){if(ok[i])for(var k3=0;k3<3;k3++){var a2=t[k3],b2=t[(k3+1)%3],c2=t[(k3+2)%3];if(hasE(i,a2,b2))continue;
    var mx=(F.VX[a2]+F.VX[b2])/2,mz=(F.VZ[a2]+F.VZ[b2])/2,my=(F.VY[a2]+F.VY[b2])/2,ex=F.VX[b2]-F.VX[a2],ez=F.VZ[b2]-F.VZ[a2],l=Math.sqrt(ex*ex+ez*ez)||1,nx=-ez/l,nz=ex/l;
    if(nx*(F.VX[c2]-mx)+nz*(F.VZ[c2]-mz)>0){nx=-nx;nz=-nz}
    var hit=triAt(M,mx+nx*3,mz+nz*3);for(var h=0;h<hit.length;h+=2){var j2=hit[h];if(j2===i||!ok[j2]||Math.abs(hit[h+1]-my)>24||hasN(i,j2))continue;adj[i].push(j2,a2,b2);adj[j2].push(i,a2,b2)}}
   if(++i>=nT){ph=3}return}}
 (function run(){if(walk!==gen){RMP=null;return}var t0=performance.now(),n=0;
  while(ph<3){work();if((++n&63)===0&&performance.now()-t0>(MOBILE?5:10))break}
  if(ph<3){setTimeout(run,0);return}
  RM=M;RMP=null;M.g=new Float32Array(nT);M.came=new Int32Array(nT);M.ca=new Int32Array(nT);M.cb=new Int32Array(nT);M.st=new Uint32Array(nT);M.gen=0;RT.key='';redrawSoon()})()}
/* triangles under (x, z): flat list of [triangle, floor height] pairs */
function triAt(M,x,z){var L=M.grid[Math.floor(x/M.GC)+','+Math.floor(z/M.GC)],out=[],F=M.F;if(!L)return out;
 for(var q=0;q<L.length;q++){var i=L[q],t=F.T[i],ax=F.VX[t[0]],az=F.VZ[t[0]],bx=F.VX[t[1]],bz=F.VZ[t[1]],cx=F.VX[t[2]],cz=F.VZ[t[2]];
  var den=(bz-cz)*(ax-cx)+(cx-bx)*(az-cz);if(!den)continue;var A=((bz-cz)*(x-cx)+(cx-bx)*(z-cz))/den,B=((cz-az)*(x-cx)+(ax-cx)*(z-cz))/den,C=1-A-B;
  if(A>=-0.02&&B>=-0.02&&C>=-0.02)out.push(i,A*F.VY[t[0]]+B*F.VY[t[1]]+C*F.VY[t[2]])}return out}
function pickTri(M,x,z,y){var L=triAt(M,x,z),bi=-1,by=0;for(var q=0;q<L.length;q+=2){if(!M.ok[L[q]])continue;if(bi<0||y!=null&&Math.abs(L[q+1]-y)<Math.abs(by-y)){bi=L[q];by=L[q+1]}}if(bi>=0)return bi;
 var bd=400;for(var i=0;i<M.n;i++){if(!M.ok[i])continue;var dx=M.cx[i]-x,dz=M.cz[i]-z;if(dx>bd||dx<-bd||dz>bd||dz<-bd)continue;var d=Math.sqrt(dx*dx+dz*dz)+(y!=null?Math.abs(M.cy[i]-y)*0.5:0);if(d<bd){bd=d;bi=i}}return bi<0?null:bi}
function floorNear(M,x,z,y){var L=triAt(M,x,z),b=null;for(var q=0;q<L.length;q+=2)if(b==null||Math.abs(L[q+1]-y)<Math.abs(b-y))b=L[q+1];return b!=null&&Math.abs(b-y)<40?b:null}
/* A* from triangle s to g: the corridor of triangles and the shared edge (two corners) crossed after each, or null */
function aStar(M,s,g){var gen=++M.gen,G=M.g,st=M.st,cx=M.cx,cy=M.cy,cz=M.cz,hk=[],hv=[],n=0;
 function push(k,v){hk.push(k);hv.push(v);var i=hk.length-1;while(i>0){var p=(i-1)>>1;if(hk[p]<=hk[i])break;var t=hk[p];hk[p]=hk[i];hk[i]=t;t=hv[p];hv[p]=hv[i];hv[i]=t;i=p}}
 function pop(){var v=hv[0],lk=hk.pop(),lv=hv.pop();if(hk.length){hk[0]=lk;hv[0]=lv;var i=0,N=hk.length;for(;;){var l=2*i+1,r=l+1,m=i;if(l<N&&hk[l]<hk[m])m=l;if(r<N&&hk[r]<hk[m])m=r;if(m===i)break;var t=hk[m];hk[m]=hk[i];hk[i]=t;t=hv[m];hv[m]=hv[i];hv[i]=t;i=m}}return v}
 st[s]=gen;G[s]=0;M.came[s]=-1;push(0,s);var gx=cx[g],gy=cy[g],gz=cz[g];
 while(hk.length&&n++<30000){var c=pop();if(c===g)break;var A=M.adj[c];
  for(var q=0;q<A.length;q+=3){var nb=A[q],dx=cx[nb]-cx[c],dy=cy[nb]-cy[c],dz=cz[nb]-cz[c],ng=G[c]+Math.sqrt(dx*dx+dy*dy+dz*dz);if(st[nb]===gen&&G[nb]<=ng)continue;
   st[nb]=gen;G[nb]=ng;M.came[nb]=c;M.ca[nb]=A[q+1];M.cb[nb]=A[q+2];var hx=gx-cx[nb],hy=gy-cy[nb],hz=gz-cz[nb];push(ng+Math.sqrt(hx*hx+hy*hy+hz*hz),nb)}}
 if(st[g]!==gen)return null;var corr=[g],por=[],cur=g;while(cur!==s){por.push([M.ca[cur],M.cb[cur]]);cur=M.came[cur];corr.push(cur)}corr.reverse();por.reverse();return {corr:corr,por:por}}
/* the funnel: the shortest line from p through the portals from corridor index k on to q, as [x, y, z] corners */
function funnel(M,R,k,p,q){var F=M.F,P=[[p.x,p.y,p.z],[p.x,p.y,p.z]];
 for(var i=k;i<R.por.length;i++){var a=R.por[i][0],b=R.por[i][1],t=R.corr[i],dx=M.cx[R.corr[i+1]]-M.cx[t],dz=M.cz[R.corr[i+1]]-M.cz[t],
   A=[F.VX[a],F.VY[a],F.VZ[a]],B=[F.VX[b],F.VY[b],F.VZ[b]],sa=dx*(A[2]-M.cz[t])-dz*(A[0]-M.cx[t]);P.push(sa>0?A:B,sa>0?B:A)}
 P.push([q.x,q.y,q.z],[q.x,q.y,q.z]);
 function ar(a,b,c){return (c[0]-a[0])*(b[2]-a[2])-(b[0]-a[0])*(c[2]-a[2])}
 function eq(a,b){return Math.abs(a[0]-b[0])<0.01&&Math.abs(a[2]-b[2])<0.01}
 var out=[P[0]],apex=P[0],left=P[0],right=P[1],ai=0,li=0,ri=0,n=P.length/2;
 for(var i2=1;i2<n;i2++){var l=P[2*i2],r=P[2*i2+1];
  if(ar(apex,right,r)<=0){if(eq(apex,right)||ar(apex,left,r)>0){right=r;ri=i2}else{out.push(left);apex=left;ai=li;left=right=apex;li=ri=ai;i2=ai;continue}}
  if(ar(apex,left,l)>=0){if(eq(apex,left)||ar(apex,right,l)<0){left=l;li=i2}else{out.push(right);apex=right;ai=ri;left=right=apex;li=ri=ai;i2=ai;continue}}}
 out.push(P[P.length-1]);return out}
/* the point of triangle i nearest to (x, z), on its floor: [x, y, z] (v1.99.0.14: the line's end. It used the triangle's middle height,
   which for a spot off the walkable floor, or a long sloped triangle, left the end hanging in the air: 219 units up in room 337) */
function onTri(M,i,x,z){var F=M.F,t=F.T[i],P=[0,1,2].map(function(k){return [F.VX[t[k]],F.VY[t[k]],F.VZ[t[k]]]});
 function bary(x,z){var a=P[0],b=P[1],c=P[2],den=(b[2]-c[2])*(a[0]-c[0])+(c[0]-b[0])*(a[2]-c[2]);if(!den)return null;
  var A=((b[2]-c[2])*(x-c[0])+(c[0]-b[0])*(z-c[2]))/den,B=((c[2]-a[2])*(x-c[0])+(a[0]-c[0])*(z-c[2]))/den;return [A,B,1-A-B]}
 var w=bary(x,z);if(w&&w[0]>=-0.001&&w[1]>=-0.001&&w[2]>=-0.001)return [x,w[0]*P[0][1]+w[1]*P[1][1]+w[2]*P[2][1],z];
 var best=null,bd=1e18;for(var e=0;e<3;e++){var a=P[e],b=P[(e+1)%3],ex=b[0]-a[0],ez=b[2]-a[2],l2=ex*ex+ez*ez,u=l2?((x-a[0])*ex+(z-a[2])*ez)/l2:0;u=Math.max(0,Math.min(1,u));
  var px=a[0]+ex*u,pz=a[2]+ez*u,d=(px-x)*(px-x)+(pz-z)*(pz-z);if(d<bd){bd=d;best=[px,a[1]+(b[1]-a[1])*u,pz]}}return best}
/* corners laid on the floor every RSTEP units (any floor within 40 of the line's height) */
function layRoute(M,out){var lay=[];for(var q=0;q<out.length-1;q++){var a=out[q],b=out[q+1],dx=b[0]-a[0],dz=b[2]-a[2],n=Math.max(1,Math.ceil(Math.sqrt(dx*dx+dz*dz)/RSTEP));
  for(var k=0;k<n;k++){var t=k/n,x=a[0]+dx*t,z=a[2]+dz*t,y=a[1]+(b[1]-a[1])*t,fy=null;
   fy=floorNear(M,x,z,y);lay.push([x,fy!=null?fy:y,z]);if(lay.length>=RMAX-1)break}}
 lay.push(out[out.length-1]);return lay}
M3.route=function(from,to){var M=RM;if(!M)return null;var s=pickTri(M,from.x,from.z,from.y),g=pickTri(M,to.x,to.z,to.y!=null?to.y:from.y);if(s==null||g==null)return null;
 var R=aStar(M,s,g);if(!R)return null;var e=onTri(M,g,to.x,to.z),q={x:e[0],y:e[1],z:e[2]};return layRoute(M,funnel(M,R,0,from,q))};
M3.routeReady=function(){return !!RM};
function routeHide(){if(routeG)routeG.visible=false}
/* the line and the beam share one material and are made with the room (drawing nothing), so their shader is compiled while the room
   loads rather than in the middle of a walk (a 200 ms stall at the first line on a slow CPU) */
function routeObjs(){if(RT.mesh&&RT.mesh.parent===routeG)return;var geo=new T.BufferGeometry(),pa=new T.BufferAttribute(new Float32Array(RMAX*6),3),ix2=[];pa.setUsage(T.DynamicDrawUsage);geo.setAttribute('position',pa);
 for(var i=0;i<RMAX-1;i++){var o=2*i;ix2.push(o,o+1,o+2,o+1,o+3,o+2)}geo.setIndex(ix2);geo.setDrawRange(0,0);
 var mt=new T.MeshBasicMaterial({color:0x55ff66,transparent:true,opacity:0.6,depthWrite:false,side:T.DoubleSide,polygonOffset:true,polygonOffsetFactor:-4,clippingPlanes:[clip]});
 RT.mesh=new T.Mesh(geo,mt);RT.mesh.renderOrder=1;RT.mesh.frustumCulled=false;routeG.add(RT.mesh);
 RT.beam=new T.Mesh(new T.CylinderGeometry(6,6,80,8,1,true),mt);RT.beam.renderOrder=5;RT.beam.visible=false;routeG.add(RT.beam)}
M3.routeWarm=function(){if(routeG&&M3.ready){routeObjs();RT.beam.visible=false;RT.mesh.geometry.setDrawRange(0,0);routeG.visible=true}};
/* to = {x, y (or null), z} or null to hide */
M3.setRoute=function(from,to){if(!routeG)return;if(!to||!from||!M3.ready){routeHide();RT.key='';return}
 if(!RM){prepRoute();M3.routeWarm();return}var M=RM;
 var key=Math.round(to.x)+','+Math.round(to.z)+','+(to.y==null?'-':Math.round(to.y)),now=Date.now(),dx=from.x-RT.fx,dz=from.z-RT.fz,mv=Math.sqrt(dx*dx+dz*dz);
 if(key===RT.key&&mv<(MOBILE?20:12)&&now-RT.t<3000)return;RT.t=now;RT.fx=from.x;RT.fz=from.z;
 var s=pickTri(M,from.x,from.z,from.y),k=-1;if(s==null){routeHide();return}
 if(key===RT.key&&RT.corr){var ix=RT.idx.get(s);if(ix!=null)k=ix}
 if(k<0){var g=pickTri(M,to.x,to.z,to.y!=null?to.y:from.y),R=g==null?null:aStar(M,s,g);RT.key=key;if(!R){RT.corr=null;routeHide();return}
  RT.corr=R;RT.idx=new Map();R.corr.forEach(function(t,i){RT.idx.set(t,i)});var e0=onTri(M,g,to.x,to.z);RT.to={x:e0[0],y:e0[1],z:e0[2]};k=0}
 var pts=layRoute(M,funnel(M,RT.corr,k,from,RT.to));if(pts.length<2){routeHide();return}
 routeObjs();
 var arr=RT.mesh.geometry.attributes.position.array,W2=FP?6:11,n=Math.min(pts.length,RMAX);
 for(var j=0;j<n;j++){var a=pts[Math.max(0,j-1)],b=pts[Math.min(n-1,j+1)],ex=b[0]-a[0],ez=b[2]-a[2],l=Math.sqrt(ex*ex+ez*ez)||1,nx=-ez/l*W2,nz=ex/l*W2,p=pts[j],o2=6*j;
  arr[o2]=p[0]+nx;arr[o2+1]=-p[1]+4;arr[o2+2]=-(p[2]+nz);arr[o2+3]=p[0]-nx;arr[o2+4]=-p[1]+4;arr[o2+5]=-(p[2]-nz)}
 RT.mesh.geometry.attributes.position.needsUpdate=true;RT.mesh.geometry.setDrawRange(0,(n-1)*6);
 var e=pts[n-1];
 /* the post marking the end: 80 tall (was 260, which read as the line shooting up into the air), and gone once the party is there */
 var ax=e[0]-from.x,az=e[2]-from.z;RT.beam.position.set(e[0],-e[1]+40,-e[2]);RT.beam.visible=ax*ax+az*az>60*60;routeG.visible=true};
G.M3=M3;
})(window);
