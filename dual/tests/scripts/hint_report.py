"""The page for hint_sweep.py's results: every hint, what each of its pages does, and the pictures.
  python3 hint_report.py SWEEP_DIR OUT_DIR
Writes OUT_DIR/index.html plus shots_N.js (the pictures, loaded when a row is opened)."""
import base64, json, os, re, sys, collections as C
HERE = os.path.dirname(os.path.abspath(__file__)); LINK = os.path.join(HERE, '..', '..', 'app', 'assets', 'link')
sweep, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
R = json.load(open(os.path.join(sweep, 'results.json')))
def load(fn):
    t = open(os.path.join(LINK, fn), encoding='utf-8').read(); o = {}
    for m in re.finditer(r'window\.(\w+)\s*=\s*([\{\[].*?[\}\]]);?\s*$', t, re.M): o[m.group(1)] = json.loads(m.group(2))
    return o
H = load('hints.js'); HINTS, HPATH, HPRE, HNOTE = H['HINTS'], H['HPATH'], H.get('HPRE', {}), H['HNOTE']
AREAS = load('areas.js')['AREAS']
def area(f):
    if f is None: return ''
    if f < 0: return 'World map'
    for a in AREAS:
        if a[0] <= f <= a[1]: return a[2]
    return ''
NAMES = {}
for r in R['results']:
    m = re.match(r'R(\d+)_(.+)', r['name'])
    if m: NAMES[int(m.group(1))] = m.group(2).replace('_-_', ': ').replace('_', ' ')
def rname(f): return 'World map' if f is not None and f < 0 else '%s %s' % (f, NAMES.get(f) or area(f))
def hrooms(k):
    if k in HPATH: return [[q[0], len(q[1])] for q in HPATH[k]]
    pre = HPRE.get(k, [])
    return [[q[0], len(q[1])] for q in pre] + [[q[0], 1 if len(q) > 3 else 0] for q in HINTS[k][:max(1, 3 - len(pre))]]

EX = {int(k): v for k, v in load('exits.js')['EXITS'].items()}
def out_by_doors(f):
    """can the party walk from f, through doors with places, to a room with a way out to the world map?"""
    seen, q = {f}, [f]
    while q:
        r = q.pop()
        for e in EX.get(r, []):
            if e[2] == -1 and e[0] is not None and r != f: return True
            if e[2] >= 0 and e[2] not in seen and e[0] is not None: seen.add(e[2]); q.append(e[2])
    return False
def refine(p):
    """why there's no way: a door Link knows but can't place, a walk out to the world map Link doesn't look for (both Link's to fix),
    or no doors at all between the rooms, which is right when a scene or transport takes the party there. No floor connection from a
    place off the floor says nothing about real play."""
    if p['st'] == 'noway':
        if p.get('hop') is not None: p['st'] = 'nodoor'
        elif p.get('here') is not None and out_by_doors(p['here']):
            to = p.get('toRoom')    # both ends must open onto the world map for that to be the way
            if to is not None and (to < 0 or out_by_doors(to) or any(e[2] == -1 and e[0] is not None for e in EX.get(to, []))): p['st'] = 'walkout'
    if p['st'] == 'noline' and p.get('partyOn') is False: p['st'] = 'offfloor'
for r in R['results']:
    for p in r['pages'] + r.get('nextPages', []): refine(p)
SEV = {'spot': 0, 'door': 0, 'worldexit': 0, 'arrived': 0, 'nomap': 1, 'short': 1, 'noway': 1, 'offfloor': 1, 'walkout': 2, 'nodoor': 2, 'noline': 2, 'stuck': 2, 'noparty': -1, 'world': -1, 'worldaway': -1, 'nopage': -1, None: -1}
K = sorted(map(int, HINTS)); walk = [r for r in R['results'] if r['kind'] == 'walk']; saved = [r for r in R['results'] if r['kind'] == 'saved']
byhint = C.defaultdict(list); [byhint[r['hint']].append(r) for r in walk]
savedby = C.Counter(r['head']['hint'] for r in saved)
stuck = {(s['hint'], s['room']) for s in R['stuck']}
used = set(); rows = []
def rec(p, res=None, label=None):
    o = dict(st=p['st'], gap=p.get('gap'), len=p.get('len'), shot=p.get('shot'), on=p.get('partyOn'), here=p.get('here'), res=res)
    if p.get('spotsOff'): o['off'] = p['spotsOff']
    if o['shot']: used.add(o['shot'])
    return o
