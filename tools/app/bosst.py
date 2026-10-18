import asyncio,subprocess,sys
from playwright.async_api import async_playwright
async def main():
    srv=subprocess.Popen(['python3','-m','http.server','8765','-d','/home/claude/npc/t'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);await asyncio.sleep(1)
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        for ram in sys.argv[1].split(','):
            pg=await (await b.new_context(viewport={'width':640,'height':360},device_scale_factor=2)).new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)[:200]))
            await pg.goto('http://localhost:8765/index.html');await pg.wait_for_timeout(800)
            await pg.evaluate("f=>fetch(f).then(r=>r.arrayBuffer()).then(a=>{TestKit.mem.set(new Uint8Array(a));bootStart();goodPolls=5;linkMode='m80';poll()})",ram)
            for i in range(8): await pg.wait_for_timeout(400);await pg.evaluate("poll()")
            info=await pg.evaluate("JSON.stringify({md:lastMd,bs:Date.now()-bstart,bd:bossDone,ins:inBattle(),re:roomEnemies(),pop:document.getElementById('pop').className,best:LS.get('best','')})")
            print(ram,info[:600],errs[:2])
            await pg.screenshot(path='/tmp/claude-0/boss_'+ram.replace('.bin','')+'.png');await pg.close()
        await b.close()
    srv.kill()
asyncio.run(main())
