# [category, name, how to earn, what the app reads, status R/P/N, icon, hidden(spoiler)]
# status: R = the app reads this today, P = data is mapped but needs a small new check, N = needs new RAM mapping
A=[]
def a(c,n,d,how,st,ic,hid=0):A.append(dict(c=c,n=n,d=d,how=how,st=st,ic=ic,hid=hid))
S='STORY'
a(S,'Harvest Eve','Wake up in Lahan the day before the wedding','Story step 1 or later','R','px:house')
a(S,'House on a Hill',"Bring Citan the package from the village",'Story step 10','R','px:package')
a(S,'Fallen Shadows','Live through the night Lahan burned','Story step 24','R','spr:g9_0')
a(S,'Girl in the Forest','Meet Elly in the Black Moon Forest','Story step 27','R','px:moon')
a(S,'Sand Sailor',"Reach Bart's hideout, the Pirate's Lair",'Story step 54','R','px:ship')
a(S,'Operation Aveh','Slip into Bledavik on the eve of the festival','Story step 60','R','px:castle')
a(S,'Fatima Heir','Free Margie from Fatima Castle','Story step 75','R','spr:25_0')
a(S,'City of Peace','Arrive at the cathedral town of Nisan','Story step 81','R','px:cross')
a(S,'Iron City','Enter Nortune, the capital of Kislev','Story step 99','R','px:factory')
a(S,'Sewer Rat','Find your way out of the Nortune sewers','Story step 114','R','spr:49_1')
a(S,'Gear Dock Raid',"Break into Kislev's gear dock",'Story step 126','R','px:wrench')
a(S,'Adrift at Sea','Wash out to sea after escaping Ignas','Story step 139','R','px:wave')
a(S,'Men of the Sea','Come aboard the Thames','Story step 140','R','px:anchor')
a(S,'The Orphanage',"Visit Billy's orphans in Aquvy",'Story step 152','R','px:heart')
a(S,'Ocean Floor','Dive to the ruins on the sea bed','Story step 165','R','px:fish')
a(S,'Tower of Babel','Reach Babel Tower','Story step 169','R','px:tower')
a(S,'Sky City','Set foot in Shevat','Story step 175','R','px:island')
a(S,'Hold the Line','Defend Nisan from the Solaris assault','Story step 198','R','px:shield',1)
a(S,'Gatecrasher','Bring down all three gate generators','Story step 208','R','px:gates',1)
a(S,'All-Seeing Eye','Get out of Solaris alive','Story step 219','R','px:eye',1)
a(S,'Disc 1 Complete','See the disc change at the end of disc 1','The disc-end screen (menu 6)','R','px:disc')
a(S,'Break the Seal','Break the seal','Story step 263','R','px:lock',1)
a(S,'The Stars Know','Reach the chapter of the same name','Story step 281','R','px:stars3',1)
a(S,'Paradise','Reach the chapter of the same name','Story step 288','R','px:wings',1)
a(S,'Awakening','See the true form of a familiar gear','Story step 330','R','spr:g13_1',1)
a(S,'The End','See the credits','The ending screen','R','img:title')

P='PARTY'
for i,(nm,who,ttl) in enumerate([('Elly','Elly','Black Moon Ally'),('Citan','Citan','House Call'),('Bart','Bart','Pirate Prince'),('Billy','Billy','Etone'),('Rico','Rico','Champion of Kislev'),('Emeralda','Emeralda','Deep Sea Girl'),('Chu-Chu','Chu-Chu','Pink and Fluffy'),('Maria','Maria',"Seibzehn's Pilot")]):
    a(P,ttl,who+' joins the party','Party "joined" bits (PARTY-4)','R','p48:%d'%(i+1),1 if nm in('Emeralda','Maria') else 0)
a(P,'Full House','Have all eight companions join','All eight party bits','R','px:group')

D='DEATHBLOWS'
a(D,'First Blow','Learn a deathblow','Any learned bit in the skill records','R','px:spark')
for nm,ix,cnt in [('Fei',0,13),('Elly',1,11),('Citan',2,11),('Bart',3,11),('Billy',4,10),('Rico',5,10),('Emeralda',6,10)]:
    t={'Fei':'Way of the Fist','Elly':'Officer Training','Citan':'Uzuki Style','Bart':'Whip Master','Billy':'Gunholic','Rico':'Ring King','Emeralda':'Nano Arts'}[nm]
    a(D,t,'Learn all %d of %s\'s deathblows'%(cnt,nm),'Skill record learned bits, %d of %d'%(cnt,cnt),'R','pb:%d'%ix,1 if nm=='Emeralda' else 0)
a(D,'Drawn Blade',"Learn all 11 of Citan's sword deathblows",'Skill record learned bits (sword record)','R','pb:9',1)
a(D,'Fifty Arts','Learn 50 deathblows across the party','Learned bits added up','R','px:scroll')
a(D,'Gear Arts','Unlock a gear deathblow','Gear deathblow unlock bits','P','px:cog')
a(D,'Infinity','Land an Infinity combo in a gear','The combo level in battle','P','px:infinity')

E='ETHER'
a(E,'Ether Adept','Learn every ether one character can learn','Ether bits at skill record +0x06','P','px:orb')
a(E,'Full Spectrum','Learn every ether in the party','Ether bits for all characters','P','px:orb2')

