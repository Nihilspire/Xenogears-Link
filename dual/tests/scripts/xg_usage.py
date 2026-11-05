import sys,time,re; sys.path.insert(0,'.')
from xg import *
def use(d,tag):
    h=d.c('read 80017400 3072'); b=bytes.fromhex(h)
    nz=[i for i in range(0,len(b),4) if b[i:i+4]!=b'\0\0\0\0']
    print('%-28s nonzero words in 80017400-80018000: %4d  first %s  last %s'%(tag,len(nz),hex(0x80017400+nz[0]) if nz else '-',hex(0x80017400+nz[-1]) if nz else '-'),flush=True)
    return b
if __name__=="__main__":
  d=D(); d.c('init xg/sys xg/save')
 for k,v in [('pcsx_rearmed_bios','HLE'),('pcsx_rearmed_memcard1','libretro'),('pcsx_rearmed_memcard2','disabled')]: d.c('var %s %s'%(k,v))
 d.c('load xg/disc1.chd xg/save/cardtest.srm 2')
 for k in range(8):
     d.c('run 300'); use(d,'boot %d'%((k+1)*300))
 d.tap(B,4,180); use(d,'title menu'); d.shot('u_title')
 d.tap(B,4,300); use(d,'continue/card screen'); d.shot('u_card')
 d.c('run 300'); use(d,'card screen +300')
 d.tap(B,4,300); use(d,'card screen +cross'); d.shot('u_card2')
 d.tap(B,4,300); use(d,'card screen +cross2'); d.shot('u_card3')
 d.c('loadstate xg/field.state'); d.c('run 20'); use(d,'field (state)')
 d.tap(X,4,120); use(d,'field menu'); d.shot('u_menu')
 for i in range(6):
     d.tap(DOWN,3,20); d.tap(B,4,120); use(d,'menu item %d'%i); d.shot('u_m%d'%i); d.tap(A,4,60); d.tap(A,4,60)
 d.c('quit')
