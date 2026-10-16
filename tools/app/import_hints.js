#!/usr/bin/env node
/* Puts a hint edits file from the room viewer (Edit hints > Export hint edits) into app/www/hints.js: each step's note replaces
   HNOTE[step] ("?" in front = not yet checked in game) and its path replaces HPATH[step] (the rooms and green spots the app's hint
   pop-up and map use). An empty note removes the note; an empty path removes HPATH[step] so the app falls back to the room that sets the step.
   node tools/app/import_hints.js "Xenogears hint edits 2026-10-16.json" [--dry] */
const fs=require('fs'),path=require('path');const src=process.argv[2],dry=process.argv.includes('--dry');if(!src){console.log('usage: import_hints.js edits.json [--dry]');process.exit(1)}
const J=JSON.parse(fs.readFileSync(src,'utf8'));if(!J.steps)throw new Error('not a hint edits file');
const P=path.join(__dirname,'../../app/www/hints.js');let txt=fs.readFileSync(P,'utf8');
const get=n=>{const m=txt.match(new RegExp('^window\\.'+n+'=(.*);\\s*$','m'));return JSON.parse(m[1])};
const put=(n,O)=>{const keys=Object.keys(O).sort((a,b)=>a-b),line='window.'+n+'={'+keys.map(k=>JSON.stringify(k)+':'+JSON.stringify(O[k])).join(',')+'};';txt=txt.replace(new RegExp('^window\\.'+n+'=.*;\\s*$','m'),()=>line)};
const N=get('HNOTE'),H=get('HPATH');let c=0;
for(const k of Object.keys(J.steps)){const e=J.steps[k],note=String(e.note||'').trim(),pth=(e.path||[]).map(q=>[q[0]|0,(q[1]||[]).map(s=>[Math.round(s[0]),Math.round(s[1])])]);
 const was=JSON.stringify([N[k]||null,H[k]||null]);if(note&&note!=='?')N[k]=note;else delete N[k];if(pth.length)H[k]=pth;else delete H[k];
 const now=JSON.stringify([N[k]||null,H[k]||null]);if(was!==now){c++;console.log('step '+k+':\n  was '+was+'\n  now '+now)}}
put('HNOTE',N);put('HPATH',H);console.log(c+' step'+(c===1?'':'s')+' changed'+(dry?' (dry run, nothing written)':''));if(!dry&&c)fs.writeFileSync(P,txt);
