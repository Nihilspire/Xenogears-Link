#!/usr/bin/env node
/* Puts an edits file from the room viewer (Edit places > Export edits) into app/www/exits.js, treasure.js and marks.js.
   Each room in the file replaces that room's whole list. Entries are [x, z, destination, y]; y (the floor height, smaller is higher)
   is what the app's 3D map uses to stand the door on the right level.
   node tools/app/import_exits.js "Xenogears exit edits 2026-10-16.json" [--dry] */
const fs=require('fs'),path=require('path');
const src=process.argv[2],dry=process.argv.includes('--dry');if(!src){console.log('usage: import_exits.js edits.json [--dry]');process.exit(1)}
const J=JSON.parse(fs.readFileSync(src,'utf8'));if(!J.rooms)throw new Error('not an exit edits file');
const P=path.join(__dirname,'../../app/www/exits.js'),txt=fs.readFileSync(P,'utf8'),m=txt.match(/^([\s\S]*?)window\.EXITS=(\{[\s\S]*\});\s*$/);
const E=JSON.parse(m[2]);let n=0;
for(const k of Object.keys(J.rooms)){const f=+k;if(!(f>=0&&f<730)||!Array.isArray(J.rooms[k]))continue;
 const L=J.rooms[k].map(e=>{const d=e[2]|0;if(e[0]==null)return [null,null,d];const o=[Math.round(e[0]),Math.round(e[1]),d];if(e[3]!=null)o.push(Math.round(e[3]));return o});
 const before=JSON.stringify(E[k]||[]),after=JSON.stringify(L);if(before===after)continue;n++;
 console.log('room '+k+':\n  was '+before+'\n  now '+after);if(L.length)E[k]=L;else delete E[k]}
let head=m[1];if(!/y \(the floor height/.test(head))head=head.replace(/\s*\*\/\s*$/,'')+'\n   An optional fourth number is y (the floor height, smaller is higher), placed in the room viewer for the 3D map. */\n';
const keys=Object.keys(E).sort((a,b)=>a-b),out=head+'window.EXITS={'+keys.map(k=>JSON.stringify(k)+':'+JSON.stringify(E[k])).join(',')+'};\n';
console.log(n+' room'+(n===1?'':'s')+' of exits changed'+(dry?' (dry run, nothing written)':''));if(!dry&&n)fs.writeFileSync(P,out);
/* treasure places: {room: {index: [x, z, y]}} into treasure.js (x, z at 4 and 5, y at 7; a 6th entry 0 is added where missing) */
function rewrite(file,name,fn){const p=path.join(__dirname,'../../app/www/'+file),t=fs.readFileSync(p,'utf8'),mm=t.match(new RegExp('^([\\s\\S]*?)window\\.'+name+'=(\\{[\\s\\S]*\\});\\s*$'));
 const D=JSON.parse(mm[2]),c=fn(D);console.log(c+' change'+(c===1?'':'s')+' to '+file);
 if(!dry&&c)fs.writeFileSync(p,mm[1]+'window.'+name+'={'+Object.keys(D).sort((a,b)=>a-b).map(k=>JSON.stringify(k)+':'+JSON.stringify(D[k])).join(',')+'};\n')}
if(J.treasure)rewrite('treasure.js','TREASURE',D=>{let c=0;for(const k in J.treasure){const L=D[k];if(!L)continue;for(const i in J.treasure[k]){const t=L[+i],v=J.treasure[k][i];if(!t||!v)continue;
 while(t.length<6)t.push(null);if(t.length<7)t.push(0);t[4]=Math.round(v[0]);t[5]=Math.round(v[1]);t[7]=v[2]==null?null:Math.round(v[2]);c++}}return c});
/* memory cubes and shops: {room: [[x, z, kind, y]]} replaces the room's list in marks.js */
if(J.marks)rewrite('marks.js','MARKS',D=>{let c=0;for(const k in J.marks){const L=J.marks[k].filter(e=>e&&e[0]!=null).map(e=>[Math.round(e[0]),Math.round(e[1]),e[2]].concat(e[3]!=null?[Math.round(e[3])]:[]));
 if(JSON.stringify(D[k]||[])===JSON.stringify(L))continue;c++;if(L.length)D[k]=L;else delete D[k]}return c});
