#!/bin/bash
# One-time setup on Linux (or WSL Ubuntu 24.04): packages, third-party sources, work folders.
# Nothing here runs third-party build scripts: the core is compiled by core/build_core.sh and tests/build_*.sh.
set -e
ROOT="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
cd "$ROOT"
if [ "$1" != "--no-apt" ]; then
  sudo apt-get update
  sudo apt-get install -y clang-18 lld-18 llvm-18 aapt zipalign apksigner dalvik-exchange android-sdk-platform-23 \
    openjdk-17-jdk-headless python3-pil git zip \
    gcc-aarch64-linux-gnu libc6-dev-arm64-cross qemu-user xdelta3
  # only tests/build_openbios.sh needs it, and Ubuntu 26.04 no longer has it
  sudo apt-get install -y gcc-mipsel-linux-gnu 2>/dev/null || echo "gcc-mipsel-linux-gnu not available (OpenBIOS test only)"
  # toolchain/android-clang calls clang-18 itself; the host test builds use plain "clang"/"ld.lld"
  command -v clang >/dev/null || sudo ln -s /usr/bin/clang-18 /usr/local/bin/clang
  command -v ld.lld >/dev/null || sudo ln -s /usr/bin/ld.lld-18 /usr/local/bin/ld.lld
  pip3 install --break-system-packages -q capstone playwright 2>/dev/null || true
fi
mkdir -p third_party
# pcsx_rearmed (libretro fork) at the commit every build so far used, with libpicofe
if [ ! -d third_party/pcsx_rearmed ]; then
  git clone https://github.com/libretro/pcsx_rearmed third_party/pcsx_rearmed
  git -C third_party/pcsx_rearmed checkout c881679
  git -C third_party/pcsx_rearmed submodule update --init --recursive
fi
# bionic headers + .map.txt files only (for the Android stub sysroot in toolchain/)
if [ ! -d third_party/bionic ]; then
  git clone --filter=blob:none --sparse https://github.com/aosp-mirror/platform_bionic third_party/bionic
  git -C third_party/bionic checkout 731631f
  git -C third_party/bionic sparse-checkout set --no-cone /libc/include/ /libc/kernel/uapi/ /libc/kernel/android/ \
    /libc/arch-common/ /libc/libc.map.txt /libm/libm.map.txt /libm/include/ /libdl/libdl.map.txt /libc/private/
fi
# the stub Android sysroot toolchain/android-clang links against
[ -f toolchain/sysroot/usr/lib/libc.so ] || toolchain/build_sysroot.sh
# pcsx_rearmed needs a generated header the makefiles would make
[ -f core/inc/revision.h ] || echo '#define REV "c881679"' > core/inc/revision.h
# work folders for the headless tests (game files are not in the bundle)
mkdir -p work/host/xg/sys work/host/xg/save work/host/xg/shots work/arm work/hostdbg work/chd work/obios work/scratch
cp -n tests/data/*.state tests/data/xga.bin work/host/xg/ 2>/dev/null || true
cp -n tests/data/save/* work/host/xg/save/ 2>/dev/null || true
ln -sfn ../host/xg work/arm/xg
ln -sfn ../host/xg work/hostdbg/xg
echo
echo "Done. Put your Disc 1 CHD at work/host/xg/disc1.chd for the game tests (see CLAUDE.md)."
