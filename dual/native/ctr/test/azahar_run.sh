#!/bin/bash
# azahar_run.sh APP.3dsx OUTDIR "STEPS": boots the build in Azahar (AppImage unpacked in /home/claude/work/azahar) headless under
# Xvfb with Mesa's software OpenGL, as a New 3DS, with its own config and SD card in $AZHOME so other projects' settings stay as they
# are. STEPS: "w:SECONDS" wait, "s:NAME" save OUTDIR/NAME.png of the window. Input can't be driven headless: see build_test.sh.
# The discs: work/host/xg/disc1.chd and disc2.chd (links to Jack's CHDs), linked onto the SD card. Screens show the game: keep OUTDIR
# outside the repo.
R=$(cd "$(dirname "$0")/../../.." && pwd)
APP=$(readlink -f "$1"); OUT=$2; STEPS=$3
AZ=${AZAHAR:-/home/claude/work/azahar/squashfs-root/usr/bin/azahar}
AZHOME=${AZHOME:-$HOME/xgtmp/azahar}
mkdir -p "$OUT" "$AZHOME/config/azahar-emu" "$AZHOME/data/azahar-emu/sdmc/3ds/xenogears-dual"
SD="$AZHOME/data/azahar-emu/sdmc/3ds/xenogears-dual"
CFG="$AZHOME/config/azahar-emu/qt-config.ini"
if [ ! -f "$CFG" ]; then
  cp "$HOME/.config/azahar-emu/qt-config.ini" "$CFG"
  sed -i -e 's/^is_new_3ds=.*/is_new_3ds=true/' -e 's/^is_new_3ds\\default=.*/is_new_3ds\\default=false/' "$CFG"
fi
ln -sf "$(readlink -f "$R/work/host/xg/disc1.chd")" "$SD/Xenogears (USA) (Disc 1).chd"
export XDG_CONFIG_HOME="$AZHOME/config" XDG_DATA_HOME="$AZHOME/data"
export DISPLAY=:79 LIBGL_ALWAYS_SOFTWARE=1 QT_QPA_PLATFORM=xcb
pkill -f 'Xvfb :79' 2>/dev/null; rm -f /tmp/.X79-lock
Xvfb :79 -screen 0 1280x1024x24 >/dev/null 2>&1 & XV=$!
sleep 1
openbox >/dev/null 2>&1 & WM=$!
sleep 1
"$AZ" -w "$APP" >"$OUT/azahar.log" 2>&1 & AP=$!
sleep 8
WIN=$(xdotool search --pid $AP --onlyvisible --name 'Azahar' 2>/dev/null | head -1)
[ -z "$WIN" ] && WIN=$(xdotool search --pid $AP --onlyvisible 2>/dev/null | head -1)
if [ -n "$WIN" ]; then
  xdotool windowmove "$WIN" 0 0 windowsize "$WIN" 853 526 2>/dev/null
  sleep 1
  eval $(xdotool getwindowgeometry --shell "$WIN" 2>/dev/null); OX=${X:-0}; OY=${Y:-0}
fi
for s in $STEPS; do
  IFS=: read -r op a b <<< "$s"
  case $op in
    w) sleep "$a" ;;
    s) import -window root -crop 853x526+${OX:-0}+${OY:-0} +repage "$OUT/$a.png" ;;
  esac
done
kill $AP 2>/dev/null; sleep 1; kill -9 $AP 2>/dev/null; kill $WM $XV 2>/dev/null
echo "--- azahar errors"; grep -iE 'error|critical|unimpl|unknown svc|fail' "$OUT/azahar.log" | grep -viE 'libEGL|MESA|ZINK' | sort | uniq -c | sort -rn | cut -c1-200 | head -${AZLINES:-15}
echo "--- game log"; tail -${LOGLINES:-40} "$SD/xenogears-3ds.log" 2>/dev/null | cut -c1-200
