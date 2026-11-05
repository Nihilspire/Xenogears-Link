#!/bin/bash
ROOT="${ROOT:-$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)}"
# my own compile of nugget/openbios (fast boot, no shell), mirroring its Makefile flags
set -e
R=$ROOT/third_party/nugget; O=$ROOT/work/obios/obj; mkdir -p $O; cd $ROOT/work/obios
P=mipsel-linux-gnu
ARCH="-march=mips1 -mabi=32 -EL -fno-pic -mno-shared -mno-abicalls -mfp32 -mno-llsc -fno-stack-protector -nostdlib -ffreestanding"
CPP="-ffunction-sections -fdata-sections -mno-gpopt -fomit-frame-pointer -fno-builtin -fno-strict-aliasing -Wno-attributes $ARCH -I$R -DXPRINTFNOALLOC -DOPENBIOS_BOOT_MODE_NO_SHELL -Os -g"
SRCS="common/psxlibc/fastmemset.s openbios/boot/psx.s"
for s in card/backupunit.c card/device.c cdrom/cdrom.c cdrom/events.c cdrom/filesystem.c cdrom/helpers.c cdrom/statemachine.c charset/sjis.c fileio/filesystem.c fileio/misc.c fileio/stdio.c gpu/gpu.c handlers/irq.c handlers/setup.c handlers/syscall.c kernel/alloc.c kernel/events.c kernel/flushcache.s kernel/handlers.c kernel/libcmisc.c kernel/memory-c.c kernel/memory-s.s kernel/misc.c kernel/qsort.c kernel/psxexe.c kernel/psxexec.s kernel/setjmp.s kernel/threads.c kernel/util.c kernel/vectors.s kernel/xprintf.c main/main.c main/splash.c pio/pio.c shell/shell.c sio0/busyloop.s sio0/card.c sio0/cardfasttrack.s sio0/driver.c sio0/pad.c tty/tty.c patches/hash.c patches/patches.c patches/clear_card_1.c patches/custom_handler_1.c patches/initgun_1.c patches/patch_card_info_1.c patches/patch_card_1.c patches/patch_card_2.c patches/patch_card2_1.c patches/patch_card2_2.c patches/patch_gte_1.c patches/patch_gte_2.c patches/patch_gte_3.c patches/patch_pad_1.c patches/patch_pad_2.c patches/patch_pad_3.c patches/remove_ChgclrPAD_1.c patches/remove_ChgclrPAD_2.c patches/send_pad_1.c patches/send_pad_2.c; do SRCS="$SRCS openbios/$s"; done
OBJS=""
for s in $SRCS; do
  o=$O/$(echo $s | tr / _).o; OBJS="$OBJS $o"
  case $s in *.s) $P-gcc $ARCH -I$R -g -c -o $o $R/$s ;; *.c) $P-gcc $CPP -c -o $o $R/$s ;; esac
done
$P-objcopy -I binary --set-section-alignment .data=4 --rename-section .data=.font1,alloc,load,readonly,data,contents -O elf32-tradlittlemips -B mips $R/openbios/charset/font1.raw $O/font1.o
$P-objcopy -I binary --set-section-alignment .data=4 --rename-section .data=.font2,alloc,load,readonly,data,contents -O elf32-tradlittlemips -B mips $R/openbios/charset/font2.raw $O/font2.o
$P-gcc -g -o openbios.elf $OBJS $O/font1.o $O/font2.o $EXTRA -Wl,-Map=openbios.map -nostdlib -T$R/nooverlay.ld -T$R/openbios/psx-bios.ld -static -Wl,--gc-sections $ARCH -Wl,--oformat=elf32-tradlittlemips -Os -Wl,--defsym=__openbios_reserve_code_cave=1
$P-objcopy -O binary openbios.elf openbios.bin
ls -la openbios.bin
