import sys; sys.path.insert(0,'.')
from xg import *
d=D(); d.c('init xg/sys xg/save')
for k,v in [('pcsx_rearmed_bios','HLE'),('pcsx_rearmed_memcard1','libretro'),('pcsx_rearmed_memcard2','disabled')]: d.c('var %s %s'%(k,v))
d.c('load xg/disc1.chd xg/save/n2.srm 2'); d.c('loadstate xg/natob_room.state'); d.c('xga 1 23 xg/xga.bin'); d.c('run 5')
room=d.c('read 8006f94e 2')
moves=[(20000,20000),(25000,0),(0,25000),(20000,20000),(25000,-5000),(0,25000),(25000,25000)]
for i,(x,y) in enumerate(moves*3):
    d.c('axes %d %d 0 0'%(x,y)); d.c('run 40'); d.c('axes 0 0 0 0'); d.c('run 5')
    r=d.c('read 8006f94e 2'); 
    if r!=room: print('room changed',room,'->',r,'after move',i); d.c('run 200'); break
d.shot('wo'); print('room',d.c('read 8006f94e 2'),'mode',d.c('read 800af934 4'),'lock',d.c('read 800b2176 2'))
d.c('save xg/walkout.state'); d.c('quit')
