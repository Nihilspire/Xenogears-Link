import sys,json,collections
sys.path.insert(0,'/home/claude/xg/fld')
import tre,surv,chest,exits
def actor_pos(f,acts):
    r=tre.vm.load(f); ent=r[2]; out={}
    for own,a,b,o,stt,code in tre.routines(f):
        if own[0] in acts and a==ent[own[0]][0] and own[0] not in out:
            for p,k,arg in surv.ins(o,b,code):
                if k=='19' and len(arg)>=5 and arg[4]&0xC0==0xC0: out[own[0]]=[chest.s16(arg),chest.s16(arg,2)]; break
                if k=='1D' and len(arg)>=6: out[own[0]]=[chest.s16(arg),chest.s16(arg,2)]; break
                if k=='FE1C' and len(arg)>=7 and arg[6]==0xE0 and abs(chest.s16(arg))<5000: out[own[0]]=[chest.s16(arg),chest.s16(arg,2)]; break   # FE1C x, z, y (Noah OPX_1C); added 19 Oct 2026
                if k=='1B' and len(arg)>=6 and arg[len(arg)-1]&0xC0==0xC0: out[own[0]]=[chest.s16(arg),chest.s16(arg,2)]; break
    # no place in the set-up routine: the room's object placement table, then the trigger zone the give sits behind
    E=exits.ents(f); Z=exits.zones(f)
    for a in acts:
        if a not in out and a<len(E) and (E[a][4] or E[a][6]): out[a]=[E[a][4],E[a][6]]
    for own,a,b,o,stt,code in tre.routines(f):
        if own[0] not in acts or own[0] in out: continue
        guards=[]
        for p,k,arg in surv.ins(o,b,code):
            guards=[g for g in guards if g[1]>p]
            if k in exits.ZT and len(arg)>=3: guards.append((arg[0],arg[1]|arg[2]<<8))
            if k in('8C','8F') and guards and guards[-1][0]<len(Z):
                q=Z[guards[-1][0]]; out[own[0]]=[round(sum(c[0] for c in q)/4),round(sum(c[1] for c in q)/4)]; break
    # a place far off the room's walkable area is not trusted (one case: room 318)
    import trim_plan,numpy as np
    m=trim_plan.mesh(f)
    if m is not None:
        v=m[0]; ext=max(np.ptp(v[:,0]),np.ptp(v[:,1]))
        for a in list(out):
            if np.hypot(v[:,0]-out[a][0],v[:,1]-out[a][1]).min()>ext*0.15: del out[a]
    return out
OUT={}; st=collections.Counter()
for f in range(730):
    L=[t for t in chest.room(f) if t['flag']]
    if not L: continue
    pos=actor_pos(f,{t['actor'] for t in L if t['src']=='actor'})
    groups=collections.OrderedDict()
    for t in L:
        key=(tuple(t['flag']),t['src'])
        g=groups.setdefault(key,{'items':[],'gold':0,'pos':None,'src':t['src']})
        if t['k']=='gold': g['gold']+=t['v']
        elif t['v'] not in g['items']: g['items'].append(t['v'])
        if t['pos']: g['pos']=t['pos']
        elif t['src']=='actor' and t.get('actor') in pos: g['pos']=pos[t['actor']]
        g['n']=g.get('n',0)+1
    rows=[]
    for (flag,src),g in groups.items():
        if src=='actor' and g['n']>3: st['dropped: one flag, many gives']+=1; continue
        if src=='chest' and len(g['items'])>1: st['chest with alternatives']+=1
        if any((c>>8)>4 for c in g['items']): st['dropped: bad item code']+=1; continue
        row=[flag[0],flag[1],g['items'],g['gold']]+(g['pos'] if g['pos'] else [])+([1] if src=='actor' and g['pos'] else [])
        rows.append(row); st[src+(' pos' if g['pos'] else ' nopos')]+=1
    if rows: OUT[f]=rows
print(dict(st),'rooms',len(OUT),'entries',sum(len(v) for v in OUT.values()))
js='/* treasure and one-time pickups per room, read off the room scripts on the disc (see "Room scripts" in the RAM map).\n   room -> [flag variable, bit, [item codes], gold, x, z, gift]; item code = inventory x 256 + id (0 items, 1 weapons, 2 equipment, 3 gear weapons, 4 gear parts);\n   taken when bit `bit` of the 16-bit script variable at 0x800C3A68 + variable is set; x, z are missing when the script gives no position;\n   a seventh entry of 1 marks a gift (handed over by a person or an event at that spot, not a chest). */\nwindow.TREASURE='+json.dumps(OUT,separators=(',',':'))+';\n'
open('/home/claude/xg/v/www/treasure.js','w').write(js); print(len(js))
json.dump(OUT,open('treasure.json','w'))
