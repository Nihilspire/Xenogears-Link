"""Show Link's hint system every memory dump there is, with no playing, and report which hint appears and whether its guide line
is drawn. Uses the app's own page in headless Chromium, with a stand-in for the app's bridge serving the dump.

Two kinds of dump:
  saved: real play, from the Link repo's test bundle (HANDOFF, default ~/xghandoff/x). Each is taken as it is, at its own step and room.
  walk:  hint_walk.py's, one per room each hint names. The step is set back to the one that shows the hint; other switches aren't real.
For each dump: the page(s) of the hint in the room the party is in, and the next page after it (a line to the door). A walk dump of a hint's
last room also tries the next hint's first page. It catches page, spot and route mistakes, not whether the words are right.
  python3 hint_sweep.py WALK_DIR OUT_DIR [workers]
Writes OUT_DIR/results.json and OUT_DIR/shots/*.jpg. hint_report.py makes the page."""
import base64, glob, json, multiprocessing as mp, os, struct, sys
XGROOT = os.environ.get('XGROOT') or os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
HANDOFF = os.environ.get('HANDOFF') or os.path.expanduser('~/xghandoff/x')
SAVED_DIRS = ['npc/bins/st', 'fis', 'pst', 'st']
STORY, FIELD, SIG = 0x6EF64, 0x6F94E, 0x6FAF0
BATCH = 25

