#!/bin/bash
# build_cia.sh: Xenogears Dual 3DS as a .cia (HOME Menu title), from the .3dsx build's ELF. Needs makerom and bannertool in $TOOLS
# (default /home/claude/work/ctr/tools) and Pillow. The banner is the project's own plain text, no game logo or font, and silent.
set -e
HERE=$(cd "$(dirname "$0")/.." && pwd)
TOOLS=${TOOLS:-/home/claude/work/ctr/tools}
OUT=${OUT:-$HOME/xgtmp/ctr}
VER=$(grep -E '^VERSION' "$HERE/Makefile" | sed 's/.*:= *//')
B=$OUT/cia; mkdir -p "$B"
python3 - "$B/banner.png" <<'EOF'
import sys
from PIL import Image, ImageDraw, ImageFont
im = Image.new('RGBA', (256, 128), (14, 22, 58, 255)); d = ImageDraw.Draw(im)
d.rectangle((0, 94, 255, 127), fill=(40, 56, 110, 255))
f = ImageFont.load_default(size=26)
d.text((128, 34), 'XENOGEARS', font=f, fill=(240, 240, 240, 255), anchor='mm')
d.text((128, 66), 'DUAL', font=f, fill=(90, 210, 230, 255), anchor='mm')
d.text((128, 110), 'Link on the second screen', font=ImageFont.load_default(size=13), fill=(240, 240, 240, 255), anchor='mm')
im.save(sys.argv[1])
EOF
python3 -c "import wave,sys; w=wave.open(sys.argv[1],'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(32728); w.writeframes(bytes(4*3273)); w.close()" "$B/silence.wav"
"$TOOLS/bannertool-bin" makebanner -i "$B/banner.png" -a "$B/silence.wav" -o "$B/banner.bnr"
"$TOOLS/bannertool-bin" makesmdh -s "Xenogears Dual 3DS" -l "Xenogears Dual 3DS $VER: your discs + a Link screen" \
    -p "Jack" -i "$HERE/tools/icon.png" -o "$B/icon.icn"
"$TOOLS/makerom-bin" -f cia -o "$OUT/Xenogears Dual 3DS.cia" -target t -exefslogo \
    -elf "$OUT/xenogears3ds.elf" -rsf "$HERE/cia/xenogearsdual.rsf" -icon "$B/icon.icn" -banner "$B/banner.bnr" \
    -major "$(echo $VER | cut -d. -f1)" -minor "$(echo $VER | cut -d. -f2 | cut -d- -f1)" -micro 0
ls -la "$OUT/Xenogears Dual 3DS.cia"
