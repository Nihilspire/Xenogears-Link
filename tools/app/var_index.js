#!/usr/bin/env node
// Which rooms set and which check each script variable (byte offset into the bank at 0x800C3A68), and which bits where the command
// names one. For the room viewer's snapshot comparison. Commands (RAM map, "Room scripts"):
//   set:   35 var value / 36 var / 37 var (whole value), 34 item var, A8 var (random), 87 (story step, var 0), 3A/3B var n (bit n),
//          FE0A/FE0B flag (var = flag >> 4, bit = flag & 15)
//   check: 02 a b flags (a and b when they name variables; test 6 = AND with a literal gives the bits), FB flag, 84/85/86 (var 0)
// Output: tools/room_viewer/data/var_index.json  {var: {s: {room: mask}, c: {room: mask}}}, mask 0 = the whole value.
const H=require('./harness.js'),fs=require('fs');const W=__dirname+'/../../app/www/';
const LEN=JSON.parse(fs.readFileSync(W+'npc.js','utf8').match(/var LEN=(\{[^}]*\})/)[1]);
const hx=v=>(v<16?'0':'')+v.toString(16).toUpperCase(),u16=(b,p)=>b[p]|b[p+1]<<8;
(async()=>{const {d,XN}=await H(),XB=global.XB;const X={};let rooms=0;
 const add=(k,v,f,mask)=>{if(v==null||v<0||v>=0x400)return;const e=X[v]=X[v]||{s:{},c:{}},o=e[k];o[f]=mask===0||o[f]===0&&o[f]!==undefined?0:((o[f]||0)|mask)};
 const isVar=a=>!(a&0x8000);
 for(let f=0;f<730;f++){const h=await d.file(606+2*f);if(!h)continue;let sc;try{sc=XN.script(h,XB)}catch(e){continue}if(!sc)continue;rooms++;
  const c=sc.code,starts=[...new Set(sc.ent.flat().filter(p=>p>0&&p<c.length))].sort((a,b)=>a-b);
  starts.forEach((p0,si)=>{const end=si+1<starts.length?starts[si+1]:c.length;let p=p0;
   while(p<end){const op=c[p],key=op===0xFE?'FE'+hx(c[p+1]):hx(op),L=op===0?1:LEN[key];if(!L)break;
    switch(key){
     case '35':case '36':case '37':case 'A8':add('s',u16(c,p+1),f,0);break;
     case '34':add('s',u16(c,p+3),f,0);break;
     case '87':add('s',0,f,0);break;
     case '84':case '85':case '86':add('c',0,f,0);break;
     case '3A':case '3B':{const v=u16(c,p+1),n=u16(c,p+3),fl=c[p+5];add('s',v,f,(fl&0x40)||(n&0x8000)?1<<((n&0x7FFF)&15):0);break}
     case 'FE0A':case 'FE0B':{const fl=u16(c,p+2);add('s',fl>>4,f,1<<(fl&15));break}
     case 'FB':{const fl=u16(c,p+1);add('c',fl>>4,f,1<<(fl&15));break}
     case '02':{const a=u16(c,p+1),b=u16(c,p+3),fl=c[p+5],litA=fl&0x80||!isVar(a),litB=fl&0x40||!isVar(b);
      if(!litA)add('c',a,f,(fl&15)===6&&litB?(b&0x7FFF)&0xFFFF:0);if(!litB)add('c',b,f,(fl&15)===6&&litA?(a&0x7FFF)&0xFFFF:0);break}}
    p+=L}})}
 fs.writeFileSync(__dirname+'/../room_viewer/data/var_index.json',JSON.stringify(X));
 console.log(rooms+' rooms, '+Object.keys(X).length+' variables; e.g. 152:',JSON.stringify(X[152]).slice(0,200),' 712:',JSON.stringify(X[712]).slice(0,200))})();
