#!/bin/bash
# Builds the stub Android sysroot that toolchain/android-clang links against (toolchain/sysroot/usr/lib):
# libc/libm/libdl/liblog .so stubs (only their symbol names matter; the device's real libraries are used at run time),
# bionic's crtbegin_so.o, crtend_so.o, and libgcc.a with __clear_cache. Needs setup.sh's third_party/bionic.
# The *_stub.c files were generated from bionic's .map.txt files with gen_stubs.py (API 30).
set -e
ROOT="${ROOT:-$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)}"
T=$ROOT/toolchain
L=$T/sysroot/usr/lib
B=$ROOT/third_party/bionic
mkdir -p $L
CC="clang-18 --target=aarch64-linux-android30 -fPIC -mno-outline-atomics -O2 -w"
for n in c m dl log; do
  $CC -nostdlib -shared -Wl,-soname,lib$n.so -fuse-ld=lld $T/lib${n}_stub.c -o $L/lib$n.so
done
"$T/android-clang" -O2 -w -I$B/libc/arch-common/bionic -c $B/libc/arch-common/bionic/crtbegin_so.c -o $L/crtbegin_so.o
$CC -c $T/crtend_so.S -o $L/crtend_so.o
$CC -nostdinc -isystem /usr/lib/llvm-18/lib/clang/18/include -c $T/clear_cache.c -o $L/clear_cache.o
rm -f $L/libgcc.a && llvm-ar-18 rcs $L/libgcc.a $L/clear_cache.o && rm $L/clear_cache.o
echo "sysroot: $(ls $L | tr '\n' ' ')"
