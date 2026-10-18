import asyncio,subprocess
from playwright.async_api import async_playwright
OUT='/tmp/claude-0/prev/th/';import os;os.makedirs(OUT,exist_ok=True)
CSS={
'classic':'',
'solaris':""".win{border-image-source:url(themes/frame_solaris.png)!important}#app{background:radial-gradient(ellipse at 50% 20%,#20343e 0%,#0a1218 60%,#030608 100%)!important}
.fy{filter:hue-rotate(150deg) saturate(.7) brightness(1.15)}.fo{filter:hue-rotate(170deg) saturate(.5) brightness(1.2)}.pt{border-color:#7a8a96!important}.bar{border-color:#8a9aa8!important}""",
'weltall':""".win{border-image-source:url(themes/frame_weltall.png)!important}#app{background:radial-gradient(ellipse at 50% 30%,#2a0a0e 0%,#120406 60%,#050102 100%)!important}
.fy{filter:hue-rotate(-40deg) saturate(1.3)}.fc{filter:hue-rotate(150deg) saturate(1.2)}.pt{border-color:#7a2026!important}.bar{border-color:#8c2a2a!important}""",
'shevat':""".win{border-image-source:url(themes/frame_shevat.png)!important}#app{background:radial-gradient(ellipse at 50% 30%,#123028 0%,#06140f 60%,#020604 100%)!important}
.fy{filter:hue-rotate(70deg) saturate(.8) brightness(1.1)}.pt{border-color:#4f7a62!important}.bar{border-color:#5f8f72!important}""",
'kislev':""".win{border-image-source:url(themes/frame_kislev.png)!important}#app{background:radial-gradient(ellipse at 50% 30%,#3a2412 0%,#170c05 60%,#060302 100%)!important}
.fc{filter:hue-rotate(170deg) saturate(.9)}.pt{border-color:#8a5426!important}.bar{border-color:#9a6030!important}""",
'oled':""".win{border-image-source:url(themes/frame_oled.png)!important}#app{background:#000!important}
.fy{filter:saturate(.6)}.pt{border-color:#333!important}.bar{border-color:#444!important;background:#000!important}"""}
async def shot(p,ram,th,name):
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
    cx=await b.new_context(viewport={'width':640,'height':360},device_scale_factor=2);pg=await cx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)[:200]))
    await pg.goto('http://localhost:8765/index.html');await pg.wait_for_timeout(900)
    await pg.evaluate("c=>{var s=document.createElement('style');s.textContent=c;document.head.appendChild(s)}",CSS[th])
    await pg.evaluate("f=>fetch(f).then(r=>r.arrayBuffer()).then(a=>{TestKit.mem.set(new Uint8Array(a));bootStart();goodPolls=5;linkMode='m80';poll()})",ram)
    for i in range(6): await pg.wait_for_timeout(400);await pg.evaluate("poll()")
    await pg.wait_for_timeout(300);await pg.screenshot(path=OUT+name);print(name,errs[:2]);await b.close()
async def main():
    srv=subprocess.Popen(['python3','-m','http.server','8765','-d','/home/claude/npc/t'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);await asyncio.sleep(1)
    async with async_playwright() as p:
        for th in CSS:
            await shot(p,'field266.bin',th,th+'_status.png')
            await shot(p,'fis_after.bin',th,th+'_battle.png')
    srv.kill()
asyncio.run(main())
