import asyncio,subprocess,json
from playwright.async_api import async_playwright
BEST=json.dumps({"Hecht":{"h":7500,"x":48106,"g":20000,"d":[["HP Drive",100],["EP Drive",50]],"s":132,"n":1},"Fis-6":{"h":6800,"x":67284,"g":15000,"d":[["Ground",100]],"s":135,"n":2},"White Knight":{"h":290,"x":2800,"g":500,"d":[["Ether Ar",20],["Lite Ar+1",50]],"s":182,"n":3},"Shakhan Guard":{"h":250,"x":6528,"g":65,"d":[],"s":189,"n":4},"Shakhan Monk":{"h":200,"x":1101,"g":500,"d":[["Rosesol",50]],"s":189,"n":4}})
JLOG=json.dumps({"0":[0,1],"5":[3600*2+500,8],"10":[3600*6,15],"20":[3600*14,26],"25":[3600*20,31]})
VW,VH=int(__import__('os').environ.get('VW','640')),int(__import__('os').environ.get('VH','360'))
async def shot(p,name,js,ram='s1.bin',sub=None):
    pg=await (await p.new_context(viewport={'width':VW,'height':VH},device_scale_factor=2)).new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)[:200]))
    await pg.add_init_script("try{localStorage.setItem('xg_best',%s);localStorage.setItem('xg_jlog',%s);localStorage.setItem('xg_tab','journal');localStorage.setItem('xg_jsub','%s')}catch(e){}"%(json.dumps(BEST),json.dumps(JLOG),sub or 'prog'))
    await pg.goto('http://localhost:8765/index.html');await pg.wait_for_timeout(800)
    await pg.evaluate("f=>fetch(f).then(r=>r.arrayBuffer()).then(a=>{TestKit.mem.set(new Uint8Array(a));bootStart();goodPolls=5;linkMode='m80';poll()})",ram)
    for i in range(5): await pg.wait_for_timeout(400);await pg.evaluate("poll()")
    if js: await pg.evaluate(js);await pg.wait_for_timeout(500)
    await pg.screenshot(path='/tmp/claude-0/j_'+name+'.png');print(name,errs[:3]);await pg.close()
async def main():
    srv=subprocess.Popen(['python3','-m','http.server','8765','-d','/home/claude/npc/t'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);await asyncio.sleep(1)
    async with async_playwright() as pw:
        p=await pw.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        await shot(p,'prog',None,sub='prog')
        await shot(p,'miss',None,sub='miss')
        await shot(p,'misspop',"missPop(0)",sub='miss')
        await shot(p,'best',None,sub='best')
        await shot(p,'bestpop',"bestPop('Hecht')",sub='best')
        # gear shop: menu 5, first gear shop number
        await shot(p,'shop',"(function(){var ks=Object.keys(SHOPS.g);var n=+ks[ks.length>8?8:0];var m=TestKit.mem;var w=function(a,v,b){for(var i=0;i<b;i++)m[(a&0x1FFFFF)+i]=(v>>(8*i))&255};w(A.MENU,5,4);m[A.MARG&0x1FFFFF]=n;poll();last={};render();setTimeout(function(){poll();last={};render()},300)})()")
        await shot(p,'shop2',"(function(){var ks=Object.keys(SHOPS.i);var n=+ks[ks.length>8?8:0];var m=TestKit.mem;var w=function(a,v,b){for(var i=0;i<b;i++)m[(a&0x1FFFFF)+i]=(v>>(8*i))&255};w(A.MENU,4,4);m[A.MARG&0x1FFFFF]=n;poll();last={};render();setTimeout(function(){poll();last={};render()},300)})()")
        await p.close()
    srv.kill()
asyncio.run(main())
