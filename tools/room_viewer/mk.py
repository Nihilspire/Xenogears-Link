# Builds xenogears-room-viewer.html: viewer_src.html with chd.js, discbuild.js, npc.js and data.js inlined.
# Run node mkdata.js first (data.js from the app's own tables in ../../app/www, plus the arrival spots from tools/app/exit_check.js).
import os
H=os.path.dirname(os.path.abspath(__file__));W=os.path.join(H,'..','..','app','www')
src=open(os.path.join(H,'viewer_src.html')).read();libs=''
for f in [os.path.join(W,'chd.js'),os.path.join(W,'discbuild.js'),os.path.join(H,'npc.js'),os.path.join(H,'data.js')]:
    t=open(f).read(); assert '</script' not in t
    libs+='<script>\n'+t+'\n</script>\n'
open(os.path.join(H,'xenogears-room-viewer.html'),'w').write(src.replace('/*INLINE_LIBS*/',libs));print('built')
