# Review pictures: room picture + walkable outline (white) + exits (green = unchanged, yellow = moved this pass, with a line from the
# old place) labelled with where they lead + the game's arrival spots (cyan cross, "in from N"). Usage: review.py OUTDIR rooms|all
import sys,json,os,math
from PIL import Image,ImageDraw,ImageFont
M=json.load(open('/tmp/claude-0/meta.json'));WALK=json.load(open('/tmp/claude-0/walk.json'));CK=json.load(open('/tmp/claude-0/exitcheck.json'))
NEW=json.load(open(sys.argv[3])) if len(sys.argv)>3 else None
R,AR,P=M['ROOMS'],M['AREAS'],M['PLAN'];PL='/home/claude/xenogears-link/app/www/plan/'
def area(f):
    for a in AR:
        if a[0]<=f<=a[1]: return a[2]
    return ''
def lab(d): return 'World map' if d==-1 else '%d %s'%(d,R.get(str(d)) or area(d))
try: FONT=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
except: FONT=ImageFont.load_default()
def render(f,out):
    p=P.get(str(f));fn=PL+'%d.webp'%f
    if not p or not os.path.exists(fn): return False
    im=Image.open(fn).convert('RGBA');S=im.width
    if S<1024: im=im.resize((1024,1024),Image.NEAREST);S=1024
    cx,cz,sp=p
    def px(x,z): return ((x-cx)/sp+.5)*S,((z-cz)/sp+.5)*S
    ov=Image.new('RGBA',im.size,(0,0,0,0));dr=ImageDraw.Draw(ov)
    for t in WALK.get(str(f),[]):
        pts=[px(*v) for v in t];dr.line(pts+[pts[0]],fill=(200,200,200,55),width=1)
    for A,spots in (CK['ARR'].get(str(f)) or {}).items():
        for s in spots:
            x,y=px(*s);dr.line([x-7,y-7,x+7,y+7],fill=(0,230,255,255),width=3);dr.line([x-7,y+7,x+7,y-7],fill=(0,230,255,255),width=3)
            dr.text((x+9,y+2),'in from '+A,fill=(0,230,255,255),font=FONT,stroke_width=2,stroke_fill=(0,0,0,255))
    old=M['EXITS'].get(str(f),[]);new=(NEW or {}).get(str(f),old)
    for i,e in enumerate(new):
        if e[0] is None: continue
        x,y=px(e[0],e[1]);o=old[i] if i<len(old) else e;moved=o[0] is not None and (o[0],o[1])!=(e[0],e[1])
        col=(255,150,0,255) if moved else (255,60,230,255)
        if moved:
            ox,oy=px(o[0],o[1]);dr.line([ox,oy,x,y],fill=col,width=2);dr.ellipse([ox-5,oy-5,ox+5,oy+5],outline=(255,80,80,255),width=2)
        dr.rectangle([x-8,y-8,x+8,y+8],outline=col,width=3)
        dr.text((x+11,y-16),'#%d -> %s'%(i,lab(e[2])),fill=col,font=FONT,stroke_width=2,stroke_fill=(0,0,0,255))
    dr.rectangle([0,0,S,24],fill=(0,0,0,170));dr.text((6,4),'Room %d  %s / %s   (magenta = exit, orange = moved this pass from the red ring, cyan x = where the game puts you)'%(f,area(f),R.get(str(f),'')),fill=(255,255,255,255),font=FONT)
    Image.alpha_composite(im,ov).convert('RGB').save(out,quality=88);return True
if __name__=='__main__':
    OUT=sys.argv[1];os.makedirs(OUT,exist_ok=True)
    rooms=range(730) if sys.argv[2]=='all' else [int(x) for x in sys.argv[2].split(',')]
    import re
    def fname(f):
        nm=(area(f)+' - '+(R.get(str(f)) or '')).strip(' -');nm=re.sub(r'[<>:"/\\|?*]','',nm)
        return os.path.join(OUT,'%03d %s.jpg'%(f,nm))
    n=sum(render(f,fname(f)) for f in rooms);print(n,'pictures')
