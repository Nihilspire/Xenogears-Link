"""stateBytes (0.20 safety save): at the same frame it must give exactly what saveState writes, and load back to the same picture.
Uses lh_loaded.state (Disc 1) and, if work/host/xg/disc2.chd is there, Disc 2's title screen."""
import sys, os, filecmp; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xg import *
from PIL import Image, ImageChops
OK = []
def check(n, c, x=''): OK.append(c); print(('PASS ' if c else 'FAIL ') + n, x, flush=True)
def boot(d):
    d.c('init xg/sys xg/save')
    for k, v in [('pcsx_rearmed_bios', 'HLE'), ('pcsx_rearmed_memcard1', 'libretro'), ('pcsx_rearmed_memcard2', 'disabled')]: d.c('var %s %s' % (k, v))
X = XGROOT + '/work/host/xg/'
for disc, prep in [('disc1.chd', 'loadstate xg/lh_loaded.state'), ('disc2.chd', None)]:
    if not os.path.exists(X + disc): continue
    d = D(); boot(d); d.c('load xg/%s xg/save/sb.srm 2' % disc)
    if prep: d.c(prep)
    d.c('run %d' % (60 if prep else 2400))
    # two saves in a row differ in one byte themselves (the core bumps a counter on every save), so compare against that
    d.c('save xg/sb_file0.state'); n = d.c('statebytes xg/sb_bytes.state'); d.c('save xg/sb_file.state')
    check(disc + ': stateBytes size', n.isdigit() and int(n) == os.path.getsize(X + 'sb_file.state'), '%s vs %d' % (n, os.path.getsize(X + 'sb_file.state')))
    f0, sb, f1 = (open(X + p, 'rb').read() for p in ('sb_file0.state', 'sb_bytes.state', 'sb_file.state'))
    noise = {i for i in range(len(f0)) if f0[i] != f1[i]}
    off = {i for i in range(len(sb)) if sb[i] != f1[i]}
    check(disc + ': same bytes as saveState (apart from the save counter)', off <= noise, 'differs at %s; two saves differ at %s' % (sorted(off)[:6], sorted(noise)[:6]))
    d.c('run 60'); d.shot('sb_a'); d.c('quit')
    d = D(); boot(d); d.c('load xg/%s xg/save/sb.srm 2' % disc)
    check(disc + ': loads back', d.c('loadstate xg/sb_bytes.state') == '1')
    d.c('run 60'); d.shot('sb_b'); d.c('quit')
    diff = ImageChops.difference(Image.open(X + 'shots/sb_a.png').convert('RGB'), Image.open(X + 'shots/sb_b.png').convert('RGB')).getbbox()
    check(disc + ': same picture 60 frames on', diff is None, diff)
print('ALL PASS' if all(OK) else '%d FAILED' % OK.count(False))
