"""Fixes the right-stick camera bug (lw -> lhu on the 16-bit camera mode at 0x800AF934) in Jack's analog controls
outside the app: the RetroArch .cht and the two Disc 1 xdelta patches (see docs/NOTES-analog-and-memcard.md).

  python3 fix_analog_camera.py DISC1.chd RETROARCH_DIR OUT_DIR

RETROARCH_DIR holds "Xenogears (USA) - Analog Controls.cht" and the two "... Analog Controls*.xdelta". Writes fixed
copies (same names) to OUT_DIR, plus SHA1SUMS. The xdeltas are fixed by applying each one to the retail .bin, changing
the one instruction word in place (the disc patch's program is a different build, so the word is found by its bytes
inside the sectors the patch changed), recomputing that sector's EDC/ECC, and encoding a new xdelta against the retail
.bin. The EDC/ECC code is checked first by regenerating sectors that are already valid."""
import sys, os, hashlib, subprocess, tempfile, struct, re, shutil

RETAIL_SHA1 = '12db8ccb93516c391630f046a143762337cc21f4'
SECTOR = 2352
def is_bad(w):  # lw rt,-0x6cc(rs): the camera mode read as a word (the .cht build uses t5/t2, the disc-patch build t4/v1)
    return (w >> 26) == 0x23 and (w & 0xFFFF) == 0xF934
def to_lhu(w): return (w & 0x03FFFFFF) | (0x25 << 26)

# ---- CD-ROM EDC/ECC (ECMA-130), Mode 2 Form 1 ----
EDC = []
for i in range(256):
    e = i
    for _ in range(8): e = (e >> 1) ^ (0xD8018001 if e & 1 else 0)
    EDC.append(e)
F = [((i << 1) ^ (0x11D if i & 0x80 else 0)) & 0xFF for i in range(256)]
B = [0] * 256
for i in range(256): B[i ^ F[i]] = i
def edc(data):
    e = 0
    for x in data: e = (e >> 8) ^ EDC[(e ^ x) & 0xFF]
    return e
def ecc_block(s, major_count, minor_count, major_mult, minor_inc, dest):
    size = major_count * minor_count
    for major in range(major_count):
        index = (major >> 1) * major_mult + (major & 1)
        a = b = 0
        for _ in range(minor_count):
            t = s[0xC + index]
            index += minor_inc
            if index >= size: index -= size
            a ^= t; b ^= t; a = F[a]
        a = B[F[a] ^ b]
        s[dest + major] = a; s[dest + major + major_count] = a ^ b
def fix_sector(sec):
    """recomputes EDC and ECC of a Mode 2 Form 1 sector in place"""
    s = bytearray(sec)
    struct.pack_into('<I', s, 0x818, edc(s[0x10:0x818]))
    hdr = bytes(s[0xC:0x10]); s[0xC:0x10] = b'\0\0\0\0'          # Mode 2: the header counts as zero for ECC
    ecc_block(s, 86, 24, 2, 86, 0x81C)
    ecc_block(s, 52, 43, 86, 88, 0x8C8)
    s[0xC:0x10] = hdr
    return bytes(s)

def sha1(p):
    h = hashlib.sha1()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''): h.update(c)
    return h.hexdigest()
def run(*a): subprocess.run(a, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def fix_cht(src, dst):
    t = open(src, encoding='utf-8').read()
    n = len(re.findall(r'8001785E 8D4D', t))
    open(dst, 'w', encoding='utf-8', newline='').write(t.replace('8001785E 8D4D', '8001785E 954D'))
    return n

def main(chd, rdir, out):
    os.makedirs(out, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix='xgfix', dir=os.environ.get('TMPDIR', '/tmp'))
    retail = os.path.join(tmp, 'retail.bin')
    run('chdman', 'extractcd', '-i', chd, '-o', os.path.join(tmp, 'retail.cue'), '-ob', retail)
    assert sha1(retail) == RETAIL_SHA1, 'Disc 1 .bin from the CHD is not the retail image'
    sums = []
    cht = 'Xenogears (USA) - Analog Controls.cht'
    n = fix_cht(os.path.join(rdir, cht), os.path.join(out, cht))
    print('%s: %d code line fixed' % (cht, n)); assert n == 1
    sums.append((sha1(os.path.join(out, cht)), cht))
    for name in sorted(f for f in os.listdir(rdir) if f.endswith('.xdelta')):
        patched = os.path.join(tmp, 'patched.bin')
        run('xdelta3', '-d', '-f', '-s', retail, os.path.join(rdir, name), patched)
        with open(retail, 'rb') as f: a = f.read()
        with open(patched, 'rb') as f: b = bytearray(f.read())
        changed = [i for i in range(len(a) // SECTOR) if a[i*SECTOR:(i+1)*SECTOR] != b[i*SECTOR:(i+1)*SECTOR]]
        # the EDC/ECC code must reproduce every changed sector exactly as the original build wrote it
        for i in changed:
            sec = bytes(b[i*SECTOR:(i+1)*SECTOR]); assert fix_sector(sec) == sec, 'EDC/ECC check failed on sector %d' % i
        hits = [(i, o) for i in changed for o in range(0x18, 0x818, 4) if is_bad(struct.unpack_from('<I', b, i*SECTOR+o)[0])]
        print('%s: patch changes sectors %s; buggy lw at %s' % (name, changed,
              ['sector %d +0x%x: %08x' % (i, o - 0x18, struct.unpack_from('<I', b, i*SECTOR+o)[0]) for i, o in hits]))
        assert len(hits) == 1, 'expected exactly one camera-mode lw'
        i, off = hits[0]
        struct.pack_into('<I', b, i*SECTOR+off, to_lhu(struct.unpack_from('<I', b, i*SECTOR+off)[0]))
        b[i*SECTOR:(i+1)*SECTOR] = fix_sector(bytes(b[i*SECTOR:(i+1)*SECTOR]))
        fixed = os.path.join(tmp, 'fixed.bin')
        with open(fixed, 'wb') as f: f.write(b)
        dst = os.path.join(out, name)
        run('xdelta3', '-e', '-9', '-f', '-S', 'djw', '-s', retail, fixed, dst)
        check = os.path.join(tmp, 'check.bin')
        run('xdelta3', '-d', '-f', '-s', retail, dst, check)
        assert sha1(check) == sha1(fixed), 'new xdelta does not reproduce the fixed image'
        print('  fixed image SHA-1 %s, CRC32 %08X, new patch %d bytes' % (sha1(fixed), __import__('zlib').crc32(b) & 0xFFFFFFFF, os.path.getsize(dst)))
        sums.append((sha1(dst), name)); sums.append((sha1(fixed), name.replace('.xdelta', '') + ' -> patched .bin'))
        for p in (patched, fixed, check): os.remove(p)
    with open(os.path.join(out, 'SHA1SUMS'), 'w') as f:
        for h, n in sums: f.write('%s  %s\n' % (h, n))
    shutil.rmtree(tmp)

if __name__ == '__main__':
    try: main(*sys.argv[1:4])
    finally:
        for d in os.listdir(os.environ.get('TMPDIR', '/tmp')):
            if d.startswith('xgfix') and d != os.path.basename(sys.argv[3].rstrip('/')):
                shutil.rmtree(os.path.join(os.environ.get('TMPDIR', '/tmp'), d), ignore_errors=True)
