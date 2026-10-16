// node harness: the app's disc reader + the viewer's NPC reader on real rooms
const fs=require('fs');global.window=global;global.self=global;
for(const f of ['chd.js','discbuild.js'])eval(fs.readFileSync('/home/claude/xenogears-link/app/www/'+f,'utf8'));
const XN=require(process.env.NPC||'/home/claude/npc/npc_viewer.js');
const fd=fs.openSync('/home/claude/disc/Xenogears_PW_CD1.bin','r'),size=fs.fstatSync(fd).size;
const reader=async(o,n)=>{const b=Buffer.alloc(n);fs.readSync(fd,b,0,n,o);return new Uint8Array(b.buffer,b.byteOffset,n)};
module.exports=async function(){const d=await XB.open(reader,size);return {d,XN,XB}};
if(require.main===module)(async()=>{const {d}=await module.exports();
 for(const f of (process.argv[2]||'1,4,13,35,102').split(',').map(Number)){const h=await d.file(606+2*f),t=await d.file(607+2*f);
  const VR=XB.vram(t);XN.uploadSheets(h,VR,XB);const S=XN.sprites(h,XB),sc=XN.script(h,XB);
  const r=sc?XN.run(sc,{step:+(process.env.STEP||10),head:XN.head(h),vars:{2:0},party:[0]}):{E:[]};
  const npcs=r.E.filter(e=>e.kind==='npc');
  console.log('room',f,'sprites',S.length,'entities',r.E.length,'npcs',npcs.length,'shown',npcs.filter(e=>!e.hidden&&!e.deleted).length,
   npcs.slice(0,6).map(e=>e.i+':s'+e.sprite+'@'+e.x+','+e.z+(e.hidden?'h':'')).join(' '));
  const e=npcs.find(e=>S[e.sprite]);if(e){const fr=XN.frame(S[e.sprite],VR,0,e.variant);console.log('  frame',fr&&[fr.w,fr.h,fr.x0,fr.y0])}}
})();
