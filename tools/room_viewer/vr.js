const fs=require('fs'),XB=require('/home/claude/xg/v/www/discbuild.js');
const fd=fs.openSync('/home/claude/xg/disc/d1.bin','r'),size=fs.fstatSync(fd).size;
const reader=async(o,n)=>{const b=Buffer.alloc(n);fs.readSync(fd,b,0,n,o);return new Uint8Array(b.buffer,b.byteOffset,n)};
(async()=>{const d=await XB.open(reader,size);for(const f of process.argv.slice(2).map(Number)){const t=await d.file(607+2*f);const V=XB.vram(t);fs.writeFileSync('/tmp/claude-0/sp/vr'+f+'.bin',Buffer.from(V.buffer))}})();
