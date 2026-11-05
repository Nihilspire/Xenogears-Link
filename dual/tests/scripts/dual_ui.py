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
 analogOn:false,mods:[],bezel:'window',bezels:['Xenogears 4x3.png','Weltall.png'],card:{exists:true,formatted:true,blocksUsed:2,saves:['BASLUS-00664XG000','BASLUS-00664XG001']}};
window.__S=S;
window.App=new Proxy({},{get:(t,k)=>(...a)=>{__calls.push([k,...a]);
 if(k==='state')return JSON.stringify(S);
 if(k==='setDisc'){S.discs[a[0]]={path:a[1],name:a[1].split('/').pop(),ok:true};}
 if(k==='setBootDisc'){S.bootDisc=a[0];}
 if(k==='setBool'){S.opts[a[0]]=a[1];}
 if(k==='addMod'){S.mods.push({id:'mod:'+a[0],name:a[0],code:a[1],source:'Added here',removable:true,on:true});return true;}
 if(k==='setBool'&&a[0]==='analogOn'){S.analogOn=a[1];}
 if(k==='setMod'){S.mods.forEach(m=>{if(m.id===a[0])m.on=a[1]})}
 if(k==='listDir')return JSON.stringify({path:'/storage/emulated/0/PSX',parent:'/storage/emulated/0',entries:[{name:'Saves',path:'/x/Saves',dir:true},{name:'Xenogears (USA) (Disc 2).cue',path:'/sdcard/PSX/Xenogears (USA) (Disc 2).cue',dir:false,size:120,disc:true},{name:'notes.txt',path:'/x/n.txt',dir:false,size:12}]});
 return true;}});
"""
errs=[]
with sync_playwright() as p:
    b=p.chromium.launch()
    for vw,vh,tag in [(540,720,'p'),(720,540,'l')]:
        pg=b.new_page(viewport={'width':vw,'height':vh},device_scale_factor=2.5)
        pg.on('pageerror',lambda e: errs.append(str(e)))
        pg.on('console',lambda m: errs.append(m.text) if m.type=='error' else None)
        pg.add_init_script(mock)
        pg.goto('file://'+XGROOT+'/app/assets/menu/index.html'); pg.wait_for_timeout(700)
        pg.screenshot(path=f'{SH}/d_launch_{tag}.png')
        if tag=='p':
            pg.evaluate("pickDisc(1)"); pg.wait_for_timeout(200); pg.screenshot(path=f'{SH}/d_files.png')
            pg.evaluate("pickFile(1)"); pg.wait_for_timeout(200)
            print('after pick:', pg.evaluate("cur()"), pg.evaluate("__S.discs[1].name"))
            pg.evaluate("go('s-settings')"); pg.wait_for_timeout(200); pg.screenshot(path=f'{SH}/d_settings.png')
            pg.evaluate("fmtArm=true;render()"); pg.wait_for_timeout(100)
            pg.evaluate("document.querySelector('#s-settings [data-key=fmt], #s-settings [data-key=fmtgo]').scrollIntoView()"); pg.wait_for_timeout(100); pg.screenshot(path=f'{SH}/d_card.png')
            pg.evaluate("document.querySelector('#s-settings [data-key=fmtgo]').click()")
            pg.evaluate("pickCard()"); pg.wait_for_timeout(150); print('card picker title ok', pg.evaluate("document.querySelector('#s-files').innerText.length>=0"))
            pg.evaluate("back()")
            pg.evaluate("navKey('down');navKey('down');navKey('ok')"); pg.wait_for_timeout(100)
            pg.evaluate("__S.running=true;__S.inserted=0;openPause()"); pg.wait_for_timeout(200); pg.screenshot(path=f'{SH}/d_pause.png')
            print('calls:', pg.evaluate("__calls.filter(c=>!['state','listDir'].includes(c[0])).map(c=>c.join(' '))"))
    b.close()
print('ERRORS:', errs or 'none')
