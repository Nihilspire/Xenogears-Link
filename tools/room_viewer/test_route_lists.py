"""Headless check of the room viewer's two route check lists (world-map ways out with no place, hint pages with no way through
doors). Needs the built xenogears-room-viewer.html and a disc 1 image: python3 test_route_lists.py DISC [outdir]
Uses the viewer's test hook window.__RVQ."""
import sys, os
from playwright.sync_api import sync_playwright
H = os.path.dirname(os.path.abspath(__file__)); disc = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else H
errs, res = [], {}
def ok(name, cond, extra=''): res[name] = (bool(cond), extra)
Q = "window.__RVQ()"
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 1400, 'height': 900})
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('file://' + H + '/xenogears-room-viewer.html'); pg.wait_for_timeout(1500)
    opts = pg.evaluate("[...document.querySelectorAll('#rqSel option')].map(o=>o.value+' = '+o.textContent)")
    ok('lists in the menu', any(o.startswith('wmx') for o in opts) and any(o.startswith('gaps') for o in opts), opts[-2:])
    nw, ng = pg.evaluate(Q + ".RQ.wmx[1].length"), pg.evaluate(Q + ".RQ.gaps[1].length")
    ok('25 world-map ways out', nw == 25, nw); ok('32 hint gaps', ng == 32, ng)
    print('gap kinds', pg.evaluate(Q + ".RQ.gaps[1].reduce((o,q)=>(o[q[5]]=(o[q[5]]||0)+1,o),{})"))
    print('menu:', opts[-2:])
    pg.set_input_files('#discFile', disc)
    pg.wait_for_function(Q + ".disc", timeout=180000); pg.wait_for_timeout(1500)
    # world-map list: first entry
    w0 = pg.evaluate(Q + ".RQ.wmx[1][0]")
    # the Check list section starts folded: open it by its heading, as Jack would
    pg.click('#rvSec > .lab'); pg.select_option('#rqSel', 'wmx'); pg.click('#rqNext')
    pg.wait_for_function(Q + ".f===%d" % w0[0], timeout=60000); pg.wait_for_timeout(2500)
    sel = pg.evaluate("(function(){var r=%s;return r.exSel>=0?r.exitsOf(r.f)[r.exSel]:null})()" % Q)
    ok('world-map entry opens its room', pg.evaluate(Q + ".f") == w0[0], w0)
    ok('its way out is selected', sel is not None and sel[2] == -1 and sel[0] is None, sel)
    ok('edit mode on', pg.evaluate(Q + ".state.edit"))
    print('  why:', pg.inner_text('#rqWhy')[:220])
    pg.evaluate("document.getElementById('rvSec').scrollIntoView()"); pg.screenshot(path=os.path.join(out, 'rv_world.png'))
    pg.evaluate(Q + ".exSet(120,340,0)"); pg.evaluate(Q + ".rqShow()")
    ok('placing it marks it done', 'placed at 120, 340' in pg.inner_text('#rqWhy') and pg.inner_text('#rqDone').startswith('1 done'), pg.inner_text('#rqDone'))
    # gaps list: first entry with an arrival spot, so Add door places it
    gi = pg.evaluate("(function(){var r=%s;return r.RQ.gaps[1].findIndex(function(q){return r.ARR[q[0]]&&r.ARR[q[0]][q[2]]})})()" % Q)
    q = pg.evaluate(Q + ".RQ.gaps[1][%d]" % gi)
    pg.select_option('#rqSel', 'gaps'); pg.evaluate(Q + ".rqGo(%d)" % gi)
    pg.wait_for_function(Q + ".f===%d" % q[0], timeout=60000); pg.wait_for_timeout(2500)
    ok('gap entry opens its room at the step', pg.evaluate(Q + ".f") == q[0] and pg.evaluate(Q + ".state.step") == q[3] - 1, q)
    print('  why:', pg.inner_text('#rqWhy')[:300])
    ok('Add door button shown and enabled', pg.is_visible('#rqGapAdd') and pg.is_enabled('#rqGapAdd'), pg.inner_text('#rqGapAdd'))
    pg.screenshot(path=os.path.join(out, 'rv_gap.png'))
    n0 = pg.evaluate(Q + ".exitsOf(%d).length" % q[0]); pg.click('#rqGapAdd'); pg.wait_for_timeout(400)
    last = pg.evaluate(Q + ".exitsOf(%d).slice(-1)[0]" % q[0])
    ok('Add door adds a placed door to the next room', pg.evaluate(Q + ".exitsOf(%d).length" % q[0]) == n0 + 1 and last[2] == q[2] and last[0] is not None, last)
    ok('the gap then reads fixed', 'Fixed' in pg.inner_text('#rqWhy'), pg.inner_text('#rqWhy')[:120])
    pg.screenshot(path=os.path.join(out, 'rv_gap_fixed.png'))
    ok('both edits are in the exit edits (Export edits)', sorted(pg.evaluate("Object.keys(%s.EXED)" % Q)) == sorted([str(w0[0]), str(q[0])]), pg.evaluate("Object.keys(%s.EXED)" % Q))
    # a gap with no arrival spot: added with no place and selected
    gj = pg.evaluate("(function(){var r=%s;return r.RQ.gaps[1].findIndex(function(q){return q[2]>=0&&!(r.ARR[q[0]]&&r.ARR[q[0]][q[2]])})})()" % Q)
    if gj >= 0:
        q2 = pg.evaluate(Q + ".RQ.gaps[1][%d]" % gj); pg.evaluate(Q + ".rqGo(%d)" % gj)
        pg.wait_for_function(Q + ".f===%d" % q2[0], timeout=60000); pg.wait_for_timeout(2000)
        pg.click('#rqGapAdd'); pg.wait_for_timeout(300)
        sel2 = pg.evaluate("(function(){var r=%s;return r.exitsOf(r.f)[r.exSel]})()" % Q)
        ok('no arrival spot: door added unplaced and selected', sel2 and sel2[2] == q2[2] and sel2[0] is None, sel2)
    b.close()
for k, (v, e) in res.items(): print(('PASS ' if v else 'FAIL ') + k, '' if v else e)
print('ERRORS:', errs[:6] or 'none')
