import os as _os
XGROOT=_os.environ.get('XGROOT') or _os.path.abspath(_os.path.join(_os.path.dirname(__file__),'..','..'))
import sys,shutil; sys.path.insert(0,'.')
from xg import *
bios=sys.argv[1]; tag=sys.argv[2]
shutil.copy(XGROOT+'/work/host/xg/save/real.srm',XGROOT+'/work/host/xg/save/r_%s.srm'%tag)
d=D(); d.c('init xg/sys xg/save')
for k,v in [('pcsx_rearmed_bios',bios),('pcsx_rearmed_memcard1','libretro'),('pcsx_rearmed_memcard2','disabled'),('pcsx_rearmed_show_bios_bootlogo','disabled')]: d.c('var %s %s'%(k,v))
print(d.c('load xg/disc1.chd xg/save/r_%s.srm 2'%tag))
d.c('run 2700'); d.tap(B,4,180); d.tap(B,4,300); d.c('run 200')
d.tap(DOWN,4,30); d.tap(DOWN,4,30); d.shot('%s_d0'%tag); d.tap(B,4,200); d.shot('%s_d1'%tag); d.tap(B,4,200); d.shot('%s_d2'%tag)
d.tap(LEFT,4,30); d.tap(B,4,400); d.shot('%s_d3'%tag); d.tap(LEFT,4,30); d.tap(B,4,600); d.shot('%s_d4'%tag); d.c('run 300'); d.shot('%s_d5'%tag)
d.c('quit')
import time; time.sleep(1)
x=open(XGROOT+'/work/host/xg/save/r_%s.srm'%tag,'rb').read()
print('dir entry 1 state byte after:', hex(x[0x80]))
