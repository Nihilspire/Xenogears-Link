#!/bin/bash
# build_test.sh [SCRIPTFILE] [OUT]: the build with CTR_TEST, which plays a compiled-in script by frame because Azahar's input can't be
# driven headless. SCRIPTFILE is C: "#define TEST_SCRIPT {frame, frames, pad bits, tap x, tap y, lx, ly, rx, ry}, ..." and optionally
# #define TEST_STATE "sdmc:/..." (loaded at frame 2) and #define TEST_QUIT frame. Pad bits are libretro ids: B(cross) 1<<0, START 1<<3,
# UP 1<<4, DOWN 1<<5, LEFT 1<<6, RIGHT 1<<7, A(circle) 1<<8, X(triangle) 1<<9.
set -e
HERE=$(cd "$(dirname "$0")/.." && pwd)
T=${2:-$HOME/xgtmp/ctr-test}
mkdir -p "$T/obj"
if [ -n "$1" ]; then cp "$1" "$T/test_script.h"; else echo '#define TEST_SCRIPT {0,0,0,-1,-1,0,0,0,0}' > "$T/test_script.h"; fi
# the core is the same as the plain build's: reuse its objects
[ -e "$T/obj/core" ] || ln -s "$HOME/xgtmp/ctr/obj/core" "$T/obj/core"; cp "$HOME/xgtmp/ctr/obj/linkdata.h" "$T/obj/" 2>/dev/null
rm -f "$T/obj/main.o" "$T/obj/linkscr.o" "$T/obj/linkmap.o" "$T/obj/linkfight.o"
export DEVKITPRO=/opt/devkitpro DEVKITARM=/opt/devkitpro/devkitARM
make -j8 -C "$HERE" OUT="$T" OBJDIR="$T/obj" EXTRA="-DCTR_TEST -I$T" 2>&1 | grep -E 'error|warning: impl|3dsx' | tail -5
