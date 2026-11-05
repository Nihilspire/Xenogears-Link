#!/usr/bin/env python3
"""mk_pak.py ASSETS OUT.pak: Link's pictures as one file of raw RGB565 for the 3DS (no WebP or PNG decoder there, and no time for one).

The pictures come from the app's assets/link folder, which discbuild.js made from the developer's own disc, so this file holds
game graphics: it stays beside the player's discs on the SD card and is never put in the .3dsx, the .cia or git.

  "XGPK", u32 count, then count x { u32 key, u32 offset, u16 w, u16 h } sorted by key, then the pictures, row by row, little-endian.
  key: (room << 2) | (level + 1)   a room's overhead picture, 256 x 256 (level -1 = the main picture; plan/<room>_<level>.webp)
       0x10000 + 0 / 1             the world maps a / b, 512 x 512
       0x20000 + n                 enemy sprite n (sorted list of spr/, as mk_linkdata.py numbers them), at most 28 x 36; 0 = see-through
"""
import os, re, struct, sys
from PIL import Image

assets, out = sys.argv[1], sys.argv[2]
link = os.path.join(assets, 'link')
ROOM_BG = (16, 16, 24)

def rgb565(im, keyed=False):
    """an RGB or RGBA image as RGB565 bytes; keyed: pixels under half alpha become 0, real black becomes the nearest other value"""
    w, h = im.size
    px = im.load()
    b = bytearray(w * h * 2)
    i = 0
    for y in range(h):
        for x in range(w):
            p = px[x, y]
            v = (p[0] >> 3) << 11 | (p[1] >> 2) << 5 | p[2] >> 3
            if keyed:
                v = 0 if p[3] < 128 else (v or 0x0021)
            b[i] = v & 255
            b[i + 1] = v >> 8
            i += 2
    return bytes(b)

entries = []
for name in sorted(os.listdir(os.path.join(link, 'plan'))):
    m = re.match(r'^(\d+)(?:_(\d+))?\.webp$', name)
    if not m:
        continue
    room, lv = int(m.group(1)), int(m.group(2)) if m.group(2) else -1
    im = Image.open(os.path.join(link, 'plan', name)).convert('RGBA').resize((256, 256), Image.LANCZOS)
    bg = Image.new('RGBA', im.size, ROOM_BG + (255,))
    bg.alpha_composite(im)
    entries.append(((room << 2) | (lv + 1), 256, 256, rgb565(bg.convert('RGB'))))
for i, k in enumerate('ab'):
    im = Image.open(os.path.join(link, 'world', k + '.png')).convert('RGB').resize((512, 512), Image.LANCZOS)
    entries.append((0x10000 + i, 512, 512, rgb565(im)))
for i, name in enumerate(sorted(os.listdir(os.path.join(link, 'spr')))):
    im = Image.open(os.path.join(link, 'spr', name)).convert('RGBA')
    k = min(1.0, 28 / im.size[0], 36 / im.size[1])
    if k < 1:
        size = (max(1, round(im.size[0] * k)), max(1, round(im.size[1] * k)))
        im = im.resize(size, Image.LANCZOS if name[0] == 'g' else Image.NEAREST)
    entries.append((0x20000 + i, im.size[0], im.size[1], rgb565(im, True)))

entries.sort(key=lambda e: e[0])
off = 8 + 12 * len(entries)
with open(out, 'wb') as f:
    f.write(b'XGPK' + struct.pack('<I', len(entries)))
    for key, w, h, data in entries:
        f.write(struct.pack('<IIHH', key, off, w, h))
        off += len(data)
    for e in entries:
        f.write(e[3])
print('pak: %d pictures, %.1f MB' % (len(entries), off / 1048576))
