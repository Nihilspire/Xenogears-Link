import asyncio,subprocess
from playwright.async_api import async_playwright
OUT='/tmp/claude-0/prev/'
MOCK=r"""(function(){
var A2=[
 ['STORY',[
  [1,'A Night in Lahan','Survive the attack on Lahan','0:41:12'],
  [1,'Desert Crossing','Reach Bledavik','3:05:48'],
  [1,'Champion of Bledavik','Win the Bledavik tournament','6:22:30'],
  [1,'Sea Legs','Board the Yggdrasil','7:10:04'],
  [1,'Nisan Pilgrim','Arrive in Nisan','11:48:51'],
  [1,'Up the Tower','Reach the summit of Babel Tower','24:16:09'],
  [0,'Disc 1 Complete','See the end of disc 1',null],
  [0,'The End','See the credits',null]]],
 ['BATTLE',[
  [1,'Deathblow!','Land a deathblow','0:52:40'],
  [1,'Overdrive','Deal 2,000 damage in one hit','14:03:11'],
  [2,'Fei\'s Arts','Learn every Fei deathblow',[17,24]],
  [1,'Grounded','Beat Fis-6 before its Mechanics arrive','20:44:02'],
  [0,'Arena Regular','Win 10 Battle Arena matches',[3,10]]]],
 ['EXPLORE',[
  [2,'Treasure Hunter','Open every chest on disc 1',[87,134]],
  [1,'Lost in the Ducts','Walk every room of the Babel duct system','23:58:27'],
  [0,'Cartographer','Visit 300 rooms',[212,300]]]],
 ['CHALLENGE',[
  [0,'Swift Pilgrim','Finish disc 1 in under 30 hours','24:16 so far'],
  [0,'Light Packer','Beat Ramsus with no item used',null]]]];
var h='',tot=0,un=0;A2.forEach(function(c){c[1].forEach(function(a){tot++;if(a[0]===1)un++})});
h+='<div class="row">'+T('ACHIEVEMENTS','y')+'<span class="sp"></span>'+T(un+' / '+tot,'n')+'</div>';
h+='<div class="row">'+['ALL','STORY','BATTLE','EXPLORE','CHALLENGE'].map(function(t,i){return T(i===0?'['+t+']':' '+t+' ',i===0?'y':'g')}).join('')+'</div><div class="sep"></div>';
A2.forEach(function(c){h+='<div class="row">'+T(c[0],'c')+'</div>';
 c[1].forEach(function(a){var st=a[0],r;
  if(st===2){var p=a[3];r='<span class="bar ep s" style="width:40rem"><i style="width:'+Math.round(p[0]/p[1]*100)+'%"></i></span>'+T(p[0]+'/'+p[1],'w')}
  else if(st===1)r=T(a[3],'g');else r=T(a[3]?(Array.isArray(a[3])?a[3][0]+'/'+a[3][1]:a[3]):'LOCKED','g');
  h+='<div class="row">'+T(st===1?'* ':st===2?'+ ':'- ',st===1?'y':st===2?'c':'g')+T(a[1],st===1?'w':st===2?'w':'g')+'<span class="sp"></span>'+r+'</div>';
  h+='<div class="row" style="height:8rem">'+T('  '+a[2],'g')+'</div>'})});
document.getElementById('main').className='scroll';
document.getElementById('main').innerHTML=win('<div class="col" style="padding:0 4rem;gap:0">'+h+'</div>','card');
})()"""
TOAST=r"""(function(){var d=document.createElement('div');d.style.cssText='position:absolute;left:50%;top:26rem;transform:translateX(-50%);z-index:50;width:300rem';
d.innerHTML=win('<div class="col" style="padding:0 2rem;gap:0"><div class="row">'+T('* ACHIEVEMENT UNLOCKED','y')+'<span class="sp"></span>'+T('11/18','g')+'</div><div class="row">'+T('Up the Tower','w')+'</div><div class="row">'+T('Reach the summit of Babel Tower','g')+'</div></div>','');
document.getElementById('app').appendChild(d)})()"""
async def shot(p,ram,name,js,poll=True):
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium',args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist','--enable-unsafe-swiftshader'])
    cx=await b.new_context(viewport={'width':640,'height':360},device_scale_factor=2);pg=await cx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)[:200]))
    await pg.goto('http://localhost:8765/index.html');await pg.wait_for_timeout(900)
    await pg.evaluate("f=>fetch(f).then(r=>r.arrayBuffer()).then(a=>{TestKit.mem.set(new Uint8Array(a));bootStart();goodPolls=5;linkMode='m80';poll()})",ram)
    for i in range(6): await pg.wait_for_timeout(400);await pg.evaluate("poll()")
    await pg.evaluate("if(window.TestKit&&TestKit.stop)TestKit.stop()");await pg.evaluate(js);await pg.wait_for_timeout(500)
    await pg.screenshot(path=OUT+name);print(name,errs[:3]);await b.close()
async def main():
    srv=subprocess.Popen(['python3','-m','http.server','8765','-d','/home/claude/npc/t'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);await asyncio.sleep(1)
    async with async_playwright() as p:
        await shot(p,'field266.bin','ach_list.png',"window.poll=function(){};window.render=function(){};"+MOCK)
        await shot(p,'field266.bin','ach_list2.png',"window.poll=function(){};window.render=function(){};"+MOCK+";document.getElementById('main').scrollTop=9999")
        await shot(p,'field266.bin','ach_toast.png',"window.poll=function(){};"+TOAST)
    srv.kill()
asyncio.run(main())
