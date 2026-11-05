#!/usr/bin/env python3
"""mk_linkdata.py ASSETS OUT.h: Link's data as C tables for the 3DS Link screen, plus the analog controls program.

Reads the same files the phone's Link page uses (assets/link/*.js, the boss tips in its index.html) and assets/analog.cht, so the two
versions can't drift apart. The room list of a hint follows hintRooms() in Link's index.html: HPATH when the step has one, else HPRE
plus the first rows of HINTS. Sprites are numbered as mk_pak.py numbers them: the sorted list of spr/."""
import base64, json, re, sys, os

assets, out = sys.argv[1], sys.argv[2]
link = os.path.join(assets, 'link')

def js_vars(name):
    """every window.X={...}; or window.X=[...]; in a Link data file, as Python data"""
    text = open(os.path.join(link, name), encoding='utf-8').read()
    res = {}
    for m in re.finditer(r'window\.(\w+)\s*=\s*', text):
        val, _ = json.JSONDecoder().raw_decode(text, m.end())
        res[m.group(1)] = val
    return res

def cstr(s):
    b = s.encode('ascii', 'replace').decode('ascii')
    return '"' + b.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ') + '"'

h = js_vars('hints.js')
HNOTE, HPATH, HINTS, HPRE, HROOM = h['HNOTE'], h['HPATH'], h['HINTS'], h.get('HPRE', {}), h.get('HROOM', {})
HSPLIT = js_vars('hsplit.js')['HSPLIT']
AREAS = js_vars('areas.js')['AREAS']
CHAPTERS = js_vars('chapters.js')['CHAPTERS']
ROOMS = js_vars('rooms.js')['ROOMS']
T = js_vars('tables.js')['TABLES']
GEARTBL = js_vars('gearparts.js')['GEARTBL']
PLAN = js_vars('plan.js')['PLAN']
LEVELS = js_vars('levels.js')['LEVELS']
TREASURE = js_vars('treasure.js')['TREASURE']
MISS = js_vars('missables.js')['MISS']
MARKS = js_vars('marks.js')['MARKS']
WSIG = js_vars('world.js')['WSIG']
DB = js_vars('deathblows.js')
ENEMIES = js_vars('enemies.js')['ENEMIES']
SPRITES = {os.path.splitext(n)[0]: i for i, n in enumerate(sorted(os.listdir(os.path.join(link, 'spr'))))}

def hint_rooms(k):
    """the rooms of a hint with no split applied, each [room, [[x, z]...]], and whether they come from HPATH"""
    if k in HPATH:
        return [[q[0], q[1]] for q in HPATH[k]], True
    pre = [[q[0], q[1]] for q in HPRE.get(k, [])]
    return pre + [[r[0], [[r[2], r[3]]] if len(r) > 3 else []] for r in HINTS.get(k, [])[:max(1, 3 - len(pre))]], False

def room_seq(rs):
    """rooms as a flat list: room, number of spots, x, z, x, z..."""
    o = []
    for room, spots in rs:
        o += [room, len(spots)]
        for s in spots:
            o += [s[0], s[1]]
    return ', '.join(map(str, o)) or '0'

o = ['/* made by tools/mk_linkdata.py from assets/link/*.js and assets/analog.cht: do not edit */', '#include <stdint.h>', '#include <stddef.h>', '']

