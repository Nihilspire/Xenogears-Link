import sys,json,collections,re
sys.path.insert(0,'/home/claude/xg/fld')
import tre,surv,dlg
RT={}; SETS=collections.defaultdict(list); STEP=collections.defaultdict(list); GO=collections.defaultdict(list)
TXT={}
def atom_flag(f): return ((f>>4)*2, 1<<(f&15))
for f in range(720):
    for own,a,b,o,stt,code in tre.routines(f):
        ins=list(surv.ins(o,b,code)); RT[(f,own)]=ins
        for p,k,x in ins:
            if k=='87' and len(x)>=2 and x[1]&0x80: STEP[(x[0]|x[1]<<8)&0x7fff].append((f,own,p))
            elif k=='3A' and len(x)>=5 and x[4]&0x40:
                v=x[0]|x[1]<<8; n=x[2]|x[3]<<8
                if 0x80<=v<0x400 and n<16: SETS[(v,1<<n)].append((f,own,p))
            elif k=='FE0A' and len(x)>=2:
                SETS[atom_flag(x[0]|x[1]<<8)].append((f,own,p))
            elif k=='8C' and len(x)>=2 and x[1]&0x80:
                SETS[('item',(x[0]|x[1]<<8)&0x7fff)].append((f,own,p))
            elif k=='98' and len(x)>=4:
                r=(x[0]|x[1]<<8)
                if r&0x8000: GO[r&0x3ff].append((f,own,p))
def lines(f): 
    if f not in TXT: TXT[f]=dlg.lines(f)
    return TXT[f]
def say(f,own,upto=None,_d=0):
    out=[]
    for p,k,x in RT.get((f,own),[]):
        if upto is not None and p>=upto: break
        if k in('07','08','09') and len(x)>=2 and _d<1 and x[0]<0xF0:
            for t in say(f,(x[0],x[1]&0x1f),None,_d+1):
                if t not in out: out.append(t)
        i=None
        if k in('D2','D4') and len(x)>=2: i=x[0]|x[1]<<8
        elif k=='FC' and len(x)>=3: i=x[1]|x[2]<<8
        if i is not None and i<len(lines(f)):
            t=re.sub(r'<..>|!|\|',' ',lines(f)[i]).replace('/',' ').replace('  ',' ').strip()
            if len(t)>4 and t not in out: out.append(t)
    return out
LOCALSET=collections.defaultdict(list)
for (f,own),ins in RT.items():
    for p,k,x in ins:
        if k in('35','36','3A') and len(x)>=2:
            v=x[0]|x[1]<<8
            if v>=0x400: LOCALSET[(f,v)].append((own,p))
def gates(f,own,upto=None,_d=0,_seen=None):
    g=[]; _seen=_seen if _seen is not None else set()
    for p,k,x in RT.get((f,own),[]):
        if upto is not None and p>=upto: break
        if k=='FB' and len(x)>=2: g.append(atom_flag(x[0]|x[1]<<8))
        elif k=='8B' and len(x)>=2 and x[1]&0x80: g.append(('item',(x[0]|x[1]<<8)&0x7fff))
        elif k=='02' and len(x)>=7 and (x[4]&0xF0)==0x40 and (x[4]&0xF)==6:
            v=x[0]|x[1]<<8; m=x[2]|x[3]<<8
            if 0x80<=v<0x400 and m and m&(m-1)==0: g.append((v,m))
        if k=='02' and len(x)>=2 and _d<3:
            v=x[0]|x[1]<<8
            if v>=0x400 and (f,v) not in _seen:
                _seen.add((f,v))
                for o2,p2 in LOCALSET.get((f,v),[])[:4]:
                    if o2!=own: g+=gates(f,o2,p2,_d+1,_seen)
    return g
def callers(f,own):
    return [o2 for (g,o2),ins in RT.items() if g==f for p,k,x in ins if k in('07','08','09') and len(x)>=2 and (x[0],x[1]&0x1f)==own]
def chain(f,own,upto,depth=0,seen=None):
    seen=seen or set(); out=[]
    gs=list(gates(f,own,upto))
    for c in callers(f,own)[:2]: gs+=gates(f,c)
    for at in gs:
        if at in seen: continue
        seen.add(at)
        st=SETS.get(at,[])
        if not st or len(st)>6: continue
        for g,o2,p2 in st[:2]:
            if abs(g-f)>40: continue
            out.append(dict(depth=depth,var=at[0],mask=at[1],room=g,actor=o2[0],routine=o2[1],said=say(g,o2,p2)[-3:] or say(g,o2,None)[:3]))
            if depth<3: out+=chain(g,o2,p2,depth+1,seen)
    return out
res={}
for s in sorted(STEP):
    if s>353: continue
    ms=[]
    for f,own,p in STEP[s]:
        ms+=chain(f,own,p)
    # dedupe by atom
    seen=set(); m2=[]
    for m in ms:
        k=(m['var'],m['mask'])
        if k in seen: continue
        seen.add(k); m2.append(m)
    if m2: res[s]=dict(setters=[(f,list(own)) for f,own,p in STEP[s]],milestones=m2)
json.dump(res,open('/home/claude/xg/fld/step_splits.json','w'),indent=1)
print(len(res),'steps with milestones', sum(len(v['milestones']) for v in res.values()))
for s in (108,111,114,117,120):
    print(s,json.dumps(res.get(s),ensure_ascii=False)[:1200])
