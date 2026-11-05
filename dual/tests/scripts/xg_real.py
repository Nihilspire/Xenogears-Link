import os as _os
XGROOT=_os.environ.get('XGROOT') or _os.path.abspath(_os.path.join(_os.path.dirname(__file__),'..','..'))
import sys,shutil; sys.path.insert(0,'.')
from xg import *
bios=sys.argv[1]; tag=sys.argv[2]
shutil.copy(XGROOT+'/work/host/xg/save/real.srm',XGROOT+'/work/host/xg/save/r_%s.srm'%tag)
d=D(); d.c('init xg/sys xg/save')
for k,v in [('pcsx_rearmed_bios',bios),('pcsx_rearmed_memcard1','libretro'),('pcsx_rearmed_memcard2','disabled'),('pcsx_rearmed_show_bios_bootlogo','disabled')]: d.c('var %s %s'%(k,v))
print(d.c('load xg/disc1.chd xg/save/r_%s.srm 2'%tag), 'card', d.c('cardstatus'))
d.c('run 2700'); d.tap(B,4,180); d.shot('%s_menu'%tag)
d.tap(B,4,300); d.shot('%s_c1'%tag)
d.c('run 300'); d.shot('%s_c2'%tag)
d.tap(B,4,300); d.shot('%s_c3'%tag)
d.tap(B,4,300); d.shot('%s_c4'%tag)
d.c('quit')