# ---- story hints
o.append('typedef struct { int16_t v; uint16_t m; } HFlag;')
o.append('typedef struct { const HFlag *flags; uint8_t nflags; uint32_t dropS, dropP; const char *text; const int16_t *rooms; int8_t nrooms; } HSplit;')
o.append('typedef struct { uint16_t step; const char *note; const int16_t *rooms; uint8_t nrooms, hasPath; const HSplit *sp; uint8_t nsp; } Hint;')
rows = []
for n in sorted(map(int, HINTS)):
    k = str(n)
    rs, has = hint_rooms(k)
    o.append('static const int16_t HR%d[] = { %s };' % (n, room_seq(rs)))
    spn = 'NULL'; nsp = 0
    if k in HSPLIT:
        parts = []
        for j, r in enumerate(HSPLIT[k]):
            o.append('static const HFlag HF%d_%d[] = { %s };' % (n, j, ', '.join('{%d,%d}' % (f[0], f[1]) for f in r[0])))
            ds = sum(1 << x for x in r[1]); dp = sum(1 << x for x in r[2])
            if len(r) > 3:
                o.append('static const int16_t HSR%d_%d[] = { %s };' % (n, j, room_seq(r[4])))
                parts.append('{HF%d_%d,%d,%d,%d,%s,HSR%d_%d,%d}' % (n, j, len(r[0]), ds, dp, cstr(r[3]), n, j, len(r[4])))
            else:
                parts.append('{HF%d_%d,%d,%d,%d,NULL,NULL,-1}' % (n, j, len(r[0]), ds, dp))
        o.append('static const HSplit HS%d[] = { %s };' % (n, ', '.join(parts)))
        spn = 'HS%d' % n; nsp = len(parts)
    rows.append('{%d,%s,HR%d,%d,%d,%s,%d}' % (n, cstr(HNOTE.get(k, '')), n, len(rs), 1 if has else 0, spn, nsp))
o.append('static const Hint HINT[] = {\n ' + ',\n '.join(rows) + '\n};')
o.append('#define NHINT %d' % len(rows))
o.append('static const struct { int16_t room; float l, t, s; } HROOMTAB[] = {')
for k in sorted(map(int, HROOM)):
    v = HROOM[str(k)]
    o.append(' {%d,%.5ff,%.5ff,%.5ff},' % (k, v[0], v[1], v[2]))
o.append('};')

# ---- names
o.append('static const struct { int16_t a, b; const char *n, *s; } AREA[] = {')
for a in AREAS:
    o.append(' {%d,%d,%s,%s},' % (a[0], a[1], cstr(a[2]), cstr(a[3] if len(a) > 3 else a[2])))
o.append('};')
o.append('static const struct { int16_t step; const char *n; } CHAPTER[] = {')
for c in CHAPTERS:
    o.append(' {%d,%s},' % (c[0], cstr(c[1])))
o.append('};')
o.append('static const struct { int16_t id; const char *n; } ROOMNAME[] = {  /* by id */')
for k in sorted(map(int, ROOMS)):
    o.append(' {%d,%s},' % (k, cstr(ROOMS[str(k)])))
o.append('};')
o.append('static const char *const CHARNAME[] = { %s };' % ', '.join(cstr(x or '???') for x in T['characters']))
o.append('static const char *const GEARNAME[] = { %s };' % ', '.join(cstr(x or '???') for x in T['gears']))

TKIND = ['items', 'weapons', 'equipment', 'gear_weapons', 'gear_parts']
def gear_name(kind, i):
    """gearName() in Link: the gear tables first, then TABLES"""
    t = GEARTBL.get(kind) or T.get(kind) or []
    v = t[i] if i < len(t) else None
    return v if v and v != '/' else None
for kind in ('items', 'equipment', 'gear_weapons', 'gear_parts'):
    t = GEARTBL.get(kind) or T.get(kind) or []
    o.append('static const char *const NAMES_%s[] = { %s };' % (kind, ', '.join(cstr(x) if x and x != '/' else 'NULL' for x in t)))

# ---- the map: pictures' places, walkable outlines, levels, treasure, places
o.append('static const struct { int16_t room; float x, z, w; } PLANTAB[] = {  /* by room */')
for k in sorted(map(int, PLAN)):
    p = PLAN[str(k)]
    o.append(' {%d,%.5ff,%.5ff,%.5ff},' % (k, p[0], p[1], p[2]))
