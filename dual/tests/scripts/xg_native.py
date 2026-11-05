import sys,time,re,os; sys.path.insert(0,'.')
from xg import *
bios,tag=sys.argv[1],sys.argv[2]
d=D(); d.c('init xg/sys xg/save')
for k,v in [('pcsx_rearmed_bios',bios),('pcsx_rearmed_memcard1','libretro'),('pcsx_rearmed_memcard2','disabled'),('pcsx_rearmed_show_bios_bootlogo','disabled')]: d.c('var %s %s'%(k,v))
print(d.c('load xg/disc1.chd xg/save/nat_%s.srm 2'%tag))
print('xga ->', d.c('xga 1 23 xg/xga.bin'))
for k in range(9):
    d.c('run 300'); print((k+1)*300,'state',d.c('xgastate'),'hook',d.c('read 800501fc 4'),'prog',d.c('read 8006faf0 4'),flush=True)
d.tap(B,4,180); d.tap(UP,6,40); d.tap(B,4,200)
t=time.time()
for k in range(int(os.environ.get('N','30'))):
    for j in range(25): d.tap(B,3,17)
    if k%5==4: print(k,'state',d.c('xgastate'),'hook',d.c('read 800501fc 4'),'prog',d.c('read 8006faf0 4'),'%.0fs'%(time.time()-t),flush=True)
d.c('run 60'); d.shot('%s_room'%tag)
t0=d.c('read 800adf68 16'); p0=d.c('read 800b2176 2')
d.c('axes 14000 -28000 0 0'); d.c('run 6'); tab=d.c('read 800adf68 16'); d.c('run 60'); d.shot('%s_walk'%tag); d.c('axes 0 0 0 0'); d.c('run 10')
print('dir table', t0, '-> pushed', tab, '| after release', d.c('read 800adf68 16'))
d.c('save xg/%s_room.state'%tag); d.c('quit')
