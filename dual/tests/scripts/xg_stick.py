import sys,re; sys.path.insert(0,'.')
from xg import *
from xg_analog import setup
d=setup(True); d.c('loadstate xg/field3.state'); d.c('analog 1'); d.c('run 30'); d.shot('s0')
print('hook', d.c('read 800501fc 4'), 'state', d.c('read 80017f00 32'))
d.c('axes 0 30000 0 0')
for i in range(6):
    d.c('run 10'); print(i, 'sticks', d.c('read 80059430 12'), 'tab', d.c('read 800adf68 16'), 'st', d.c('read 80017f00 16'))
d.c('run 40'); d.shot('s1'); d.c('axes -30000 0 0 0'); d.c('run 60'); d.shot('s2'); d.c('axes 0 0 0 0')
d.c('axes 0 0 32000 0'); d.c('run 60'); d.shot('s3'); print('orbit', d.c('read 800afa0c 4'), 'tilt', d.c('read 800af9fc 4'))
d.c('quit')
