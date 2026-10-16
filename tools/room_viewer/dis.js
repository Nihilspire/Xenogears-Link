const fs=require('fs'),XB=require('/home/claude/xg/v/www/discbuild.js'),XN=require('./npc.js');const LEN=JSON.parse(fs.readFileSync('oplen.min.json'));
const fd=fs.openSync('/home/claude/xg/disc/d1.bin','r'),size=fs.fstatSync(fd).size;
const reader=async(o,n)=>{const b=Buffer.alloc(n);fs.readSync(fd,b,0,n,o);return new Uint8Array(b.buffer,b.byteOffset,n)};
const hx=v=>(v<16?'0':'')+v.toString(16).toUpperCase();
(async()=>{const d=await XB.open(reader,size);const f=+process.argv[2],e=+process.argv[3],k=+(process.argv[4]||0),max=+(process.argv[5]||60);const h=await d.file(606+2*f);const sc=XN.script(h,XB);const c=sc.code;
 let pc=sc.ent[e][k];console.log('entity',e,'script',k,'at',pc,'all',sc.ent[e].slice(0,8).join(','));
 for(let i=0;i<max;i++){const op=c[pc],key=op===0xFE?'FE'+hx(c[pc+1]):hx(op),L=op===0?1:op===1?3:op===0xD?1:LEN[key];
  console.log(String(pc).padStart(5),key.padEnd(5),Array.from(c.subarray(pc,pc+(L||8))).map(hx).join(' '));if(!L){console.log('?');break}pc+=L;if(op===0)break}})();
