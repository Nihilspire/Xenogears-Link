import sys,time,os; sys.path.insert(0,'.')
from xg import *
d=D(); d.c('init xg/sys xg/save')
for k,v in [('pcsx_rearmed_bios','HLE'),('pcsx_rearmed_memcard1','libretro'),('pcsx_rearmed_memcard2','disabled'),('pcsx_rearmed_drc','enabled')]: d.c('var %s %s'%(k,v))
print(d.c('load xg/disc1.chd xg/save/arm.srm 2'))
for k in range(4):
    t=time.time(); d.c('run 300'); print((k+1)*300,'prog',d.c('read 8006faf0 4'),'%.1fs'%(time.time()-t),flush=True)
d.shot(os.environ.get('TAG','arm_boot')); d.c('quit')
