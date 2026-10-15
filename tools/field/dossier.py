# Per-step evidence for writing story hints: who sets each step and where, what is said, what it waits for, where the scene goes,
# and which scripts react to the story step while the hint is showing. Output: dossier.txt (steps LO..HI of the hint keys).
import sys,json,re,collections
sys.path.insert(0,'/home/claude/xg/fld')
exec(open('/home/claude/xg/fld/splits.py').read().split("res={}")[0])
import exits as EX
ns={}; exec(open('/home/claude/xg/fld/mktre.py').read().split('OUT={}')[0],ns)
LO,HI=int(sys.argv[1]),int(sys.argv[2])
H=open('/home/claude/xg/v/www/hints.js').read()
def obj(name): return json.loads(re.search(r'window\.'+name+r'=(\{.*?\});\s*\n',H,re.S).group(1))
NOTE=obj('HNOTE'); PATH=obj('HPATH'); HINTS=obj('HINTS')
ROOMS=json.loads(re.search(r'window\.ROOMS=(\{.*?\});',open('/home/claude/xg/v/www/rooms.js').read(),re.S).group(1))
AREAS=json.loads(re.search(r'window\.AREAS=(\[.*?\]);',open('/home/claude/xg/v/www/areas.js').read(),re.S).group(1))
XT=json.load(open('/home/claude/xg/fld/exits.json'))
def area(f):
    for a in AREAS:
        if a[0]<=f<=a[1]: return a[2]
    return '?'
def rn(f): return '%d %s / %s'%(f,area(f),ROOMS.get(str(f),'?'))
POS={}
def apos(f,a):
    if (f,a) not in POS:
        try: POS[(f,a)]=ns['actor_pos'](f,{a}).get(a)
        except Exception: POS[(f,a)]=None
    return POS[(f,a)]
ZC={}
def zones(f):
    if f not in ZC:
        try: ZC[f]=EX.zones(f)
        except Exception: ZC[f]=[]
    return ZC[f]
def zone_at(f,own,upto):
    z=None
    for p,k,x in RT.get((f,own),[]):
        if p>=upto: break
        if k in EX.ZT and len(x)>=1 and x[0]<len(zones(f)):
            q=zones(f)[x[0]]; z=(round(sum(c[0] for c in q)/4),round(sum(c[1] for c in q)/4))
    return z
KIND={0:'set-up',1:'run',2:'talk',3:'touch'}
# step tests: 84 n (step<n), 85 n (step>n), 86 n (step==n)
TESTS=collections.defaultdict(list)
for (f,own),ins in RT.items():
    for p,k,x in ins:
        if k in('84','85','86') and len(x)>=2:
            n=(x[0]|x[1]<<8)&0x7fff
            TESTS[n].append((f,own,k,p))
EV=json.load(open('/home/claude/xg/fld/events.json'))
keys=sorted(int(k) for k in HINTS)
out=[]
for i,S in enumerate(keys):
    if not(LO<=S<=HI): continue
    P=keys[i-1] if i else 0
    o=['='*100,'STEP %d   (hint shows while the story step is %d..%d)'%(S,P,S-1),'Current hint: %s'%NOTE.get(str(S),''),'Current path: %s'%PATH.get(str(S),'')]
    for f,own,p in STEP.get(S,[]):
        pos=apos(f,own[0]); z=zone_at(f,own,p)
        o.append('SET by room %s, actor %d routine %d (%s)%s%s'%(rn(f),own[0],own[1],KIND.get(own[1],'event'),' actor at %s'%pos if pos else '',' zone at %s'%(z,) if z else ''))
        cs=callers(f,own)
        if cs: o.append('   started by: '+', '.join('actor %d routine %d (%s)%s'%(c[0],c[1],KIND.get(c[1],'event'),' at %s'%apos(f,c[0]) if apos(f,c[0]) else '') for c in cs[:4]))
        g=gates(f,own,p)
        if g: o.append('   waits for: '+', '.join(('item %d'%a[1]) if a[0]=='item' else '0x%08X&0x%04X'%(0x8006EF64+a[0],a[1]) for a in g[:8]))
        s1=say(f,own,p)
        if s1: o.append('   said before: '+' | '.join(t[:120] for t in s1[-6:]))
        after=[(pp,k,x) for pp,k,x in RT.get((f,own),[]) if pp>p]
        s2=[]
        for pp,k,x in after:
            if k=='98' and len(x)>=4: s2.append('GO room %s'%rn((x[0]|x[1]<<8)&0x3ff))
            if k=='56' and len(x)>=4: s2.append('GO world map place %d'%(x[2]|x[3]<<8))
        if s2: o.append('   then: '+', '.join(s2[:3]))
        sa=[t for t in say(f,own,None) if t not in s1]
        if sa: o.append('   said after: '+' | '.join(t[:120] for t in sa[:4]))
    # scripts that react to the step during this hint
    seen=set(); rx=[]
    for n in range(P,S+1):
        for f,own,k,p in TESTS.get(n,[]):
            if k=='86' and not(P<=n<S): continue
            if k=='84' and not(P<n<=S): continue
            if k=='85' and not(P<=n<S): continue
            if (f,own) in seen: continue
            seen.add((f,own)); rx.append((f,own,k,n))
    byroom=collections.OrderedDict()
    for f,own,k,n in sorted(rx):
        byroom.setdefault(f,[]).append((own,k,n))
    if byroom:
        o.append('REACTS to the step (room: actor/routine test):')
        for f,L in list(byroom.items())[:16]:
            items=[]
            for own,k,n in L[:5]:
                t=say(f,own,None)[:2]; pos=apos(f,own[0])
                items.append('a%d/r%d %s%d%s%s'%(own[0],own[1],{'84':'<','85':'>','86':'=='}[k],n,(' @%s'%pos) if pos else '',(' "'+' | '.join(x[:70] for x in t)+'"') if t else ''))
            o.append('  %s: %s'%(rn(f),'; '.join(items)))
    ex=[e for e in EV if e['lo']>=P and e['hi']<S and not (e['lo']==0 and e['hi']==999) and e['atom'][0]!='step']
    if ex:
        o.append('ONE-TIME FLAGS set during the hint:')
        for e in ex[:10]:
            t=say(e['room'],(e['actor'],e['routine']),e['pos'])[-2:]
            o.append('  room %s actor %d r%d (step %d-%d)%s'%(rn(e['room']),e['actor'],e['routine'],e['lo'],e['hi'],(' "'+' | '.join(x[:80] for x in t)+'"') if t else ''))
    out.append('\n'.join(o))
open('/home/claude/xg/fld/dossier_%d_%d.txt'%(LO,HI),'w').write('\n'.join(out)+'\n')
print(len(out),'steps')
