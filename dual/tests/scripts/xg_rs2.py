import sys,re; sys.path.insert(0,'.')
from xg import *
from xg_analog import setup
d=setup(True); d.c('loadstate xg/field3.state'); d.c('analog 1'); d.c('run 30')
print('cam mode', d.c('read 800af934 2'), 'lock', d.c('read 800b2176 2'), 'flags', d.c('read 800af9d8 2'), 'yaw', d.c('read 800af9e6 2'), 'dip', d.c('read 800af9fc 2'))
d.c('axes 0 0 32000 0'); d.c('run 60'); print('after R-stick right: yaw', d.c('read 800af9e6 2'), 'target', d.c('read 800afa0c 2'))
d.c('axes 0 0 0 32000'); d.c('run 60'); print('after R-stick down: dip', d.c('read 800af9fc 2'))
d.c('axes 0 0 0 0'); d.c('btn %x'%(1<<10)); d.c('run 30'); d.c('btn 0'); d.c('run 10'); print('after L1: yaw', d.c('read 800af9e6 2'))
d.c('quit')
