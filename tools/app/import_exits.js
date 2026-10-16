#!/usr/bin/env node
/* Puts an exit edits file from the room viewer (Edit exits > Export edits) into app/www/exits.js.
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
console.log(n+' room'+(n===1?'':'s')+' changed'+(dry?' (dry run, nothing written)':''));if(!dry&&n)fs.writeFileSync(P,out)
