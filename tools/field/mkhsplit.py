# Story hint splits (v1.91): one-time flags inside a long hint step. When a split's flags are all set, the listed sentences of the
# hint text (counted as the app's hintParts splits them, at each full stop) and the listed rooms of its path are dropped; a split
# with its own text and path replaces the hint instead. If every sentence is gone, the app moves on to the next hint.
import json,re
H=open('/home/claude/xg/v/www/hints.js').read()
def obj(name): return json.loads(re.search(r'window\.'+name+r'=(\{.*?\});\s*\n',H,re.S).group(1))
NOTE=obj('HNOTE'); PATH=obj('HPATH')
B=0x8006EF64
def F(a,m): return [a-B,m]
def parts(t):
    t=t.lstrip('?'); o=[];cur=''
    for x in re.split(r'(\.\s+)',t):
        cur+=x
        if re.search(r'\.\s+$',x): o.append(cur.strip()); cur=''
    if cur.strip(): o.append(cur.strip())
    return o
# step: [ [ [flags...], drop sentences, drop path entries, (replacement text, replacement path) ], ... ]  later rows win
S={
 10: [[[F(0x8006F226,0x1000)],[0,1],[0,1]]],                       # Yui: "I'll go out into the backyard" -> next hint
 15: [[[F(0x8006F22A,0x0008)],[0],[0]]],                            # good night with Citan in the backyard -> next hint
 42: [[[F(0x8006F0E6,0x0001)],[0],[0]]],                            # in the desert: "I'd better follow them"
 52: [[[F(0x8006F024,0x0008)],[0,1],[0,1]],                        # Grand Hall sand sensor off
      [[F(0x8006F024,0x0010)],[0,2],[0,2]]],                        # Waterfall Grotto sand sensor off
 63: [[[F(0x8006F068,0x0008)],[0],[0]],                             # tried the waterway grate (no key)
      [[F(0x8006F068,0x2000),F(0x8006F06C,0x0002)],[1],[1]]],       # signed up at the castle booth
 81: [[[F(0x8006F160,0x0010)],[0,1],[0,1]],                         # Sigurd on the command bridge
      [[F(0x8006F180,0x8000)],[0,1,2],[0,1,2]]],                    # reached Nisan's secret dock
 114:[[[F(0x8006F164,0x0001)],[],[],'?Explore the sewers with Rico. Find Gramps for the passkey and ring the bell.',[[240,[]]]],
      [[F(0x8006F166,0x8000)],[],[],'?Go back to the sewer entrance.',[[239,[]]]]],
 152:[[[F(0x8006F04E,0x0004)],[0],[]]],                             # reached the infirmary with Billy
 153:[[[F(0x8006F12E,0x0400)],[0],[]]],                             # talked to Sigurd on the bridge
 160:[[[F(0x8006F050,0x0080)],[0],[]],                              # back at Ethos HQ, the assassins
      [[F(0x8006F050,0x0800)],[0,1,2],[0]]],                        # Jessie in the overview room
 166:[[[F(0x8006F160,0x0800)],[0],[]],                              # Captain and Hans told you about the dig site
      [[F(0x8006F0B2,0x0010)],[0,1],[]],                            # manual scan run on the sealed door
      [[F(0x8006F0B2,0x0004),F(0x8006F0B2,0x0008)],[0,1,2],[]]],    # emergency level reset
 180:[[[F(0x8006F22E,0x0100)],[0],[]]],                             # agreed to help Zephyr
}
out={}
for s,rows in S.items():
    p=parts(NOTE[str(s)]); n=len(PATH.get(str(s),[]))
    for r in rows:
        assert all(i<len(p) for i in r[1]),(s,p,r); assert all(i<n for i in r[2]),(s,n,r)
    for r in rows:
        left=[x for i,x in enumerate(p) if i not in r[1]]
        print(s,'flags',[(hex(B+v),hex(m)) for v,m in r[0]],'->',(r[3] if len(r)>3 else (' '.join(left) or '(next hint)')))
    out[str(s)]=rows
open('/home/claude/xg/v/www/hsplit.js','w').write('/* story hint splits (fld/mkhsplit.py): step -> [[[var, mask]...], sentences dropped, path rooms dropped, (text, path)]; var is the\n   script variable offset (saved copy 0x8006EF64, live copy 0x800C3A68 in rooms) */\nwindow.HSPLIT='+json.dumps(out,separators=(',',':'))+';\n')
