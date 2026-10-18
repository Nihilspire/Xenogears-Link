import asyncio,subprocess
from playwright.async_api import async_playwright
MOCK="""n=>{var e=null,k=-1;ENEMIES.some(function(b){var i=b.n.indexOf(n[0]);if(i>=0){e=b;k=i;return true}return false});
 window.reward=function(){return {exp:e?e.x[k]:0,gold:e?e.g[k]:0,drops:[]}};var hp=e?(e.h[k][1]||e.h[k][0]):0;var m=TestKit.mem,b=(A.BSLOT+3*BREC)&0x1FFFFF,w32=function(o,v){for(var i=0;i<4;i++)m[o+i]=(v>>(8*i))&255};m[b+0x4C]=hp&255;m[b+0x4D]=hp>>8;w32(b+REC+0x60,hp);w32(b+REC+0x64,hp);
 var bb=(A.BSLOT+3*BREC)&0x1FFFFF;window.u16=(function(o){return function(a){if(a===A.STORY)return n[1];if((a&0x1FFFFF)===bb+0x4C)return hp;return o(a)}})(window.u16);window.u32=(function(o){return function(a){var q=a&0x1FFFFF;if(q===bb+REC+0x60||q===bb+REC+0x64)return hp;return o(a)}})(window.u32);showEnemy(3,n[0],hp,true)}"""
async def main():
    srv=subprocess.Popen(['python3','-m','http.server','8765','-d','/home/claude/npc/t'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);await asyncio.sleep(1)
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        async def go(ram,name,mock=None):
            pg=await (await b.new_context(viewport={'width':640,'height':360},device_scale_factor=2)).new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)[:200]))
            await pg.goto('http://localhost:8765/index.html');await pg.wait_for_timeout(800)
            await pg.evaluate("f=>fetch(f).then(r=>r.arrayBuffer()).then(a=>{TestKit.mem.set(new Uint8Array(a));bootStart();goodPolls=5;linkMode='m80';poll()})",ram)
            for i in range(8): await pg.wait_for_timeout(400);await pg.evaluate("poll()")
            if mock: await pg.evaluate("window.poll=function(){};window.render=function(){}");await pg.evaluate(MOCK,mock);await pg.wait_for_timeout(300)
            await pg.screenshot(path='/tmp/claude-0/card_'+name+'.png');print(name,errs[:2]);await pg.close()
        await go('ram.bin','hecht')
        for nm,st in [['Shakhan',201],['Sufal Mass',280],['Amphysvena',301],['Sundel',350],['Urobolus',350],['Ramsus',74]]:
            await go('fis_after.bin',nm.replace(' ','_'),[nm,st])
        await b.close()
    srv.kill()
asyncio.run(main())
