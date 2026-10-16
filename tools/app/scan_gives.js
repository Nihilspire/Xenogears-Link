// Every item (8C) and gold (8F) give in every room script, compared with the app's treasure list (treasure.js). Needs a harness that opens
// disc 1 with discbuild.js and the room viewer's npc.js (XG_HARNESS). Writes /tmp/claude-0/tre_scan.json: {out: every give, miss: gives not in the list}.
const H=require(process.env.XG_HARNESS||'./harness.js'),fs=require('fs');
const W='/home/claude/xenogears-link/app/www/';global.window=global;
for(const f of ['treasure.js','tables.js','gearparts.js','rooms.js','areas.js'])eval(fs.readFileSync(W+f,'utf8'));
const LEN=JSON.parse(fs.readFileSync(W+'npc.js','utf8').match(/var LEN=(\{[^}]*\})/)[1]);
const hx=v=>(v<16?'0':'')+v.toString(16).toUpperCase(),u16=(b,p)=>b[p]|b[p+1]<<8;
const TK=['items','weapons','equipment','gear_weapons','gear_parts'];
function nm(c){const k=TK[c>>8],id=c&255,t=(window.GEARTBL&&window.GEARTBL[k])||window.TABLES[k],v=t&&t[id];return v&&v!=='/'?v:(k||'?')+' '+id}
function area(f){for(const r of window.AREAS)if(f>=r[0]&&f<=r[1])return r[2];return '?'}
(async()=>{const {d,XN,XB}=await H();const out=[];let rooms=0,routines=0,bad=0;
 for(let f=0;f<730;f++){const h=await d.file(606+2*f);if(!h)continue;let sc;try{sc=XN.script(h,XB)}catch(e){continue}if(!sc)continue;rooms++;
  const c=sc.code,starts=[...new Set(sc.ent.flat().filter(p=>p>0&&p<c.length))].sort((a,b)=>a-b);
  const owner={};sc.ent.forEach((e,i)=>e.forEach((p,r)=>{if(!(p in owner))owner[p]=[i,r]}));
  const sets={},gives=[];
  starts.forEach((p0,si)=>{const end=si+1<starts.length?starts[si+1]:c.length;let p=p0,ow=owner[p0];routines++;const flags=[];const local=[];
   while(p<end){const op=c[p],key=op===0xFE?'FE'+hx(c[p+1]):hx(op),L=op===0x00?1:LEN[key];if(!L){bad++;break}
    if(key==='35'&&(c[p+5]&0x40)){(sets[u16(c,p+1)]=sets[u16(c,p+1)]||new Set()).add(u16(c,p+3))}
    if(key==='3A')flags.push(hx(u16(c,p+1)>>8)+hx(u16(c,p+1)&255)+'.'+(c[p+5]&0x40?u16(c,p+3):'v'));
    if(key==='FE0A'){const fl=u16(c,p+2);flags.push(hx((fl>>4)>>8)+hx((fl>>4)&255)+'.'+(fl&15))}
    if(key==='8C')local.push({k:'item',a:u16(c,p+1),at:p});
    if(key==='8F')local.push({k:'gold',a:u16(c,p+1),at:p});
    p+=L}
   local.forEach(g=>gives.push(Object.assign(g,{actor:ow[0],routine:ow[1],flags:flags.slice()})))});
  // resolve variable items through the room's literal assignments
  gives.forEach(g=>{let vals;if(g.a&0x8000)vals=[g.a&0x7FFF];else vals=[...(sets[g.a]||[])].map(v=>v&0x7FFF);
   if(!vals.length)vals=[null];vals.forEach(v=>out.push({f,actor:g.actor,routine:g.routine,kind:g.k,val:v,viaVar:!(g.a&0x8000),flags:g.flags}))})}
 // compare
 const T=window.TREASURE,miss=[],have={items:0,gold:0};
 out.forEach(g=>{if(g.f>=720||g.val==null)return;const L=T[g.f]||[];
  const hit=g.kind==='item'?L.some(t=>t[2].indexOf(g.val)>=0):L.some(t=>t[3]===g.val);
  if(hit){have[g.kind==='item'?'items':'gold']++;return}
  // listed in another room? (a shared give)
  const elsewhere=Object.keys(T).filter(r=>T[r].some(t=>g.kind==='item'?t[2].indexOf(g.val)>=0:t[3]===g.val)).slice(0,4);
  miss.push(Object.assign(g,{name:g.kind==='item'?nm(g.val):g.val+' G',elsewhere}))});
 fs.writeFileSync('/tmp/claude-0/tre_scan.json',JSON.stringify({out,miss}));
 console.log('rooms',rooms,'routines',routines,'undecodable',bad,'gives',out.length,'matched',JSON.stringify(have),'not in list',miss.length);
})();
