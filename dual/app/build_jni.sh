#!/bin/bash
# Builds jni/psxlink.c into out/lib/arm64-v8a/libxenolink.so, and copies in the core if core/ has a newer build.
set -e
ROOT="${ROOT:-$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)}"
cd "$ROOT/app"
J=/usr/lib/jvm/java-17-openjdk-amd64/include
CORE="$ROOT/core/pcsx_rearmed_libretro_android.so"
if [ -f "$CORE" ] && [ "$CORE" -nt out/lib/arm64-v8a/libpcsx_rearmed.so ]; then cp "$CORE" out/lib/arm64-v8a/libpcsx_rearmed.so; echo "core updated"; fi
"$ROOT/toolchain/android-clang" -O2 -w -shared -I$J -I$J/linux -Ijni jni/psxlink.c -o out/lib/arm64-v8a/libxenolink.so \
  -Wl,-soname,libxenolink.so -Lout/lib/arm64-v8a -lpcsx_rearmed -llog -lc -ldl -Wl,-z,max-page-size=16384 -Wl,-z,defs
echo "built out/lib/arm64-v8a/libxenolink.so ($(nm -D out/lib/arm64-v8a/libxenolink.so | grep -c Java_) JNI functions)"
