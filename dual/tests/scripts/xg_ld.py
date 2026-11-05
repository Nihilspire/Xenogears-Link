import os as _os
XGROOT=_os.environ.get('XGROOT') or _os.path.abspath(_os.path.join(_os.path.dirname(__file__),'..','..'))
import sys,shutil; sys.path.insert(0,'.')
from xg import *
bios=sys.argv[1]; tag=sys.argv[2]
shutil.copy(XGROOT+'/work/host/xg/save/real.srm',XGROOT+'/work/host/xg/save/l_%s.srm'%tag)
d=D(); d.c('init xg/sys xg/save')
for k,v in [('pcsx_rearmed_bios',bios),('pcsx_rearmed_memcard1','libretro'),('pcsx_rearmed_memcard2','disabled'),('pcsx_rearmed_show_bios_bootlogo','disabled')]: d.c('var %s %s'%(k,v))
print(d.c('load xg/disc1.chd xg/save/l_%s.srm 2'%tag))
d.c('run 2700'); d.tap(B,4,180); d.tap(B,4,300); d.c('run 200')
d.tap(B,4,300); d.tap(B,4,300); d.tap(LEFT,6,60); d.shot('%s_l0'%tag); d.tap(B,4,900); d.shot('%s_l1'%tag); d.c('run 600'); d.shot('%s_l2'%tag)
d.c('save xg/%s_loaded.state'%tag); d.c('quit')
