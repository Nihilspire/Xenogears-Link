"""Makes save-state style thumbnails (192 wide, 4:3, JPEG like the app's) from the test states, for the UI tests.
Usage: python3 thumbs.py  -> work/host/xg/shots/thumb_<state>.jpg"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xg import *
from PIL import Image
d = D(); d.c('init xg/sys xg/save')
for k, v in [('pcsx_rearmed_bios', 'HLE'), ('pcsx_rearmed_memcard1', 'libretro'), ('pcsx_rearmed_memcard2', 'disabled')]: d.c('var %s %s' % (k, v))
print(d.c('load xg/disc1.chd xg/save/thumbs.srm 2'))
for st in ['natob_room', 'lh_loaded', 'clean_field', 'newgame']:
    print(st, d.c('loadstate xg/%s.state' % st)); d.c('run 3'); d.shot('st_' + st)
    im = Image.open(XGROOT + '/work/host/xg/shots/st_%s.png' % st).convert('RGB').resize((192, 144), Image.BILINEAR)
    im.save(XGROOT + '/work/host/xg/shots/thumb_%s.jpg' % st, quality=85)
d.c('quit')
