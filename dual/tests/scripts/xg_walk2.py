import os as _os
XGROOT=_os.environ.get('XGROOT') or _os.path.abspath(_os.path.join(_os.path.dirname(__file__),'..','..'))
import sys; sys.path.insert(0,'.')
from xg import *
from PIL import Image
d=D(); d.c('init xg/sys xg/save')
for k,v in [('pcsx_rearmed_bios','HLE'),('pcsx_rearmed_memcard1','libretro'),('pcsx_rearmed_memcard2','disabled')]: d.c('var %s %s'%(k,v))
d.c('load xg/disc1.chd xg/save/n2.srm 2'); d.c('loadstate xg/natob_room.state'); d.c('xga 1 23 xg/xga.bin'); d.c('run 5')
seq=eval(sys.argv[1]); shots=[]
room=d.c('read 8006f94e 2')
for i,(x,y,n) in enumerate(seq):
    d.c('axes %d %d 0 0'%(x,y)); d.c('run %d'%n); d.shot('w2_%d'%i); shots.append('w2_%d'%i)
    r=d.c('read 8006f94e 2')
    if r!=room: print('room',room,'->',r,'at',i); room=r
d.c('axes 0 0 0 0'); d.c('run 120'); d.shot('w2_end'); shots.append('w2_end')
print('room',d.c('read 8006f94e 2'),'mode',d.c('read 800af934 4'),'lock',d.c('read 800b2176 2'))
d.c('save xg/walk2.state'); d.c('quit')
ims=[Image.open(XGROOT+'/work/host/xg/shots/%s.png'%s) for s in shots]
w,h=ims[0].size; g=Image.new('RGB',(w*min(4,len(ims)),h*((len(ims)+3)//4)))
for i,im in enumerate(ims): g.paste(im,((i%4)*w,(i//4)*h))
g.save('walk2.png')