o.append('};')
o.append('static const struct { int16_t room; uint8_t mask; } LEVELTAB[] = {  /* by room: walk layers with their own picture */')
for k in sorted(map(int, LEVELS)):
    o.append(' {%d,%d},' % (k, sum(1 << l for l in LEVELS[str(k)])))
o.append('};')

def hull(pts):
    pts = sorted(set(pts))
    if len(pts) < 3:
        return pts
    def half(seq):
        r = []
        for p in seq:
            while len(r) > 1 and (r[-1][0] - r[-2][0]) * (p[1] - r[-2][1]) - (r[-1][1] - r[-2][1]) * (p[0] - r[-2][0]) <= 0:
                r.pop()
            r.append(p)
        return r[:-1]
    return half(pts) + half(pts[::-1])

def room_hull(room):
    """the outline of a room's walkable floor from maps/<room>.js, which Link fits its view to: main floor if it has one, else all of it"""
    path = os.path.join(link, 'maps', '%d.js' % room)
    if not os.path.exists(path):
        return None
    m = re.search(r'="([^"]*)"', open(path).read())
    if not m:
        return None
    b = base64.b64decode(m.group(1))
    if len(b) < 4:
        return None
    nv = b[0] | b[1] << 8; nt = b[2] | b[3] << 8
    def s16(i):
        v = b[i] | b[i + 1] << 8
        return v - 65536 if v > 32767 else v
    vs = [(s16(4 + i * 4), s16(6 + i * 4)) for i in range(nv)]
    base = 4 + nv * 4
    main, every = [], []
    for t in range(nt):
        q = base + t * 7
        fl = b[q + 6]
        if fl & 3 == 2:
            continue
        tri = [b[q + k * 2] | b[q + k * 2 + 1] << 8 for k in range(3)]
        every += tri
        if not (fl >> 5) & 3:
            main += tri
    use = main or every
    return hull([vs[i] for i in use]) if use else None

hrows = []
for k in sorted(map(int, PLAN)):
    pts = room_hull(k)
    if pts:
        o.append('static const int16_t HU%d[] = { %s };' % (k, ', '.join('%d,%d' % p for p in pts)))
        hrows.append('{%d,%d,HU%d}' % (k, len(pts), k))
o.append('static const struct { int16_t room; int16_t n; const int16_t *p; } HULLTAB[] = {  /* by room */\n ' + ',\n '.join(hrows) + '\n};')

o.append('typedef struct { int16_t v, bit; const char *n; int16_t x, z; uint8_t hasPos, gift; const char *miss; } Tre;')
trows = []
rooms = sorted(set(map(int, TREASURE)) | set(map(int, MISS['extra'])))
for f in rooms:
    k = str(f); parts = []
    for t in TREASURE.get(k, []):
        names = [gear_name(TKIND[c >> 8], c & 255) or ['Item', 'Weapon', 'Equip', 'Gear weapon', 'Gear part'][c >> 8] + ' %d' % (c & 255) for c in t[2]]
        if t[3]:
            names.append('%d G' % t[3])
        tag = MISS['tag'].get('%s:%d:%d' % (k, t[0], t[1]))
        has = len(t) > 5 and t[4] is not None
        gift = len(t) < 6 or (len(t) > 6 and t[6] == 1)
        parts.append('{%d,%d,%s,%d,%d,%d,%d,%s}' % (t[0], t[1], cstr(' + '.join(names)), t[4] if has else 0, t[5] if has else 0, has, gift, cstr(tag) if tag else 'NULL'))
    for e in MISS['extra'].get(k, []):           # [variable or -1, bit or item, name, x, z, when lost, gift]
        parts.append('{%d,%d,%s,%d,%d,1,%d,%s}' % (e[0], e[1], cstr(e[2]), e[3], e[4], 1 if e[6] else 0, cstr(e[5]) if e[5] else 'NULL'))
    o.append('static const Tre TR%d[] = { %s };' % (f, ', '.join(parts)))
    trows.append('{%d,%d,TR%d}' % (f, len(parts), f))