MOCK = """
window.__RAMB = new Uint8Array(0x200000); window.__errs = [];
localStorage.setItem('xg_tourDone', '1'); localStorage.setItem('xg_tab', 'map');
window.__setRam = function(b64){ var s = atob(b64); for (var i = 0; i < s.length; i++) __RAMB[i] = s.charCodeAt(i); };
var HX = []; for (var i = 0; i < 256; i++) HX.push((i < 16 ? '0' : '') + i.toString(16));
window.Native = {
  poll: function(host, port, mode, csv, seq){ setTimeout(function(){
    var pages = csv ? csv.split(',') : [], ok = {};
    pages.forEach(function(p){ var pg = parseInt(p, 16) & 0x1FFF, o = pg * 256, h = ''; for (var i = 0; i < 256; i++) h += HX[__RAMB[o + i]]; ok[pg.toString(16)] = h; });
    onMem({seq: seq, sent: pages.length, got: pages.length, err: '', ok: ok}); }, 0); },
  send: function(){}, discName: function(){ return 'Xenogears (USA) (Disc 1).chd'; }, discSize: function(){ return 357651775; },
  discPick: function(){}, discRead: function(){ return 'ERR:test'; }, genDir: function(){ return '/gen'; }, genHas: function(){ return false; },
  genRead: function(){ return ''; }, genWrite: function(){ return 'ok'; }, genClear: function(){},
  exitLog: function(){ return 'ok'; }, exitLogClear: function(){}, exitLogShare: function(){}, focusable: function(){}, beat: function(){}, lastHang: function(){ return ''; },
  stateInfo: function(){ return '[0,0,0,0]'; }, stateThumb: function(){ return ''; }, stateSave: function(){}, stateLoad: function(){}
};
/* forget everything about the last dump */
window.__fresh = function(){ last = {}; fullKey = ''; lastField = -1; pendF = -1; pendN = 0; mapLast = null; entry = null; prevEntry = null; heading = null; exitTap = null; exitTapF = -1;
  HPG = null; LS.set('hintpg', 'null'); HF = {key:null,pg:-1,near:false,talk:false,nearR:null,manual:null,flash:0,room:null}; RTM.key = ''; R2.C = null; CFG.follow = false; };
function onFloor(m, x, z){ for (var i = 0; i < m.nt; i++){ if ((m.fl[i] & 3) === 2) continue; var a = m.tr[i*3], b = m.tr[i*3+1], c = m.tr[i*3+2], ax = m.vx[a], az = m.vz[a], bx = m.vx[b], bz = m.vz[b], qx = m.vx[c], qz = m.vz[c], d = (bz-qz)*(ax-qx)+(qx-bx)*(az-qz); if (!d) continue;
   var A0 = ((bz-qz)*(x-qx)+(qx-bx)*(z-qz))/d, B0 = ((qz-az)*(x-qx)+(ax-qx)*(z-qz))/d; if (A0 >= -0.02 && B0 >= -0.02 && 1-A0-B0 >= -0.02) return true; } return false; }
/* one page of the current hint with the party where it is: what Link would aim at and draw */
window.__page = function(hn, pg){ var rooms = hintRooms(hn), f = hintRoomNow(), p = playerPos(), hr = rooms[pg], m = f != null && f >= 0 ? mapLoad(f) : null;
  hintSetPage(hn, pg, false); RTM.key = ''; R2.C = null; exitTap = null;
  var o = {pg: pg, pages: hintPages(hn), rooms: rooms.length, toRoom: hr ? hr[0] : null, spots: hr ? hr[1].length : 0, here: f, pos: p ? [p.x, p.z] : null, map: !!m};
  if (!hr) { o.st = 'nopage'; return o; }
  if (f == null || !p) { o.st = 'noparty'; return o; }
  if (f < 0) { o.st = hr[0] < 0 ? 'world' : 'worldaway'; return o; }
  var to = routeTo(f, p); o.to = to ? [to.x, to.z] : null;
  if (hr[0] === f && m) o.spotsOff = hr[1].filter(function(q){ return !onFloor(m, q[0], q[1]); });
  if (m) o.partyOn = onFloor(m, p.x, p.z);
  if (hr[0] !== f) o.hop = RTM.v;
  if (!m) { o.st = 'nomap'; return o; }
  if (!to) { o.st = hr[0] === f ? 'arrived' : 'noway'; return o; }
  var L = route2d(m, f, 0, null, p, to); if (!L || L.length < 2) { o.st = 'noline'; return o; }
  var e = L[L.length - 1], n = 0; for (var i = 1; i < L.length; i++) n += Math.hypot(L[i][0]-L[i-1][0], L[i][1]-L[i-1][1]);
  o.len = Math.round(n); o.gap = Math.round(Math.hypot(e[0]-to.x, e[1]-to.z)); o.st = o.gap > 48 ? 'short' : hr[0] === f ? 'spot' : o.hop === -1 || hr[0] < 0 ? 'worldexit' : 'door'; return o; };
window.__head = function(){ var hn = hintNext(), s = u16(A.STORY), f = hintRoomNow(), sig = u32(A.SIG), fr = u16(A.FIELD);
  return {sig: sig, step: s, field: fr == null ? null : fr & 0x7FF, room: f, hint: hn ? hn.step : null, key: hn ? hn.key : null, note: hn ? hn.note : '', rooms: hn ? hintRooms(hn).map(function(r){ return r[0]; }) : []}; };
"""

def saved_cases():
    out = []
    for d in SAVED_DIRS:
        for fp in sorted(glob.glob(os.path.join(HANDOFF, d, '*.bin'))):
            if os.path.getsize(fp) == 0x200000: out.append(dict(kind='saved', path=fp, name=os.path.basename(fp)[:-4]))
    return out
def walk_cases(walk):
    rows = json.load(open(os.path.join(walk, 'walk.json')))
    return [dict(kind='walk', path=os.path.join(walk, r['file']), name=r['file'][:-4], hint=r['hint'], setstep=r['step'], room=r['room'], result=r['result'], disc=r.get('disc')) for r in rows if r['result'] != 'stuck'], [r for r in rows if r['result'] == 'stuck']

def run(args):
    cases, out, wid = args
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        for at in range(0, len(cases), BATCH): batch(pw, cases[at:at + BATCH], out, wid)

