import sys; sys.path.insert(0,'.')
from xg import *
d=D(); d.c('init xg/sys xg/save')
for k,v in [('pcsx_rearmed_bios','HLE'),('pcsx_rearmed_memcard1','libretro'),('pcsx_rearmed_memcard2','disabled')]: d.c('var %s %s'%(k,v))
d.c('load xg/disc1.chd xg/save/n2.srm 2'); d.c('loadstate xg/natob_room.state'); d.c('xga 1 23 xg/xga.bin'); d.c('run 5')
d.c('axes 0 0 30000 0'); d.c('run 4')
print('rx buf',d.c('read 800625fc 8'),'L',d.c('read 80059430 12'),'R',d.c('read 80059444 12'))
print('lock',d.c('read 800b2176 2'),'mode',d.c('read 800af934 2'),'flags',d.c('read 800af9d8 2'),'st',d.c('read 80017f00 32'))
d.c('quit')
