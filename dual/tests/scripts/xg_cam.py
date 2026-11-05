import sys,re; sys.path.insert(0,'.')
from xg import *
from xg_analog import setup
for label,ch in [('analog',True),('stock',False)]:
    d=setup(ch); d.c('loadstate xg/field3.state'); d.c('analog 1'); d.c('run 30')
    d.shot('c_%s_0'%label); o0=d.c('read 800afa0c 4'); tilt0=d.c('read 800af9fc 4')
    d.c('axes 0 0 30000 0'); d.c('run 45'); o1=d.c('read 800afa0c 4'); d.c('axes 0 0 0 0'); d.c('run 30'); d.shot('c_%s_1'%label)
    d.c('axes 0 0 0 30000'); d.c('run 45'); d.c('axes 0 0 0 0'); d.c('run 20'); tilt1=d.c('read 800af9fc 4'); d.shot('c_%s_2'%label)
    d.c('axes 23000 -23000 0 0'); d.c('run 50'); d.c('axes 0 0 0 0'); d.c('run 10'); d.shot('c_%s_3'%label)
    print(label,'orbit target',o0,'->',o1,'| tilt',tilt0,'->',tilt1)
    d.c('quit')
