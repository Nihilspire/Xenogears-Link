import sys,json,collections,re
sys.path.insert(0,'/home/claude/xg/fld')
exec(open('/home/claude/xg/fld/splits.py').read().split("res={}")[0])
T=json.loads(re.search(r'window\.TREASURE=(\{.*?\});',open('/home/claude/xg/v/www/treasure.js').read(),re.S).group(1))
TF=set()
for r,L in T.items():
    for e in L:
        try:
            if not (len(e)>6 and e[6]==1): TF.add((e[0],1<<e[1]))
        except Exception: pass
def bounds(f,own,upto,_d=0):
    lo,hi=0,999
    for p,k,x in RT.get((f,own),[]):
        if p>=upto: break
        if k in('84','85','86') and len(x)>=4:
            n=(x[0]|x[1]<<8); tgt=x[2]|x[3]<<8
            if not n&0x8000: continue
            n&=0x7fff
            if tgt<=upto: continue
            if k=='84': hi=min(hi,n-1)
            elif k=='85': lo=max(lo,n+1)
            else: lo=max(lo,n); hi=min(hi,n)
    if _d<2:
        for c in callers(f,own)[:3]:
            # constraint at the call site
            for p,k,x in RT.get((f,c),[]):
                if k in('07','08','09') and len(x)>=2 and (x[0],x[1]&0x1f)==own:
                    l2,h2=bounds(f,c,p,_d+1); lo=max(lo,l2); hi=min(hi,h2); break
    return lo,hi
IT=json.loads(re.search(r'window\.TABLES=(\{.*?\});',open('/home/claude/xg/v/www/tables.js').read(),re.S).group(1))
def itemname(i):
    inv,iid=i>>8,i&0xff
    key=['items','weapons','equipment','gear_weapons','gear_parts'][inv] if inv<5 else 'items'
    L=IT.get(key,[]); return L[iid] if iid<len(L) else '#%d'%i
EV=[]
for (f,own),ins in RT.items():
    if f>=720: continue
    for p,k,x in ins:
        at=None
        if k=='3A' and len(x)>=5 and x[4]&0x40:
            v=x[0]|x[1]<<8; n=x[2]|x[3]<<8
            if 0x80<=v<0x400 and n<16: at=(v,1<<n)
        elif k=='FE0A' and len(x)>=2: at=atom_flag(x[0]|x[1]<<8)
        elif k=='8C' and len(x)>=2 and x[1]&0x80: at=('item',(x[0]|x[1]<<8)&0x7fff)
        elif k=='87' and len(x)>=2 and x[1]&0x80: at=('step',(x[0]|x[1]<<8)&0x7fff)
        if at is None or at in TF: continue
        if at[0]=='item' and any(k2=='FE0A' or k2=='3A' for p2,k2,x2 in ins) and any((own==(o_)) for o_ in []): pass
        lo,hi=bounds(f,own,p)
        EV.append(dict(room=f,actor=own[0],routine=own[1],pos=p,atom=at,lo=lo,hi=hi))
print(len(EV),'events', sum(1 for e in EV if e['lo']>0 or e['hi']<999),'with step bounds')
json.dump(EV,open('/home/claude/xg/fld/events.json','w'))
