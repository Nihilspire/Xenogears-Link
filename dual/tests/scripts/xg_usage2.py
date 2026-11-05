import sys,time,re; sys.path.insert(0,'.')
from xg import *
from xg_use import use
d=D(); d.c('init xg/sys xg/save')
for k,v in [('pcsx_rearmed_bios','HLE'),('pcsx_rearmed_memcard1','libretro'),('pcsx_rearmed_memcard2','disabled')]: d.c('var %s %s'%(k,v))
d.c('load xg/disc1.chd xg/save/cardtest.srm 2'); d.c('loadstate xg/newgame.state')
mx=0
for k in range(34):
    for j in range(25): d.tap(B,3,17)
    b=use(d,'newgame %d'%k)
d.shot('u_clean'); d.c('save xg/clean_field.state')
d.tap(X,4,120); use(d,'field menu'); d.shot('u_menu')
d.c('quit')
