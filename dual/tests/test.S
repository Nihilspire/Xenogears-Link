    .set noreorder
    .set noat
    .text
    .globl _start
_start:
    lui   $t0, 0x1f80
    sw    $zero, 0x1814($t0)        # GP1 reset
    lui   $t1, 0x0300
    sw    $t1, 0x1814($t0)          # display enable
    lui   $t1, 0x0800
    ori   $t1, $t1, 0x0001
    sw    $t1, 0x1814($t0)          # 320x240 NTSC 15bpp
    lui   $t1, 0x0500
    sw    $t1, 0x1814($t0)          # display area start 0,0
    lui   $t1, 0x06c6
    ori   $t1, $t1, 0x0260
    sw    $t1, 0x1814($t0)          # h range
    lui   $t1, 0x0704
    ori   $t1, $t1, 0x2018
    sw    $t1, 0x1814($t0)          # v range
    lui   $t1, 0xe300
    sw    $t1, 0x1810($t0)          # draw area top-left
    lui   $t1, 0xe403
    ori   $t1, $t1, 0xbd3f
    sw    $t1, 0x1810($t0)          # draw area bottom-right 319,239
    lui   $t1, 0xe500
    sw    $t1, 0x1810($t0)          # draw offset 0
    lui   $s0, 0x8010               # counter address 0x80100000
    li    $s1, 0
loop:
    addiu $s1, $s1, 1
    sw    $s1, 0($s0)
    andi  $t2, $s1, 0x3fff
    bnez  $t2, loop
    nop
    # every 16384 iterations: fill the screen with a colour derived from the counter
    srl   $t3, $s1, 14
    andi  $t3, $t3, 0xff
    lui   $t1, 0x0200
    or    $t1, $t1, $t3            # 0x020000RR  (red channel ramps)
    sw    $t1, 0x1810($t0)
    sw    $zero, 0x1810($t0)       # x,y = 0,0
    lui   $t1, 0x00f0
    ori   $t1, $t1, 0x0140
    sw    $t1, 0x1810($t0)         # w,h = 320,240
    sw    $t3, 4($s0)              # mirror the colour at 0x80100004
    b     loop
    nop
