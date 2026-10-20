// Viewer data from the app's own tables (run: node v3d/mkdata.js). Names, chapters, hints, exits, treasure, cubes and shops.
global.window={};
['rooms','areas','chapters','hints','hsplit','exits','treasure','missables','marks','tables','gearparts'].forEach(f=>require(__dirname+'/../../app/www/'+f+'.js'));
const W=window,fs=require('fs');
const FAQ=JSON.parse(fs.readFileSync(__dirname+'/data/faq_room_names.json','utf8'));
const TK=['items','weapons','equipment','gear_weapons','gear_parts'];
function nm(c){const k=TK[c>>8],id=c&255,t=(W.GEARTBL&&W.GEARTBL[k])||W.TABLES[k],v=t&&t[id];return v&&v!=='/'?v:['Item','Weapon','Equip','Gear weapon','Gear part'][c>>8]+' '+id}
// [name, x, z, gift, var, bit, y, lost when (missables.js) or null]; the missables' own pickups follow the room's treasure
const MS=W.MISS||{tag:{},extra:{}};const TRE={};for(const f in W.TREASURE)TRE[f]=W.TREASURE[f].map(t=>{const n=t[2].map(nm);if(t[3])n.push(t[3]+' G');return [n.join(' + '),t.length>5?t[4]:null,t.length>5?t[5]:null,(t.length<6||t[6]===1)?1:0,t[0],t[1],t.length>7?t[7]:null,MS.tag[f+':'+t[0]+':'+t[1]]||null]});
for(const f in MS.extra)TRE[f]=(TRE[f]||[]).concat(MS.extra[f].map(e=>[e[2],e[3],e[4],e[6]?1:0,e[0],e[1],null,e[5]]));
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
let REVIEW={look:[],far:[],noY:[],noYm:[]};try{REVIEW.look=JSON.parse(fs.readFileSync(__dirname+'/data/review_1.99.0.3.json','utf8'));const r=JSON.parse(fs.readFileSync(__dirname+'/data/exit_review.json','utf8'));REVIEW.far=r.far;REVIEW.noY=r.noY;REVIEW.noYm=r.noYm||[]}catch(e){console.log('no review lists')}
let VIDX={};try{VIDX=JSON.parse(fs.readFileSync(__dirname+'/data/var_index.json','utf8'))}catch(e){console.log('no var index')}
// hint spot check (tools/sheets/spotcheck.py): [step, page, room, x, z, verdict, actor, actor x, actor z, distance, first line]
let SPOTCHK=[];try{SPOTCHK=JSON.parse(fs.readFileSync(__dirname+'/data/spotcheck.json','utf8')).map(r=>{const np=(r.near_pos||'').split(',').map(Number);return [r.step,r.page,r.room,r.x,r.z,r.verdict,r.near_actor==null?null:r.near_actor,np.length===2?np[0]:null,np.length===2?np[1]:null,r.near_d==null?null:r.near_d,(r.says||'').replace(/[\/|]/g,' ').replace(/!/g,'').replace(/\s+/g,' ').trim()]})}catch(e){console.log('no spot check')}
// doors with a place on one side only: the room is entered from 'from' at (x, z) but has no door back to it; cutscene rooms left out
const MISSDOOR=[];for(const a in ARR)for(const b in ARR[a]){const f=+a,d=+b;if(d<=0||d>=720)continue;const ea=W.EXITS[f]||[];if(ea.some(e=>e[2]===d&&e[0]!=null))continue;if(!(W.EXITS[d]||[]).some(e=>e[2]===f))continue;
 if(/Cutscene/.test((W.ROOMS[f]||'')+(W.ROOMS[d]||'')))continue;const p=ARR[a][b][0];MISSDOOR.push([f,d,p[0],p[1]])}
MISSDOOR.sort((x,y)=>x[0]-y[0]||x[1]-y[1]);
const XD={SPOTCHK:SPOTCHK,MISSDOOR:MISSDOOR,VIDX:VIDX,HPATH:W.HPATH||{},REVIEW:REVIEW,ARR:ARR,HSPLIT:W.HSPLIT||{},WPLACES:WP,ROOMS:W.ROOMS,AREAS:W.AREAS,CHAPTERS:W.CHAPTERS,HNOTE:W.HNOTE,HINTS:HINTS,HROOMS:HR,FAQ:FAQ,EXITS:W.EXITS,TRE:TRE,MARKS:W.MARKS};
fs.writeFileSync(__dirname+'/data.js','window.XD='+JSON.stringify(XD)+';\n');
console.log(Object.keys(XD).map(k=>k+':'+Object.keys(XD[k]).length).join(' '),fs.statSync(__dirname+'/data.js').size);
