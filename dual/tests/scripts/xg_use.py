import sys,time,re; sys.path.insert(0,'.')
from xg import *
def use(d,tag):
    h=d.c('read 80017400 3072'); b=bytes.fromhex(h)
    nz=[i for i in range(0,len(b),4) if b[i:i+4]!=b'\0\0\0\0']
    print('%-28s nonzero words in 80017400-80018000: %4d  first %s  last %s'%(tag,len(nz),hex(0x80017400+nz[0]) if nz else '-',hex(0x80017400+nz[-1]) if nz else '-'),flush=True)
    return b
