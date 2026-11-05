#!/bin/bash
# Links tests/drive.c (a line-command driver around app/jni/psxlink.c) against the x86 and ARM test cores.
set -e
ROOT="${ROOT:-$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)}"
J=/usr/lib/jvm/java-17-openjdk-amd64/include
cd "$ROOT/work/host" && gcc -O1 -w -I$J -I$J/linux "$ROOT/tests/drive.c" -o drive -L. -lpcsx_rearmed -Wl,-rpath,. -lpthread && echo "work/host/drive"
if [ -f "$ROOT/work/arm/libpcsx_rearmed.so" ]; then
  cd "$ROOT/work/arm" && aarch64-linux-gnu-gcc -O1 -w -I$J -I$J/linux "$ROOT/tests/drive.c" -o drive -L. -lpcsx_rearmed -Wl,-rpath,'$ORIGIN' -lpthread && echo "work/arm/drive"
fi
if [ -f "$ROOT/work/hostdbg/libpcsx_rearmed.so" ]; then cp "$ROOT/work/host/drive" "$ROOT/work/hostdbg/drive"; fi
