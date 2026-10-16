const fs=require('fs'),XB=require('/home/claude/xg/v/www/discbuild.js'),XN=require('./npc.js');const LEN=JSON.parse(fs.readFileSync('oplen.min.json'));
const fd=fs.openSync('/home/claude/xg/disc/d1.bin','r'),size=fs.fstatSync(fd).size;
const reader=async(o,n)=>{const b=Buffer.alloc(n);fs.readSync(fd,b,0,n,o);return new Uint8Array(b.buffer,b.byteOffset,n)};
const hx=v=>(v<16?'0':'')+v.toString(16).toUpperCase();
(async()=>{const d=await XB.open(reader,size);const f=+process.argv[2];const h=await d.file(606+2*f);const sc=XN.script(h,XB);const c=sc.code;
 const starts=[];sc.ent.forEach((e,i)=>e.forEach((p,k)=>starts.push([p,i,k])));starts.sort((a,b)=>a[0]-b[0]);
 const seen={};for(const [p0,i,k] of starts){if(seen[p0])continue;seen[p0]=1;let p=p0,g=0;while(p<c.length&&g++<3000){const op=c[p],key=op===0xFE?'FE'+hx(c[p+1]):hx(op),L=op===0?1:op===1?3:op===0xD?1:LEN[key];if(!L)break;
  if(op>=0x84&&op<=0x86)console.log('ent',i,'script',k,'at',p,key,u(c,p+1)&0x7FFF);if(op===0)break;p+=L}}
 function u(c,p){return c[p]|c[p+1]<<8}})();
