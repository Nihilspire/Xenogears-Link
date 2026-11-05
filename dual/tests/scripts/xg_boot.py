import sys,time; sys.path.insert(0,'.')
from xg import *
d=D()
print(d.c('init xg/sys xg/save'))
for k,v in [('pcsx_rearmed_bios','HLE'),('pcsx_rearmed_memcard1','libretro'),('pcsx_rearmed_memcard2','disabled'),('pcsx_rearmed_show_bios_bootlogo','disabled')]: d.c('var %s %s'%(k,v))
t=time.time(); print('load', d.c('load xg/disc1.chd xg/save/xeno.srm 2'))
print('analog', d.c('analog 1'))
for i in range(8):
    t=time.time(); d.c('run 300'); print('frames %d took %.1fs'%((i+1)*300, time.time()-t), d.shot('boot%d'%i), 'prog', d.c('read 8006faf0 4'))
d.c('save xg/boot2400.state'); print('saved')
d.c('quit')
