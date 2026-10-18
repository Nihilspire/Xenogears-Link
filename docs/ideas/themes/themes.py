from PIL import Image
src=Image.open('/home/claude/xenogears-link/app/www/img/frame.png').convert('RGBA')
def lerp(a,b,t):return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))
def ramp(stops,t):
    t=max(0,min(1,t))
    for i in range(len(stops)-1):
        if t<=stops[i+1][0]:
            a,b=stops[i],stops[i+1];return lerp(a[1],b[1],(t-a[0])/(b[0]-a[0]+1e-9))
    return stops[-1][1]
TH={
 'solaris':dict(fill=(8,16,22),inner=(70,110,130),metal=[(0,(10,14,18)),(.5,(120,130,140)),(1,(225,232,240))],hi=(240,250,255)),
 'weltall':dict(fill=(14,6,8),inner=(90,30,36),metal=[(0,(20,6,6)),(.5,(120,24,28)),(1,(220,80,70))],hi=(255,220,210)),
 'shevat':dict(fill=(8,22,20),inner=(50,100,90),metal=[(0,(10,20,16)),(.5,(90,140,110)),(1,(200,235,200))],hi=(235,255,240)),
 'kislev':dict(fill=(26,16,10),inner=(100,70,45),metal=[(0,(24,12,6)),(.5,(150,80,40)),(1,(240,170,100))],hi=(255,236,210)),
 'oled':dict(fill=(0,0,0),inner=(40,40,44),metal=[(0,(0,0,0)),(.5,(55,55,60)),(1,(110,110,118))],hi=(150,150,160)),
}
for n,t in TH.items():
    im=src.copy();p=im.load()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            r,g,b,a=p[x,y]
            if a==0: continue
            if (r,g,b)==(12,12,34): c=t['fill']
            elif (r,g,b)==(57,57,99): c=t['inner']
            elif r>200 and g>200 and b>200: c=t['hi']
            else: c=ramp(t['metal'],(r+g+b)/3/140)
            p[x,y]=c+(a,)
    im.save('/home/claude/npc/t/themes/frame_%s.png'%n)
print('ok')
