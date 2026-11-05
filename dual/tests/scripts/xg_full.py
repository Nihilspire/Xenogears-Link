import os as _os
XGROOT=_os.environ.get('XGROOT') or _os.path.abspath(_os.path.join(_os.path.dirname(__file__),'..','..'))
import sys,time,re,os; sys.path.insert(0,'.')
from xg import *
bios,tag,cheats=sys.argv[1],sys.argv[2],sys.argv[3]=='1'
d=D(); d.c('init xg/sys xg/save')
for k,v in [('pcsx_rearmed_bios',bios),('pcsx_rearmed_memcard1','libretro'),('pcsx_rearmed_memcard2','disabled'),('pcsx_rearmed_show_bios_bootlogo','disabled')]: d.c('var %s %s'%(k,v))
print(d.c('load xg/disc1.chd xg/save/full_%s.srm 2'%tag))
cht=open(XGROOT+'/app/assets/analog.cht').read()
codes={int(m.group(1)):m.group(2) for m in re.finditer(r'cheat(\d+)_code = "(.*)"',cht)}
ens={int(m.group(1)):m.group(2)=='true' for m in re.finditer(r'cheat(\d+)_enable = (\w+)',cht)}
if cheats:
    for i in sorted(codes): d.c('cheat %d %d %s'%(i,1 if ens[i] else 0,codes[i]))
d.c('analog 1')
d.c('run 2700'); d.tap(B,4,180); d.tap(UP,6,40); d.shot('%s_ng'%tag); d.tap(B,4,200)
t=time.time(); last=None; same=0
for k in range(int(os.environ.get('N','34'))):
    for j in range(25): d.tap(B,3,17)
    hook=d.c('read 800501fc 4'); fr=d.c('read 8006faf0 4')
    if k%6==5: d.shot('%s_%03d'%(tag,k))
    print(k,'hook',hook,'prog',fr,'%.0fs'%(time.time()-t),flush=True)
d.shot('%s_end'%tag); d.c('save xg/%s_end.state'%tag); d.c('quit')
