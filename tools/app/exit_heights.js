#!/usr/bin/env node
// Fills the fourth number (y, the floor height) of every exit in app/www/exits.js that has none, for the 3D map's doors.
// The level comes from the game: the way back from the exit's destination puts the party on an entrance-table spot in this room,
// with its walk layer. y is the floor of that layer under the exit (or, when the exit point is off the walk mesh, under the arrival
// spot). Exits with no way back known use the floor under them when every level there agrees within 40 units; otherwise they are left
// for the app's fallback (the floor nearest the party). Exits already holding a y (placed in the room viewer) are kept.
// node tools/app/exit_heights.js [--dry]
const H=require('./harness.js'),fs=require('fs');const W=__dirname+'/../../app/www/';global.window=global;
eval(fs.readFileSync(W+'exits.js','utf8'));
const LEN=JSON.parse(fs.readFileSync(W+'npc.js','utf8').match(/var LEN=(\{[^}]*\})/)[1]);
const hx=v=>(v<16?'0':'')+v.toString(16).toUpperCase(),u16=(b,p)=>b[p]|b[p+1]<<8,dry=process.argv.includes('--dry');
function floorsAt(WL,x,z,only){const out=[];WL.L.forEach((L,l)=>{if(only!=null&&l!==only)return;if(WL.L.length>1&&l===WL.L.length-1)return;   /* the last layer is the camera bounds, not floor */for(const t of L.T){if((WL.surf[t[3]]||0)&0x800000)continue;const ax=L.VX[t[0]],az=L.VZ[t[0]],bx=L.VX[t[1]],bz=L.VZ[t[1]],cx=L.VX[t[2]],cz=L.VZ[t[2]];
  if(x<Math.min(ax,bx,cx)-1||x>Math.max(ax,bx,cx)+1||z<Math.min(az,bz,cz)-1||z>Math.max(az,bz,cz)+1)continue;
  const den=(bz-cz)*(ax-cx)+(cx-bx)*(az-cz);if(!den)continue;const A=((bz-cz)*(x-cx)+(cx-bx)*(z-cz))/den,B=((cz-az)*(x-cx)+(ax-cx)*(z-cz))/den,C=1-A-B;
  if(A>=-0.05&&B>=-0.05&&C>=-0.05)out.push(A*L.VY[t[0]]+B*L.VY[t[1]]+C*L.VY[t[2]])}});return out}
