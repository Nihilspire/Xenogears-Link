import os as _os
XGROOT=_os.environ.get('XGROOT') or _os.path.abspath(_os.path.join(_os.path.dirname(__file__),'..','..'))
import subprocess, sys, time, os
from PIL import Image
class D:
    def __init__(s):
        arm=os.environ.get('ARM')=='1'
        s.p=subprocess.Popen(['qemu-aarch64','-L','/usr/aarch64-linux-gnu','./drive'] if arm else ['./drive'],cwd=XGROOT+'/work/arm' if arm else (XGROOT+'/work/hostdbg' if os.environ.get('DBG') else XGROOT+'/work/host'),stderr=open(os.environ['ERRF'],'w') if os.environ.get('ERRF') else None,stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1)
    def c(s,cmd):
        s.p.stdin.write(cmd+'\n'); s.p.stdin.flush(); return s.p.stdout.readline().strip()
    def shot(s,name):
        r=s.c('shot xg/shots/%s.ppm'%name); Image.open(XGROOT+'/work/host/xg/shots/%s.ppm'%name).save(XGROOT+'/work/host/xg/shots/%s.png'%name); return r
    def tap(s,mask,hold=4,after=20):
        s.c('btn %x'%mask); s.c('run %d'%hold); s.c('btn 0'); s.c('run %d'%after)
B,Y,SEL,START,UP,DOWN,LEFT,RIGHT,A,X,L,R=[1<<i for i in range(12)]
