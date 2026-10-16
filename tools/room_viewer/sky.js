const fs=require('fs'),XB=require('/home/claude/xg/v/www/discbuild.js'),XN=require('./npc.js');
const fd=fs.openSync('/home/claude/xg/disc/d1.bin','r'),size=fs.fstatSync(fd).size;
const reader=async(o,n)=>{const b=Buffer.alloc(n);fs.readSync(fd,b,0,n,o);return new Uint8Array(b.buffer,b.byteOffset,n)};
(async()=>{const d=await XB.open(reader,size);const f=+process.argv[2];const h=await d.file(606+2*f);const M=XB.models(h),HD=XN.head(h);
 const W=XB.walkLayers(h);let wb=[1e9,-1e9,1e9,-1e9,1e9,-1e9];W.L.slice(0,Math.max(1,W.L.length-1)).forEach(L=>{for(let i=0;i<L.VX.length;i++){wb[0]=Math.min(wb[0],L.VX[i]);wb[1]=Math.max(wb[1],L.VX[i]);wb[2]=Math.min(wb[2],-L.VY[i]);wb[3]=Math.max(wb[3],-L.VY[i]);wb[4]=Math.min(wb[4],L.VZ[i]);wb[5]=Math.max(wb[5],L.VZ[i])}});
 console.log('walk',wb.join(' '));
 HD.forEach((e,i)=>{if(e.flags&0x40||!M[e.model])return;let b=[1e9,-1e9,1e9,-1e9,1e9,-1e9];M[e.model].forEach(p=>{for(let j=0;j<p.V.length;j+=3){const x=p.V[j]+e.x,y=-(p.V[j+1]+e.y),z=p.V[j+2]+e.z;b[0]=Math.min(b[0],x);b[1]=Math.max(b[1],x);b[2]=Math.min(b[2],y);b[3]=Math.max(b[3],y);b[4]=Math.min(b[4],z);b[5]=Math.max(b[5],z)}});
  if(b[1]-b[0]>1500)console.log(i,'model',e.model,b.map(Math.round).join(' '))})})();