L='LEVELS'
a(L,'Growing Up','Reach level 20 with anyone','Character level','R','px:arrowup')
a(L,'Veteran','Reach level 40 with anyone','Character level','R','px:star2')
a(L,'Elite','Reach level 60 with anyone','Character level','R','px:star')
a(L,'Legend','Reach level 99 with anyone','Character level','R','px:crown')
a(L,'Fifty Strong','Get every party member to level 50','Levels of all joined characters','R','px:stars3')
a(L,'Nine Nines','Reach 9,999 max HP on foot','Character max HP','R','px:heartplus')

B='BOSSES'
for nm,sp,t,d,hid in [
 ('Rankar Dragon','g11_0','Dragon Slayer','Beat the Rankar Dragon in the forest',0),
 ('Calamity','g19_0','Calamity Averted','Beat the Calamity',0),
 ('Wyrm','g39_0','Worm Turned','Beat the Wyrm',0),
 ('Brigandier','g31_0','Just Hit Him','Beat the Brigandier',0),
 ('Dan','8_0','Settle Down, Dan','Beat Dan in Lahan',0),
 ('Big Joe','47_0','Crowd Pleaser','Beat Big Joe in the ring',0),
 ('Ramsus','45_1','Mirror Breaker','Beat Ramsus',0),
 ('Redrum','66_0','Redrum Reversed','Beat Redrum in Aquvy',0),
 ('Fis-6','g38_0','Shop Closed','Beat Fis-6',0),
 ('Bladegash','g53_0','Speed Bump','Beat the Bladegash',0),
 ('Dominia','56_0','Elemental','Beat the four Elements on foot',0),
 ('Alkanshel','g15_0','Barrier Breaker','Beat the Alkanshel',0),
 ('Avalanche','g35_2','Snowed Under','Beat the Avalanche',1),
 ('Shakhan','g52_0','Off the Throne','Beat Shakhan',1),
 ('Grahf','55_0','Shadow Boxing','Beat Grahf',1),
 ('Sufal Mass','g44_2','Exactly Three','Beat the Sufal Mass',1),
 ('Id','51_0','Face the Id','Beat Id',1),
 ('Vendetta','g52_1','Vendetta','Beat the Vendetta',1),
 ('Metatron','g61_0','Fallen Angel','Beat Metatron',1),
 ('Deus','g62_0','Deicide','Beat Deus',1)]:
    a(B,t,d,'Won fight with "%s" in the enemy list'%nm,'P','spr:'+sp,hid)

X='EXPLORE'
a(X,'First Find','Open your first chest','Treasure flags','R','px:chest')
a(X,'Treasure Hunter','Open 100 chests','Treasure flags counted','R','px:chestopen')
a(X,'Every Last Chest','Open every chest on disc 1','Treasure flags, disc 1 rooms','R','px:chest2')
a(X,"Midori's Ring",'Find the ring hidden outside Citan\'s house','Flag 0x2C4 bit 3','R','px:ring')
a(X,'Secret Stash','Find the 120 G on the walkway above Citan\'s house','Flag 706 bit 13','R','px:coinbag')
a(X,'Mountain Forager','Pick up the Spider and the Bird Egg on the Mountain Path','Their treasure flags','R','px:egg')
a(X,'Nothing Lost','Reach the disc change with no missables lost','Missables list empty at menu 6','R','px:check')
a(X,'Wanderer','Walk through 100 rooms','The app\'s room list','P','px:boot')
a(X,'Cartographer','Walk through 400 rooms','The app\'s room list','P','px:map')
a(X,'Globetrotter','Land at every place on the world map','World map place reads','P','px:globe')

M='MINI-GAMES'
a(M,'Paper Covers Rock','Beat the rock-paper-scissors man in Lahan','RPS win counter (SVAR+0x40C)','R','px:hand')
a(M,'Undefeated','Win five rock-paper-scissors rounds in a row for his badge','Badge bit (SVAR+0x2CE bit 15)','R','px:badge')
a(M,'Speed Demon','Win a game of Speed','Speed result, room 321','P','px:cards')
a(M,'Emer Jr.','Beat Kanna at Speed','Kanna streak, bit 3 = doll given','R','px:doll')
a(M,'Elly Jr.','Beat Kanna five times in a row','Kanna streak (SVAR+0x194)','R','px:doll2')
a(M,'Bledavik Champion','Win the Bledavik tournament','Story step 72','R','px:trophy')
a(M,'Battling Champ','Win the Battling league in Nortune','Story step 120','R','px:belt')

W='BATTLE & WEALTH'
a(W,'Big Hitter','Deal 1,000 damage in one hit','Best hit (journal)','R','px:fist')
a(W,'Heavy Hitter','Deal 5,000 damage in one hit','Best hit (journal)','R','px:burst')
a(W,'Monster Scholar','Fill 100 bestiary entries','Bestiary count','R','px:book')
a(W,'Penny Saved','Hold 10,000 G','Gold','R','px:coin')
a(W,'Gold Rush','Hold 1,000,000 G','Gold','R','px:coins')
a(W,'Long Haul','Play for 60 hours','Play time','R','px:clock')
a(W,'Swift Pilgrim','Reach the disc change in under 30 hours','Play time at the disc-end screen','R','px:hourglass')
a(W,'Battle Arena Regular','Win 10 Battle Arena matches','Battle Arena result (new)','N','px:belt2')
assert len(A)==100,len(A)
