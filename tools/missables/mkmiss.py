"""Missable pickups (Oct 2026): app/www/missables.js.
List from the community write-ups (roughatsea.com 'Secrets of Xenogears', GameFAQs board threads, Almar's guide), each matched to the
room scripts on the disc: a chest or gift already in treasure.js is tagged by room + item code; pickups the treasure scan does not
see (no inventory item, or a give the scan dropped) are added with the flag read off their routine (tools/field, chest.py / surv.py).
MISS.tag  'room:var:bit' -> when it is lost
MISS.extra room -> [[var, bit, name, x, z, when lost, gift]]; var -1 = no flag, taken while item `bit` is in the inventory"""
import json,re,subprocess
TRE=json.loads(subprocess.check_output(['node','-e','global.window=global;require("/home/claude/xenogears-link/app/www/treasure.js");console.log(JSON.stringify(TREASURE))']))
L=[ # room, item code, when it is lost
 (9,79,'Leaving Lahan'),(7,76,'Leaving Lahan'),(1,61,'Leaving Lahan'),(1,2,'Leaving Lahan'),(1,602,'Leaving Lahan'),
 (15,88,'Yui cooks it'),
 (102,77,'Bledavik fair ends'),
 (241,634,'Leaving the sewers'),(240,616,'Leaving the sewers'),(242,645,'Leaving the sewers'),(228,1103,'Gear dock raid ends'),(236,655,'Gear dock raid ends'),(195,92,'Before Night Purge'),
 (264,1090,'Past the conveyor'),
 (318,607,'Leaving Thames'),(315,609,'Leaving Thames'),(316,1120,'Leaving Thames'),(318,1072,'Leaving Thames'),(312,628,'Short window'),
 (327,84,'Orphanage moves on'),(331,85,'Orphanage moves on'),(328,86,'Orphanage moves on'),(326,78,'Orphanage moves on'),(329,288,'Orphanage moves on'),
 (414,1105,'Before repair bot'),
 (430,1125,'Before Solaris'),(430,603,'Before Solaris'),(423,101,'Shevat falls'),(432,102,'Shevat falls'),(431,103,'Shevat falls'),(428,654,'Shevat falls'),
 (445,629,'Past the ladder exit'),(447,618,'Past the ladder exit'),
 (486,1120,'Jasper lock used'),(502,1121,'Boss door'),(568,1122,'Past hologram room'),
 (570,637,'Past hologram room'),(571,543,'Past hologram room'),(568,645,'Past hologram room'),(589,567,'Past hologram room'),
 (588,558,'Past hologram room'),(566,1033,'Past hologram room'),(582,281,'Past hologram room'),(580,615,'Past hologram room'),
 (628,550,'Leaving the Relic'),(628,639,'Leaving the Relic'),(628,568,'Leaving the Relic'),(629,619,'Leaving the Relic'),
 (641,639,'Leaving the Relic'),(642,639,'Leaving the Relic'),(646,559,'Leaving the Relic'),(649,541,'Leaving the Relic'),
 (644,568,'Leaving the Relic'),(651,568,'Leaving the Relic'),(644,638,'Leaving the Relic'),(651,638,'Leaving the Relic'),
]
tag={};miss=[]
for r,c,w in L:
    hit=[t for t in TRE.get(str(r),[]) if c in t[2]]
    if not hit: miss.append((r,c));continue
    for t in hit: tag['%d:%d:%d'%(r,t[0],t[1])]=w
extra={
 17:[[708,3,"Midori's Ring",-121,-959,'1st Citan visit',1]],          # actor 30: 'Found Midori's Ring', flag 0x2C4 bit 3; spot = the room's otherwise unused trigger zone 1, behind the house
 15:[[-1,87,'Spider',-642,1476,'Leaving mtn path',1]],              # actor 16 gives item 87 with no flag
 428:[[716,10,'Power Crisis + Yamato Belt + 12 more',None,None,'Shevat falls',1]], # actor 12, flag 0x2CC bit 10 (three rocks on the platform)
}
open('/home/claude/xenogears-link/app/www/missables.js','w').write('/* missable pickups: see tools/missables/mkmiss.py */\nwindow.MISS='+json.dumps({'tag':tag,'extra':extra},separators=(',',':'))+';\n')
print(len(tag),'tagged; not found:',miss)
