// Every room change in every room script (47 door, 98 go-to-room) with its literal destination room and entry point, and every
// room's entrance table; then each exit in exits.js is measured against the arrival spots the game uses on the far side's way back.
const H=require('./harness.js'),fs=require('fs');const W='/home/claude/xenogears-link/app/www/';global.window=global;
eval(fs.readFileSync(W+'exits.js','utf8'));
const LEN=JSON.parse(fs.readFileSync(W+'npc.js','utf8').match(/var LEN=(\{[^}]*\})/)[1]);
const hx=v=>(v<16?'0':'')+v.toString(16).toUpperCase(),u16=(b,p)=>b[p]|b[p+1]<<8;
(async()=>{const {d,XN,XB}=await H();const ENT={},TR={};
 for(let f=0;f<730;f++){const h=await d.file(606+2*f);if(!h)continue;let sc;try{sc=XN.script(h,XB)}catch(e){continue}if(!sc)continue;
  ENT[f]=XN.entries(sc).map(e=>[e.x,e.z]);const c=sc.code,starts=[...new Set(sc.ent.flat().filter(p=>p>0&&p<c.length))].sort((a,b)=>a-b);
  starts.forEach((p0,si)=>{const end=si+1<starts.length?starts[si+1]:c.length;let p=p0;
   while(p<end){const op=c[p],key=op===0xFE?'FE'+hx(c[p+1]):hx(op),L=op===0?1:LEN[key];if(!L)break;
    let room=null,entry=null;
    if(key==='47'){room=u16(c,p+2);entry=u16(c,p+4)}if(key==='98'){room=u16(c,p+1);entry=u16(c,p+3)}
    if(room!=null&&(room&0x8000)&&(entry&0x8000)){const B=room&0x3FF,e=entry&0x7FFF;(TR[f]=TR[f]||[]).push([B,e])}
    p+=L}})}
 // arrival spots in room B for a way in from A
 const ARR={};for(const A in TR)for(const [B,e] of TR[A]){const sp=ENT[B]&&ENT[B][e];if(!sp)continue;((ARR[B]=ARR[B]||{})[A]=ARR[B][A]||[]).push(sp)}
 const rows=[];for(const B in window.EXITS)window.EXITS[B].forEach((ex,i)=>{const [x,z,A]=ex;if(x==null||A<0)return;const c=(ARR[B]||{})[A];
  if(!c){rows.push({B:+B,i,A,x,z,d:null});return}let best=null,bd=1e9;c.forEach(s=>{const dd=Math.hypot(s[0]-x,s[1]-z);if(dd<bd){bd=dd;best=s}});rows.push({B:+B,i,A,x,z,d:Math.round(bd),to:best})});
 fs.writeFileSync('/tmp/claude-0/exitcheck.json',JSON.stringify({rows,ENT,ARR}));
 const ds=rows.filter(r=>r.d!=null).map(r=>r.d).sort((a,b)=>a-b),q=p=>ds[Math.floor(ds.length*p)];
 console.log('exits',rows.length,'with an arrival spot to check',ds.length,'none',rows.filter(r=>r.d==null).length);
 console.log('distance to arrival spot: median',q(.5),'p75',q(.75),'p90',q(.9),'p95',q(.95),'max',ds[ds.length-1]);
 for(const t of [200,300,400,600,1000])console.log(' over',t,':',ds.filter(v=>v>t).length);
})();
