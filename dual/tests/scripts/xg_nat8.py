import sys; sys.path.insert(0,'.')
from xg import *
d=D(); d.c('init xg/sys xg/save')
for k,v in [('pcsx_rearmed_bios','HLE'),('pcsx_rearmed_memcard1','libretro'),('pcsx_rearmed_memcard2','disabled')]: d.c('var %s %s'%(k,v))
d.c('load xg/disc1.chd xg/save/n2.srm 2'); d.c('loadstate xg/'+sys.argv[1]); d.c('xga 1 23 xg/xga.bin'); d.c('run 5')
r=lambda a,n: d.c('read %s %d'%(a,n))
print('lock',r('800b2176',2),'mode',r('800af934',4),'flags',r('800af9d8',4),'auto/stop',r('800af9f4',2),'frames_left',r('800af9f6',2),'yaw',r('800af9e6',2),'target',r('800afa0c',4),'room',r('8006f94e',2),'orbitfn',r('800726e8',12),'sectors',r('800adc1c',8))
d.c('quit')
