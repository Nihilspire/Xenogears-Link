import os
# Story hints: for every story step, the room(s) whose script sets it (command 87 n), with the place of the actor when the set
# is in a talk (2) or touch (3) routine. Writes v/www/hints.js:
#   HINTS  = step -> [[room, routine, x, z], ...]   (x, z only when known)
#   HROOM  = room -> [left, top, size]  the square part of the room picture (fractions of its width) that holds the walkable area
import sys,json,collections
sys.path.insert(0,'/home/claude/xg/fld')
import tre,surv,trim_plan,numpy as np
ns={}; exec(open('/home/claude/xg/fld/mktre.py').read().split('OUT={}')[0],ns)
sets=collections.defaultdict(list)
for f in range(720):                      # 720-726 are the debug rooms
    for own,a,b,o,stt,code in tre.routines(f):
        for p,k,arg in surv.ins(o,b,code):
            if k=='87' and len(arg)>=2 and arg[1]&0x80: sets[(arg[0]|arg[1]<<8)&0x7FFF].append((f,own[0],own[1]))
H={};rooms=set()
for v in sorted(sets):
    if v>353: continue
    rows=[];seen=set()
    for f,a,r in sets[v]:
        if (f,a) in seen: continue
        seen.add((f,a)); pos=None
        if r in(2,3):
            try: pos=ns['actor_pos'](f,{a}).get(a)
            except Exception: pos=None
        rows.append([f,r]+([int(pos[0]),int(pos[1])] if pos else [])); rooms.add(f)
    H[v]=rows
# HPRE = step -> [[room, [[x, z], ...]], ...]: where the things the step waits for are done (a flag the setting routine, or the routines
# that start it, test with FB before the set, and that is set elsewhere: the well grate, the old man with the key, the sign-up booth).
# Only flags set by at most three routines, in the same area as the step's room (by room number, within 40), at most two rooms.
FS=collections.defaultdict(list)
RT={}
for f in range(720):
    for own,a,b,o,stt,code in tre.routines(f):
        ins=list(surv.ins(o,b,code)); RT[(f,own)]=ins
        for p,k,arg in ins:
            if k=='FE0A' and len(arg)>=2: FS[arg[0]|arg[1]<<8].append((f,own[0],own[1]))
def callers(f,own):
    return [o2 for (g,o2),ins in RT.items() if g==f for p,k,arg in ins if k in('07','08','09') and len(arg)>=2 and (arg[0],arg[1]&0x1f)==own]
PRE={}
for v in sorted(sets):
    if v>353 or v not in H: continue
    need=[];base=None
    for f,a,r in sets[v]:
        ins=RT.get((f,(a,r)),[]);p87=[p for p,k,x in ins if k=='87' and len(x)>=2 and ((x[0]|x[1]<<8)&0x7fff)==v]
        if not p87: continue
        base=base or f;chain=[(a,r)];c=(a,r);seen={c}
        while True:
            cs=[x for x in callers(f,c) if x not in seen]
            if not cs: break
            c=cs[0];seen.add(c);chain.append(c)
        for o2 in chain:
            for p,k,x in RT.get((f,o2),[]):
                if o2==(a,r) and p>=p87[0]: break
                if k=='FB' and len(x)>=2:
                    fl=x[0]|x[1]<<8
                    if fl not in need: need.append(fl)
    if base is None: continue
    spots=collections.OrderedDict()
    for fl in need:
        st=FS.get(fl,[])
        if not st or len(st)>3: continue
        for g,b,r in st:
            if (g,b)==(base,None) or abs(g-base)>40: continue
            if g==base and any(s_[0]==g and s_[1]==a for s_ in [(f,a) for f,a,r_ in sets[v]] ): continue
            pos=None
            try: pos=ns['actor_pos'](g,{b}).get(b)
            except Exception: pos=None
            if not pos:   # placed by FE1C x z y (or 1B) in its set-up routine
                for p_,k_,x_ in RT.get((g,(b,0)),[]):
                    if k_=='FE1C' and len(x_)>=6 or k_=='1B' and len(x_)>=6 and x_[-1]&0xC0==0xC0:
                        import struct as _s; pos=_s.unpack_from('<hh',bytes(x_),0); break
            L=spots.setdefault(g,[])
            if pos and [int(pos[0]),int(pos[1])] not in L: L.append([int(pos[0]),int(pos[1])])
    spots={g:L for g,L in spots.items() if g!=base or L}
    if spots: PRE[v]=[[g,L] for g,L in list(spots.items())[:2]]; rooms.update(spots)
# HPATH = step -> [[room, [[x, z]...]], ...]: the rooms Jack listed for a step in the hints sheet (fld/hint_rooms.json), in the order
# to visit them; spots where the script gives one (the step's own set, or a place from HPRE). It replaces HPRE for that step.
HR=json.load(open('/home/claude/xg/fld/hint_rooms.json'))
# spots Jack typed in the sheet (room (x, z; x, z)) are kept exactly as typed for the steps listed there (fld/hint_spots.json, v1.80)
SP=json.load(open('/home/claude/xg/fld/hint_spots.json')) if os.path.exists('/home/claude/xg/fld/hint_spots.json') else {}
PATH={}
for st,L in HR.items():
    v=int(st);out=[]
    if st in SP:
        PATH[v]=[[g,d] for g,d in SP[st]];rooms.update(g for g,d in SP[st]);PRE.pop(v,None);continue
    for g in L:
        d=[]
        for r in H.get(v,[]):
            if r[0]==g and len(r)>3: d.append([r[2],r[3]])
        for q in PRE.get(v,[]):
            if q[0]==g: d+=[x for x in q[1] if x not in d]
        out.append([g,d]);rooms.add(g)
    PATH[v]=out;PRE.pop(v,None)
R={}
for f in sorted(r for r in rooms if r>=0):
    m=trim_plan.mesh(f)
    if m is None or str(f) not in trim_plan.PLAN: continue
    v,t=m; w=t[(t[:,3]&3)!=2]
    if not len(w): w=t
    cx,cz,s=trim_plan.PLAN[str(f)]; p=(v[np.unique(w[:,:3])]-[cx,cz])/s+0.5
    x0,y0,x1,y1=p[:,0].min(),p[:,1].min(),p[:,0].max(),p[:,1].max(); size=min(1.0,max(x1-x0,y1-y0)*1.3)
    l=min(max((x0+x1)/2-size/2,0),1-size); tp=min(max((y0+y1)/2-size/2,0),1-size)
    R[f]=[round(float(l),3),round(float(tp),3),round(float(size),3)]
js='/* story hints, read off the room scripts (fld/mkhints.py): HINTS = story step -> [[room that sets it, routine, x, z]] (x, z when the\n   actor has a place); HROOM = room -> [left, top, size] of the walkable part of its picture, as fractions of the picture. */\n'
N=json.load(open('/home/claude/xg/fld/hint_notes.json'))   # short notes per step; a leading ? = written from memory, not from the game's text
js+='window.HNOTE='+json.dumps(N,separators=(',',':'))+';\n'
js+='window.HPRE='+json.dumps(PRE,separators=(',',':'))+';\nwindow.HPATH='+json.dumps(PATH,separators=(',',':'))+';\n'
js+='window.HINTS='+json.dumps(H,separators=(',',':'))+';\nwindow.HROOM='+json.dumps(R,separators=(',',':'))+';\n'
open('/home/claude/xg/v/www/hints.js','w').write(js); print(len(PRE),'steps with places to go first',len(H),'steps',sum(1 for L in H.values() for r in L if len(r)>2),'spots',len(R),'rooms',len(js),'bytes')
