import sys; sys.path.insert(0,'.')
from xg import *
d=D(); d.c('init xg/sys xg/save')
for k,v in [('pcsx_rearmed_bios','HLE'),('pcsx_rearmed_memcard1','libretro'),('pcsx_rearmed_memcard2','disabled')]: d.c('var %s %s'%(k,v))
d.c('load xg/disc1.chd xg/save/n2.srm 2'); d.c('loadstate xg/natob_room.state'); d.c('xga 1 23 xg/xga.bin'); d.c('run 5')
t0=d.c('read 800af9fc 4'); d.c('axes 0 0 0 30000'); d.c('run 40'); t1=d.c('read 800af9fc 4'); d.c('axes 0 0 0 0'); d.c('run 5'); d.shot('n4_tilt')
print('tilt/zoom', t0, '->', t1)
d.c('quit')
