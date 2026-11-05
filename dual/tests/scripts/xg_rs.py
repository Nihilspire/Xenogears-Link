import sys,re; sys.path.insert(0,'.')
from xg import *
from xg_analog import setup
d=setup(True); d.c('loadstate xg/field3.state'); d.c('analog 1'); d.c('run 30')
d.shot('r0')
d.c('axes 0 0 32000 0')
for i in range(5):
    d.c('run 12'); print('rstick', d.c('read 80059444 12'), 'orbit', d.c('read 800afa08 8'), 'st', d.c('read 80017f00 32'))
d.shot('r1'); d.c('axes 0 0 0 -32000'); d.c('run 40'); print('tilt', d.c('read 800af9fc 4')); d.shot('r2')
d.c('axes 0 0 0 0'); d.c('run 10'); d.c('quit')
