/* NPCs from the room file (disc 1 file 606 + 2 x room) and its texture file: the room scripts and the NPC sprites (from the room viewer, v3).
   Sprite format and the script semantics follow the Noah decompile (github.com/yaz0r/Noah). */
(function(root){
var XN={};
function u16(b,p){return b[p]|b[p+1]<<8}
function s16(b,p){var v=b[p]|b[p+1]<<8;return v&0x8000?v-65536:v}
function u32(b,p){return (b[p]|b[p+1]<<8|b[p+2]<<16|b[p+3]<<24)>>>0}
function s8(v){return v&0x80?v-256:v}
function arch(b){var n=u32(b,0),o=[];for(var i=0;i<=n;i++)o.push(u32(b,4+4*i));var out=[];for(i=0;i<n;i++)out.push(b.subarray(o[i],o[i+1]));return out}
XN.block=function(h,k,XB){var a=u32(h,0x130+4*k),b=k<8?u32(h,0x134+4*k):h.length;if(!(a<b&&b<=h.length))return null;return XB.lzss(h.subarray(a,b))};
/* ---------- sprites ---------- */
function frames(s1){var n=s1[0],out=[];
 for(var i=0;i<n;i++){var o=u16(s1,2+2*i);try{var nt=s1[o],wide=nt&0x80;nt&=0x3f;var tiles=[];for(var k=0;k<nt;k++)tiles.push(u16(s1,o+4+2*k));
   var p=o+4+2*nt,pl=[];
   for(k=0;k<nt;k++){var t=tiles[k];while(s1[p]>=0xC0)p+=s1[p]>=0xE0?3:1;var fl=s1[p++],rot=null;if(fl&0x80)rot=s1[p++];
    var x,y;if(wide){x=s16(s1,p);y=s16(s1,p+2);p+=4}else{x=s8(s1[p]);y=s8(s1[p+1]);p+=2}
    pl.push([t,fl,x,y,rot])}
   out.push(pl)}catch(e){out.push(null)}}
 return out}
function pals(s2){var a=u16(s2,0),n=(s2.length-4)>>5,out=[];
 for(var i=0;i<n;i++){var p=[];for(var k=0;k<16;k++){var v=u16(s2,4+32*i+2*k);p.push([(v&31)*255/31|0,((v>>5)&31)*255/31|0,((v>>10)&31)*255/31|0,(k===0||v===0)?0:255])}out.push(p)}
 return {a:Math.max(a,1),P:out}}
/* room sprite n, frame fi -> {w,h,x0,y0,rgba} ; pixels from VRAM (VR = XB.vram of the texture file plus the room's own sheets) */
XN.sprites=function(h,XB){var b=XN.block(h,3,XB);if(!b||b.length<8)return [];var n=u32(b,0);if(n<1||n>64)return [];
 var out=[];for(var i=0;i<n;i++){var o=u32(b,4+4*i);try{var A=arch(b.subarray(o));out.push({A:A,fr:frames(A[1]),pal:pals(A[2]),vx:u16(h,8*i),vy:u16(h,8*i+2),m6:u16(h,8*i+6)})}catch(e){out.push(null)}}
 return out};
/* the room's own NPC sheets (block 4) go into VRAM at each slot's place when the slot says so (m6 = 0) */
XN.uploadSheets=function(h,VR,XB){var b=XN.block(h,4,XB);if(!b||b.length<8)return;var n=u32(b,0);
 for(var i=0;i<n&&i<32;i++){if(u16(h,8*i+6)!==0)continue;var x=u16(h,8*i),y=u16(h,8*i+2),eo=u32(b,4+4*i);if(eo+4>b.length)continue;var e=b.subarray(eo),m=u32(e,0),xo=0;
  if(!(m>=1&&m<=64))continue;   /* v2.0.0.17: room 164 (Gebler airship) has a sheet in another layout; its count read as ~3.7 billion and the loop never ended */
  for(var k=0;k<m;k++){var so=u32(e,4+4*k);if(so+4>e.length)break;var d=e.subarray(so),w=u16(d,0),hh=u16(d,2);if(w>1024||hh>512||4+2*w*hh>d.length)continue;
   for(var j=0;j<hh&&y+j<512;j++)for(var q=0;q<w&&x+xo+q<1024;q++)VR[(y+j)*1024+x+xo+q]=u16(d,4+2*(j*w+q));xo+=0x40}}};
XN.frame=function(sp,VR,fi,variant){if(!sp)return null;var pl=sp.fr[fi||0];if(!pl)return null;var s1=sp.A[1],a=sp.pal.a,P=sp.pal.P,px={},x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;
 for(var k=pl.length-1;k>=0;k--){var t=pl[k][0],fl=pl[k][1],x=pl[k][2],y=pl[k][3];if(t+5>s1.length)continue;
  var tf=s1[t],u=s1[t+1],v=s1[t+2],w=s1[t+3],hh=s1[t+4],sheet=(tf>>1)&7,pi=(variant||0)*a+((fl&15)<a?fl&15:0),pal=P[pi<P.length?pi:0]||P[0];if(!pal)continue;
  var bx=sp.vx+sheet*64,by=sp.vy;
  for(var yy=0;yy<hh;yy++)for(var xx=0;xx<w;xx++){var sx=u+xx,sy=v+yy,wd=VR[((by+sy)&511)*1024+((bx+(sx>>2))&1023)],c=(wd>>((sx&3)*4))&15;if(!c||!pal[c][3])continue;
   var dx=fl&0x10?w-1-xx:xx,dy=fl&0x20?hh-1-yy:yy,X=x+dx,Y=y+dy;px[X+','+Y]=pal[c];if(X<x0)x0=X;if(Y<y0)y0=Y;if(X>x1)x1=X;if(Y>y1)y1=Y}}
 if(x1<x0)return null;var W=x1-x0+1,H=y1-y0+1,rgba=new Uint8ClampedArray(W*H*4);
 for(var key in px){var c2=px[key],q2=key.split(','),i2=((+q2[1]-y0)*W+(+q2[0]-x0))*4;rgba[i2]=c2[0];rgba[i2+1]=c2[1];rgba[i2+2]=c2[2];rgba[i2+3]=255}
 return {w:W,h:H,x0:x0,y0:y0,rgba:rgba}};

/* ---------- room script: who is in the room at a given story step ----------
   Runs every entity's set-up routine (script 0) the way the game does when a room loads (Noah: startAllEntityScripts):
   entities in order, each until it stops (00) or idles. Story step = variable 0; every other variable and flag starts at 0
   unless the caller sets it. Branches, variable writes and the set-up commands are followed; anything else is stepped over by
   its length. An unknown command ends that entity's run (noted as 'stopped at XX'). */
var LEN={"02":8,"03":4,"05":3,"06":5,"07":3,"08":3,"09":3,"0A":4,"0B":3,"0C":1,"0E":1,"0F":1,"13":1,"14":1,"15":1,"16":3,"17":18,"18":5,"19":6,"1A":2,"1B":7,"1C":4,"1D":7,"1E":1,"1F":2,"20":3,"21":3,"22":1,"23":1,"24":2,"25":2,"26":3,"27":2,"28":2,"29":2,"2A":1,"2B":1,"2C":2,"2D":8,"2E":3,"2F":3,"30":3,"31":5,"32":5,"33":1,"34":5,"35":6,"36":3,"37":3,"38":6,"39":6,"3A":6,"3B":6,"3C":3,"3D":3,"3E":6,"3F":6,"40":6,"41":5,"42":5,"43":3,"44":5,"45":8,"46":1,"47":6,"48":7,"49":8,"4A":6,"4B":8,"4C":8,"4D":10,"4E":6,"4F":8,"50":8,"51":10,"52":2,"53":4,"54":5,"55":7,"56":10,"58":4,"59":1,"5A":1,"5D":2,"5E":1,"5F":2,"60":1,"61":8,"62":2,"63":8,"64":1,"65":8,"66":2,"67":4,"68":4,"69":3,"6A":3,"6B":3,"6C":3,"6D":8,"6E":8,"6F":2,"70":2,"71":3,"72":3,"73":8,"74":3,"75":3,"76":1,"77":1,"78":4,"79":1,"7A":1,"7B":4,"7C":4,"7D":4,"7E":4,"7F":3,"80":5,"81":5,"82":5,"83":5,"84":5,"85":5,"86":5,"87":3,"88":3,"89":6,"8A":4,"8B":5,"8C":3,"8D":3,"8E":7,"8F":3,"90":3,"91":4,"93":3,"94":5,"95":2,"96":1,"97":3,"98":5,"99":1,"9A":3,"9B":5,"9C":1,"9D":4,"9E":1,"9F":1,"A0":7,"A1":3,"A2":2,"A3":8,"A4":4,"A5":3,"A7":1,"A8":5,"A9":2,"AA":2,"AB":1,"AC":4,"AD":7,"AE":7,"AF":4,"B0":4,"B1":4,"B2":2,"B3":3,"B4":3,"B5":5,"B6":5,"B7":1,"B8":1,"B9":4,"BA":2,"BB":2,"BC":1,"BD":3,"BE":3,"BF":3,"C0":3,"C1":3,"C2":3,"C3":1,"C4":2,"C5":2,"C6":1,"C7":3,"C8":3,"C9":4,"CA":8,"CB":4,"CC":4,"CD":1,"CE":1,"CF":5,"D0":11,"D2":4,"D3":4,"D5":3,"D6":3,"D7":3,"D8":3,"D9":3,"DA":17,"DB":5,"DC":5,"DD":6,"DE":6,"DF":6,"E0":7,"E1":14,"E2":5,"E3":5,"E5":17,"E6":9,"E7":7,"E8":7,"E9":7,"EA":6,"EB":20,"EC":15,"ED":8,"EE":3,"EF":3,"F0":7,"F1":11,"F2":9,"F3":7,"F4":2,"F5":4,"F6":2,"F7":5,"F8":4,"F9":2,"FA":5,"FB":5,"FD":1,"FE":2,"FF":1,"FE01":2,"FE02":5,"FE03":4,"FE04":4,"FE05":7,"FE06":7,"FE07":3,"FE08":8,"FE09":4,"FE0A":4,"FE0B":4,"FE0C":14,"FE0D":4,"FE0E":6,"FE0F":7,"FE10":6,"FE11":7,"FE12":4,"FE13":6,"FE14":6,"FE15":6,"FE16":2,"FE17":4,"FE19":3,"FE1A":2,"FE1B":6,"FE1C":9,"FE1D":9,"FE1E":3,"FE1F":2,"FE20":3,"FE21":4,"FE22":4,"FE23":21,"FE24":2,"FE25":3,"FE26":16,"FE27":3,"FE28":4,"FE29":4,"FE2A":4,"FE2B":4,"FE2C":4,"FE2D":4,"FE2E":4,"FE2F":4,"FE30":6,"FE31":6,"FE32":6,"FE33":6,"FE34":7,"FE35":7,"FE36":7,"FE37":7,"FE38":6,"FE39":4,"FE3A":4,"FE3B":4,"FE3C":6,"FE3D":11,"FE3E":11,"FE3F":8,"FE40":8,"FE41":4,"FE42":4,"FE43":2,"FE44":2,"FE45":3,"FE46":3,"FE47":4,"FE48":9,"FE49":2,"FE4A":4,"FE4B":2,"FE4C":3,"FE4D":3,"FE4E":2,"FE4F":2,"FE50":2,"FE51":2,"FE52":2,"FE53":2,"FE54":2,"FE55":2,"FE56":4,"FE57":2,"FE58":4,"FE59":4,"FE5A":4,"FE5B":4,"FE5C":5,"FE5D":8,"FE5E":4,"FE5F":9,"FE60":10,"FE61":2,"FE62":6,"FE63":6,"FE64":4,"FE65":6,"FE66":10,"FE67":20,"FE68":7,"FE69":6,"FE6A":4,"FE6B":6,"FE6C":2,"FE6D":2,"FE6E":5,"FE6F":9,"FE70":4,"FE71":4,"FE72":11,"FE73":13,"FE74":4,"FE75":5,"FE76":17,"FE77":3,"FE7F":2,"FE80":16,"FE81":9,"FE82":26,"FE83":4,"FE84":10,"FE85":4,"FE86":3,"FE87":2,"FE88":19,"FE89":12,"FE8A":4,"FE8B":4,"FE8C":8,"FE8D":4,"FE8E":6,"FE8F":9,"FE90":10,"FE91":15,"FE92":15,"FE93":12,"FE94":11,"FE95":15,"FE96":2,"FE97":3,"FE98":4,"FE99":3,"FE9A":10,"FE9B":4,"FE9C":4,"FE9D":4,"FE9E":10,"FE9F":5,"FEA0":13,"FEA1":6,"FEA2":2,"FEA3":3,"FEA4":2,"FEA5":8,"FEA6":6,"FEA7":10,"FEA8":8,"FEA9":8,"FEAA":3,"FEAB":5,"FEAC":5,"FEAD":5,"FEAE":8,"FEAF":19,"FEB1":2,"FEB2":5,"FEB3":5,"FEB4":5,"FEB5":2,"FEB6":3,"FEB7":4,"FEB8":5,"FEB9":10,"FEBA":11,"FEBB":4,"FEBC":5,"FEBD":8,"FEBE":2,"FEBF":14,"FEC0":4,"FEC1":8,"FEC2":10,"FEC3":2,"FEC4":3,"FEC5":6,"FEC7":6,"FEC8":19,"FEC9":19,"FECA":3,"FECB":2,"FECC":2,"FECD":4,"FECE":4,"FECF":6,"FED0":6,"FED1":2,"FED2":4,"FED3":18,"FED4":11,"FED5":6,"FED6":6,"FED7":7,"FED8":3,"FED9":3,"FEDA":2,"FEDB":4,"FEDC":6,"FEDE":6,"FEDF":4,"FEE0":3,"FEE1":6,"FEE2":2,"00":1,"01":3,"04":1,"0D":1,"92":1,"5B":1,"A6":1,"D1":1,"E4":1,"FC":6,"D4":6,"12":4,"5C":3,"57":13};
/* commands that make the per-frame routine (script 1) wait or walk: the look a room has on arrival is what comes before them */
var BLOCK={0x26:1,0x4A:1,0x4B:1,0x47:1,0x53:1,0x57:1,0x59:1,0x5E:1,0x9C:1,0xEF:1,0xA2:1,0x0C:1,0x5B:1,0xD2:1,0xD4:1,0xFC:1,0xF5:1,0x07:1,0x08:1,0x09:1};
var DIR=[0xC00,0xE00,0x000,0x200,0x400,0x600,0x800,0xA00],DIR3=[0xC00,0x400,0x800,0x000,0xA00,0xE00,0x600,0x200];
XN.script=function(h,XB){var s=XN.block(h,5,XB);if(!s||s.length<0x88)return null;var n=u32(s,0x80);if(!(n>0&&n<400&&0x84+n*64<=s.length))return null;
 var ent=[];for(var i=0;i<n;i++){var e=[];for(var k=0;k<32;k++)e.push(u16(s,0x84+i*64+2*k));ent.push(e)}
 return {sign:s.subarray(0,0x80),n:n,ent:ent,code:s.subarray(0x84+n*64)}};
XN.entries=function(sc){var c=sc.code,out=[];if(c[0]!==0xFF)return out;
 for(var i=0;i<64;i++){var p=7*i+1;if(p+7>c.length)break;var x=s16(c,p),z=s16(c,p+2),l=c[p+4],cam=c[p+5],fc=c[p+6];
  if(i>0&&x===0&&z===0&&l===0)break;if(l>3)break;out.push({x:x,z:z,layer:l,cam:cam,facing:fc===0xFF?null:((fc-2)&7)<<9})}
 return out};
/* every story-step value the room's scripts compare against (84/85/86 anywhere in the code) - the steps worth trying */
XN.stepTests=function(sc){var c=sc.code,set={},starts=[];sc.ent.forEach(function(e){e.forEach(function(p){starts.push(p)})});
 starts=starts.filter(function(v,i,a){return a.indexOf(v)===i}).sort(function(a,b){return a-b});
 starts.forEach(function(p){var guard=0;while(p<c.length&&guard++<4000){var k=c[p]===0xFE?'FE'+hx(c[p+1]):hx(c[p]),L=k==='00'?1:LEN[k];if(!L)break;
   if((k==='84'||k==='85'||k==='86')){var v=u16(c,p+1);if(v&0x8000){v&=0x7FFF;set[v]=1;if(k==='84')set[v]=1;if(k==='85')set[v+1]=1}}
   if(k==='00'||k==='01'||k==='0D')break;p+=L}});
 return Object.keys(set).map(Number).sort(function(a,b){return a-b})};
function hx(v){return (v<16?'0':'')+v.toString(16).toUpperCase()}
XN.head=function(h){var n=u32(h,0x18C)&0xFFFF,out=[];for(var i=0;i<Math.min(n,2000);i++){var o=0x190+16*i;out.push({flags:u16(h,o),rx:s16(h,o+2),ry:s16(h,o+4),rz:s16(h,o+6),x:s16(h,o+8),y:s16(h,o+10),z:s16(h,o+12),model:u16(h,o+14)})}return out};
XN.run=function(sc,opt){opt=opt||{};var HD=opt.head||[];var c=sc.code,V=Object.assign({},opt.vars||{}),reads={},party=opt.party||[0];V[0]=opt.step|0;
 function gv(v){v&=0xFFFF;if(v>=0x8000)return v&0x7FFF;if(v!==0&&!(v in reads))reads[v]=V[v]|0;var x=V[v]|0;var signed=!(sc.sign[v>>6<<2|0]!==undefined&&((u32(sc.sign,(v>>6)*4)>>>((v>>1)&31))&1));return signed?((x<<16)>>16):(x&0xFFFF)}
 function rawv(v){if(v!==0&&!(v in reads))reads[v]=V[v]|0;return V[v]|0}
 function setv(v,x){V[v]=x&0xFFFF}
 function lit(p,flag,ctl){return ctl&flag?s16(c,p):gv(u16(c,p))}
 var E=sc.ent.map(function(e,i){var hd=HD[i]||{};var isModel=hd.flags!==undefined&&!(hd.flags&0x40);return {i:i,kind:isModel?'model':'none',model:isModel?hd.model:null,x:hd.x!=null?hd.x:null,z:hd.z!=null?hd.z:null,y:hd.y!=null?hd.y:null,fixedY:isModel,layer:0,rot:null,hidden:!isModel,deleted:false,stop:'',tests:[],talk:e[2]!==undefined&&c[e[2]]!==0&&e[2]!==e[0]}}),entries=XN.entries(sc);
 var SAY=null;
 function who(b,self){if(b===0xFB)return self;if(b>=0xFD)return -1;return b<E.length?b:-1}
 function exec(i,pc,upd){var me=E[i],stack=[],steps=0;
  while(true){if(upd&&BLOCK[c[pc]]){break}if(++steps>3000){me.stop='loop';break}if(pc>=c.length){me.stop='end of code';break}
   var op=c[pc],key=op===0xFE?'FE'+hx(c[pc+1]):hx(op),q=op===0xFE?pc+1:pc,L=LEN[key];
   if(op===0x00){me.stop='';break}
   if(op===0x01){var t=u16(c,pc+1);if(upd&&t<=pc)break;if(t<=pc&&steps>400){me.stop='loop';break}pc=t;continue}
   if(op===0x02){var ctl=c[pc+5],a,b;
    if((ctl&0xF0)===0xC0){a=s16(c,pc+1);b=s16(c,pc+3)}else if((ctl&0xF0)===0x80){a=s16(c,pc+1);b=gv(u16(c,pc+3))}else if((ctl&0xF0)===0x40){a=gv(u16(c,pc+1));b=s16(c,pc+3)}else{a=gv(u16(c,pc+1));b=gv(u16(c,pc+3))}
    var tt=ctl&15,r=tt===0?a===b:tt===1||tt===7?a!==b:tt===2?b<a:tt===3?a<b:tt===4?b<=a:tt===5?a<=b:tt===6||tt===9?(a&b)!==0:tt===8?(a|b)!==0:tt===10?(~a&b)!==0:false;
    var va=u16(c,pc+1);if((ctl&0x80)===0&&va===0||(ctl&0x40)===0&&u16(c,pc+3)===0)me.tests.push(['step',['=','!=','>','<','>=','<=','&','!=','|','&','~&'][tt]+' '+((ctl&0x40)?b:a),r]);
    else if((ctl&0x80)===0)me.tests.push(['var',hx(va>>8)+hx(va&255)+' '+['=','!=','>','<','>=','<=','&','!=','|','&','~&'][tt]+' '+b,r,va]);
    pc=r?pc+8:u16(c,pc+6);continue}
   if(op===0x84||op===0x85||op===0x86){var v=gv(u16(c,pc+1)),st=V[0]|0,ok=op===0x84?st<v:op===0x85?st>v:st===v;me.tests.push(['step',(op===0x84?'< ':op===0x85?'> ':'= ')+v,ok]);pc=ok?pc+5:u16(c,pc+3);continue}
   if(op===0xFB){var fl=u16(c,pc+1),fv=fl>>4,bit=fl&15,set=((rawv(fv)>>bit)&1)===1;me.tests.push(['flag',hx(fv>>8)+hx(fv&255)+'.'+bit,set,fv,bit]);pc=set?pc+5:u16(c,pc+3);continue}
   if(op===0x91){var ch=c[pc+1],inp=party.indexOf(ch)>=0;me.tests.push(['party','member '+ch,inp]);pc=inp?pc+4:u16(c,pc+2);continue}
   if(op===0xB9){var ch2=c[pc+1],av=party.indexOf(ch2)>=0;me.tests.push(['party','available '+ch2,av]);pc=av?pc+4:u16(c,pc+2);continue}
   if(op===0x05){if(stack.length>=8){me.stop='stack';break}stack.push(pc+3);pc=u16(c,pc+1);continue}
   if(op===0x0D){if(!stack.length){me.stop='';break}pc=stack.pop();continue}
   if(op===0x0C){me.stop='';break}   /* idles from here on */
   if(!L){me.stop='stopped at '+key;break}
   if(SAY){if(key==='D2')SAY.push(c[pc+1]|c[pc+2]<<8);else if(key==='D4'||key==='FC')SAY.push(c[pc+2]|c[pc+3]<<8)}
   switch(key){
    case '0B':me.kind='npc';var sp=u16(c,pc+1);me.sprite=sp&0x8000?sp&0x7FFF:gv(sp);me.variant=0;me.hidden=false;break;
    case 'BC':if(me.kind==='none')me.kind='script';break;
    case 'FE15':me.kind='npc';var sp2=u16(c,q+1);me.sprite=sp2&0x8000?sp2&0x7FFF:gv(sp2);var vr=u16(c,q+3);me.variant=vr&0x8000?vr&0x7FFF:gv(vr);me.hidden=false;break;
    case '16':me.kind='pc';me.hidden=false;me.slot=c[pc+1];var en=entries[opt.entry|0]||entries[0];if(en){me.x=en.x;me.z=en.z;me.layer=en.layer;me.y=null;if(en.facing!=null)me.rot=en.facing}break;
    case '19':var c19=c[pc+5];me.x=lit(pc+1,0x80,c19);me.z=lit(pc+3,0x40,c19);me.y=null;break;
    case '1A':me.layer=c[pc+1];break;
    case '1D':me.x=s16(c,pc+1);me.z=s16(c,pc+3);me.y=s16(c,pc+5);me.fixedY=true;break;
    case 'FE1C':var cc=c[q+7];me.x=lit(q+1,0x80,cc);me.z=lit(q+3,0x40,cc);me.y=lit(q+5,0x20,cc);me.fixedY=true;break;
    case '22':me.hidden=false;break;
    case '23':me.hidden=true;break;
    case '24':var w=who(c[pc+1],i);if(w>=0&&!E[w].deleted)E[w].hidden=false;break;
    case '25':w=who(c[pc+1],i);if(w>=0)E[w].hidden=true;break;
    case '29':w=who(c[pc+1],i);if(w>=0){E[w].deleted=true;E[w].hidden=true}break;
    case '5F':me.rot=DIR3[c[pc+1]&7];break;
    case '69':case '6A':me.rot=DIR[gv(u16(c,pc+1))&7];break;
    case '35':setv(u16(c,pc+1),lit(pc+3,0x40,c[pc+5]));break;
    case '36':setv(u16(c,pc+1),1);break;
    case '37':setv(u16(c,pc+1),0);break;
    case '38':setv(u16(c,pc+1),rawv(u16(c,pc+1))+lit(pc+3,0x40,c[pc+5]));break;
    case '39':setv(u16(c,pc+1),rawv(u16(c,pc+1))-lit(pc+3,0x40,c[pc+5]));break;
    case '3A':setv(u16(c,pc+1),rawv(u16(c,pc+1))|1<<(lit(pc+3,0x40,c[pc+5])&31));break;
    case '3B':setv(u16(c,pc+1),rawv(u16(c,pc+1))&~(1<<(lit(pc+3,0x40,c[pc+5])&31)));break;
    case '3C':setv(u16(c,pc+1),rawv(u16(c,pc+1))+1);break;
    case '3D':setv(u16(c,pc+1),rawv(u16(c,pc+1))-1);break;
    case '87':V[0]=gv(u16(c,pc+1));break;
    case 'FE0A':var f2=u16(c,q+1);setv(f2>>4,rawv(f2>>4)|1<<(f2&15));break;
    case 'FE0B':f2=u16(c,q+1);setv(f2>>4,rawv(f2>>4)&~(1<<(f2&15)));break;
   }
   pc+=L}
  }
 for(var i=0;i<E.length;i++)exec(i,sc.ent[i][0],false);
 if(opt.update!==false)for(i=0;i<E.length;i++){var u1=sc.ent[i][1];if(u1&&u1!==sc.ent[i][0]&&c[u1]!==0){var pre=E[i].tests.length,st0=E[i].stop;exec(i,u1,true);E[i].stop=st0;for(var k=pre;k<E[i].tests.length;k++)E[i].tests[k][5]='update'}}
 /* what a person says: run their talk routine (script 2) after the room has set up, once for the first talk and again for a second
    one (a talk often sets a flag that changes the next). Choices are not asked: a test on the answer takes the "no" path. */
 var talk=null;if(opt.talk!=null&&E[opt.talk]&&sc.ent[opt.talk][2]!==undefined){var ti=opt.talk,me=E[ti],keep={tests:me.tests,stop:me.stop},vis=E.map(function(e){return [e.hidden,e.deleted]});talk={first:null,again:null};
  ['first','again'].forEach(function(k){SAY=[];me.tests=[];me.stop='';exec(ti,sc.ent[ti][2],false);talk[k]={say:SAY,tests:me.tests,stop:me.stop}});
  SAY=null;me.tests=keep.tests;me.stop=keep.stop;E.forEach(function(e,j){e.hidden=vis[j][0];e.deleted=vis[j][1]})}
 return {E:E,reads:reads,entries:entries,step:opt.step|0,talk:talk}};
/* the room's text (header block 7): u32 count, u16 offsets, then each message. Byte codes from the game's font: 0x01 new line, 0x02 next
   box, 0x10 space, 0x16-0x1F digits, 0x20-0x39 A-Z, 0x3D-0x56 a-z, 0x0F + code is a control (02, 05 and 01 take one more byte: waits,
   colours), 0x58 starts the spoken part after the speaker's name. Codes not worked out are left out. */
var TXT={0x10:' ',0x11:':',0x12:',',0x13:'-',0x14:'.',0x15:'~',0x3C:'&',0x57:'!',0x5A:'%',0x5B:'"',0x5C:"'",0x5D:'(',0x5E:')',0x5F:':',0x60:'?'};
XN.lines=function(h,XB){var d=XN.block(h,7,XB);if(!d||d.length<8)return [];var n=u32(d,0);if(n<1||n>4000||4+2*n>d.length)return [];var out=[];
 for(var i=0;i<n;i++){var a=u16(d,4+2*i),b=i+1<n?u16(d,6+2*i):d.length,boxes=[],lines=[],cur='',spk=null;if(b<a||b>d.length)b=d.length;
  for(var j=a;j<b;j++){var ch=d[j];if(ch===0)break;
   if(ch===0x0F){var k=d[j+1];j+=(k===1||k===2||k===5)?2:1;continue}
   if(ch===0x01){lines.push(cur);cur='';continue}
   if(ch===0x02){lines.push(cur);boxes.push(lines);lines=[];cur='';continue}
   if(ch===0x58){if(spk===null&&boxes.length===0&&lines.length===1&&!cur){spk=lines.pop()}continue}
   if(ch>=0x20&&ch<=0x39)cur+=String.fromCharCode(65+ch-0x20);else if(ch>=0x3D&&ch<=0x56)cur+=String.fromCharCode(97+ch-0x3D);else if(ch>=0x16&&ch<=0x1F)cur+=String(ch-0x16);else if(TXT[ch])cur+=TXT[ch]}
  if(cur||lines.length)lines.push(cur);if(lines.length)boxes.push(lines);
  boxes=boxes.map(function(L){return L.map(function(x){return x.replace(/\s+$/,'')}).filter(function(x,q,A){return x||q<A.length-1})}).filter(function(L){return L.join('').trim()});
  out.push({spk:spk&&spk.trim()||null,boxes:boxes})}
 return out};
/* the standing frame the sprite shows at a given angle (Noah setSpriteActorAngle): animation 0, one frame stream per direction;
   angle = the actor's facing relative to the camera, 4096 a turn. Returns [frame index, mirrored] */
XN.dirFrame=function(sp,angle){var a=sp.A[0];if(!a||a.length<8)return [0,false];var an=u16(a,2);if(an+8>a.length)return [0,false];var mode=u16(a,an)&3,d,mir=false;
 angle&=0xFFF;
 if(mode===2){d=((angle+0x500)>>9)&7;if(d>4){d=(d-5)^3;mir=true}}
 else if(mode===1){d=((angle+0x600)>>10)&3;if(d>=3){d=1;mir=true}}
 else{d=0;mir=((angle+0x400)&0xFFF)>=0x801}
 var p=an+4+2*d;if(p+2>a.length)return [0,mir];var q=p+u16(a,p);var fb=q<a.length?a[q]:0;
 var fi=fb>0&&fb<0x80?fb-1:0;if(fi>=sp.fr.length)fi=0;return [fi,mir]};
root.XN=XN;if(typeof module!=='undefined')module.exports=XN;
})(typeof window!=='undefined'?window:globalThis);
