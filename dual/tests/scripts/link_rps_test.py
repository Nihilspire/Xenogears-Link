"""RPS helper in Dual: on by default, its switch under SETTINGS > MINIGAMES, and the card shows while talking to the
RPS man (room 7). Uses link_state_test.py's mock bridge and Lahan RAM dump, with the bytes the helper reads set by hand.
Shots: tests/scripts/shots/link_rps_*.png"""
import os, json, re
XGROOT = os.environ.get('XGROOT') or os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
from playwright.sync_api import sync_playwright
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'link_state_test.py')).read()
mock = re.search(r'mock = """(.*?)"""', src, re.S).group(1)
ram = open(XGROOT + '/work/host/xg/ram_lahan2.hex').read().strip()
mock = mock % (json.dumps(ram), XGROOT)
# set u16/u32 little-endian values in the hex RAM the mock serves
poke = """window.poke=function(a,v,n){a&=0x1FFFFF;var h='';for(var i=0;i<n;i++)h+=((v>>(8*i))&255).toString(16).padStart(2,'0');
 __RAM=__RAM.substr(0,a*2)+h+__RAM.substr(a*2+n*2)};"""
errs, res = [], {}
os.makedirs('shots', exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 540, 'height': 720}, device_scale_factor=2)
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.add_init_script(mock + poke + "localStorage.setItem('tour','done');")
    pg.goto('file://' + XGROOT + '/app/assets/link/index.html'); pg.wait_for_timeout(2500)
    res['rps on by default'] = pg.evaluate('CFG.rps')
    res['speed on by default'] = pg.evaluate('CFG.speed')
    # field (SIG 4), room 7, he throws Scissors (1), no streaks yet
    pg.evaluate("poke(A.SIG,4,4);poke(A.FIELD,(u16(A.FIELD)&0xF800)|7,2);poke(A.SVAR+0x408,1,2);[0x40C,0x40E,0x410,0x412,0x2CE,0x2DE].forEach(function(o){poke(A.SVAR+o,0,2)})")
    pg.wait_for_timeout(1500)
    card = pg.evaluate("rpsView()")
    res['card shows'] = bool(card)
    if card:
        # Link redraws #main several times a second and only keeps the card up during a dialogue, which the mock
        # RAM doesn't fake; so draw it and shoot at once
        pg.evaluate("clearTimeout(pollT);document.getElementById('main').innerHTML=rpsView()"); pg.screenshot(path='shots/link_rps_card.png')
    # the standalone app (not DIRECT) draws the same card plus a DEV tag; Dual's must be shorter by exactly that
    dev = pg.evaluate("(function(){var d=DIRECT;DIRECT=false;var r=rpsView();DIRECT=d;return r})()")
    res['no DEV tag on the card'] = bool(card) and len(dev) - len(card) == len(pg.evaluate("T('DEV','g')"))
    pg.evaluate("openSet()"); pg.wait_for_timeout(300)
    txt = pg.evaluate("lastSet")
    res['MINIGAMES row in settings'] = 'MINIGAMES' in json.dumps(txt) or pg.evaluate("lastSet.indexOf(\"sv('rps'\")>=0")
    pg.evaluate("var s=document.querySelector('#setin');s&&(s.scrollTop=s.scrollHeight)"); pg.wait_for_timeout(200)
    pg.screenshot(path='shots/link_rps_settings.png')
    # switching it off hides the card
    pg.evaluate("sv('rps','0')"); res['off hides the card'] = pg.evaluate("rpsView()") is None
    pg.evaluate("sv('rps','1')")
    b.close()
for k, v in res.items(): print(('PASS ' if v else 'FAIL ') + k)
print('ERRORS:', errs[:8] or 'none')