o.append('static const struct { int16_t room; int16_t n; const Tre *t; } TRETAB[] = {  /* by room */\n ' + ',\n '.join(trows) + '\n};')
o.append('typedef struct { int16_t x, z; char kind; } Mark;')
mrows = []
for k in sorted(map(int, MARKS)):
    o.append('static const Mark MK%d[] = { %s };' % (k, ', '.join("{%d,%d,'%s'}" % (e[0], e[1], e[2]) for e in MARKS[str(k)])))
    mrows.append('{%d,%d,MK%d}' % (k, len(MARKS[str(k)]), k))
o.append('static const struct { int16_t room; int16_t n; const Mark *m; } MARKTAB[] = {  /* by room */\n ' + ',\n '.join(mrows) + '\n};')
for w in 'ab':
    flat = []; idx = []
    for chunk in WSIG[w]:
        idx.append(len(flat)); flat += chunk
    idx.append(len(flat))
    o.append('static const uint32_t WSIG_%s[] = { %s };' % (w, ','.join(map(str, flat))))
    o.append('static const uint16_t WSIX_%s[] = { %s };' % (w, ','.join(map(str, idx))))
WPLACE = {1:'Lahan',2:'Mountain Path',3:"Citan's House",4:'Blackmoon Forest',5:'Blackmoon Forest',6:'Dazil',7:'Dazil',8:'Aveh Desert',9:'Stalactite Cave',10:'Nisan',11:'Bledavik',12:'Nortune',13:'Goliath Factory',
 15:'Orphanage',16:'Ethos HQ',17:'Ethos Dig Site',18:'Babel Tower',19:'Lighthouse',20:"Taura's House",23:'Snow Hideout',26:'Gate Generator',27:'Gate Generator',31:'Merkava',32:'Anima Relic 1',33:'Anima Relic 2',36:'Duneman Isle',38:'Fort Jasper'}
o.append('static const char *const WPLACE[40] = { %s };' % ', '.join(cstr(WPLACE[i]) if i in WPLACE else 'NULL' for i in range(40)))

# ---- battle: enemies, deathblows, boss tips
o.append('typedef struct { const char *n; int32_t h0, h1, l0, l1, x; int32_t g; uint8_t d[6], s[8]; int16_t spr; } ERec;')
o.append('static const ERec ENEMY[][8] = {')
def hexb(s, n):
    b = bytes.fromhex(s or '')
    return ','.join(str(x) for x in (b + bytes(n))[:n])
for e in ENEMIES:
    recs = []
    for k in range(8):
        nm = e['n'][k] if k < len(e['n']) else ''
        if not nm or re.match(r'^Monster \d$', nm):
            nm = ''
        hh = e['h'][k]; ll = e['l'][k]
        p = e.get('p'); p = p[k] if p and k < len(p) else None
        spr = SPRITES.get(p[0], -1) if p else -1
        recs.append('{%s,%d,%d,%d,%d,%d,%d,{%s},{%s},%d}' % (cstr(nm), hh[0], hh[1], ll[0], ll[1], e['x'][k], e['g'][k], hexb(e['d'][k], 6), hexb(e['s'][k], 8), spr))
    o.append(' {' + ','.join(recs) + '},')
o.append('};')
o.append('#define NBANK %d' % len(ENEMIES))
o.append('#define SPR_GRAHF %d' % SPRITES.get('55_0', -1))

o.append('typedef struct { const char *n; int16_t r[7]; uint8_t lv; } Blow;')
DBLOW = DB['DBLOW']; drows = []
for c, d in enumerate(DBLOW):
    parts = []
    if d:
        for i, r in enumerate(d.get('r') or []):
            nm = d['n'][i] if i < len(d['n']) else None
            ok = r and nm and nm != 'null' and nm[0] != '{'
            lv = d['l'][i] if d.get('l') and i < len(d['l']) else 0
            parts.append('{%s,{%s},%d}' % (cstr(nm) if ok else 'NULL', ','.join(map(str, r or [0] * 7)), lv))
    o.append('static const Blow DB%d[] = { %s };' % (c, ', '.join(parts) or '{NULL,{0},0}'))
    drows.append('{DB%d,%d}' % (c, len(parts)))
