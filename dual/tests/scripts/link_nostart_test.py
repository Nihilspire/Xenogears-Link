import os as _os
XGROOT=_os.environ.get('XGROOT') or _os.path.abspath(_os.path.join(_os.path.dirname(__file__),'..','..'))
from playwright.sync_api import sync_playwright
import json
ram=open(XGROOT+'/work/host/xg/ram_lahan2.hex').read().strip()
# mirrors MainActivity.LinkNative.poll(): page = hex & 0x1FFF, 256 bytes from main RAM, reply via onMem
mock = """
window.__RAM = %s;
window.__polls = 0; window.__sends = [];
window.Native = {
  poll: function(host, port, mode, csv, seq){
    window.__polls++;
    setTimeout(function(){
      var pages = csv ? csv.split(',') : [], ok = {}, got = 0;
      pages.forEach(function(p){ var pg = parseInt(p,16) & 0x1FFF; ok[pg.toString(16)] = __RAM.substr(pg*512, 512); got++; });
      onMem({seq: seq, sent: pages.length, got: got, err: '', ok: ok});
    }, 15);
  },
  send: function(h,p,c){ __sends.push(c); },
  discName: function(){ return 'Xenogears (USA) (Disc 1).chd'; }, discSize: function(){ return 357651775; },
  discPick: function(){}, discRead: function(){ return 'ERR:test'; },
  genDir: function(){ return '/data/user/0/com.jack.xenogears/files/gen'; }, genHas: function(){ return false; },
  genRead: function(){ return ''; }, genWrite: function(){ return 'ok'; }, genClear: function(){},
  exitLog: function(){ return 'ok'; }, exitLogClear: function(){}, exitLogShare: function(){},
  focusable: function(){}, beat: function(){}, lastHang: function(){ return ''; },
  __st: [Date.now()-3600e3, 0, 0, 0],
  stateInfo: function(){ return JSON.stringify(this.__st); },
  stateSave: function(n){ var me=this; __sends.push('save'+n); setTimeout(function(){ me.__st[n-1]=Date.now(); onStateDone(n,true,'save'); },50); },
  stateLoad: function(n){ __sends.push('load'+n); setTimeout(function(){ onStateDone(n,true,'load'); },50); }
};
""" % json.dumps(ram)
errs=[]
with sync_playwright() as p:
    b=p.chromium.launch()
    pg=b.new_page(viewport={'width':540,'height':720},device_scale_factor=2)
    pg.on('pageerror',lambda e: errs.append(str(e)))
    pg.on('console',lambda m: errs.append(m.text) if m.type=='error' else None)
    pg.add_init_script(mock)
    pg.goto('file://'+XGROOT+'/app/assets/link/index.html'); pg.wait_for_timeout(2500)
    pg.screenshot(path='shots/link_nostart.png')
    print('bootGo', pg.evaluate('bootGo'), 'booted', pg.evaluate('booted'), 'boot layer shown', pg.evaluate("getComputedStyle(document.getElementById('boot')).display"), 'polls', pg.evaluate('__polls'))
    pg2=b.new_page(viewport={'width':540,'height':720},device_scale_factor=2)
    pg2.on('pageerror',lambda e: errs.append('idle: '+str(e)))
    pg2.add_init_script(mock.replace("onMem({seq: seq, sent: pages.length, got: got, err: '', ok: ok});","onMem({seq: seq, sent: pages.length, got: 0, err: 'timeout', ok: {}});"))
    pg2.goto('file://'+XGROOT+'/app/assets/link/index.html'); pg2.wait_for_timeout(6500); pg2.screenshot(path='shots/link_idle.png')
    print('idle: booted', pg2.evaluate('booted'), '| text has RETROARCH:', 'RETROARCH' in pg2.evaluate("document.getElementById('boot').innerHTML"))
    b.close()
print('ERRORS:', errs[:8] or 'none')
