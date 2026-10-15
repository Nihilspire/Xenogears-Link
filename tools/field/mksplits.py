import json,re,collections,sys
exec(open('/home/claude/xg/fld/splits.py').read().split("res={}")[0])
EV=json.load(open('events.json')); A=json.load(open('step_splits.json'))
ROOMS=json.loads(re.search(r'window\.ROOMS=(\{.*?\});',open('/home/claude/xg/v/www/rooms.js').read(),re.S).group(1))
IT=json.loads(re.search(r'window\.TABLES=(\{.*?\});',open('/home/claude/xg/v/www/tables.js').read(),re.S).group(1))
def itemname(i):
    inv,iid=i>>8,i&0xff; key=['items','weapons','equipment','gear_weapons','gear_parts'][inv] if inv<5 else 'items'
    L=IT.get(key,[]); return (L[iid] if iid<len(L) else '#%d'%i).strip()
STEPS=sorted(int(s) for s in STEP if int(s)<=353)
nsets=collections.Counter(tuple(e['atom']) for e in EV)
def addr(at):
    if at[0]=='item': return 'item: '+itemname(at[1])
    return '0x%08X & 0x%04X'%(0x8006EF64+at[0]+(1 if at[1]>0xFF else 0), at[1]>>8 if at[1]>0xFF else at[1])
def addr16(at):
    if at[0]=='item': return 'item: '+itemname(at[1])
    return '0x%08X (u16) & 0x%04X'%(0x8006EF64+at[0],at[1])
rows=collections.defaultdict(list)
FIRST={}
for s_ in sorted(A,key=int):
    for m in A[s_]['milestones']:
        at=('item',m['mask']) if m['var']=='item' else (m['var'],m['mask'])
        FIRST.setdefault(at,int(s_))
for s in STEPS:
    prev=max([x for x in STEPS if x<s],default=0)
    seen=set()
    for m in reversed(A.get(str(s),{}).get('milestones',[])):
        at=('item',m['mask']) if m['var']=='item' else (m['var'],m['mask'])
        if at in seen or FIRST.get(at)!=s or not m['said']: continue
        seen.add(at)
        rows[s].append(dict(order=-m['depth'],room=m['room'],at=at,said=m['said'],src='needed before step %d is set (script prerequisite)'%s))
    for e in EV:
        at=tuple(e['atom'])
        if at[0]=='step' or at in seen or nsets[at]>3: continue
        if not (prev<=e['lo'] and e['hi']<s and e['lo']<=e['hi']): continue
        if e['lo']==0 and e['hi']==999: continue
        said=say(e['room'],(e['actor'],e['routine']),e['pos'])
        if not said: continue
        seen.add(at)
        rows[s].append(dict(order=e['lo']-1000,room=e['room'],at=at,said=said[-3:],src='happens while the story step is %s'%(e['lo'] if e['lo']==e['hi'] else '%d-%d'%(e['lo'],e['hi']))))
# Nortune sewer milestones found by hand (14 Oct)
rows[114]=[dict(order=-100,room=213,at=(0x244,1),said=['Rico For the sake of my men too, I am about to check out the sewers.'],src='checked by hand: Rico teams up for the sewer search'),
           dict(order=-99,room=239,at=(0x200,1),said=['First scene inside the sewers with Rico (Rico: "Let\'s look for it...")'],src='checked by hand: first sewer entry with Rico')]+[r for r in rows[114] if r['at'] not in ((0x244,1),(0x200,1))]
out=[]
for s in sorted(rows):
    L=sorted(rows[s],key=lambda r:r['order'])
    for i,r in enumerate(L,1):
        out.append(dict(step=s,n=i,room=r['room'],room_name=ROOMS.get(str(r['room']),''),flag=addr16(r['at']),said=' / '.join(t[:110] for t in r['said']),src=r['src']))
json.dump(out,open('/home/claude/xg/fld/split_rows.json','w'),indent=0)
print(len(out),'rows over',len(rows),'steps')
c=collections.Counter(r['step'] for r in out); print(c.most_common(15))
