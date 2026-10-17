#!/usr/bin/env python3
"""Main RAM (2 MB) out of a XenogearsRecomp save state (.pst, "BXSP" version 10).
Layout found 17 Oct 2026: 40-byte header (magic BXSP, version, checksum, game entry 0x80019524, ...), raw CPU/other state up to
byte 600, then zlib streams; the first one inflates to main RAM exactly (0x80000000-0x801FFFFF). VRAM / SPU follow in the rest.
Usage: pst_ram.py state.pst out.bin   (prints program word, room and story step)"""
import sys, zlib, struct
def pst_ram(path):
    d = open(path, 'rb').read()
    if d[:4] != b'BXSP': raise ValueError('not a BXSP state')
    for o in range(40, 8192):                     # the stream starts at 600 in version 10; search in case that moves
        if d[o] != 0x78: continue
        try:
            x = zlib.decompressobj().decompress(d[o:], 0x200000)
            if len(x) == 0x200000: return x
        except zlib.error: pass
    raise ValueError('no RAM stream found')
if __name__ == '__main__':
    r = pst_ram(sys.argv[1])
    if len(sys.argv) > 2: open(sys.argv[2], 'wb').write(r)
    u32 = lambda a: struct.unpack_from('<I', r, a & 0x1FFFFF)[0]; u16 = lambda a: struct.unpack_from('<H', r, a & 0x1FFFFF)[0]
    print('program', u32(0x8006FAF0), 'room', u16(0x8006F94E) & 0x7FF, 'step', u16(0x8006EF64))
