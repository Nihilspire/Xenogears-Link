"""Link's developer options in Dual (0.21): five taps on the version line do nothing inside Dual, and the call the app
makes for the Konami code (MainActivity.toggleDev) turns them on and off; standalone Link still unlocks with five taps."""
import os, json, re
XGROOT = os.environ.get('XGROOT') or os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
from playwright.sync_api import sync_playwright
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'link_state_test.py')).read()
dual = re.search(r'mock = """(.*?)"""', src, re.S).group(1) % (json.dumps(open(XGROOT + '/work/host/xg/ram_lahan2.hex').read().strip()), XGROOT)
alone = dual.replace('stateInfo:', 'stateInfoX:').replace('stateThumb:', 'stateThumbX:')   # no Native.stateInfo: standalone Link
mjs = open(XGROOT + '/app/src/com/jack/xenogears/MainActivity.java').read()
TOGGLE = re.search(r'link\.evaluateJavascript\("(\(function\(\)\{if\(!window\.sv.*?\}\)\(\))"', mjs).group(1)
res, errs = {}, []
def taps(pg, n=5):
    for _ in range(n): pg.evaluate("devTap()")
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, mock in (('dual', dual), ('standalone', alone)):
        pg = b.new_context().new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.add_init_script(mock); pg.goto('file://' + XGROOT + '/app/assets/link/index.html'); pg.wait_for_timeout(1500)
        res[name + ': DIRECT'] = pg.evaluate('DIRECT') == (name == 'dual')
        res[name + ': dev starts off'] = pg.evaluate('CFG.dev') is False
        pg.evaluate('openSet()'); taps(pg)
        res[name + ': five taps ' + ('do nothing' if name == 'dual' else 'unlock')] = pg.evaluate('CFG.dev') is (name != 'dual')
        if name == 'dual':
            r1 = pg.evaluate(TOGGLE); on = pg.evaluate('CFG.dev'); pg.wait_for_timeout(200)
            res['dual: Konami turns DEV on'] = r1 == 'on' and on is True and 'DEVELOPER' in pg.evaluate('lastSet') or False
            pg.reload(); pg.wait_for_timeout(1500)
            res['dual: still on after a reload'] = pg.evaluate('CFG.dev') is True
            r2 = pg.evaluate(TOGGLE)
            res['dual: Konami again turns it off'] = r2 == 'off' and pg.evaluate('CFG.dev') is False
        b.contexts[-1].close()
    b.close()
for k, v in res.items(): print(('PASS ' if v else 'FAIL ') + k)
print('ERRORS:', errs or 'none')