for i, k in enumerate(K):
    ks = str(k); rooms = hrooms(ks); pages = []
    prev = rooms[0][0]
    for pg, (room, nsp) in enumerate(rooms):
        e = dict(n=pg + 1, room=room, name=rname(room), spots=nsp, at=None, way=None)
        for r in byhint[k]:
            if r['room'] == room:
                for p in r['pages']:
                    if p['pg'] == pg: e['at'] = rec(p, r['result'])
            if pg and r['room'] == rooms[pg - 1][0]:
                for p in r['pages']:
                    if p['pg'] == pg: e['way'] = rec(p, r['result']); e['from'] = rname(r['room'])
        if room >= 0 and (k, room) in stuck: e['at'] = dict(st='stuck')
        if pg == 0 and i:          # coming from the last room of the hint before
            for r in byhint[K[i - 1]]:
                for p in r.get('nextPages', []):
                    if p['pg'] == 0 and r.get('nextHead', {}).get('hint') == k: e['way'] = rec(p, r['result']); e['from'] = rname(r['room']) + ' (end of hint %d)' % K[i - 1]
        pages.append(e)
    checks = [c for e in pages for c in (e['at'], e['way']) if c]
    worst = max([SEV[c['st']] for c in checks] + [1 if c.get('off') else -1 for c in checks] + [-1])
    tested = sum(1 for c in checks if SEV[c['st']] >= 0)
    shown = {r['head']['hint'] for r in byhint[k]} - {k}
    note = HNOTE.get(ks, ''); unv = note.startswith('?')
    rows.append(dict(k=k, step=K[i - 1] if i else 0, note=note[1:] if unv else note, unv=unv, pages=pages, worst=worst, tested=tested, saved=savedby.get(k, 0), shown=sorted(shown)))
# saved dumps: where real play found no line, one row per hint, page and room
sv = {}
for r in saved:
    for p in r['pages']:
        if SEV[p['st']] >= 1:
            key = (r['head']['hint'], p['pg'], p['here'], p['toRoom'], p['st'])
            if key not in sv: sv[key] = dict(k=key[0], pg=key[1] + 1, here=rname(key[2]), to=rname(key[3]), st=key[4], gap=p.get('gap'), shot=p.get('shot'), on=p.get('partyOn'), n=0); used.add(p.get('shot'))
            sv[key]['n'] += 1
svrows = sorted(sv.values(), key=lambda s: (s['k'], s['pg']))
savedc = C.Counter(p['st'] for r in saved for p in r['pages'])
# pictures
chunks = [[]]; size = 0; where = {}
for s in sorted(x for x in used if x):
    b = base64.b64encode(open(os.path.join(sweep, 'shots', s), 'rb').read()).decode()
    if size + len(b) > 3 << 20: chunks.append([]); size = 0
    chunks[-1].append((s, b)); size += len(b); where[s] = len(chunks) - 1
for i, c in enumerate(chunks):
    open(os.path.join(out, 'shots_%d.js' % i), 'w').write('__S(' + json.dumps(dict(c)) + ');')
stats = dict(hints=len(K), walk=len(walk), saved=len(saved), errs=sum(1 for r in R['results'] if r['errs']), savedHints=len([k for k in K if savedby.get(k)]), rooms=len({r['room'] for r in walk}),
             res=C.Counter(r['result'] for r in walk), stuck=len(R['stuck']), savedc=savedc, savedsteps=len({r['head']['step'] for r in saved}))
html = open(os.path.join(HERE, 'hint_report.tpl.html'), encoding='utf-8').read().replace('/*DATA*/', 'var ROWS=%s,SV=%s,ST=%s,WHERE=%s;' % (json.dumps(rows), json.dumps(svrows), json.dumps(stats), json.dumps(where)))
open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(html)
print('hints', len(rows), C.Counter(r['worst'] for r in rows), 'saved rows', len(svrows), 'pictures', len(where), 'chunks', len(chunks))
for w, l in ((2, 'problems'), (1, 'check')):
    print(l, [(r['k']) for r in rows if r['worst'] == w])
print('not tested', [(r['k']) for r in rows if r['tested'] == 0])
pairs = C.Counter((rname(c['here']), e['name'], c['st']) for r in rows for e in r['pages'] for c in [e['way']] if c and c['st'] in ('walkout', 'nodoor'))
print(len(pairs), list(pairs.items())[:40])
print(C.Counter(c['st'] for r in rows for e in r['pages'] for c in (e['at'], e['way']) if c))
print('off', sum(1 for r in rows for e in r['pages'] for c in (e['at'], e['way']) if c and c.get('off')))
