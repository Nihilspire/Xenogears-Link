# Checks every hint spot (HPATH) against the room scripts: actor places (19/1D/1B/FE1C), who sets the step (87), trigger zones.
# Needs /tmp/claude-0/hpath.json ({P: HPATH, N: HNOTE} from hints.js) and XG_DISC; run from /home/claude/xg/fld. Writes /tmp/claude-0/spotcheck.json.
import sys,json,math,collections
sys.path.insert(0,'/home/claude/xg/fld')
ns={};exec(open('/home/claude/xg/fld/mktre.py').read().split('OUT={}')[0],ns)
tre,surv,chest,exits=ns['tre'],ns['surv'],ns['chest'],ns['exits']
import dlg
D=json.load(open('/tmp/claude-0/hpath.json'));P=D['P'];N=D['N']
rooms=sorted({r[0] for s in P for r in P[s] if r[1] and r[0]>=0})
info={}
for f in rooms:
    try: R=list(tre.routines(f))
    except Exception as e: info[f]=None;continue
    pos=collections.defaultdict(set);talk=collections.defaultdict(set);sets=collections.defaultdict(set)
    for own,a,b,o,stt,code in R:
        A=own[0]
        for p,k,arg in surv.ins(o,b,code):
            if k=='19' and len(arg)>=5 and arg[4]&0xC0==0xC0: pos[A].add((chest.s16(arg),chest.s16(arg,2)))
            elif k=='1D' and len(arg)>=6: pos[A].add((chest.s16(arg),chest.s16(arg,2)))
            elif k=='1B' and len(arg)>=6 and arg[-1]&0xC0==0xC0: pos[A].add((chest.s16(arg),chest.s16(arg,2)))
            elif k=='FE1C' and len(arg)>=7 and arg[6]==0xE0 and abs(chest.s16(arg))<5000: pos[A].add((chest.s16(arg),chest.s16(arg,2)))
            elif k in('D2','D4','F5') and len(arg)>=2: talk[A].add(chest.s16(arg)&0xFFFF)
            elif k=='87' and len(arg)>=2 and arg[1]&0x80: sets[A].add((arg[0]|arg[1]<<8)&0x7FFF)
    E=exits.ents(f)
    for a in range(len(E)):
        if a not in pos and (E[a][4] or E[a][6]): pos[a].add((E[a][4],E[a][6]))
    Z=[(sum(c[0] for c in z)/4,sum(c[1] for c in z)/4) for z in exits.zones(f)]
    try: L=dlg.lines(f)
    except Exception: L=[]
    info[f]=dict(pos=pos,talk=talk,sets=sets,Z=Z,L=L)
rows=[]
for s in sorted(P,key=int):
    for i,(f,spots) in enumerate(P[s]):
        for sp in spots:
            x,z=sp;I=info.get(f)
            row=dict(step=int(s),page=i+1,room=f,x=x,z=z,note=N.get(s,''))
            if not I: row.update(verdict='NO SCRIPT');rows.append(row);continue
            best=None
            for a,ps in I['pos'].items():
                for q in ps:
                    d=math.hypot(q[0]-x,q[1]-z)
                    if best is None or d<best[0]: best=(d,a,q)
            # the actor that sets this step (or the next) in this room
            st=None
            for a,ss in I['sets'].items():
                if int(s) in ss or int(s)+1 in ss:
                    for q in I['pos'].get(a,[]):
                        d=math.hypot(q[0]-x,q[1]-z)
                        if st is None or st[0] is None or d<st[0]: st=(d,a,q)
                    if a not in I['pos'] and st is None: st=(None,a,None)
            zb=min([math.hypot(q[0]-x,q[1]-z) for q in I['Z']] or [None]) if I['Z'] else None
            if best:
                row.update(near_actor=best[1],near_pos='%d, %d'%best[2],near_d=round(best[0]))
                tl=sorted(I['talk'].get(best[1],[]))
                if tl and tl[0]<len(I['L']): row['says']=I['L'][tl[0]][:90]
            if st and st[0] is not None: row.update(setter=st[1],setter_pos='%d, %d'%st[2],setter_d=round(st[0]))
            elif st: row.update(setter=st[1])
            if zb is not None: row['zone_d']=round(zb)
            d=min([v for v in [row.get('near_d'),row.get('zone_d')] if v is not None] or [9999])
            row['verdict']='OK' if d<=120 else 'CHECK' if d<=300 else 'FAR'
            if row.get('setter_d') is not None and row['setter_d']>300 and row['verdict']=='OK': row['verdict']='CHECK'
            rows.append(row)
json.dump(rows,open('/tmp/claude-0/spotcheck.json','w'),indent=0)
import collections as C;print(len(rows),C.Counter(r['verdict'] for r in rows))
