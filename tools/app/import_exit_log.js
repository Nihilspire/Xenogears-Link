#!/usr/bin/env node
/* Turns the app's exit log (Documents\Xenogears Link\Exit log\exit log.jsonl, Windows DEV) into an exit edits file for
   tools/app/import_exits.js (or the room viewer's Import edits). Walks through the same door (same two rooms, within 150 units) are
   averaged; each group moves the nearest way out to that room in app/www/exits.js, or is added when there is none left.
   node tools/app/import_exit_log.js "exit log.jsonl" > edits.json */
const fs=require('fs');global.window=global;eval(fs.readFileSync(__dirname+'/../../app/www/exits.js','utf8'));
const L=[];fs.readFileSync(process.argv[2],'utf8').split(/\r?\n/).forEach(t=>{t=t.trim();if(!t)return;let o;try{o=JSON.parse(t)}catch(e){return}if(o.undo)L.pop();else if(o.from!=null&&o.to!=null&&o.x!=null)L.push(o)});
const G={};for(const o of L){const k=o.from+'>'+o.to,g=G[k]=G[k]||[];let c=g.find(c=>Math.hypot(c.x/c.n-o.x,c.z/c.n-o.z)<150);if(!c){c={from:o.from,to:o.to,x:0,z:0,y:0,n:0};g.push(c)}c.x+=o.x;c.z+=o.z;c.y+=o.y;c.n++}
const out={};let moved=0,added=0;
for(const k in G)for(const c of G[k]){const f=c.from,x=Math.round(c.x/c.n),z=Math.round(c.z/c.n),y=Math.round(c.y/c.n);
 if(!out[f])out[f]=(EXITS[f]||[]).map(e=>Object.assign(e.slice(),{used:0}));const A=out[f];let best=-1,bd=1e9;
 A.forEach((e,i)=>{if(e[2]!==c.to||e.used)return;const d=e[0]==null?5e8:Math.hypot(e[0]-x,e[1]-z);if(d<bd){bd=d;best=i}});
 const ne=Object.assign([x,z,c.to,y],{used:1});if(best>=0){A[best]=ne;moved++}else{A.push(ne);added++}}
for(const f in out)out[f]=out[f].map(e=>e.slice(0,4));
console.error(L.length+' walks, '+Object.keys(out).length+' rooms, '+moved+' moved, '+added+' added');
process.stdout.write(JSON.stringify({format:'xenogears-link-exit-edits',version:1,made:new Date().toISOString(),from:'exit log',rooms:out})+'\n');
