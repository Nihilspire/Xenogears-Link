"""The single-screen layout (0.23) in headless Chromium, with real field and battle RAM: quick info either side of a see-through middle, the panel sliding in and out.
Off unless the app asks for it, and the normal page is untouched. What it can't test: Android's own part (the page over the game, touches passing through).
  python3 link_rail_test.py WALK_DUMP BATTLE_DUMP   (hint_walk.py's and a dumpram from a fight; s7_r1.bin and a fight are what was used)"""
import base64, io, json, os, struct, sys, importlib.util
from PIL import Image
XGROOT = os.environ.get('XGROOT') or os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sp = importlib.util.spec_from_file_location('hint_sweep', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hint_sweep.py')); hs = importlib.util.module_from_spec(sp); sp.loader.exec_module(hs)
from playwright.sync_api import sync_playwright
walk = bytearray(open(sys.argv[1], 'rb').read()); struct.pack_into('<H', walk, 0x6EF64, 6); fight = open(sys.argv[2], 'rb').read()
res, errs = {}, []
def alpha(pg, x, y):
    return Image.open(io.BytesIO(pg.screenshot(omit_background=True))).convert('RGBA').getpixel((x, y))[3]
with sync_playwright() as pw:
    b = pw.chromium.launch(args=['--disable-gpu', '--disable-dev-shm-usage'])
    def page(w, h, hash_, raw):
        pg = b.new_page(viewport={'width': w, 'height': h}); pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
        pg.add_init_script(hs.MOCK); pg.goto('file://' + XGROOT + '/app/assets/link/index.html' + hash_); pg.wait_for_timeout(1400)
        pg.evaluate("bootStart()"); pg.wait_for_timeout(300)
        pg.evaluate("__setRam(%s);__fresh();last={};fullKey=''" % json.dumps(base64.b64encode(bytes(raw)).decode())); pg.wait_for_timeout(1300)
        return pg
    # field, 1080p
    pg = page(1920, 1080, '#rail', walk)
    res['rem is 3 at 1080p, bars 240 wide'] = pg.evaluate("[getComputedStyle(document.documentElement).fontSize,document.getElementById('railL').offsetWidth,document.getElementById('railR').offsetWidth]") == ['3px', 240, 240]
    res['the middle is see-through'] = alpha(pg, 960, 540) == 0 and alpha(pg, 245, 100) == 0 and alpha(pg, 1675, 1000) == 0
    res['the bars are not'] = alpha(pg, 100, 540) == 255 and alpha(pg, 1800, 540) == 255
    txt = pg.evaluate("railWrap('Blackmoon Forest of the night')")
    res['words wrap to 8 letters'] = max(map(len, txt)) <= 8; print(txt)
    res['nothing runs under the arrow'] = pg.evaluate("(function(){var r=document.getElementById('railR'),b=document.getElementById('railBtn').getBoundingClientRect(),l=r.lastElementChild.getBoundingClientRect();return l.bottom<=b.top+1&&r.scrollHeight<=r.clientHeight})()")
    mr = pg.evaluate("(function(){var r=document.getElementById('railmap').getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2,r.width]})()")
    res['map copied to the bar'] = mr[2] > 150 and Image.open(io.BytesIO(pg.screenshot())).convert('RGB').getpixel((int(mr[0]), int(mr[1]))) != (11, 11, 28)   # the canvas can't be read back from file:// here, so look at the screen
    res['chests and countdown shown'] = 'row' in pg.evaluate("document.getElementById('railR').innerHTML") and pg.evaluate("document.querySelectorAll('#railR .rw').length") >= 4
    x0 = pg.evaluate("document.getElementById('app').getBoundingClientRect().left")
    res['panel starts off screen'] = x0 >= 1920
    pg.evaluate("document.getElementById('railBtn').click()"); pg.wait_for_timeout(500)
    res['arrow slides it in, over the right half'] = pg.evaluate("document.getElementById('app').getBoundingClientRect().left") == 960 and pg.evaluate("railIsOpen") is True
    res['the game still shows beside it'] = alpha(pg, 500, 300) == 0
    pg.evaluate("setTab('status')"); pg.wait_for_timeout(300)
    pg.evaluate("document.getElementById('railBtn').click()"); pg.wait_for_timeout(500)
    res['arrow slides it back, and the map comes back for the bar'] = pg.evaluate("document.getElementById('app').getBoundingClientRect().left") >= 1920 and pg.evaluate("tab") == 'map'
    pg.evaluate("document.querySelector('#railR .rw.grow').click()"); pg.wait_for_timeout(500)
    res['tapping the hint opens it in the panel'] = pg.evaluate("railIsOpen") is True and pg.evaluate("document.getElementById('pop').className") == 'show'
    pg.close()
    # battle
    pg = page(1920, 1080, '#rail', fight)
    t = pg.evaluate("document.getElementById('railR').innerHTML")
    res['enemies on the right in a fight'] = pg.evaluate("RAILB.foes.length") == 4 and pg.evaluate("document.querySelectorAll('#railR .rfoe').length") == 4
    res['party on the left, three cards and rewards'] = pg.evaluate("document.querySelectorAll('#railL .rw').length") == 4
    res['nothing cut off'] = pg.evaluate("(function(){var r=document.getElementById('railR'),b=document.getElementById('railBtn').getBoundingClientRect(),l=r.lastElementChild.getBoundingClientRect();return l.bottom<=b.top+1})()")
    pg.close()
    # other screens
    for w, h, rem, rw in ((1280, 720, '2px', 160), (2400, 1080, '3px', 480)):
        pg = page(w, h, '#rail', walk)
        res['%dx%d' % (w, h)] = pg.evaluate("[getComputedStyle(document.documentElement).fontSize,document.getElementById('railL').offsetWidth]") == [rem, rw]
        pg.close()
    # panel only (0.24): a 4:3 screen, no bars, a see-through arrow
    pg = page(1440, 1080, '#panel', fight)
    res['panel only: no bars'] = pg.evaluate("getComputedStyle(document.getElementById('railL')).display") == 'none' and pg.evaluate("getComputedStyle(document.getElementById('railR')).display") == 'none'
    res['panel only: the whole screen is see-through but the arrow'] = alpha(pg, 100, 100) == 0 and alpha(pg, 1400, 100) == 0 and alpha(pg, 1000, 540) == 0
    ab = pg.evaluate("(function(){var e=document.getElementById('railBtn'),r=e.getBoundingClientRect();return [r.left,r.top,r.right,r.bottom,getComputedStyle(e).opacity]})()"); print(ab)
    res['panel only: the arrow is on the right edge, half way up, part see-through'] = ab[2] == 1440 and abs((ab[1] + ab[3]) / 2 - 540) < 2 and ab[0] == 1440 - 26 * 3 and float(ab[4]) < 1
    res['panel only: the page keeps its tab'] = pg.evaluate("setTab('items');railOpen(true);railOpen(false);tab") == 'items'
    pg.evaluate("railOpen(true)"); pg.wait_for_timeout(500)
    res['panel only: slides in, the game beside it (1080 high is 3 pixels to 1, so 960 wide here)'] = pg.evaluate("document.getElementById('app').getBoundingClientRect().left") == 480 and alpha(pg, 100, 100) == 0
    res['panel only: the arrow moves to its edge'] = pg.evaluate("document.getElementById('railBtn').getBoundingClientRect().right") == 480
    pg.close()
    pg = page(1440, 1080, '#panel', walk)
    res['panel only: the app is told the real sizes, so taps land right'] = pg.evaluate("Native.railGeom=function(a,b,c){window.__g=[a,b,c]};fit();__g") == [960 / 1440, 78 / 1440, 132 / 1080]
    pg.close()
    pg = page(1920, 1200, '#rail', walk)
    res['quick info: told the real sizes too'] = pg.evaluate("Native.railGeom=function(a,b,c){window.__g=[a,b,c]};fit();__g") == [960 / 1920, 90 / 1920, 132 / 1200]
    pg.close()
    pg = page(640, 480, '#panel', walk)
    res['panel only: 640x480'] = pg.evaluate("document.getElementById('app').getBoundingClientRect().width") == 480
    pg.close()
    pg = page(480, 800, '#panel', walk)
    res['panel only: held upright it still fits'] = pg.evaluate("document.getElementById('app').getBoundingClientRect().width") == 480
    pg.close()
    # off by default
    pg = page(540, 720, '', walk)
    res['off without the app asking'] = pg.evaluate("RAIL") is False and pg.evaluate("getComputedStyle(document.getElementById('railL')).display") == 'none' and pg.evaluate("document.getElementById('app').getBoundingClientRect().width") == 540
    pg.close()
    b.close()
for k, v in res.items(): print(('PASS ' if v else 'FAIL ') + k)
print('ERRORS:', errs or 'none')
print('ALL PASS' if all(res.values()) and not errs else 'FAILED')
