#!/bin/bash
ROOT="${ROOT:-$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)}"
# Builds pcsx_rearmed libretro core for arm64 Android without running the repo's makefiles.
set -e
S=$ROOT/third_party/pcsx_rearmed
O=$ROOT/work/arm/obj
CC="aarch64-linux-gnu-gcc"
mkdir -p $O
C=$S/libpcsxcore; SPU=$S/plugins/dfsound; GPU=$S/plugins/gpulib; FE=$S/frontend; DRC=$C/new_dynarec
LC=$S/deps/libretro-common; LCHDR=$S/deps/libchdr; LZ=$LCHDR/deps/lzma-26.02; ZS=$LCHDR/deps/zstd-1.5.7; MZ=$LCHDR/deps/miniz-3.1.2
SRC="
$C/cdriso.c $C/cdrom.c $C/cdrom-async.c $C/cheat.c $C/database.c $C/decode_xa.c $C/mdec.c $C/misc.c $C/pad.c $C/plugins.c $C/ppf.c
$C/psxbios.c $C/psxcommon.c $C/psxcounters.c $C/psxdma.c $C/psxevents.c $C/psxhw.c $C/psxinterpreter.c $C/psxmem.c $C/r3000a.c
$C/sio.c $C/spu.c $C/gpu.c $C/gte.c $C/gte_nf.c $C/gte_divider.c
$SPU/dma.c $SPU/freeze.c $SPU/registers.c $SPU/spu.c $SPU/out.c $SPU/nullsnd.c
$GPU/gpu.c $GPU/prim.c $GPU/vout_pl.c $GPU/gpu_async.c
$S/plugins/cdrcimg/cdrcimg.c
$FE/main.c $FE/plugin.c $FE/cspace.c $FE/libretro.c $FE/pcsxr-threads.c
$LCHDR/src/libchdr_bitstream.c $LCHDR/src/libchdr_cdrom.c $LCHDR/src/libchdr_chd.c $LCHDR/src/libchdr_codec_cdfl.c
$LCHDR/src/libchdr_codec_cdlz.c $LCHDR/src/libchdr_codec_cdzl.c $LCHDR/src/libchdr_codec_cdzs.c $LCHDR/src/libchdr_codec_flac.c
$LCHDR/src/libchdr_codec_huff.c $LCHDR/src/libchdr_codec_lzma.c $LCHDR/src/libchdr_codec_zlib.c $LCHDR/src/libchdr_codec_zstd.c
$LCHDR/src/libchdr_flac.c $LCHDR/src/libchdr_huffman.c $LZ/src/LzmaDec.c $ZS/zstddeclib.c $MZ/miniz.c
$LC/compat/compat_posix_string.c $LC/compat/fopen_utf8.c $LC/compat/compat_strl.c $LC/encodings/encoding_utf.c
$LC/file/file_path.c $LC/file/file_path_io.c $LC/file/retro_dirent.c $LC/streams/file_stream.c $LC/streams/file_stream_transforms.c
$LC/string/stdstring.c $LC/string/rstrtod.c $LC/time/rtime.c $LC/vfs/vfs_implementation.c $LC/features/features_cpu.c

$DRC/new_dynarec.c $DRC/pcsxmem.c $DRC/emu_if.c
$S/plugins/gpu_neon/psx_gpu/psx_gpu_simd.c $S/plugins/gpu_neon/psx_gpu_if.c
$C/gte_arm64.S $C/gte_nf_arm64.S $DRC/linkage_arm64.S $LZ/Asm/arm64/LzmaDecOpt.S
"
FLAGS="-fPIC -O2 -ffast-math -fno-strict-aliasing -ffunction-sections -fdata-sections -w
 -DHAVE_LIBRETRO -DNO_FRONTEND -DREARMED -DP_HAVE_MMAP=1 -DP_HAVE_PTHREAD=1 -DP_HAVE_POSIX_MEMALIGN=1
 -DHAVE_CHD -DZ7_LZMA_DEC_OPT -DUSE_MINIZ -DMINIZ_NO_STDIO -DMINIZ_NO_DEFLATE_APIS -DMINIZ_NO_ARCHIVE_APIS -DUSE_LIBRETRO_VFS
 -DLIGHTREC_CUSTOM_MAP=0 -DNDRC_THREAD -DNEON_BUILD -DTEXTURE_CACHE_4BPP -DTEXTURE_CACHE_8BPP -DGPU_NEON -DSIMD_BUILD
 -DUSE_ASYNC_CDROM -DUSE_ASYNC_GPU -DUSE_ASYNC_SPU -DHAVE_RTHREADS -DGIT_VERSION=\"c881679\"
 -I$ROOT/core/inc -I$S/include -I$S/deps/crypto -I$LCHDR/include -I$LZ/include -I$ZS -I$MZ -I$LC/include"
OBJS=""
pids=0
for f in $SRC; do
  o=$O/$(echo ${f#$S/} | tr '/' '_').o
  OBJS="$OBJS $o"
  if [ ! -f $o ] || [ $f -nt $o ]; then
    ( $CC $FLAGS -c $f -o $o 2>$o.err || { echo "FAIL $f"; head -20 $o.err; } ) &
    pids=$((pids+1)); if [ $pids -ge 8 ]; then wait -n || true; pids=$((pids-1)); fi
  fi
done
wait
for o in $OBJS; do [ -f $o ] || { echo "missing $o"; exit 1; }; done
$CC -shared -o $ROOT/work/arm/libpcsx_rearmed.so $OBJS \
  -Wl,--version-script=$ROOT/core/psxlink-version-script -Wl,--gc-sections -Wl,-z,max-page-size=16384 \
  -Wl,-soname,libpcsx_rearmed.so -lm -ldl -lpthread
echo BUILT
