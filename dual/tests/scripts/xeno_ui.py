import os as _os
XGROOT=_os.environ.get('XGROOT') or _os.path.abspath(_os.path.join(_os.path.dirname(__file__),'..','..'))
from playwright.sync_api import sync_playwright
SH='shots'
mock = """
window.__calls=[];
const S={version:'0.2',storage:true,folder:'/storage/emulated/0/Xenogears',running:false,gameId:'',
 discs:[{path:'/sdcard/PSX/Xenogears (Disc 1).cue',name:'Xenogears (USA) (Disc 1).cue',ok:true},{path:'',name:'',ok:false}],
 bootDisc:0,inserted:-1,discCount:0,bios:['scph1001.bin'],spanned:true,secondScreen:false,linkOnPhone:false,customLink:false,fastForward:false,
 opts:{showAtStart:true,touch:true,stick:true,stickDpad:true,smooth:true,integer:false,hires:false,hleBios:false,link:true,swapScreens:false,muted:false,opacity:55,padType:2,stickThreshold:40},
 mods:[{name:'Analog movement',code:'D0012345 0000 80012346 0001',source:'Added here',removable:true,on:true}],slots:[Date.now(),0,0,0]};
window.__S=S;
window.App=new Proxy({},{get:(t,k)=>(...a)=>{__calls.push([k,...a]);
 if(k==='state')return JSON.stringify(S);
 if(k==='setDisc'){S.discs[a[0]]={path:a[1],name:a[1].split('/').pop(),ok:true};}
 if(k==='setBootDisc'){S.bootDisc=a[0];}
 if(k==='setBool'){S.opts[a[0]]=a[1];}
 if(k==='addMod'){S.mods.push({name:a[0],code:a[1],source:'Added here',removable:true,on:true});return true;}
 if(k==='listDir')return JSON.stringify({path:'/storage/emulated/0/PSX',parent:'/storage/emulated/0',entries:[{name:'Saves',path:'/x/Saves',dir:true},{name:'Xenogears (USA) (Disc 2).cue',path:'/sdcard/PSX/Xenogears (USA) (Disc 2).cue',dir:false,size:120,disc:true},{name:'notes.txt',path:'/x/n.txt',dir:false,size:12}]});
 return true;}});
"""
errs=[]
with sync_playwright() as p:
    b=p.chromium.launch()
    pg=b.new_page(viewport={'width':540,'height':720},device_scale_factor=2)
    pg.on('pageerror',lambda e: errs.append(str(e)))
    pg.on('console',lambda m: errs.append(m.text) if m.type=='error' else None)
    pg.add_init_script(mock)
    pg.goto('file://'+XGROOT+'/app/assets/menu/index.html'); pg.wait_for_timeout(400)
    pg.screenshot(path=f'{SH}/x_launch.png')
    # pick disc 2 through the picker
    pg.evaluate("pickDisc(1)"); pg.wait_for_timeout(150)
    print('picker items:', pg.evaluate("[...document.querySelectorAll('#files .item')].map(e=>e.textContent.trim())"))
    pg.screenshot(path=f'{SH}/x_files.png')
    pg.evaluate("document.querySelector('#files .item[data-dir=\"0\"]').click()"); pg.wait_for_timeout(150)
    print('after pick screen:', pg.evaluate("document.querySelector('.screen.on').id"), '| disc2:', pg.evaluate("document.querySelectorAll('.disc .f')[1].textContent"))
    # boot disc 2, add mod, toggle show-at-start
    pg.evaluate("document.querySelectorAll('.disc')[1].querySelectorAll('button')[1].click()"); pg.wait_for_timeout(100)
    pg.fill('#mod-name','Test'); pg.fill('#mod-code','80010000 0001'); pg.evaluate("addMod()"); pg.wait_for_timeout(100)
    pg.evaluate("flip('showAtStart')"); pg.wait_for_timeout(100)
    print('START label/disabled:', pg.evaluate("[$('go').textContent,$('go').disabled]"), '| note:', pg.evaluate("$('disc-note').textContent"))
    pg.screenshot(path=f'{SH}/x_launch2.png')
    # settings via gear
    pg.evaluate("document.querySelector('#s-launch .icon').click()"); pg.wait_for_timeout(150)
    pg.screenshot(path=f'{SH}/x_settings.png', full_page=False)
    print('settings on:', pg.evaluate("document.querySelector('.screen.on').id"), '| wins:', pg.evaluate("[...document.querySelectorAll('#settings .win h2')].map(e=>e.textContent)"))
    pg.evaluate("back()"); print('back ->', pg.evaluate("document.querySelector('.screen.on').id"))
    pg.evaluate("document.getElementById('go').click()")
    # pause menu while running
    pg.evaluate("__S.running=true;__S.inserted=1;__S.gameId='SLUS00669'; openPause()"); pg.wait_for_timeout(150)
    pg.screenshot(path=f'{SH}/x_pause.png')
    pg.evaluate("navKey('down');navKey('ok')")
    print('calls:', pg.evaluate("__calls.filter(c=>!['state','listDir'].includes(c[0])).map(c=>c.join(' '))"))
    b.close()
print('ERRORS:', errs or 'none')
