"""Settings > SCREENS > Layout in the menu page: one setting with 16:9, 4:3 and SECOND SCREEN, what each shows, and that picking one reaches the app. Picture: shots/menu_layout.png."""
import json, os, sys
XGROOT = os.environ.get('XGROOT') or os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
from playwright.sync_api import sync_playwright
STATE = {'version': '0.25', 'storage': True, 'folder': '/x', 'running': False, 'discs': [{}, {}], 'bootDisc': 0, 'bios': [], 'spanned': False, 'secondScreen': True, 'wideScreen': True, 'mods': [], 'binds': [], 'hotkeys': [], 'card': {}, 'slots': [],
         'opts': {'link': True, 'swapScreens': False, 'layout': 0}}
MOCK = "window.__calls=[];window.__S=%s;window.App=new Proxy({},{get:function(t,k){if(k==='state')return function(){return JSON.stringify(__S)};return function(){__calls.push([k].concat([].slice.call(arguments)));if(k==='setInt')__S.opts[arguments[0]]=arguments[1];return ''}}});" % json.dumps(STATE)
res, errs = {}, []
with sync_playwright() as p:
    b = p.chromium.launch(args=['--disable-gpu']); pg = b.new_page(viewport={'width': 640, 'height': 480}, device_scale_factor=2)
    pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
    pg.add_init_script(MOCK); pg.goto('file://' + XGROOT + '/app/assets/menu/index.html'); pg.wait_for_timeout(700)
    pg.evaluate("go('s-settings');setTab('screens')"); pg.wait_for_timeout(200)
    keys = lambda: pg.evaluate("[...document.querySelectorAll('#s-settings [data-key]')].map(e=>e.getAttribute('data-key'))")
    k = keys(); print(k)
    res['the three choices are there'] = all(x in k for x in ('layout2', 'layout1', 'layout0'))
    res['the two old switches are gone'] = 'on-rails' not in k and 'on-linkPanel' not in k and 'off-rails' not in k and 'off-linkPanel' not in k
    res['SECOND SCREEN has Swap screens'] = 'on-swapScreens' in k or 'off-swapScreens' in k
    pg.evaluate("document.querySelector('[data-key=layout2]').click()"); pg.wait_for_timeout(200)
    res['16:9 reaches the app, even with a second display'] = pg.evaluate("__calls.some(c=>c[0]==='setInt'&&c[1]==='layout'&&c[2]===2)")
    k = keys(); res['16:9 lit, Swap screens hidden'] = pg.evaluate("document.querySelector('[data-key=layout2]').classList.contains('on')") and 'off-swapScreens' not in k
    pg.screenshot(path='shots/menu_layout.png')
    pg.evaluate("document.querySelector('[data-key=layout1]').click()"); pg.wait_for_timeout(200)
    res['4:3 reaches the app'] = pg.evaluate("__calls.some(c=>c[0]==='setInt'&&c[1]==='layout'&&c[2]===1)")
    pg.evaluate("document.querySelector('[data-key=layout0]').click()"); pg.wait_for_timeout(200)
    res['back to SECOND SCREEN'] = pg.evaluate("__calls.some(c=>c[0]==='setInt'&&c[1]==='layout'&&c[2]===0)") and 'off-swapScreens' in keys()
    b.close()
for k_, v in res.items(): print(('PASS ' if v else 'FAIL ') + k_)
print('ERRORS:', errs or 'none'); print('ALL PASS' if all(res.values()) and not errs else 'FAILED')
