/* CHD (MAME compressed hunks of data) reader for CD images, so the disc builder can read the player's .chd directly.
   Version 5 files with the cdlz (LZMA), cdzl (deflate) and cdzs-free codec set chdman uses for CDs. Only the sector data is
   decompressed (the subcode is skipped); a hunk is a run of 2448-byte frames (2352 bytes of sector + 96 of subcode).
   A hunk stored with the cdfl (FLAC) codec holds audio, which the builder never needs; reading one gives an error.
   Ported from libchdr's chd.c / huffman.c / bitstream.c and the LZMA SDK's LzmaSpec.cpp; inflate is written from RFC 1951. */
(function(G){
'use strict';

/* ---------- LZMA (raw stream, known output size) ---------- */
function lzma(src,lc,lp,pb,outLen){
 var out=new Uint8Array(outLen),pos=0,ip=0,Range=0xFFFFFFFF,Code=0;
 function nb(){return ip<src.length?src[ip++]:0}
 ip++;for(var i=0;i<4;i++)Code=((Code<<8)|nb())>>>0;   /* first byte is always 0 */
 function bit(p,k){var b=(Range>>>11)*p[k]>>>0,r;
  if(Code<b){p[k]+=(2048-p[k])>>5;Range=b;r=0}else{p[k]-=p[k]>>5;Code=(Code-b)>>>0;Range=(Range-b)>>>0;r=1}
  if(Range<0x1000000){Range=(Range<<8)>>>0;Code=((Code<<8)|nb())>>>0}return r}
 function direct(n){var res=0;do{Range=Range>>>1;var top=(Code-Range)>>>0;if(top>>>31){res=res<<1}else{Code=top;res=(res<<1)|1}
   if(Range<0x1000000){Range=(Range<<8)>>>0;Code=((Code<<8)|nb())>>>0}}while(--n);return res>>>0}
 function P(n){var a=new Uint16Array(n);a.fill(1024);return a}
 function tree(p,o,n){var m=1;for(var i=0;i<n;i++)m=(m<<1)+bit(p,o+m);return m-(1<<n)}
 function rtree(p,o,n){var m=1,s=0;for(var i=0;i<n;i++){var b=bit(p,o+m);m=(m<<1)+b;s|=b<<i}return s}
 function LenDec(){return {c:P(2),low:P(16<<3),mid:P(16<<3),high:P(256)}}
 function len(L,ps){if(!bit(L.c,0))return tree(L.low,ps<<3,3);if(!bit(L.c,1))return 8+tree(L.mid,ps<<3,3);return 16+tree(L.high,0,8)}
 var lit=P(0x300<<(lc+lp)),isMatch=P(12<<4),isRep=P(12),g0=P(12),g1=P(12),g2=P(12),rep0long=P(12<<4),slot=P(4<<6),posd=P(115),align=P(16),
  LD=LenDec(),RD=LenDec(),state=0,r0=0,r1=0,r2=0,r3=0,pbm=(1<<pb)-1,lpm=(1<<lp)-1;
 while(pos<outLen){var ps=pos&pbm;
  if(!bit(isMatch,(state<<4)+ps)){var prev=pos?out[pos-1]:0,base=0x300*(((pos&lpm)<<lc)+(prev>>(8-lc))),sym=1;
   if(state>=7){var mb=out[pos-r0-1];do{var mbit=(mb>>7)&1;mb<<=1;var b=bit(lit,base+((1+mbit)<<8)+sym);sym=(sym<<1)|b;if(mbit!==b)break}while(sym<0x100)}
   while(sym<0x100)sym=(sym<<1)|bit(lit,base+sym);
   out[pos++]=sym-0x100;state=state<4?0:state<10?state-3:state-6;continue}
  var L;
  if(bit(isRep,state)){
   if(!bit(g0,state)){if(!bit(rep0long,(state<<4)+ps)){state=state<7?9:11;out[pos]=out[pos-r0-1];pos++;continue}}
   else{var dist;if(!bit(g1,state))dist=r1;else{if(!bit(g2,state))dist=r2;else{dist=r3;r3=r2}r2=r1}r1=r0;r0=dist}
   L=len(RD,ps);state=state<7?8:11}
  else{r3=r2;r2=r1;r1=r0;L=len(LD,ps);state=state<7?7:10;
   var ls=L<3?L:3,s=tree(slot,ls<<6,6);
   if(s<4)r0=s;else{var nd=(s>>1)-1,d=((2|(s&1))<<nd)>>>0;
    if(s<14)d+=rtree(posd,d-s,nd);else{d+=direct(nd-4)<<4;d+=rtree(align,0,4)}r0=d>>>0}
   if(r0===0xFFFFFFFF)break}
  L+=2;if(L>outLen-pos)L=outLen-pos;
  for(var k=0;k<L;k++){out[pos]=out[pos-r0-1];pos++}}
 return out}

/* ---------- inflate (raw deflate) ---------- */
var LBASE=[3,4,5,6,7,8,9,10,11,13,15,17,19,23,27,31,35,43,51,59,67,83,99,115,131,163,195,227,258],LEXT=[0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,0],
 DBASE=[1,2,3,4,5,7,9,13,17,25,33,49,65,97,129,193,257,385,513,769,1025,1537,2049,3073,4097,6145,8193,12289,16385,24577],DEXT=[0,0,0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13],
 CLORD=[16,17,18,0,8,7,9,6,10,5,11,4,12,3,13,2,14,1,15];
function huff(lens){var cnt=new Uint16Array(16),offs=new Uint16Array(16),sym=new Uint16Array(lens.length);
 for(var i=0;i<lens.length;i++)cnt[lens[i]]++;cnt[0]=0;for(i=1;i<16;i++)offs[i]=offs[i-1]+cnt[i-1];
 for(i=0;i<lens.length;i++)if(lens[i])sym[offs[lens[i]]++]=i;return {cnt:cnt,sym:sym}}
function inflate(src,outLen){var out=new Uint8Array(outLen),op=0,ip=0,bb=0,bc=0;
 function bits(n){while(bc<n){bb|=(ip<src.length?src[ip++]:0)<<bc;bc+=8}var v=bb&((1<<n)-1);bb>>>=n;bc-=n;return v}
 function dec(h){var code=0,first=0,idx=0;for(var l=1;l<16;l++){code|=bits(1);var c=h.cnt[l];if(code-c<first)return h.sym[idx+(code-first)];idx+=c;first+=c;first<<=1;code<<=1}throw new Error('bad deflate data')}
 var fl=new Uint8Array(288),fd=new Uint8Array(30);for(var i=0;i<288;i++)fl[i]=i<144?8:i<256?9:i<280?7:8;fd.fill(5);var FL=huff(fl),FD=huff(fd),last=0;
 while(!last&&op<outLen){last=bits(1);var t=bits(2);
  if(t===0){bb=0;bc=0;var n=src[ip]|src[ip+1]<<8;ip+=4;for(i=0;i<n&&op<outLen;i++)out[op++]=src[ip++];continue}
  var lh,dh;if(t===1){lh=FL;dh=FD}
  else{var hl=bits(5)+257,hd=bits(5)+1,hc=bits(4)+4,cl=new Uint8Array(19);for(i=0;i<hc;i++)cl[CLORD[i]]=bits(3);var ch=huff(cl),ls=new Uint8Array(hl+hd);
   for(i=0;i<hl+hd;){var s=dec(ch);if(s<16)ls[i++]=s;else{var rep,v=0;if(s===16){v=ls[i-1];rep=3+bits(2)}else if(s===17)rep=3+bits(3);else rep=11+bits(7);while(rep--)ls[i++]=v}}
   lh=huff(ls.subarray(0,hl));dh=huff(ls.subarray(hl))}
  for(;;){var sy=dec(lh);if(sy<256){if(op<outLen)out[op++]=sy;continue}if(sy===256)break;sy-=257;var ln=LBASE[sy]+bits(LEXT[sy]),ds=dec(dh),dd=DBASE[ds]+bits(DEXT[ds]);
   for(i=0;i<ln&&op<outLen;i++){out[op]=out[op-dd];op++}}}
 return out}

/* ---------- CHD v5 ---------- */
function be(b,p,n){var v=0;for(var i=0;i<n;i++)v=v*256+b[p+i];return v}
function Bits(b){this.b=b;this.p=0}   /* MSB-first bit reader */
Bits.prototype.read=function(n){var v=0;for(var i=0;i<n;i++){var byte=this.b[this.p>>3]||0;v=v*2+((byte>>(7-(this.p&7)))&1);this.p++}return v};
Bits.prototype.peek=function(n){var p=this.p,v=this.read(n);this.p=p;return v};
/* the map's Huffman decoder (16 codes, 8 bits at most), tree stored run-length coded */
function hufMap(bs){var nb=new Uint8Array(16),cur=0;
 while(cur<16){var v=bs.read(4);if(v!==1)nb[cur++]=v;else{v=bs.read(4);if(v===1)nb[cur++]=1;else{var rep=bs.read(4)+3;while(rep--)nb[cur++]=v}}}
 var histo=new Uint32Array(33),start=0;for(var i=0;i<16;i++)histo[nb[i]]++;
 for(var cl=32;cl>0;cl--){var next=(start+histo[cl])>>1;histo[cl]=start;start=next}
 var code=new Uint32Array(16);for(i=0;i<16;i++)if(nb[i])code[i]=histo[nb[i]]++;
 var look=new Int32Array(256).fill(-1);for(i=0;i<16;i++)if(nb[i]){var sh=8-nb[i];for(var k=0;k<(1<<sh);k++)look[(code[i]<<sh)|k]=i|(nb[i]<<8)}
 return function(){var e=look[bs.peek(8)];if(e<0)throw new Error('bad CHD map');bs.read(e>>8);return e&255}}
/* open(reader(offset, length) -> Promise<Uint8Array>): {frames, sector(n) -> Promise<2352 bytes>} */
G.CHD={lzma:lzma,inflate:inflate,open:async function(reader){
 var h=await reader(0,124);if(String.fromCharCode.apply(null,h.subarray(0,8))!=='MComprHD')throw new Error('not a CHD file');
 var ver=be(h,12,4);if(ver!==5)throw new Error('Only version 5 CHD files can be read (this one is version '+ver+'). Re-make it with a current chdman.');
 var codecs=[];for(var i=0;i<4;i++)codecs.push(String.fromCharCode.apply(null,h.subarray(16+4*i,20+4*i)).replace(/\0/g,''));
 var logical=be(h,32,8),mapoff=be(h,40,8),hunkbytes=be(h,56,4),unit=be(h,60,4),hunks=Math.ceil(logical/hunkbytes);
 var mh=await reader(mapoff,16),mapbytes=be(mh,0,4),first=be(mh,4,6),lenbits=mh[12],selfbits=mh[13],parentbits=mh[14];
 var bs=new Bits(await reader(mapoff+16,mapbytes)),dec=hufMap(bs),type=new Uint8Array(hunks),last=0,rep=0;
 for(i=0;i<hunks;i++){if(rep>0){type[i]=last;rep--;continue}var v=dec();
  if(v===7){type[i]=last;rep=2+dec()}else if(v===8){type[i]=last;rep=2+16+(dec()<<4);rep+=dec()}else type[i]=last=v}
 var off=new Float64Array(hunks),len=new Uint32Array(hunks),cur=first,lastSelf=0,lastParent=0;
 for(i=0;i<hunks;i++){var t=type[i],o=cur,l=0;
  if(t<4){l=bs.read(lenbits);cur+=l;bs.read(16)}
  else if(t===4){l=hunkbytes;cur+=l;bs.read(16)}
  else if(t===5){o=lastSelf=bs.read(selfbits)}
  else if(t===6){o=lastParent=bs.read(parentbits)}
  else if(t===9||t===10){if(t===10)lastSelf++;type[i]=5;o=lastSelf}
  else if(t===11){type[i]=6;o=lastParent=Math.floor(i*hunkbytes/unit)}
  else if(t===12||t===13){if(t===13)lastParent+=hunkbytes/unit;type[i]=6;o=lastParent}
  off[i]=o;len[i]=l}
 var frames=hunkbytes/2448,cache={},order=[];
 async function hunk(n){if(cache[n])return cache[n];var t=type[n],data;
  if(t===5)data=await hunk(off[n]);
  else if(t===6)throw new Error('This CHD needs a parent file; use a stand-alone .chd.');
  else if(t===4)data=await reader(off[n],hunkbytes);
  else{var src=await reader(off[n],len[n]),c=codecs[t],eccb=(frames+7)>>3,cb=hunkbytes<65536?2:3,hb=eccb+cb,base=be(src,eccb,cb),sec;
   if(c==='cdlz')sec=lzma(src.subarray(hb,hb+base),3,0,2,frames*2352);
   else if(c==='cdzl')sec=inflate(src.subarray(hb,hb+base),frames*2352);
   else throw new Error('This CHD stores data with the '+c+' codec, which cannot be read here. Convert it to .bin/.cue.');
   data=new Uint8Array(hunkbytes);for(var f=0;f<frames;f++)data.set(sec.subarray(f*2352,f*2352+2352),f*2448)}   /* subcode left as zeros */
  cache[n]=data;order.push(n);if(order.length>64)delete cache[order.shift()];return data}
 return {frames:Math.floor(logical/2448),codecs:codecs,
  /* the 2352 bytes of sector n (data track 1 starts at frame 0) */
  sector:async function(n){var hb=await hunk(Math.floor(n/frames)),k=n%frames;return hb.subarray(k*2448,k*2448+2352)}}}};
if(typeof module!=='undefined')module.exports=G.CHD;
})(typeof window!=='undefined'?window:globalThis);
