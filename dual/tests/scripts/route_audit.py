"""Audit of Link's story-hint guide line, replaying its own logic (index.html: hintRooms, routeTo, routeHop) over every
hint step, page by page, and from each step into the next. Read-only: prints a report.
  python3 route_audit.py [path/to/assets/link]"""
import json, re, sys, os
from collections import deque, Counter
L = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'app', 'assets', 'link')
def load(fn):
    t = open(os.path.join(L, fn), encoding='utf-8').read(); o = {}
    for m in re.finditer(r'window\.(\w+)\s*=\s*(\{.*?\});?\s*$', t, re.M): o[m.group(1)] = json.loads(m.group(2))
    return o
H = load('hints.js'); X = load('exits.js')
HINTS, HPATH, HNOTE, HPRE = H['HINTS'], H['HPATH'], H['HNOTE'], H.get('HPRE', {})
EX = {int(k): v for k, v in X['EXITS'].items()}
SPLIT = load('hsplit.js').get('HSPLIT', {})
try: AREAS = load('areas.js')
except Exception: AREAS = {}

def route_hop(f, g):                       # index.html routeHop: first room on the fewest-doors way from f to g
    first, q, seen = {}, deque([f]), {f}
    while q:
        r = q.popleft()
        if r == g: return first[r]
        for e in EX.get(r, []):
            d = e[2]
            if d < 0 or d in seen: continue
            if r == f and e[0] is None: continue
            seen.add(d); first[d] = d if r == f else first[r]; q.append(d)
    return None
def doors(f, to):                          # exits of f towards room `to` that have a place (what the line can end on)
    return [e for e in EX.get(f, []) if e[2] == to and e[0] is not None]
def world_exit(f): return any(e[2] == -1 and e[0] is not None for e in EX.get(f, []))
def hint_rooms(k):                         # index.html hintRooms
    if k in HPATH: return [[r[0], r[1]] for r in HPATH[k]]
    pre = HPRE.get(k, [])
    return [[r[0], r[1]] for r in pre] + [[r[0], [[r[2], r[3]]] if len(r) > 3 else []] for r in HINTS[k][:max(1, 3 - len(pre))]]

def leg(a, b):
    """what the guide line does with the party in room a and the page's room b"""
    if a == b: return 'same'
    if a < 0: return 'on world map'                         # drawWorld draws dots only, no line
    if b < 0: return 'ok' if world_exit(a) else 'no line'   # to<0: hop null -> world exit
    hop = route_hop(a, b)
    if hop is None: return 'via world map' if world_exit(a) else 'no line'
    return 'ok' if doors(a, hop) else 'door has no place'

steps = sorted(int(k) for k in HINTS)
res = Counter(); bad = []
prev_last = None
pages_total = spots = 0
for s in steps:
    k = str(s); rooms = hint_rooms(k); pages_total += len(rooms); spots += sum(1 for r in rooms if r[1])
    seq = ([prev_last] if prev_last is not None else []) + [r[0] for r in rooms]
    for i in range(1, len(seq)):
        a, b = seq[i-1], seq[i]
        r = leg(a, b); res[r] += 1
        if r not in ('ok', 'same'):
            # does the hint itself bridge a world-map hop with a world-map page that has a spot?
            bridged = r == 'via world map' and any(x[0] == -1 and x[1] for x in rooms)
            bad.append((s, 'into step' if i == 1 and prev_last is not None else 'page %d' % (i - (1 if prev_last is not None else 0)), a, b, r, bridged))
    prev_last = rooms[-1][0]

print('hint steps: %d  (hand-made path HPATH: %d, from the scripts only: %d)' % (len(steps), sum(1 for s in steps if str(s) in HPATH), sum(1 for s in steps if str(s) not in HPATH)))
print('notes: %d, of them unchecked (grey, "?"): %d; steps with no note: %d' % (len(HNOTE), sum(1 for v in HNOTE.values() if v.startswith('?')), sum(1 for s in steps if str(s) not in HNOTE)))
print('pages: %d, with a green spot: %d; split steps (HSPLIT): %d' % (pages_total, spots, len(SPLIT)))
print('world-map pages: %d (with a spot: %d)' % (sum(1 for s in steps for r in hint_rooms(str(s)) if r[0] < 0), sum(1 for s in steps for r in hint_rooms(str(s)) if r[0] < 0 and r[1])))
print('\nlegs (party in one page\'s room, line to the next):', dict(res))
print('\nlegs with no line or a hand-off to the world map:')
for s, where, a, b, r, br in bad:
    if r == 'on world map': continue
    print('  step %4d %-9s room %4s -> %4s  %s%s' % (s, where, a, b, r, '  (a world-map page with a spot bridges it)' if br else ''))
wm = [x for x in bad if x[4] == 'on world map']
print('\nlegs that start on the world map (no line is drawn there, only the green dot if the page has one): %d' % len(wm))
print('  of them heading into a room with no world-map page before it in the hint: %d' % sum(1 for x in wm if x[1] == 'into step'))

# why no line: the party's room has no exits at all (a scene room: the story moves the party on), the target room has none
# (reached only by a scene), or both have exits and the doors just don't connect them (missing or one-way exits)
def why(a, b):
    if a not in EX: return 'party room has no exits (scene room)'
    if b >= 0 and b not in EX: return 'target room has no exits (reached by a scene)'
    if b >= 0:
        # can b be reached at all if exits were two-way?
        und = {}
        for r, v in EX.items():
            for e in v:
                if e[2] >= 0: und.setdefault(r, set()).add(e[2]); und.setdefault(e[2], set()).add(r)
        q, seen = deque([a]), {a}
        while q:
            r = q.popleft()
            for d in und.get(r, ()):
                if d not in seen: seen.add(d); q.append(d)
        if b in seen: return 'connected only against a one-way exit'
        return 'not connected by any exit (other area, no world-map exit here)'
    return 'no world-map exit from this room'
nl = [x for x in bad if x[4] == 'no line']
print('\nwhy "no line" (%d):' % len(nl))
for k, v in Counter(why(x[2], x[3]) for x in nl).most_common(): print('  %3d  %s' % (v, k))
print('  page legs only (inside one step, the party walking page to page):')
for k, v in Counter(why(x[2], x[3]) for x in nl if x[1] != 'into step').most_common(): print('  %3d  %s' % (v, k))
real = [x for x in nl if x[2] in EX and (x[3] < 0 or x[3] in EX)]
print('  both rooms have exits, still no line:', ['%d:%d->%d' % (x[0], x[2], x[3]) for x in real])

# exits data
null_pos = sum(1 for v in EX.values() for e in v if e[0] is None and e[2] >= 0)
one_way = sorted({(a, e[2]) for a, v in EX.items() for e in v if e[2] >= 0 and not any(x[2] == a for x in EX.get(e[2], []))})
no_exits = sorted({r[0] for s in steps for r in hint_rooms(str(s)) if r[0] >= 0 and r[0] not in EX})
print('\nexits: %d rooms, %d room-to-room exits without a place (BFS skips them from the party\'s room), %d one-way links' % (len(EX), null_pos, len(one_way)))
print('hint rooms with no exits at all:', no_exits[:40], '...' if len(no_exits) > 40 else '')
