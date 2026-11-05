import os as _os
XGROOT=_os.environ.get('XGROOT') or _os.path.abspath(_os.path.join(_os.path.dirname(__file__),'..','..'))
import sys,os; sys.path.insert(0,'.')
from xg import *
for f in [XGROOT+'/work/host/xg/save/fresh.srm']:
    if os.path.exists(f): os.remove(f)
d=D(); d.c('init xg/sys xg/save')
for k,v in [('pcsx_rearmed_bios','HLE'),('pcsx_rearmed_memcard1','libretro'),('pcsx_rearmed_memcard2','disabled')]: d.c('var %s %s'%(k,v))
print(d.c('load xg/disc1.chd xg/save/fresh.srm 0'))
d.c('run 2400'); d.tap(B,4,180); d.shot('k1')      # opens title menu, cursor on Continue
d.tap(B,4,200); d.shot('k2')                        # Continue -> card screen
d.c('quit')
