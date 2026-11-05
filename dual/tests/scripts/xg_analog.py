import os as _os
XGROOT=_os.environ.get('XGROOT') or _os.path.abspath(_os.path.join(_os.path.dirname(__file__),'..','..'))
import sys,time,re; sys.path.insert(0,'.')
from xg import *
def setup(cheats=True):
    d=D(); d.c('init xg/sys xg/save')
    for k,v in [('pcsx_rearmed_bios','HLE'),('pcsx_rearmed_memcard1','libretro'),('pcsx_rearmed_memcard2','disabled')]: d.c('var %s %s'%(k,v))
    d.c('load xg/disc1.chd xg/save/xeno.srm 2'); d.c('loadstate xg/field.state'); d.c('analog 1')
    cht=open(XGROOT+'/app/assets/analog.cht').read()
    codes={int(m.group(1)):m.group(2) for m in re.finditer(r'cheat(\d+)_code = "(.*)"',cht)}
    ens={int(m.group(1)):m.group(2)=='true' for m in re.finditer(r'cheat(\d+)_enable = (\w+)',cht)}
    d.c('clearcheats')
    for i in sorted(codes): d.c('cheat %d %d %s'%(i,1 if (ens[i] and cheats) else 0,codes[i]))
    d.c('run 20'); return d
if __name__=="__main__":
  for label,ch in [('analog',True),('stock',False)]:
     d=setup(ch)
     t0=d.c('read 800adf68 16'); d.shot('%s_0'%label)
     d.c('axes 14000 -28000 0 0'); d.c('run 6'); tab=d.c('read 800adf68 16'); d.c('run 40'); d.shot('%s_1'%label)
     d.c('axes 0 0 0 0'); d.c('run 10')
     o0=d.c('read 800afa0c 4'); d.c('axes 0 0 30000 0'); d.c('run 40'); o1=d.c('read 800afa0c 4'); d.c('axes 0 0 0 0'); d.c('run 30'); d.shot('%s_2'%label)
     print(label, 'dir table before', t0, 'while pushed', tab, '| orbit target', o0, '->', o1)
     if label=='analog':
         d.c('save xg/field2.state')
         ram=d.c('read 80000000 2097152'); open(XGROOT+'/work/host/xg/ram_lahan.hex','w').write(ram)
     d.c('quit')
