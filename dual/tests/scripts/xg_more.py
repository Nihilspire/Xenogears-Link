import os as _os
XGROOT=_os.environ.get('XGROOT') or _os.path.abspath(_os.path.join(_os.path.dirname(__file__),'..','..'))
import sys,time,re; sys.path.insert(0,'.')
from xg import *
from xg_analog import setup
d=setup(True); d.c('loadstate xg/field2.state'); d.c('analog 1')
for k in range(40):
    for j in range(10): d.tap(B,3,17)
    if k%5==4: d.shot('p%02d'%k)
d.c('save xg/field3.state')
ram=d.c('read 80000000 2097152'); open(XGROOT+'/work/host/xg/ram_lahan2.hex','w').write(ram)
print('prog',d.c('read 8006faf0 4')); d.c('quit')
