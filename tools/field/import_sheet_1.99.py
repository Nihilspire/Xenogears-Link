import re,json,openpyxl,sys
ws=openpyxl.load_workbook('/root/.claude/uploads/cda37d0e-56d1-5d7d-ab65-f960f8302106/53057d93-Xenogears_story_hints_1AutoRecovered.xlsx').active
FIX={  # step: [(old,new),...]  typo fixes only, sentence count kept
138:[('Advance through next room','Advance through the next room'),('via switch on the wall, then ride conveyor belt again','via the switch on the wall, then ride the conveyor belt again'),('change direction of belt in this room via switch','change the direction of the belt in this room via the switch'),('After boss,','After the boss,'),('Talk with party','Talk with the party')],
123:[('Leave District','Leave the district'),('follow events','follow the events')],
27:[('Head Southwest to Forest. Explore the Forest.','Head southwest to the forest. Explore the forest.')],
42:[('Head West','Head west')],
45:[('to get to Wentall','to get to Weltall.')],
48:[('Waterfalls','waterfalls')],
51:[('Explore Cave','Explore the cave')],
56:[('Go down to docks.','Go down to the docks.')],
66:[('Talk to Guard to enter Tournament area','Talk to the guard to enter the tournament area')],
81:[('Go to command bridge','Go to the command bridge'),('in the desert, head NW on world map.','in the desert; head northwest on the world map.')],
90:[('Go to exterior of Yggdrasil up top.','Go to the exterior of the Yggdrasil up top.')],
114:[('qualifing','qualifying'),('Rico ,','Rico,'),('barrakcs','barracks')],
129:[('Find Rico','Find Rico.')],
132:[('Wentall','Weltall'),('airducts','air ducts'),('until offices; take master key','until you reach the offices; take the master key')],
135:[('wereabouts','whereabouts')],
144:[('retreive','retrieve')],
146:[('cutscence','cutscene'),('Yggrissil','Yggdrasil')],
151:[('Weh nready','When ready'),('baord','board'),('Drive north to Ethos HQ location on the world map','Drive north to the Ethos HQ location on the world map.')],
166:[('Ygdrasil','Yggdrasil'),('Thames is the southern most POI.','The Thames is the southernmost location.')],
167:[('brdige','bridge')],
174:[('side.Climb','side. Climb'),(' amd ',' and ')],
175:[('lifts up; Continue','lifts up; continue'),('pipes and step','pipes and step')],
198:[('chose to have','choose to have')],
202:[('collasping','collapsing')],
205:[('Sigard','Sigurd')],
213:[('ehad','head'),('Walkthrough','Walk through')],
216:[('Escape through the sewer Interact','Escape through the sewer, interact')],
222:[('iteract','interact')],
228:[('secruity','security')],
240:[('Continue watching then story','Continue watching the story')],
}
def split_top(s):
    out=[];d=0;cur=''
    for ch in s:
        if ch=='(':d+=1
        if ch==')':d=max(0,d-1)
        if ch==',' and d==0: out.append(cur);cur=''
        else: cur+=ch
    out.append(cur);return [x.strip().rstrip('.').strip() for x in out if x.strip().rstrip('.').strip()]
def parse(cell):
    res=[]
    for t in split_top(str(cell or '')):
        t=re.sub(r'^(\d+)\)$',r'\1',t)              # "360)" stray bracket
        m=re.match(r'^(World|\d+)\s*(?:\((.*)\))?$',t,re.I)
        if not m: raise ValueError('cannot read %r'%t)
        room=-1 if m.group(1).lower()=='world' else int(m.group(1));sp=[]
        if m.group(2) and m.group(2).strip():
            a=[int(v) for v in re.findall(r'-?\d+',m.group(2))];sp=[a[i:i+2] for i in range(0,len(a),2)]
        res.append([room,sp])
    return res
steps={};log=[]
for r in ws.iter_rows(min_row=4,values_only=True):
    if r[0] is None: continue
    k=int(r[0]);txt=re.sub(r'\s+',' ',(r[5] or '').strip())
    for a,b in FIX.get(k,[]):
        assert a in txt,(k,a);txt=txt.replace(a,b)
    if txt and not txt.endswith(('.','!','?')): txt+='.'
    chk=(r[6] or '').strip().upper()=='Y'
    steps[str(k)]={'note':('' if chk else '?')+txt,'path':parse(r[4])}
json.dump({'steps':steps},open('hint_edits_sheet.json','w'),indent=0,ensure_ascii=False)
print(len(steps),'steps')
