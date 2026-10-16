// Viewer data from the app's own tables (run: node v3d/mkdata.js). Names, chapters, hints, exits, treasure, cubes and shops.
global.window={};
['rooms','areas','chapters','hints','hsplit','exits','treasure','marks','tables','gearparts'].forEach(f=>require(__dirname+'/../../app/www/'+f+'.js'));
const W=window,fs=require('fs');
const FAQ=JSON.parse(fs.readFileSync(__dirname+'/data/faq_room_names.json','utf8'));
const TK=['items','weapons','equipment','gear_weapons','gear_parts'];
function nm(c){const k=TK[c>>8],id=c&255,t=(W.GEARTBL&&W.GEARTBL[k])||W.TABLES[k],v=t&&t[id];return v&&v!=='/'?v:['Item','Weapon','Equip','Gear weapon','Gear part'][c>>8]+' '+id}
const TRE={};for(const f in W.TREASURE)TRE[f]=W.TREASURE[f].map(t=>{const n=t[2].map(nm);if(t[3])n.push(t[3]+' G');return [n.join(' + '),t.length>5?t[4]:null,t.length>5?t[5]:null,(t.length<6||t[6]===1)?1:0,t[0],t[1]]});
// hint rooms per step, the same list the app's pop-up uses: [[room, [[x, z]...]]...]
const HR={};for(const k in W.HINTS){let L;if(W.HPATH[k])L=W.HPATH[k].map(q=>[q[0],q[1]]);else{const pre=W.HPRE[k]||[],rows=W.HINTS[k];L=pre.map(q=>[q[0],q[1]]).concat(rows.slice(0,Math.max(1,3-pre.length)).map(r=>[r[0],r.length>3?[[r[2],r[3]]]:[]]))}
 const o=[];L.forEach(([f,s])=>{if(o.length&&o[o.length-1][0]===f)o[o.length-1][1]=o[o.length-1][1].concat(s);else o.push([f,s.slice()])});HR[k]=o}
const HINTS={};for(const k in HR)HINTS[k]=HR[k].map(q=>q[0]);
// world map places, from the world program's place tables of every travel set (fld/worldloc_raw.json): [x, z, w, d, room, entry, place, type];
// sets 0-7 and 11-14 are the normal world (a), 8, 15 and 16 the late-game world (b); type 4 is a trigger strip, not a place
const WL=JSON.parse(fs.readFileSync(__dirname+'/data/worldloc_raw.json','utf8'));
const WPLACE=eval('('+fs.readFileSync(__dirname+'/../../app/index.html','utf8').match(/var WPLACE=(\{[\s\S]*?\});/)[1]+')');
const WP={a:[],b:[]};[['a',[0,1,2,3,4,5,6,7,11,12,13,14]],['b',[8,15,16]]].forEach(([k,sets])=>{const seen={};sets.forEach(si=>(WL[si]||[]).forEach(r=>{if(r[7]===4)return;const key=r[6]+'/'+r[0]+'/'+r[1];if(seen[key])return;seen[key]=1;
 WP[k].push([r[0]+r[2]/2|0,r[1]+r[3]/2|0,r[4],r[6],WPLACE[r[6]]||W.ROOMS[r[4]]||''])}))});
// arrival spots: where the game puts the party in each room, per room it comes in from (entrance tables + the room changes that
// name them; tools/app/exit_check.js writes them to exitcheck.json as ARR[room][from room] = [[x, z]...])
let ARR={};try{ARR=JSON.parse(fs.readFileSync(process.env.XG_EXITCHECK||'/tmp/claude-0/exitcheck.json','utf8')).ARR||{}}catch(e){console.log('no arrival spots')}
const XD={ARR:ARR,HSPLIT:W.HSPLIT||{},WPLACES:WP,ROOMS:W.ROOMS,AREAS:W.AREAS,CHAPTERS:W.CHAPTERS,HNOTE:W.HNOTE,HINTS:HINTS,HROOMS:HR,FAQ:FAQ,EXITS:W.EXITS,TRE:TRE,MARKS:W.MARKS};
fs.writeFileSync(__dirname+'/data.js','window.XD='+JSON.stringify(XD)+';\n');
console.log(Object.keys(XD).map(k=>k+':'+Object.keys(XD[k]).length).join(' '),fs.statSync(__dirname+'/data.js').size);
