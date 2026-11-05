import os as _os
XGROOT=_os.environ.get('XGROOT') or _os.path.abspath(_os.path.join(_os.path.dirname(__file__),'..','..'))
import gzip,glob,sys
img=open(XGROOT+'/work/chd/main.exe','rb').read()[0x800:]
sig=img[0x26388:0x26388+32]
for f in sorted(glob.glob(sys.argv[1])):
    d=gzip.decompress(open(f,'rb').read())
    p=d.find(sig)
    if p<0: print(f[:40],'sig not found'); continue
    ram=d[p-0x36388:p-0x36388+0x200000]
    blk=ram[0x17400:0x17C84]; nz=[i for i in range(len(blk)) if blk[i]]
    print('%-50s prog %s block nz %4d %s | 17C84-18000 nz %3d | 17188-17400 nz %3d'%(f.split('/')[-3][:50],ram[0x6faf0:0x6faf4].hex(),len(nz),('%#x..%#x'%(0x80017400+nz[0],0x80017400+nz[-1])) if nz else '',sum(1 for b in ram[0x17C84:0x18004] if b),sum(1 for b in ram[0x17188:0x17400] if b)))
