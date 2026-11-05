import os as _os
XGROOT=_os.environ.get('XGROOT') or _os.path.abspath(_os.path.join(_os.path.dirname(__file__),'..','..'))
import sys,re,time; sys.path.insert(0,'.')
from xg import *
bios=sys.argv[1] if len(sys.argv)>1 else 'HLE'
tag=sys.argv[2] if len(sys.argv)>2 else 'hle'
d=D(); d.c('init xg/sys xg/save')
for k,v in [('pcsx_rearmed_bios',bios),('pcsx_rearmed_memcard1','libretro'),('pcsx_rearmed_memcard2','disabled'),('pcsx_rearmed_show_bios_bootlogo','disabled')]: d.c('var %s %s'%(k,v))
print(d.c('load xg/disc1.chd xg/save/fb_%s.srm 2'%tag))
cht=open(XGROOT+'/app/assets/analog.cht').read()
codes={int(m.group(1)):m.group(2) for m in re.finditer(r'cheat(\d+)_code = "(.*)"',cht)}
ens={int(m.group(1)):m.group(2)=='true' for m in re.finditer(r'cheat(\d+)_enable = (\w+)',cht)}
# exactly what 0.3/0.4 did: every program entry + enabled options, then analog mode, before the first frame
for i in sorted(codes): d.c('cheat %d %d %s'%(i,1 if ens[i] else 0,codes[i]))
d.c('analog 1')
last=None
for k in range(12):
    t=time.time(); d.c('run 300'); pc=d.c('read 8006faf0 4'); hook=d.c('read 800501fc 4')
    d.shot('fb_%s_%02d'%(tag,k)); print(k, (k+1)*300, 'prog', pc, 'hook', hook, '%.1fs'%(time.time()-t), flush=True)
d.c('quit')
