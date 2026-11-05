import os as _os
XGROOT=_os.environ.get('XGROOT') or _os.path.abspath(_os.path.join(_os.path.dirname(__file__),'..','..'))
import sys,time,re; sys.path.insert(0,'.')
from xg import *
d=D()
d.c('init xg/sys xg/save')
for k,v in [('pcsx_rearmed_bios','HLE'),('pcsx_rearmed_memcard1','libretro'),('pcsx_rearmed_memcard2','disabled')]: d.c('var %s %s'%(k,v))
print(d.c('load xg/disc1.chd xg/save/xeno.srm 2')); d.c('analog 1')
d.c('loadstate xg/boot2400.state'); d.c('analog 1')
cht=open(XGROOT+'/app/assets/analog.cht').read()
codes={int(m.group(1)):m.group(2) for m in re.finditer(r'cheat(\d+)_code = "(.*)"',cht)}
ens={int(m.group(1)):m.group(2)=='true' for m in re.finditer(r'cheat(\d+)_enable = (\w+)',cht)}
for i in sorted(codes): d.c('cheat %d %d %s'%(i,1 if ens[i] else 0,codes[i]))
d.c('run 30'); d.tap(B,4,180); d.tap(UP,6,40); d.shot('ng'); d.tap(B,4,200)   # New Game
t=time.time()
for k in range(int(sys.argv[1]) if len(sys.argv)>1 else 60):
    for j in range(25): d.tap(B,3,17)            # mash Cross through text/FMV prompts
    hook=d.c('read 800501fc 4'); st=d.c('read 80017f00 16')
    if k%6==0: d.shot('arm_n%03d'%k)
    print(k, 'frames~%d'%((k+1)*500), 'hook', hook, 'state', st[:16], '%.0fs'%(time.time()-t), flush=True)
    pass
pass; d.c('quit')