(async()=>{const {d,XN,XB}=await H();const ENT={},TR={},WLS={};
 for(let f=0;f<730;f++){const h=await d.file(606+2*f);if(!h)continue;try{const wl=XB.walkLayers(h);if(wl&&wl.L.length)WLS[f]=wl}catch(e){}
  let sc;try{sc=XN.script(h,XB)}catch(e){continue}if(!sc)continue;
  ENT[f]=XN.entries(sc);const c=sc.code,starts=[...new Set(sc.ent.flat().filter(p=>p>0&&p<c.length))].sort((a,b)=>a-b);
  starts.forEach((p0,si)=>{const end=si+1<starts.length?starts[si+1]:c.length;let p=p0;
   while(p<end){const op=c[p],key=op===0xFE?'FE'+hx(c[p+1]):hx(op),L=op===0?1:LEN[key];if(!L)break;let room=null,entry=null;
    if(key==='47'){room=u16(c,p+2);entry=u16(c,p+4)}if(key==='98'){room=u16(c,p+1);entry=u16(c,p+3)}
    if(room!=null&&(room&0x8000)&&(entry&0x8000))(TR[f]=TR[f]||[]).push([room&0x3FF,entry&0x7FFF]);p+=L}})}
 const ARR={};for(const A in TR)for(const [B,e] of TR[A]){const sp=ENT[B]&&ENT[B][e];if(sp)((ARR[B]=ARR[B]||{})[A]=ARR[B][A]||[]).push(sp)}
 const st={arrival:0,single:0,left:0,kept:0,multi:0},far=[],noY=[];
 for(const B in EXITS){const WL=WLS[B];EXITS[B].forEach((ex,i)=>{if(ex[0]==null)return;const had=ex[3]!=null;if(!WL){if(!had){st.left++;noY.push([+B,i,ex[2],ex[0],ex[1]])}return}
  const [x,z,A]=ex,all=floorsAt(WL,x,z);if(all.length&&Math.max(...all)-Math.min(...all)>40)st.multi++;
  const c=(ARR[B]||{})[A];let y=null;
  if(c&&c.length){let s=c[0],bd=1e9;c.forEach(q=>{const dd=Math.hypot(q.x-x,q.z-z);if(dd<bd){bd=dd;s=q}});
   const ya=floorsAt(WL,s.x,s.z,s.layer).concat(floorsAt(WL,s.x,s.z));const ref=ya.length?ya[0]:null;
   const here=floorsAt(WL,x,z,s.layer);const pool=here.length?here:all;
   if(ref!=null&&pool.length)y=pool.reduce((b,v)=>Math.abs(v-ref)<Math.abs(b-ref)?v:b);else if(ref!=null)y=ref;else if(pool.length)y=pool[0];
   if(y!=null){if(!had)st.arrival++;if(bd>400&&all.length>1&&Math.max(...all)-Math.min(...all)>40)far.push([+B,i,A,x,z,Math.round(bd)])}}
  else if(all.length&&Math.max(...all)-Math.min(...all)<=40){y=all[0];if(!had)st.single++}
  if(had){st.kept++;return}if(y==null){st.left++;noY.push([+B,i,A,x,z]);return}ex[3]=Math.round(y)})}
 console.log(st,'\nmulti-level exits far (>400) from their arrival spot:',far.length);
 /* treasure and memory cubes / shops: the floor under them when every level there agrees within 40 units (chests and cubes stand on
    one floor; on a room with several levels they are left for the room viewer or the app's fallback) */
 eval(fs.readFileSync(W+'treasure.js','utf8'));eval(fs.readFileSync(W+'marks.js','utf8'));const noYm=[],ts={tre:0,treLeft:0,mk:0,mkLeft:0};
 const one=(B,x,z)=>{const WL=WLS[B];if(!WL||x==null)return null;const a=floorsAt(WL,x,z);return a.length&&Math.max(...a)-Math.min(...a)<=40?Math.round(a[0]):null};
 for(const B in TREASURE)TREASURE[B].forEach(t=>{if(t.length<6||t[4]==null||t[7]!=null)return;const y=one(B,t[4],t[5]);if(y==null){ts.treLeft++;noYm.push([+B,'tre',TREASURE[B].indexOf(t),t[4],t[5]]);return}if(t.length<7)t.push(0);t[7]=y;ts.tre++});
 for(const B in MARKS)MARKS[B].forEach(m=>{if(m[3]!=null)return;const y=one(B,m[0],m[1]);if(y==null){ts.mkLeft++;noYm.push([+B,'mk',MARKS[B].indexOf(m),m[0],m[1]]);return}m[3]=y;ts.mk++});console.log(ts);
 fs.writeFileSync(__dirname+'/../room_viewer/data/exit_review.json',JSON.stringify({far:far,noY:noY,noYm:noYm}));   /* the room viewer's review queue */
 const put=(file,name,D)=>{const t=fs.readFileSync(W+file,'utf8'),h=t.match(new RegExp('^([\\s\\S]*?)window\\.'+name+'='))[1];fs.writeFileSync(W+file,h+'window.'+name+'={'+Object.keys(D).sort((a,b)=>a-b).map(k=>JSON.stringify(k)+':'+JSON.stringify(D[k])).join(',')+'};\n')};
 if(!dry){put('treasure.js','TREASURE',TREASURE);put('marks.js','MARKS',MARKS)}
 if(!dry){const txt=fs.readFileSync(W+'exits.js','utf8'),m=txt.match(/^([\s\S]*?)window\.EXITS=/);let head=m[1];
  if(!/y \(the floor height/.test(head))head=head.replace(/\s*\*\/\s*$/,'')+'\n   An optional fourth number is y (the floor height, smaller is higher): from tools/app/exit_heights.js, or placed in the room viewer. */\n';
  fs.writeFileSync(W+'exits.js',head+'window.EXITS={'+Object.keys(EXITS).sort((a,b)=>a-b).map(k=>JSON.stringify(k)+':'+JSON.stringify(EXITS[k])).join(',')+'};\n');console.log('written')}
})();
