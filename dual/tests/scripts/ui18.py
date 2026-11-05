"""0.18 menu check: renders each screen with a mock window.App in headless Chromium and saves screenshots.
Needs thumbs.py's pictures (work/host/xg/shots/thumb_*.jpg). Output: work/scratch/ui18_<name>.png, and a list of
page errors and of any screen where controller navigation can't reach every button."""
import os, json
XGROOT = os.environ.get('XGROOT') or os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
from playwright.sync_api import sync_playwright
SH = 'file://' + XGROOT + '/work/host/xg/shots/'
NOW = 1761246000000   # a fixed "now" (ms) so the times read TODAY / YESTERDAY / a date
def state(running, resume=True, slots=True):
    s = {'version': '0.18', 'storage': True, 'folder': '/storage/emulated/0/Xenogears', 'running': running, 'gameId': 'SLUS00664',
         'discs': [{'path': '/sdcard/PSX/d1.chd', 'name': 'Xenogears (USA) (Disc 1).chd', 'ok': True},
                   {'path': '/sdcard/PSX/d2.chd', 'name': 'Xenogears (USA) (Disc 2).chd', 'ok': True}],
         'bootDisc': 0, 'inserted': 0 if running else -1, 'discCount': 2, 'bios': [], 'spanned': True, 'secondScreen': False,
         'linkOnPhone': False, 'customLink': False, 'fastForward': False,
         'opts': {'showAtStart': True, 'touch': True, 'stick': True, 'stickDpad': True, 'smooth': True, 'integer': False, 'hires': False,
                  'hleBios': False, 'link': True, 'swapScreens': False, 'muted': False, 'resume': True, 'opacity': 55, 'padType': 0, 'stickThreshold': 40},
         'analogOn': True, 'analogState': 2, 'bindWait': -1,
         'binds': [{'bit': 0, 'name': 'Cross', 'key': 'A'}, {'bit': 8, 'name': 'Circle', 'key': 'B'}],
         'mods': [{'id': 'cht:32', 'name': 'left stick walks in any direction', 'group': 'analog', 'on': True},
                  {'id': 'cht:33', 'name': 'push the left stick fully to run', 'group': 'analog', 'on': True},
                  {'id': 'cht:34', 'name': 'right stick camera (orbit, tilt)', 'group': 'analog', 'on': True},
                  {'id': 'cht:35', 'name': 'invert right stick up/down', 'group': 'analog', 'on': False},
                  {'id': 'cht:36', 'name': 'L1/R1 turn the camera smoothly', 'group': 'analog', 'on': True},
                  {'id': 'mod:Fast text', 'name': 'Fast text', 'code': '30034964 00FF', 'source': 'Added here', 'removable': True, 'on': True}],
         'card': {'exists': True, 'formatted': True, 'blocksUsed': 2, 'saves': ['BASLUS-00664XENO01']}, 'bezel': 'window', 'bezels': [],
         'slots': [{'t': NOW - 3600e3, 'img': SH + 'thumb_lh_loaded.jpg'}, {'t': NOW - 30 * 3600e3, 'img': SH + 'thumb_natob_room.jpg'},
                   {'t': NOW - 9 * 86400e3, 'img': ''}, {'t': 0, 'img': ''}] if slots else [{'t': 0}] * 4}
    if resume: s['resume'] = {'disc': 0, 't': NOW - 600e3, 'img': SH + 'thumb_natob_room.jpg'}
    return s
MOCK = """window.__S=%s; Date.now=()=>%d; const _D=Date; window.Date=class extends _D{constructor(...a){a.length?super(...a):super(%d)}};
window.App=new Proxy({},{get:(t,k)=>(...a)=>{ if(k==='state')return JSON.stringify(window.__S); window.__calls=(window.__calls||[]).concat([[k,a]]); return true;}});"""
SCENES = [  # name, running, resume, js to get there
    ('launch_resume', False, True, ''), ('launch_fresh', False, False, ''),
    ('pause', True, True, "openPause()"), ('pause_reset', True, True, "openPause();resetArm=true;render()"),
    ('mods', False, True, "go('s-mods')"),
] + [('set_' + t, True, True, "go('s-settings');setTab('%s')" % t) for t in ['controls', 'screens', 'picture', 'card', 'system']]
out = XGROOT + '/work/scratch/'; os.makedirs(out, exist_ok=True)
errs, navbad = [], []
with sync_playwright() as p:
    b = p.chromium.launch()
    for vw, vh, tag in [(540, 720, 'duo'), (960, 540, 'wide')]:
        for name, run, res, js in SCENES:
            pg = b.new_page(viewport={'width': vw, 'height': vh}, device_scale_factor=2)
            pg.on('pageerror', lambda e, n=name: errs.append('%s: %s' % (n, e)))
            pg.add_init_script(MOCK % (json.dumps(state(run, res)), NOW, NOW))
            pg.goto('file://' + XGROOT + '/app/assets/menu/index.html'); pg.wait_for_timeout(400)
            if js: pg.evaluate(js); pg.wait_for_timeout(250)
            # every nav item must be reachable by pressing down repeatedly from the first focus
            n = pg.evaluate("navItems().length"); seen = set()
            for i in range(n + 2):
                seen.add(pg.evaluate("document.activeElement&&document.activeElement.getAttribute('data-key')")); pg.evaluate("navKey('down')")
            seen.discard(None)
            if len(seen) < n: navbad.append('%s/%s: reached %d of %d' % (tag, name, len(seen), n))
            pg.evaluate("document.activeElement&&document.activeElement.blur&&document.activeElement.blur();focusFirst()")
            pg.wait_for_timeout(100)
            # anything wider than the screen (text spilling past the frame)?
            over = pg.evaluate("[...document.querySelectorAll('.screen.on .t')].filter(e=>e.getBoundingClientRect().right>innerWidth+1).length")
            if over: navbad.append('%s/%s: %d text runs past the right edge' % (tag, name, over))
            pg.screenshot(path=out + 'ui18_%s_%s.png' % (tag, name))
            pg.close()
    b.close()
print('errors', errs); print('problems', navbad)
