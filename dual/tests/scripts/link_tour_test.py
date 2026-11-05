"""Renders the Link app tour cards in Dual (mock bridge from link_state_test.py) to check the wording fits the pop-up.
Shots: tests/scripts/shots/tour_<n>.png"""
import os, json, re
XGROOT = os.environ.get('XGROOT') or os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
from playwright.sync_api import sync_playwright
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'link_state_test.py')).read()
mock = re.search(r'mock = """(.*?)"""', src, re.S).group(1) % (json.dumps(open(XGROOT + '/work/host/xg/ram_lahan2.hex').read().strip()), XGROOT)
errs = []; os.makedirs('shots', exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 540, 'height': 720}, device_scale_factor=2)
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.add_init_script(mock); pg.goto('file://' + XGROOT + '/app/assets/link/index.html'); pg.wait_for_timeout(2500)
    cards = pg.evaluate("TOUR.map(function(t){return t[2]+': '+t[3]})")
    for c in cards: print(' ', c)
    for i in (0, 1, 3, 4, 7, 8, 9):
        pg.evaluate("tourGo(%d)" % i); pg.wait_for_timeout(350); pg.screenshot(path='shots/tour_%d.png' % i)
    print('emulator/RetroArch left in the tour:', [c for c in cards if re.search(r'(?i)emulator|retroarch', c)])
    b.close()
print('ERRORS:', errs or 'none')
