import asyncio,sys,json,base64,os,subprocess,re
from playwright.async_api import async_playwright
exec(open('/home/claude/npc/run.py').read().split('SC=json')[0])
t=open('/home/claude/xenogears-link/app/www/hints.js').read();H=json.loads(re.search(r'^window\.HPATH=(.*);\s*$',t,re.M).group(1))
s=open('/home/claude/xenogears-link/app/www/exits.js').read();EX=json.loads(s[s.index('{'):s.rindex('}')+1])
jobs={}
for k,L in H.items():
    for r,sp in L:
        if r<0 or r>=612 or not sp: continue
        for q in sp: jobs.setdefault(r,[]).append(q)
rooms=sorted(jobs)[:int(sys.argv[1]) if len(sys.argv)>1 else 999]
INIT="""window.__discSize=%d;try{['x3d','map3d'].forEach(function(k){localStorage.setItem('xg_'+k,'1')});localStorage.setItem('xg_route','1');localStorage.setItem('xg_tab','map')}catch(e){}"""%SIZE
async def main():
    srv=subprocess.Popen(['python3','-m','http.server','8765','-d','/home/claude/npc/t'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);await asyncio.sleep(1)
    res=[]
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium',args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist','--enable-unsafe-swiftshader'])
        cx=await b.new_context(viewport={'width':640,'height':360});pg=await cx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)[:200]))
        await pg.expose_function('__rd',rd);await pg.add_init_script(INIT)
        await pg.goto('http://localhost:8765/index.html');await pg.wait_for_timeout(800)
        await pg.evaluate("bootStart();goodPolls=5;linkMode='m80'");await pg.wait_for_timeout(500)
        for f in rooms:
            ex=[e for e in EX.get(str(f),[]) if e[0] is not None]
            st=ex[0] if ex else [0,0]
            sc={'f':f,'step':10,'entry':0,'n':0,'me':0,'px':st[0],'pz':st[1],'tx':st[0],'tz':st[1],'act':[]}
            await pg.evaluate("s=>{SCENE(s);goodPolls=5;poll();setTab('map')}",sc)
            try: await pg.wait_for_function("window.M3&&(M3.room==%d)&&(M3.ready||M3.err)"%f,timeout=20000)
            except Exception: print(f,'no room');continue
            await pg.evaluate("s=>{s.py=M3.yAt(s.px,s.pz,0);SCENE(s);poll();M3.setRoute({x:s.px,y:s.py,z:s.pz},{x:s.px+1,z:s.pz,y:null})}",sc)
            try: await pg.wait_for_function("M3.routeReady()",timeout=20000)
            except Exception: print(f,'no route mesh');continue
            for q in jobs[f]:
                r=await pg.evaluate("""a=>{var py=M3.yAt(a[0],a[1],0),pts=M3.route({x:a[0],y:py,z:a[1]},{x:a[2],z:a[3],y:null});if(!pts)return null;
                 var e=pts[pts.length-1],pv=pts[Math.max(0,pts.length-2)],fl=M3.floors(a[2],a[3]);var mj=0;for(var i=1;i<pts.length;i++)mj=Math.max(mj,Math.abs(pts[i][1]-pts[i-1][1]));
                 return {end:e.map(Math.round),prev:pv.map(Math.round),floors:fl.map(Math.round),maxjump:Math.round(mj),n:pts.length}}""",[st[0],st[1],q[0],q[1]])
                res.append([f,q,r]);
                if r and (r['maxjump']>40 or (r['floors'] and min(abs(r['end'][1]-y) for y in r['floors'])>20) or not r['floors']): print(f,q,r)
        print('checked',len(res),'routes',sum(1 for x in res if x[2] is None),'none; errors',errs[:3]);await b.close()
    json.dump(res,open('/tmp/claude-0/rtend.json','w'));srv.kill()
asyncio.run(main())
