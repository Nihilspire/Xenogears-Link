"""Go to every room every story hint names, in the real game, and dump main RAM there for hint_sweep.py.

For each hint: load a state, set the story step to the one that shows that hint, warp to each page's room, let it settle,
dump. Not real play: the game's other switches are those of the state, the party is whoever it holds, and the room is
entered by door 0. It says where the picture and route are right or wrong, not whether a scene would really play.
  python3 hint_walk.py OUT_DIR [workers] [only hint step ...]
Writes OUT_DIR/s<hint>_r<room>.bin and OUT_DIR/walk.json ({"file":..,"hint":..,"step":..,"room":..,"result":..}). Rooms not found
on Disc 1 are tried on Disc 2. Result: control (the player can move), skipped (can after pressing through a scene), scene (never can),
stuck (the room never loaded).
The step in a dump can have moved on from the one set: hint_sweep.py sets it back before showing Link the dump."""
import json, os, re, subprocess, sys, threading, queue
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xg import D
HERE = os.path.dirname(os.path.abspath(__file__))
LINK = os.path.join(HERE, '..', '..', 'app', 'assets', 'link')
PATIENCE = 1500       # frames to wait for a room to load and hand over control (25 s)
SETTLE = 60
MASH = 1200           # frames to press through a scene

def load(fn):
    t = open(os.path.join(LINK, fn), encoding='utf-8').read(); o = {}
    for m in re.finditer(r'window\.(\w+)\s*=\s*(\{.*?\});?\s*$', t, re.M): o[m.group(1)] = json.loads(m.group(2))
    return o
H = load('hints.js'); HINTS, HPATH, HPRE = H['HINTS'], H['HPATH'], H.get('HPRE', {})
def hint_rooms(k):    # index.html hintRooms
    if k in HPATH: return [r[0] for r in HPATH[k]]
    pre = HPRE.get(k, [])
    return [r[0] for r in pre] + [r[0] for r in HINTS[k][:max(1, 3 - len(pre))]]

def jobs(only):
    K = sorted(map(int, HINTS)); out = []
    for i, k in enumerate(K):
        if only and k not in only: continue
        seen = set()
        for r in hint_rooms(str(k)):
            if r >= 0 and r not in seen: seen.add(r); out.append((k, K[i - 1] if i else 0, r))
    return out

def u16le(h): return int(h[2:4] + h[0:2], 16)
def start():
    d = D(); d.c('init xg/sys xg/save')
    for k, v in [('pcsx_rearmed_bios', 'HLE'), ('pcsx_rearmed_memcard1', 'libretro'), ('pcsx_rearmed_memcard2', 'disabled')]: d.c('var %s %s' % (k, v))
    d.c('load xg/disc1.chd xg/save/walk%d.srm 2' % threading.get_ident()); d.c('appenddisc xg/disc2.chd')
    return d

def program(d): return int(d.c('read 8006faf0 1'), 16)
def here(d): return u16le(d.c('read 8006f94e 2')) & 0x7FF
def has_control(d, room): return program(d) == 4 and here(d) == room and d.c('devcan') == '1'
def arrive(d, room, patience=PATIENCE):
    """until the new room has loaded. The room number changes at once and the old picture stays for a few seconds, with the game
    briefly looking ready in between, so wait for the load flag (0x800AFD04) to go up and come down."""
    up = False
    for _ in range(patience // 10):
        d.c('run 10')
        v = int(d.c('read 800afd04 1'), 16)
        if v: up = True
        elif up: return True
    return False

def visit(d, step, room, disc, dump):
    """'control' the player can move, 'skipped' can move after pressing through a scene, 'scene' never can, 'stuck' the room didn't load"""
    d.c('loadstate xg/natob_room.state'); d.c('run 5')
    if disc: d.c('setdisc 1'); d.c('run 5')
    d.c('devstory %d' % step); d.c('run 2'); d.c('devwarp %d 0' % room)
    if not arrive(d, room): return 'stuck'
    d.c('run 30'); dump()                                 # a first look: the room is in memory even if a scene has hold of it
    for _ in range(6):
        if has_control(d, room): d.c('run %d' % SETTLE); dump(); return 'control'
        d.c('run 30')
    for i in range(MASH // 40):
        d.c('btn %x' % (0x100 if i % 2 else 1)); d.c('run 6'); d.c('btn 0'); d.c('run 34')
        if program(d) != 4 or here(d) != room: return 'scene'   # it left for a fight, a menu or another room: keep the first look
        if has_control(d, room):
            d.c('run 30')
            if has_control(d, room): dump(); return 'skipped'
    return 'scene'

def worker(q, out, rows, lock):
    d = None
    while True:
        try: k, step, room = q.get_nowait()
        except queue.Empty: break
        name = 's%d_r%d.bin' % (k, room); row = dict(file=name, hint=k, step=step, room=room); path = os.path.abspath(os.path.join(out, name))
        def snap(): d.c('dumpram ' + path); d.c('shot ' + path[:-4] + '.ppm')
        for disc in (0, 1):
            try:
                if d is None: d = start()
                row['result'] = visit(d, step, room, disc, snap); row['disc'] = disc + 1
            except Exception as e:
                row['result'] = 'stuck'; row['error'] = str(e)[:80]; row['disc'] = disc + 1
                try: d.p.kill()
                except Exception: pass
                d = None
                continue
            if row['result'] != 'stuck': break
        with lock:
            rows.append(row); print(len(rows), row, flush=True)
    if d is not None:
        try: d.c('quit')
        except Exception: pass

if __name__ == '__main__':
    out = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 4; only = set(map(int, sys.argv[3:]))
    os.makedirs(out, exist_ok=True)
    q = queue.Queue(); [q.put(j) for j in jobs(only)]; print('rooms to visit', q.qsize(), flush=True)
    rows = []; lock = threading.Lock(); T = [threading.Thread(target=worker, args=(q, out, rows, lock)) for _ in range(n)]
    [t.start() for t in T]; [t.join() for t in T]
    rows.sort(key=lambda r: (r['hint'], r['room'])); json.dump(rows, open(os.path.join(out, 'walk.json'), 'w'), indent=0)
    from collections import Counter; print(Counter(r['result'] for r in rows))
