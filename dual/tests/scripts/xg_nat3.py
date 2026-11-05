import sys; sys.path.insert(0,'.')
from xg import *
d=D(); d.c('init xg/sys xg/save')
for k,v in [('pcsx_rearmed_bios','HLE'),('pcsx_rearmed_memcard1','libretro'),('pcsx_rearmed_memcard2','disabled')]: d.c('var %s %s'%(k,v))
d.c('load xg/disc1.chd xg/save/n2.srm 2'); d.c('loadstate xg/'+sys.argv[1])
print('xga on ->',d.c('xga 1 23 xg/xga.bin')); d.c('run 5')
print('rx',d.c('read 800625fc 4'),'lock',d.c('read 800b2176 2'),'cam mode',d.c('read 800af934 2'))
d.shot('n3'); d.c('quit')
