// per room: walkable triangles (from the disc, or the hand-drawn MAPFIX), for the review pictures
const H=require('./harness.js'),fs=require('fs');const W='/home/claude/xenogears-link/app/www/';global.window=global;
for(const f of ['mapfix.js','plan.js'])eval(fs.readFileSync(W+f,'utf8'));
(async()=>{const {d,XB}=await H();const out={};
 for(let f=0;f<730;f++){if(!window.PLAN[f])continue;const h=await d.file(606+2*f);if(!h)continue;let T=[];
  const fx=window.MAPFIX[f];
  if(fx){T=fx.t.map(t=>t.map(i=>fx.v[i]))}
  else{try{const F=XB.walkFloors(h);if(F)T=F.T.filter(t=>!((F.surf[t[3]]||0)&0x800000)).map(t=>[0,1,2].map(k=>[F.VX[t[k]],F.VZ[t[k]]]))}catch(e){}}
  out[f]=T}
 fs.writeFileSync('/tmp/claude-0/walk.json',JSON.stringify(out));console.log(Object.keys(out).length,'rooms')})();
