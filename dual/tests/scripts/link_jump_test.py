"""Link's story jump in DEV (0.22): the rows only show with DEV on inside Dual, < HINT and HINT > land on the step that shows the hint
before and after, SET STEP and WARP call the app, HINT ROOM goes to the page's room, a world-map page says so, and once jumped the
room log and progress log stop. Picture: shots/link_jump.png."""
import os, json, re
XGROOT = os.environ.get('XGROOT') or os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
from playwright.sync_api import sync_playwright
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'link_state_test.py')).read()
mock = re.search(r'mock = """(.*?)"""', src, re.S).group(1) % (json.dumps(open(XGROOT + '/work/host/xg/ram_lahan2.hex').read().strip()), XGROOT)
# the stand-in acts as the app does: a story step lands in RAM, and the warp reports through its state
mock += """
window.__dev = {story: [], warp: [], state: 0, jumped: false};
function setStep(v){ var h = ('0' + (v & 255).toString(16)).slice(-2) + ('0' + (v >> 8).toString(16)).slice(-2), o = 0x6EF64 * 2; __RAM = __RAM.slice(0, o) + h + __RAM.slice(o + 4); }
Native.devStory = function(v){ __dev.story.push(v); __dev.jumped = true; setStep(v); };
Native.devWarp = function(r, d){ __dev.warp.push([r, d]); __dev.jumped = true; __dev.state = 2; };
Native.devWarpState = function(){ return __dev.state; };
Native.devJumped = function(){ return __dev.jumped; };
"""
res, errs = {}, []
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 540, 'height': 720}, device_scale_factor=2)
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.add_init_script(mock); pg.goto('file://' + XGROOT + '/app/assets/link/index.html'); pg.wait_for_timeout(1800)
    pg.evaluate("LS.set('tourDone','1');tourEnd&&tourEnd();openSet()"); pg.wait_for_timeout(200)
    res['hidden with DEV off'] = pg.evaluate("document.getElementById('idrm')") is None
    pg.evaluate("sv('dev','1')"); pg.wait_for_timeout(200)
    res['shown with DEV on'] = pg.evaluate("!!document.getElementById('idrm')")
    k = pg.evaluate("hintNext();hintNext.k"); s0 = pg.evaluate("u16(A.STORY)")
    i = next(j for j, x in enumerate(k) if x > s0)
    pg.evaluate("devHintGo(1)"); pg.wait_for_timeout(400)
    res['HINT > shows the next hint'] = pg.evaluate("hintNext().step") == k[i + 1] and pg.evaluate("u16(A.STORY)") == k[i]
    pg.evaluate("devHintGo(-1)"); pg.wait_for_timeout(400)
    res['< HINT goes back'] = pg.evaluate("hintNext().step") == k[i]
    pg.evaluate("devSetStory(21)"); pg.wait_for_timeout(400)
    res['SET STEP'] = pg.evaluate("u16(A.STORY)") == 21 and pg.evaluate("__dev.story[__dev.story.length-1]") == 21
    pg.evaluate("devSetStory('nonsense')"); res['a bad step is ignored'] = pg.evaluate("__dev.story[__dev.story.length-1]") == 21
    pg.evaluate("devWarpGo(103,2)"); res['WARP'] = pg.evaluate("__dev.warp[__dev.warp.length-1]") == [103, 2]
    pg.evaluate("devWarpGo(9999,0)"); res['a bad room is refused'] = pg.evaluate("__dev.warp.length") == 1
    hr = pg.evaluate("hintRooms(hintNext())[0][0]"); pg.evaluate("hintSetPage(hintNext(),0,false);devHintRoom()")
    res['HINT ROOM warps to the page\'s room'] = pg.evaluate("__dev.warp[__dev.warp.length-1]") == [hr, 0]
    w = pg.evaluate("Object.keys(HINTS).map(Number).sort(function(a,b){return a-b}).filter(function(s){return (HPATH[s]||[]).length&&HPATH[s][0][0]<0})[0]")
    pg.evaluate("devSetStory(%d)" % (w - 1)); pg.wait_for_timeout(400); n = pg.evaluate("__dev.warp.length")
    pg.evaluate("hintSetPage(hintNext(),0,false);devHintRoom()")
    res['a world-map page says so'] = pg.evaluate("__dev.warp.length") == n and pg.evaluate("devMsg").find('WORLD MAP') >= 0
    res['room log stops once jumped'] = pg.evaluate("xlogOn()") is False
    pg.evaluate("devSetStory(21);lastSet='';drawSet()"); pg.wait_for_timeout(300)
    pg.evaluate("document.getElementById('idrm').scrollIntoView({block:'center'})"); pg.wait_for_timeout(200)
    pg.screenshot(path='shots/link_jump.png')
    b.close()
for k_, v in res.items(): print(('PASS ' if v else 'FAIL ') + k_)
print('ERRORS:', errs or 'none')
