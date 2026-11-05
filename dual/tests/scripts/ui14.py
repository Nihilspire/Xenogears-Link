import os as _os
XGROOT=_os.environ.get('XGROOT') or _os.path.abspath(_os.path.join(_os.path.dirname(__file__),'..','..'))
from playwright.sync_api import sync_playwright
mock = """
const S={version:'0.14',storage:true,folder:'/storage/emulated/0/Xenogears',running:%s,gameId:'SLUS00664',
 discs:[{path:'/sdcard/PSX/Xenogears (Disc 1).chd',name:'Xenogears (USA) (Disc 1).chd',ok:true},{path:'',name:'',ok:false}],
 bootDisc:0,inserted:0,discCount:1,bios:[],spanned:false,secondScreen:true,linkOnPhone:false,customLink:false,fastForward:false,
 opts:{showAtStart:true,touch:true,stick:true,stickDpad:true,smooth:true,integer:false,hires:false,hleBios:false,link:true,swapScreens:false,muted:false,opacity:55,padType:0,stickThreshold:40},
 analogOn:true,analogState:%d,mods:[{id:'cht:32',name:'Analog: left stick walks in any direction'.slice(7),group:'analog',on:true},{id:'cht:33',name:'push the left stick fully to run',group:'analog',on:true},{id:'cht:34',name:'right stick camera (orbit, tilt; R3+stick zoom, R3 tap reset)',group:'analog',on:true},{id:'cht:35',name:'invert right stick up/down',group:'analog',on:false},{id:'cht:36',name:'L1/R1 turn the camera smoothly (stepless)',group:'analog',on:true}],slots:[0,0,0,0],card:{},bezel:'none',bezels:[]};
window.App=new Proxy({},{get:(t,k)=>(...a)=>{ if(k==='state')return JSON.stringify(S); if(k==='setBool'&&a[0]==='analogOn')S.analogOn=a[1]; return true;}});
"""
errs=[]
with sync_playwright() as p:
    b=p.chromium.launch()
    for run,st,name in [('false',-1,'idle'),('true',2,'running'),('true',3,'stood')]:
        pg=b.new_page(viewport={'width':960,'height':540})
        pg.on('pageerror',lambda e: errs.append(str(e)))
        pg.add_init_script(mock%(run,st))
        pg.goto('file://'+XGROOT+'/app/assets/menu/index.html'); pg.wait_for_timeout(500)
        pg.screenshot(path='ui14_%s.png'%name, full_page=True)
    print('errors',errs)
