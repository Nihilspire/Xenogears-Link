import sys,re; sys.path.insert(0,'.')
from xg import *
from xg_analog import setup
d=setup(True); d.c('loadstate xg/field3.state'); d.c('analog 1'); d.c('run 30'); d.shot('d0')
d.c('btn %x'%DOWN); d.c('run 60'); d.c('btn 0'); d.c('run 5'); d.shot('d1')
d.c('btn %x'%LEFT); d.c('run 60'); d.c('btn 0'); d.c('run 5'); d.shot('d2')
d.c('btn %x'%(1<<10)); d.c('run 40'); d.c('btn 0'); d.c('run 30'); d.shot('d3')   # L1
print('pad rx', d.c('read 800625fc 8'), 'sticks', d.c('read 80059430 12'))
d.c('quit')
