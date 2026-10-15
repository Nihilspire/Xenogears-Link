# Room exits read off the room scripts: [x, z, destination room] per room. Only exits with a known place and a believable destination:
#  - a room change guarded by a trigger-zone test (place = centre of the zone), or
#  - a room change in the talk / touch routine of an actor that was given a position, when the destination room also leads back here
#    (which doors do and story scenes do not) or the actor is an invisible trigger.
import json,exits,collections,sys
RAW={int(k):v for k,v in json.load(open('exits_raw.json')).items()}
AUD={r['f']:r for r in json.load(open('/home/claude/xg/audit/audit.json'))}
def near(f,p):
    b=AUD.get(f,{}).get('bbox')
    if not b: return True
    mg=max(b[2]-b[0],b[3]-b[1])*0.15+150
    return b[0]-mg<=p[0]<=b[2]+mg and b[1]-mg<=p[1]<=b[3]+mg
# A walk-off zone usually covers the last stretch of a path, so its centre lies short of where the path ends. The door is put
# instead on the outline of the walkable area inside the zone, at the point farthest from the middle of the walkable area
# (the path end, or the wall the exit is in). Walkable area = the app's map file for the room (dtest/maps/<room>.bin, all layers).
import struct,os
MAPS='/home/claude/xg/dtest/maps/%d.bin'
_mc={}
def mapinfo(f):
    if f in _mc: return _mc[f]
    r=None
    if os.path.exists(MAPS%f):
        b=open(MAPS%f,'rb').read();nv,nt=struct.unpack_from('<HH',b);V=[struct.unpack_from('<hh',b,4+4*i) for i in range(nv)]
        bnd=set();walkv=set();o=4+4*nv
        for i in range(nt):
            a,b_,c,fl=struct.unpack_from('<3HB',b,o+7*i);t=(a,b_,c)
            if fl&3==2: continue
            walkv.update(t)
            for k in range(3):
                if fl>>(2+k)&1: bnd.add(t[k]);bnd.add(t[(k+1)%3])
        if walkv:
            cx=sum(V[i][0] for i in walkv)/len(walkv);cz=sum(V[i][1] for i in walkv)/len(walkv);r=(V,bnd,cx,cz)
    _mc[f]=r;return r
def inquad(p,q):
    s=0
    for i in range(4):
        a,b=q[i],q[(i+1)%4];c=(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
        if c: 
            if s and (c>0)!=(s>0): return False
            s=c
    return True
def snap(f,q):
    m=mapinfo(f)
    if not m: return None
    V,bnd,cx,cz=m;best=None
    for i in bnd:
        if inquad(V[i],q):
            d=(V[i][0]-cx)**2+(V[i][1]-cz)**2
            if best is None or d>best[0]: best=(d,i)
    return [V[best[1]][0],V[best[1]][1]] if best else None
links=collections.defaultdict(set)
for f,s in RAW.items():
    for x in s:
        if x['dest']<730 and x['dest']!=f: links[f].add(x['dest'])
out={};st=collections.Counter()
for f,s in sorted(RAW.items()):
    Z=None;got=[]
    for x in s:
        d=x['dest']
        if d>=730 or d==f: continue
        back=f in links.get(d,())
        if x['zone'] is not None:
            if Z is None: Z=exits.zones(f)
            if x['zone']>=len(Z): st['zone missing']+=1;continue
            q=Z[x['zone']];p=snap(f,q) or [round(sum(c[0] for c in q)/4),round(sum(c[1] for c in q)/4)];kind='zone'
        elif x['pos'] and x['r'] in(2,3) and (back or x.get('door') or (x['bc'] and not x['spr'])):
            p=x['pos'];kind='door'
        else: st['skipped']+=1;continue
        if not near(f,p): st['off the map']+=1;continue
        if any(abs(p[0]-g[0])+abs(p[1]-g[1])<40 and g[2]==d for g in got): continue
        got.append([p[0],p[1],d]);st[kind]+=1;st['with way back' if back else 'one way']+=1
    if got: out[f]=got
# Room 238 ("Debug Map") is a Nortune dispatcher, not a place: its actor 2 routine 1 reads the entrance number and story flags and sends
# the party on (entrance 0 + var 0x246 bit 11, set by the A Block Wildcat door: Wildcat Bar 205; entrance 3: A Block 195; entrance 1 or 2:
# Babel rooms 412 / 411). Exits into it are shown with the real destination (v1.92, Jack saw "Debug Map" on the Wildcat door).
VIA238={(195,864,-29):205,(205,-264,84):195,(411,124,-255):412}
def resolve238(out):
    for f in list(out):
        L=[]
        for x,z,d in out[f]:
            if d==238:   # matched within 60 units: the app's copy has the door snapped onto the walkable edge
                d=next((v for (g,a,b),v in VIA238.items() if g==int(f) and abs(a-x)+abs(b-z)<60),None)
                if d is None: continue
            L.append([x,z,d])
        out[f]=L
resolve238(out)
print(dict(st),'rooms with exits',len(out),'exits',sum(len(v) for v in out.values()))
json.dump(out,open('exits.json','w'),separators=(',',':'))
if len(sys.argv)>1:
    open('/home/claude/xg/data/exits.js','w').write('/* Room exits read off the room scripts on the disc: room -> [x, z, destination room]. Places are trigger zones or door actors. */\nwindow.EXITS='+json.dumps(out,separators=(',',':'))+';\n')
for f in (1,14,23,24,29,58,65,102,290,406): print(f,out.get(f))
