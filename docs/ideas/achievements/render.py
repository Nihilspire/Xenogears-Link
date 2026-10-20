from PIL import Image
exec(open('/home/claude/ach/icons.py').read())
VAR={'doll2':('doll',{'e':'o','f':'b'}),'star2':('star',{'y':'l','h':'w','o':'g'}),'star3':('star',{'y':'c','h':'w','o':'s'}),
 'chest2':('chestopen',{'o':'u','b':'q','n':'z'}),'orb2':('orb',{'u':'e','q':'f'}),'belt2':('belt',{'r':'s','m':'v'}),
 'cog2':('cog',{'g':'o','l':'y'}),'shield2':('shield',{'s':'r'}),'heart2':('heart',{'r':'p','m':'r'})}
def hexc(h):return tuple(int(h[i:i+2],16) for i in (1,3,5))+(255,)
def draw(rows,swap={}):
    im=Image.new('RGBA',(18,18),(0,0,0,0));px=im.load()
    for y,r in enumerate(rows):
        for x,ch in enumerate(r):
            if ch!='.':px[x+1,y+1]=hexc(PAL[swap.get(ch,ch)])
    out=im.copy();op=out.load();K=hexc('#120f1c')
    for y in range(18):
        for x in range(18):
            if px[x,y][3]==0 and any(0<=x+dx<18 and 0<=y+dy<18 and px[x+dx,y+dy][3] for dx,dy in((1,0),(-1,0),(0,1),(0,-1))):op[x,y]=K
    return out
import os;os.makedirs('px',exist_ok=True)
for k,v in I.items():draw(v).save('px/%s.png'%k)
for k,(b,sw) in VAR.items():draw(I[b],sw).save('px/%s.png'%k)
names=sorted(os.listdir('px'));C=10;S=18*4+6
sheet=Image.new('RGBA',(C*S,((len(names)+C-1)//C)*(S+10)),(30,34,56,255))
from PIL import ImageDraw;d=ImageDraw.Draw(sheet)
for i,n in enumerate(names):
    im=Image.open('px/'+n).resize((72,72),Image.NEAREST);x=(i%C)*S;y=(i//C)*(S+10);sheet.alpha_composite(im,(x+3,y+3));d.text((x+2,y+S-2),n[:-4],fill=(255,255,255,255))
sheet.save('/tmp/claude-0/pxsheet.png');print(len(names))
