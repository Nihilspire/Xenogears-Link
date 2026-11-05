import sys; sys.path.insert(0,'.')
from xg import *
d=D(); d.c('init xg/sys xg/save')
for k,v in [('pcsx_rearmed_bios','HLE'),('pcsx_rearmed_memcard1','libretro'),('pcsx_rearmed_memcard2','disabled')]: d.c('var %s %s'%(k,v))
d.c('load xg/disc1.chd xg/save/real.srm 2'); d.c('loadstate xg/natob_room.state'); d.c('xga 1 23 xg/xga.bin'); d.c('cheat 0 1 80017800 1234'); d.c('run 3')
d.p.stdin.write('diag\n'); d.p.stdin.flush()
while True:
    l=d.p.stdout.readline()
    if l.startswith('<<end>>') or not l: break
    print(l,end='')
d.c('quit')