def batch(pw, cases, out, wid):
    """a few dumps, then a fresh browser. Each result goes to its own file as it's done, so a run that dies can be started again and carries on."""
    if True:
        b = pw.chromium.launch(args=['--disable-gpu', '--disable-dev-shm-usage']); pg = b.new_page(viewport={'width': 360, 'height': 480})
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
        pg.add_init_script(MOCK); pg.goto('file://' + XGROOT + '/app/assets/link/index.html'); pg.wait_for_timeout(1500)
        pg.evaluate("bootStart()"); pg.wait_for_timeout(600)
        for c in cases:
            raw = bytearray(open(c['path'], 'rb').read())
            if 'setstep' in c: struct.pack_into('<H', raw, STORY, c['setstep'])
            errs.clear(); r = dict(c); r.pop('path')
            def load(ram):
                pg.evaluate("__setRam(%s);__fresh()" % json.dumps(base64.b64encode(bytes(ram)).decode()))
                sig = struct.unpack_from('<I', ram, SIG)[0]; room = struct.unpack_from('<H', ram, FIELD)[0] & 0x7FF
                try: pg.wait_for_function("(function(){var s=u32(A.SIG);return %d===4?lastField===%d:s===%d})()" % (sig, room, sig), timeout=1200, polling=25)
                except Exception: r['timeout'] = 1
            def probe(hn_expr, tag):
                """the pages to look at: the hint's page(s) for this room, the page after, else the first; each drawn and pictured"""
                rooms = pg.evaluate("hintNext()?hintRooms(hintNext()).map(function(x){return x[0]}):[]"); f = pg.evaluate("hintRoomNow()")
                want = [i for i, x in enumerate(rooms) if x == f]; want = sorted(set(want + [i + 1 for i in want if i + 1 < len(rooms)])) or ([0] if rooms else [])
                pages = []
                for i in want:
                    o = pg.evaluate("__page(hintNext(),%d)" % i); o['tag'] = tag
                    pg.evaluate("last={};fullKey='';render();drawMap()")
                    if o['st'] not in ('nopage',):
                        shot = '%s_%s_p%d.jpg' % (c['name'][:60], tag, i)
                        pg.screenshot(path=os.path.join(out, 'shots', shot), type='jpeg', quality=55); o['shot'] = shot
                    pages.append(o)
                return pages
            load(raw); r['head'] = pg.evaluate("__head()"); r['pages'] = probe(None, 'a')
            if c['kind'] == 'walk':
                rs = r['head']['rooms']
                if rs and rs[-1] == c['room']:   # the hint is done here: the next hint's first page, from the same place
                    struct.pack_into('<H', raw, STORY, c['hint'])
                    load(raw); r['nextHead'] = pg.evaluate("__head()"); r['nextPages'] = probe(None, 'n')[:1]
            r['errs'] = list(errs)
            with open(os.path.join(out, 'res', c['name'] + '.json'), 'w') as f: json.dump(r, f); f.flush(); os.fsync(f.fileno())
            print(wid, c['kind'], c['name'][:40], 'hint', r['head']['hint'], [p['st'] for p in r['pages']], flush=True)
        b.close()

if __name__ == '__main__':
    walk, out = sys.argv[1], sys.argv[2]; n = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    os.makedirs(os.path.join(out, 'shots'), exist_ok=True)
    wc, stuck = walk_cases(walk) if os.path.isfile(os.path.join(walk, 'walk.json')) else ([], [])
    limit = int(os.environ.get('LIMIT', 0)); cases = saved_cases() + wc
    if limit: cases = cases[:limit // 2] + wc[:limit // 2]
    os.makedirs(os.path.join(out, 'res'), exist_ok=True)
    left = [c for c in cases if not os.path.isfile(os.path.join(out, 'res', c['name'] + '.json'))]; print('left', len(left), 'of', len(cases), flush=True)
    parts = [(left[i::n], out, i) for i in range(n)]
    with mp.Pool(n) as P: P.map(run, parts)
    res = [json.load(open(os.path.join(out, 'res', c['name'] + '.json'))) for c in cases]
    json.dump(dict(results=res, stuck=stuck), open(os.path.join(out, 'results.json'), 'w'))
    from collections import Counter
    print(Counter(p['st'] for r in res for p in r['pages']))
