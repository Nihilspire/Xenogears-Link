"""Helpers for writing story hints from the room scripts (load with: import sys; sys.path.insert(0,'/home/claude/xg/fld'); from hintkit import *).
   rn(f)            room number -> 'f Area / Room name'
   find_room(text)  rooms whose name or area contains text
   exits(f)         [(x, z, destination room or -1 world map)]  door / trigger positions in room f
   actors(f)        [(actor, (x, z) or None, first lines said in its talk routine)]  who stands where in room f
   lines(f,a,r)     what actor a says in routine r of room f (the game's own text, in order)
   step_tests(f)    [(actor, routine, op, n)]  where room f's scripts test the story step (op '<', '>', '==')
   world(room)      [(x, z)] world-map spots (world units) whose place leads into that room
   zone(f,i)        centre of trigger zone i of room f
   ROUTINES(f)      [(actor, routine)] all routines of room f
Coordinates are room units, the same ones the hint sheet uses for spots."""
import sys,json,re,collections
sys.path.insert(0,'/home/claude/xg/fld')
_g={}
exec(open('/home/claude/xg/fld/splits.py').read().split("res={}")[0],_g)
RT=_g['RT']; say=_g['say']
import exits as _EX
_ns={}; exec(open('/home/claude/xg/fld/mktre.py').read().split('OUT={}')[0],_ns)
ROOMS=json.loads(re.search(r'window\.ROOMS=(\{.*?\});',open('/home/claude/xg/v/www/rooms.js').read(),re.S).group(1))
AREAS=json.loads(re.search(r'window\.AREAS=(\[.*?\]);',open('/home/claude/xg/v/www/areas.js').read(),re.S).group(1))
XT=json.load(open('/home/claude/xg/fld/exits.json'))
WL=json.load(open('/home/claude/xg/fld/worldloc_raw.json'))
def area(f):
    for a in AREAS:
        if a[0]<=f<=a[1]: return a[2]
    return '?'
def rn(f): return '%d %s / %s'%(f,area(f),ROOMS.get(str(f),'?'))
def find_room(t):
    t=t.lower(); return [rn(int(k)) for k in sorted(ROOMS,key=int) if t in ROOMS[k].lower() or t in area(int(k)).lower()]
def exits(f): return [tuple(e) for e in XT.get(str(f),[])]
def ROUTINES(f): return sorted(k[1] for k in RT if k[0]==f)
def lines(f,a,r): return say(f,(a,r),None)
_P={}
def pos(f,a):
    if (f,a) not in _P:
        try: _P[(f,a)]=_ns['actor_pos'](f,{a}).get(a)
        except Exception: _P[(f,a)]=None
    return _P[(f,a)]
def actors(f):
    out=[]
    for a in sorted(set(x[0] for x in ROUTINES(f))):
        t=lines(f,a,2)[:2] or lines(f,a,3)[:1]
        out.append((a,pos(f,a),t))
    return out
def step_tests(f):
    o=[]
    for (g,own),ins in RT.items():
        if g!=f: continue
        for p,k,x in ins:
            if k in('84','85','86') and len(x)>=2: o.append((own[0],own[1],{'84':'<','85':'>','86':'=='}[k],(x[0]|x[1]<<8)&0x7fff))
    return sorted(set(o))
def world(room):
    o=[]
    for k,L in WL.items():
        for r in L:
            if r[4]==room and (r[0],r[1]) not in o: o.append((r[0],r[1]))
    return o
def zone(f,i):
    q=_EX.zones(f)[i]; return (round(sum(c[0] for c in q)/4),round(sum(c[1] for c in q)/4))
