import os as _os
XGROOT=_os.environ.get('XGROOT') or _os.path.abspath(_os.path.join(_os.path.dirname(__file__),'..','..'))
import sys,shutil; sys.path.insert(0,'.')
from xg import *
from PIL import Image
bios=sys.argv[1]; tag=sys.argv[2]; seq=eval(sys.argv[3]); srm=sys.argv[4] if len(sys.argv)>4 else 'real.srm'
shutil.copy(XGROOT+'/work/host/xg/save/'+srm,XGROOT+'/work/host/xg/save/s_%s.srm'%tag)
d=D(); d.c('init xg/sys xg/save')
for k,v in [('pcsx_rearmed_bios',bios),('pcsx_rearmed_memcard1','libretro'),('pcsx_rearmed_memcard2','disabled'),('pcsx_rearmed_show_bios_bootlogo','disabled')]: d.c('var %s %s'%(k,v))
d.c('load xg/disc1.chd xg/save/s_%s.srm 2'%tag); d.c('loadstate xg/lh_loaded.state'); d.c('run 10')
names=[]
for i,(btn,hold,after) in enumerate(seq):
    if btn: d.tap(btn,hold,after)
    else: d.c('run %d'%after)
    d.shot('%s_%d'%(tag,i)); names.append('%s_%d'%(tag,i))
d.c('quit')
import time; time.sleep(0.5)
x=open(XGROOT+'/work/host/xg/save/s_%s.srm'%tag,'rb').read()
print('dir:',[ (i,hex(x[i*128]),x[i*128+10:i*128+30].split(b'\0')[0]) for i in range(1,16) if x[i*128]!=0xa0])
ims=[Image.open(XGROOT+'/work/host/xg/shots/%s.png'%n) for n in names]; w,h=ims[0].size
g=Image.new('RGB',(w*4,h*((len(ims)+3)//4)))
for i,im in enumerate(ims): g.paste(im,((i%4)*w,(i//4)*h))
g.save('sv_%s.png'%tag)
