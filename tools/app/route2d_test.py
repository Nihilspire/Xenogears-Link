import asyncio,sys,json,subprocess
from playwright.async_api import async_playwright
exec(open('/home/claude/npc/rtend.py').read().split('async def main')[0])
async def main():
    srv=subprocess.Popen(['python3','-m','http.server','8765','-d','/home/claude/npc/t'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);await asyncio.sleep(1)
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        pg=await (await b.new_context(viewport={'width':640,'height':360})).new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)[:200]))
        await pg.expose_function('__rd',rd);await pg.add_init_script(INIT)
        await pg.goto('http://localhost:8765/index.html');await pg.wait_for_timeout(800)
        await pg.evaluate("bootStart();goodPolls=5;linkMode='m80'");await pg.wait_for_timeout(500)
        ok=bad=0;worst=0;fails=[]
        for f in rooms:
            for tq in [None]:
                pass
            await pg.evaluate("f=>{mapLoad(f)}",f);await pg.wait_for_timeout(150)
            await pg.evaluate("f=>{mapLoad(f)}",f);await pg.wait_for_timeout(100)
            ex=[e for e in EX.get(str(f),[]) if e[0] is not None]
            for st in ex[:3]:
                for q in jobs[f]:
                    r=await pg.evaluate("""a=>{var m=mapLoad(a[0]);if(!m)return 'nomap';R2.key='';var t0=performance.now();var r=route2d(m,a[0],1,function(){return 1},{x:a[1],z:a[2]},{x:a[3],z:a[4]});return [r?r.length:0,performance.now()-t0]}""",[f,st[0],st[1],q[0],q[1]])
                    if r=='nomap': continue
                    worst=max(worst,r[1])
                    if r[0]>1: ok+=1
                    else: bad+=1;fails.append([f,st[:3],q])
        print('ok',ok,'fail',bad,'worst ms',round(worst,1),errs[:2]);print(fails[:40]);await b.close()
    srv.kill()
asyncio.run(main())
