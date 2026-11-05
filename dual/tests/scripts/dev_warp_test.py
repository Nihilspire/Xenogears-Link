"""Developer warp and story step (0.22) in the real game: from Fei's room, warp to other rooms, check the room really
loads and the player gets control back and can walk, entrances differ, the story step lands in both copies and survives
a room change, and a warp during a scene gives up instead of forcing it. ARM=1 runs the phone's recompiler under qemu."""
import sys, os, struct; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xg import *
OK = []
def check(n, c, x=''): OK.append(bool(c)); print(('PASS ' if c else 'FAIL ') + n, x, flush=True)
def u16le(h): return int(h[2:4] + h[0:2], 16)
d = D(); d.c('init xg/sys xg/save')
for k, v in [('pcsx_rearmed_bios', 'HLE'), ('pcsx_rearmed_memcard1', 'libretro'), ('pcsx_rearmed_memcard2', 'disabled')]: d.c('var %s %s' % (k, v))
d.c('load xg/disc1.chd xg/save/warp.srm 2'); d.c('loadstate xg/natob_room.state'); d.c('run 30')
def room(): return u16le(d.c('read 8006f94e 2')) & 0x7FF
def lock(): return u16le(d.c('read 800b2176 2'))
def step(): return u16le(d.c('read 8006ef64 2'))
def xz():
    h = d.c('read 800afb10 4'); actors = int(h[6:8] + h[4:6] + h[2:4] + h[0:2], 16)
    h = d.c('read 800b226c 4'); i = int(h[6:8] + h[4:6] + h[2:4] + h[0:2], 16)
    h = d.c('read %x 4' % (actors + i * 0x5c + 0x4c)); ent = int(h[6:8] + h[4:6] + h[2:4] + h[0:2], 16)
    b = bytes.fromhex(d.c('read %x 12' % (ent + 0x20))); x, y, z = struct.unpack('<iii', b)
    return x >> 16, z >> 16
def settle(frames=900):
    # the room number changes at once and the old picture stays for a few seconds, the game briefly looking ready in between:
    # arrived means the load flag has gone up and down, then the player has control
    up = False
    for _ in range(frames // 10):
        d.c('run 10')
        v = int(d.c('read 800afd04 1'), 16)
        if v: up = True
        if up and not v and d.c('devcan') == '1' and room() == want: return True
    return False
start = room(); step0 = step(); print('start room', start, 'step', step0, 'position', xz())
for want, door in [(13, 0), (9, 0), (9, 1), (11, 0)]:
    d.c('devwarp %d %d' % (want, door)); d.c('run 2')
    st = d.c('devstate'); ok = settle()
    d.c('run 30'); p = xz(); check('warp to room %d door %d arrives with control' % (want, door), ok and room() == want, 'state %s room %d lock %04x at %s' % (st, room(), lock(), p))
    if want == 9:
        if door == 0: p0 = p
        else: check('a different entrance is a different place', p != p0, '%s vs %s' % (p0, p))
    d.shot('warp_%d_%d' % (want, door))
# the player can walk after arriving
p0 = xz(); d.c('btn %x' % UP); d.c('run 40'); d.c('btn 0'); d.c('run 10'); p1 = xz()
d.c('axes 0 0 0 0'); d.c('btn %x' % LEFT); d.c('run 40'); d.c('btn 0'); d.c('run 10'); p2 = xz()
check('the player can walk after a warp', p0 != p1 or p1 != p2, '%s -> %s -> %s' % (p0, p1, p2))
# story step: both copies, and it survives a room change
d.c('devstory 21'); d.c('run 2')
vars0 = u16le(d.c('read 800c3a68 2'))
check('story step lands in both copies', step() == 21 and vars0 == 21, 'saved %d, live %d' % (step(), vars0))
want = 13; d.c('devwarp 13 0'); d.c('run 2'); settle()
check('story step survives a room change', step() == 21 and room() == 13, 'step %d room %d' % (step(), room()))
# a warp while the player has no control (here, the console booting) waits, then gives up, and leaves the game alone
d.c('reset'); d.c('devwarp 13 0'); d.c('run 300'); mid = d.c('devstate'); d.c('run 310'); end = d.c('devstate')
check('a warp with no player control waits, then gives up', mid == '1' and end == '3', 'after 5 s %s, after 10 s %s' % (mid, end))
print('ALL PASS' if all(OK) else '%d FAILED' % OK.count(False))
d.c('quit')
