import sys; sys.path.insert(0,'.')
from xg import *
def s16(h): v=int(h[2:4]+h[0:2],16); return v-65536 if v>32767 else v
for on in (0,1):
    d=D(); d.c('init xg/sys xg/save')
    for k,v in [('pcsx_rearmed_bios','HLE'),('pcsx_rearmed_memcard1','libretro'),('pcsx_rearmed_memcard2','disabled')]: d.c('var %s %s'%(k,v))
    d.c('load xg/disc1.chd xg/save/n2.srm 2'); d.c('loadstate xg/'+sys.argv[1]); d.c('xga %d 23 xg/xga.bin'%on); d.c('run 5')
    seq=[]; d.c('btn %x'%L)
    for i in range(12): d.c('run 2'); seq.append(s16(d.c('read 800af9e6 2')))
    d.c('btn 0'); 
    rs=[]; d.c('axes 0 0 30000 0')
    for i in range(12): d.c('run 3'); rs.append(s16(d.c('read 800af9e6 2')))
    d.c('axes 0 0 0 0')
    print('mod',on,'L1:',seq,' right stick:',rs,' state',d.c('read 80017f00 16')); d.c('quit')
