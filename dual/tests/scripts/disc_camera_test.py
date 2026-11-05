"""Boots a patched Disc 1 (.cue) from power-on to Fei's room with the frontend's analog installer off (the program comes
from the disc patch itself), then measures the camera like xg_nat6.py: yaw at 0x800AF9E6 while holding L1, then while
pushing the right stick. With the camera-mode lw bug the right stick does nothing in Fei's room.
Usage: python3 disc_camera_test.py tag path/to/patched.cue   (shots in work/host/xg/shots/<tag>_*.png)"""
import sys, os, time; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xg import *
def s16(h): v = int(h[2:4] + h[0:2], 16); return v - 65536 if v > 32767 else v
tag, cue = sys.argv[1], sys.argv[2]
d = D(); d.c('init xg/sys xg/save')
for k, v in [('pcsx_rearmed_bios', 'HLE'), ('pcsx_rearmed_memcard1', 'libretro'), ('pcsx_rearmed_memcard2', 'disabled'), ('pcsx_rearmed_show_bios_bootlogo', 'disabled')]:
    d.c('var %s %s' % (k, v))
print(tag, 'load', d.c('load %s xg/save/disc_%s.srm 2' % (cue, tag)))
t = time.time()
d.c('run 2700'); d.c('analog 1')
# the same way into a new game as xg_native.py
d.tap(B, 4, 180); d.tap(UP, 6, 40); d.tap(B, 4, 200)
for k in range(30):
    for j in range(25): d.tap(B, 3, 17)
d.c('analog 1'); d.c('run 60'); d.shot('%s_room' % tag)
print(tag, 'in room after %.0fs; hook slot' % (time.time() - t), d.c('read 800501fc 4'), 'camera mode', d.c('read 800af934 4'))
l1 = []; d.c('btn %x' % L)
for i in range(12): d.c('run 2'); l1.append(s16(d.c('read 800af9e6 2')))
d.c('btn 0'); d.c('run 30')
rs = []; d.c('axes 0 0 30000 0')
for i in range(12): d.c('run 3'); rs.append(s16(d.c('read 800af9e6 2')))
d.c('axes 0 0 0 0'); d.shot('%s_after' % tag)
print(tag, 'L1:', l1); print(tag, 'right stick:', rs)
print(tag, 'RESULT right stick turns camera:', len(set(rs)) > 1)
d.c('quit')