o.append('static const struct { const Blow *b; int n; } DBLOW[] = { %s };' % ', '.join(drows))
grows = []
for g, t in enumerate(DB['GDBLOW']):
    grows.append('{ %s }' % ', '.join(cstr(x) if x else 'NULL' for x in (list(t or []) + [None] * 14)[:14]))
o.append('static const char *const GDBLOW[][14] = {\n ' + ',\n '.join(grows) + '\n};')

page = open(os.path.join(link, 'index.html'), encoding='utf-8').read()
start = page.index('var BOSSTIP=['); end = page.index('\n];', start) if '\n];' in page[start:start + 60000] else page.index('];', start)
strre = r"""'((?:[^'\\]|\\.)*)'|"((?:[^"\\]|\\.)*)\""""
tips = []
for m in re.finditer(r"\[\s*(?:" + strre + r")\s*,\s*(?:" + strre + r")\s*(?:,\s*(\d+)\s*,\s*(\d+)\s*)?\]", page[start:end]):
    a = m.group(1) or m.group(2); b = m.group(3) or m.group(4)
    un = lambda s: s.replace("\\'", "'").replace('\\"', '"')
    tips.append('{%s,%s,%s,%s}' % (cstr(un(a)), cstr(un(b)), m.group(5) or '-1', m.group(6) or '-1'))
o.append('static const struct { const char *n, *tip; int16_t a, b; } BOSSTIP[] = {\n ' + ',\n '.join(tips) + '\n};')

# ---- the analog program: as MainActivity.analogProgram() / analogOptions()
mem = bytearray(0xC00); hi = 0; opts = 0; ents = {}
for line in open(os.path.join(assets, 'analog.cht'), encoding='utf-8'):
    m = re.match(r'^cheat(\d+)_(desc|code|enable)\s*=\s*"?(.*?)"?\s*$', line.strip())
    if m:
        ents.setdefault(int(m.group(1)), {})[m.group(2)] = m.group(3)
for i in sorted(ents):
    e = ents[i]; d = e.get('desc', ''); code = e.get('code', '')
    if d.startswith('Analog:'):
        m = re.search(r'30017F0([4-8])', code.upper())
        if m and e.get('enable') == 'true':
            opts |= 1 << (int(m.group(1)) - 4)
    elif '- code' in d.lower():
        for part in code.split('+'):
            av = part.split()
            if len(av) != 2:
                continue
            a = int(av[0], 16); v = int(av[1], 16)
            if a >> 24 != 0x80:
                continue
            off = (a & 0x1fffff) - 0x17400
            if off < 0 or off + 2 > len(mem):
                continue
            mem[off] = v & 255; mem[off + 1] = v >> 8 & 255; hi = max(hi, off + 2)
# the camera fix, as setAnalogMod in psxlink.c (lw -> lhu at offset 0x45C), should the .cht ever carry the old word
if mem[0x45C:0x460] == bytes.fromhex('34F94D8D'):
    mem[0x45C:0x460] = bytes.fromhex('34F94D95')
o.append('#define XGA_OPTS_DEFAULT %d' % opts)
o.append('static const uint8_t XGA_PROG[%d] = {' % hi)
for i in range(0, hi, 24):
    o.append(' ' + ','.join(str(b) for b in mem[i:i + 24]) + ',')
o.append('};')
open(out, 'w').write('\n'.join(o) + '\n')
print('linkdata: %d hints, %d rooms, %d with treasure, %d enemy banks, %d boss tips, analog %d bytes opts %x' % (len(rows), len(ROOMS), len(trows), len(ENEMIES), len(tips), hi, opts))
