from PIL import Image
exec(open('/home/claude/ach/ach.py').read())
W='/home/claude/xenogears-link/app/www/'
C=72;atlas=Image.new('RGBA',(C*10,C*10),(0,0,0,0))
def load(ic):
    k,v=ic.split(':',1)
    if k=='px':return Image.open('px/%s.png'%v).resize((72,72),Image.NEAREST),True
    p={'spr':W+'spr/%s.png','p48':W+'img/p48/%s.png','pb':W+'img/pb/%s.png','img':W+'img/%s.png'}[k]%v
    return Image.open(p).convert('RGBA'),False
for i,x in enumerate(A):
    im,px=load(x['ic'])
    if not px:
        bb=im.getbbox();im=im.crop(bb);f=min(68/im.width,68/im.height)
        if f>=1:f=int(f);im=im.resize((im.width*f,im.height*f),Image.NEAREST)
        else:im=im.resize((max(1,round(im.width*f)),max(1,round(im.height*f))),Image.LANCZOS)
    atlas.alpha_composite(im,((i%10)*C+(C-im.width)//2,(i//10)*C+(C-im.height)//2))
import os;os.makedirs('/tmp/claude-0/-home-claude/cda37d0e-56d1-5d7d-ab65-f960f8302106/scratchpad/ach',exist_ok=True)
out='/tmp/claude-0/-home-claude/cda37d0e-56d1-5d7d-ab65-f960f8302106/scratchpad/ach/'
atlas.save(out+'atlas.png')
bg=Image.new('RGBA',atlas.size,(20,24,48,255));bg.alpha_composite(atlas);bg.save('/tmp/claude-0/atlas_view.png')
import shutil;shutil.copy(W+'img/frame.png',out+'frame.png');shutil.copy(W+'img/title.png',out+'title.png')
