    .set noreorder
    .set noat
    .text
    .globl _start
_start:
    lui   $sp, 0x801f
    ori   $sp, $sp, 0xff00
    lui   $s0, 0x8010              # results at 0x80100000
    # InitCard(0)  B(0x4A)
    li    $a0, 0
    li    $t1, 0x4a
    jal   0xb0
    nop
    # StartCard()  B(0x4B)
    li    $t1, 0x4b
    jal   0xb0
    nop
    # _bu_init()  A(0x55)
    li    $t1, 0x55
    jal   0xa0
    nop
    # fd = open("bu00:BASLUS-00664TEST", FCREATE | 1 block<<16)  B(0x32)
    la    $a0, name
    lui   $a1, 0x0001
    ori   $a1, $a1, 0x0200
    li    $t1, 0x32
    jal   0xb0
    nop
    sw    $v0, 0($s0)
    move  $a0, $v0
    li    $t1, 0x36                # close
    jal   0xb0
    nop
    # fd = open(name, FWRITE=2)
    la    $a0, name
    li    $a1, 2
    li    $t1, 0x32
    jal   0xb0
    nop
    sw    $v0, 4($s0)
    move  $s1, $v0
    # write(fd, buf, 8192)  B(0x35)
    move  $a0, $s1
    la    $a1, buf
    li    $a2, 8192
    li    $t1, 0x35
    jal   0xb0
    nop
    sw    $v0, 8($s0)
    move  $a0, $s1
    li    $t1, 0x36
    jal   0xb0
    nop
    li    $t0, 0x600d
    sw    $t0, 12($s0)
spin:
    b     spin
    nop
    .data
name: .asciz "bu00:BASLUS-00664TEST"
    .align 4
buf:  .fill 8192, 1, 0x5a
