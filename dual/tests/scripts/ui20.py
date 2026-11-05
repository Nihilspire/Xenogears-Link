"""0.20 menu check (follows ui18.py): QUICK + 8 save-state slots with DEL, Hotkeys setup, EXPORT CARD, the safety-save note.
Mock window.App in headless Chromium; needs thumbs.py's pictures. Screenshots: work/scratch/ui20_<layout>_<scene>.png"""
import os, json
XGROOT = os.environ.get('XGROOT') or os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
from playwright.sync_api import sync_playwright
SH = 'file://' + XGROOT + '/work/host/xg/shots/'
NOW = 1762070400000
def state(running):
    sl = [{'t': NOW - 3600e3, 'img': SH + 'thumb_lh_loaded.jpg'}, {'t': NOW - 30 * 3600e3, 'img': SH + 'thumb_natob_room.jpg'}, {'t': NOW - 9 * 86400e3, 'img': ''}] + [{'t': 0, 'img': ''}] * 5
    return {'version': '0.20', 'storage': True, 'folder': '/storage/emulated/0/Xenogears', 'running': running, 'gameId': 'SLUS00664',
            'discs': [{'path': '/sdcard/d1.chd', 'name': 'Xenogears (USA) (Disc 1).chd', 'ok': True}, {'path': '/sdcard/d2.chd', 'name': 'Xenogears (USA) (Disc 2).chd', 'ok': True}],
            'bootDisc': 0, 'inserted': 0 if running else -1, 'discCount': 2, 'bios': [], 'spanned': True, 'secondScreen': False, 'linkOnPhone': False,
            'fastForward': False, 'opts': {'showAtStart': True, 'touch': True, 'stick': True, 'stickDpad': True, 'smooth': True, 'integer': False, 'hires': False,
            'hleBios': False, 'link': True, 'swapScreens': False, 'muted': False, 'resume': True, 'opacity': 55, 'padType': 0, 'stickThreshold': 40},
            'analogOn': True, 'analogState': 2, 'bindWait': 101,
            'binds': [{'bit': 0, 'name': 'Cross', 'key': 'A'}, {'bit': 8, 'name': 'Circle', 'key': 'B'}],
            'hotkeys': [{'i': 0, 'name': 'Quick save', 'key': 'THUMBR'}, {'i': 1, 'name': 'Quick load', 'key': ''}, {'i': 2, 'name': 'Fast forward', 'key': ''}],
            'mods': [{'id': 'cht:32', 'name': 'left stick walks in any direction', 'group': 'analog', 'on': True}],
            'card': {'exists': True, 'formatted': True, 'blocksUsed': 2, 'saves': ['BASLUS-00664XENO01']}, 'bezel': 'window', 'bezels': [],
            'slots': sl, 'quick': {'t': NOW - 120e3, 'img': SH + 'thumb_natob_room.jpg'},
            'resume': {'disc': 0, 't': NOW - 600e3, 'img': SH + 'thumb_natob_room.jpg'}}
MOCK = """window.__S=%s; Date.now=()=>%d; const _D=Date; window.Date=class extends _D{constructor(...a){a.length?super(...a):super(%d)}};
window.App=new Proxy({},{get:(t,k)=>(...a)=>{ if(k==='state')return JSON.stringify(window.__S); window.__calls=(window.__calls||[]).concat([[k,a]]); return true;}});"""
SCENES = [('pause', True, "openPause()"), ('pause_del', True, "openPause();delArm=2;render()"),
          ('set_hotkeys', True, "go('s-settings');setTab('controls');hotOpen=true;render()"),
          ('set_card', True, "go('s-settings');setTab('card')"), ('set_system', True, "go('s-settings');setTab('system')")]
out = XGROOT + '/work/scratch/'; os.makedirs(out, exist_ok=True)
errs, bad = [], []
with sync_playwright() as p:
    b = p.chromium.launch()
    for vw, vh, tag in [(540, 720, 'duo'), (960, 540, 'wide')]:
        for name, run, js in SCENES:
            pg = b.new_page(viewport={'width': vw, 'height': vh}, device_scale_factor=2)
            pg.on('pageerror', lambda e, n=name: errs.append('%s: %s' % (n, e)))
            pg.add_init_script(MOCK % (json.dumps(state(run)), NOW, NOW))
            pg.goto('file://' + XGROOT + '/app/assets/menu/index.html'); pg.wait_for_timeout(400)
            pg.evaluate(js); pg.wait_for_timeout(250)
            n = pg.evaluate("navItems().filter(e=>e.getAttribute('data-key')).length"); seen = set()
            for i in range(pg.evaluate("navItems().length") + 2):
                seen.add(pg.evaluate("document.activeElement&&document.activeElement.getAttribute('data-key')")); pg.evaluate("navKey('down')")
            seen.discard(None)
            if len(seen) < n: bad.append('%s/%s: controller reaches %d of %d' % (tag, name, len(seen), n))
            over = pg.evaluate("[...document.querySelectorAll('.screen.on .t, .screen.on .chip')].filter(e=>e.getBoundingClientRect().right>innerWidth+1).length")
            if over: bad.append('%s/%s: %d items run past the right edge' % (tag, name, over))
            pg.evaluate("document.activeElement&&document.activeElement.blur&&document.activeElement.blur();focusFirst()"); pg.wait_for_timeout(100)
            pg.screenshot(path=out + 'ui20_%s_%s.png' % (tag, name))
            if name == 'pause_del':
                pg.evaluate("document.querySelector('[data-key=dgo2]').click()")
                calls = pg.evaluate("window.__calls||[]")
                if ['deleteState', [2]] not in calls: bad.append('SURE? did not call deleteState(2): %s' % calls[-3:])
            if name == 'set_card':
                pg.evaluate("document.querySelector('[data-key=expc]').click()")
                if ['exportCard', []] not in pg.evaluate("window.__calls||[]"): bad.append('EXPORT CARD did not call exportCard')
            pg.close()
    b.close()
print('errors', errs); print('problems', bad)
