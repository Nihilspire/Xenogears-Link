import sys; sys.path.insert(0,'.')
from xg import *
for on in (0,1):
    d=D(); d.c('init xg/sys xg/save')
    for k,v in [('pcsx_rearmed_bios','HLE'),('pcsx_rearmed_memcard1','libretro'),('pcsx_rearmed_memcard2','disabled')]: d.c('var %s %s'%(k,v))
    d.c('load xg/disc1.chd xg/save/n2.srm 2'); d.c('loadstate xg/natob_room.state'); d.c('xga %d 23 xg/xga.bin'%on); d.c('run 5')
    a=d.c('read 800afa0c 4'); d.c('btn %x'%L); d.c('run 30'); b=d.c('read 800afa0c 4'); d.c('btn 0'); d.c('run 60'); c=d.c('read 800afa0c 4'); d.shot('n5_%d'%on)
    print('mod',on,'L1 orbit target',a,'->',b,'->',c); d.c('quit')
