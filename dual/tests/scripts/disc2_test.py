"""Disc 2 in the app's own ways (there's no Disc 2 save to play from, so this covers what can be reached from power-on):
 A  boot Disc 2 with the analog installer on: disc ID, installer state, hook slot, title / Continue screens
 B  swap Disc 1 -> Disc 2 like the pause menu (appendDisc, then setDisc 1), reset, and check the console reads Disc 2
 C  CONTINUE on Disc 2: save a state, then a fresh emulator with Disc 2 first (as continueGame does) loads it straight
    after loadGame; the next frames must match the frames after saving
Needs work/host/xg/disc2.chd. Shots: work/host/xg/shots/d2_*.png"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xg import *
from PIL import Image, ImageChops
OK = []
def check(name, cond, extra=''):
    OK.append(cond); print(('PASS ' if cond else 'FAIL ') + name, extra, flush=True)
def boot(d, srm):
    d.c('init xg/sys xg/save')
    for k, v in [('pcsx_rearmed_bios', 'HLE'), ('pcsx_rearmed_memcard1', 'libretro'), ('pcsx_rearmed_memcard2', 'disabled'), ('pcsx_rearmed_show_bios_bootlogo', 'disabled')]:
        d.c('var %s %s' % (k, v))
def img(n): return Image.open(XGROOT + '/work/host/xg/shots/%s.png' % n).convert('RGB')

# ---- A ----
import shutil; shutil.copy(XGROOT + '/work/host/xg/save/real.srm', XGROOT + '/work/host/xg/save/d2a.srm')
d = D(); boot(d, 'd2a')
r = d.c('load xg/disc2.chd xg/save/d2a.srm 2'); check('A disc 2 loads as SLUS00669', r.endswith('SLUS00669'), r)
d.c('xga 1 23 xg/xga.bin')
states = []
for k in range(9): d.c('run 300'); states.append(d.c('xgastate'))
print('   installer state every 300 frames:', states, ' hook slot', d.c('read 800501fc 4'), ' program', d.c('read 80017400 8'))
check('A analog installer running on Disc 2', states[-1] == '2', '(2 = running)')
check('A VSync hook slot set', d.c('read 800501fc 4') not in ('00000000', '-1'))
d.shot('d2_title'); d.tap(B, 4, 180); d.shot('d2_menu'); d.tap(B, 4, 300); d.c('run 300'); d.shot('d2_continue')
d.c('quit')

# ---- B ----
# The core clears CdromId when it switches discs and only a game load fills it in again, so the ID can't tell which
# disc is in after a swap. Instead: where the two discs' executables differ in RAM after a fresh boot, which one does
# the swapped console match?
EXE = (0x80010000, 0x60000)
def exe_after_boot(disc):
    d = D(); boot(d, 'd2x'); d.c('load xg/%s xg/save/d2x.srm 2' % disc); d.c('run 2700')
    r = bytes.fromhex(d.c('read %x %d' % EXE)); d.c('quit'); return r
e1, e2 = exe_after_boot('disc1.chd'), exe_after_boot('disc2.chd')
diffs = [i for i in range(len(e1)) if e1[i] != e2[i]]
print('   executables differ in %d of %d bytes after boot' % (len(diffs), len(e1)))
d = D(); boot(d, 'd2b')
print('   B load disc 1:', d.c('load xg/disc1.chd xg/save/d2b.srm 2'), ' append disc 2:', d.c('appenddisc xg/disc2.chd'), ' discs:', d.c('discs'))
d.c('run 1200'); r = d.c('setdisc 1'); check('B setDisc(1) accepted', r == '1', r)
d.c('run 60'); ds = d.c('discs'); check('B Disc 2 is the inserted image', ds.split()[0] == '1', ds)
d.c('reset'); d.c('run 2700')
sw = bytes.fromhex(d.c('read %x %d' % EXE))
m1 = sum(sw[i] == e1[i] for i in diffs); m2 = sum(sw[i] == e2[i] for i in diffs)
check('B after the swap and a reset the console runs Disc 2', m2 > 0.95 * len(diffs) and m1 < 0.05 * len(diffs),
      '(matches Disc 2 at %d, Disc 1 at %d of %d differing bytes)' % (m2, m1, len(diffs)))
d.shot('d2_swapped'); d.c('quit')

# ---- C ----
d = D(); boot(d, 'd2c')
d.c('load xg/disc2.chd xg/save/d2c.srm 2'); d.c('appenddisc xg/disc1.chd'); d.c('xga 1 23 xg/xga.bin'); d.c('run 2400')
d.tap(B, 4, 120)
check('C save state on Disc 2', d.c('save xg/d2_resume.state') == '1')
d.c('run 90'); d.shot('d2_c_before'); d.c('quit')
d = D(); boot(d, 'd2c')
d.c('load xg/disc2.chd xg/save/d2c.srm 2'); d.c('appenddisc xg/disc1.chd'); d.c('xga 1 23 xg/xga.bin')
check('C load it straight after loadGame', d.c('loadstate xg/d2_resume.state') == '1')
d.c('run 90'); d.shot('d2_c_after'); print('   discs', d.c('discs'), 'id', d.c('gameid'), 'installer', d.c('xgastate'))
diff = ImageChops.difference(img('d2_c_before'), img('d2_c_after')).getbbox()
check('C same picture 90 frames on as when it was saved', diff is None, 'diff box %s' % (diff,))
d.c('quit')
print('ALL PASS' if all(OK) else '%d FAILED' % OK.count(False))
