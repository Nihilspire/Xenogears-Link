"""Pack app/ into an unsigned APK: python tools/build.py out_unsigned.apk
Then: zipalign -f 4 out_unsigned.apk out_aligned.apk ; apksigner sign --ks <your.jks> --out out.apk out_aligned.apk
resources.arsc must stay uncompressed (Android 11+ requirement); images are stored as-is."""
import os, sys, zipfile
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'app')
out = sys.argv[1] if len(sys.argv) > 1 else 'xenogears-link_unsigned.apk'
with zipfile.ZipFile(out, 'w') as z:
    for d, _, files in os.walk(root):
        for f in sorted(files):
            p = os.path.join(d, f); name = os.path.relpath(p, root).replace(os.sep, '/')
            raw = name == 'resources.arsc' or f.lower().endswith(('.png', '.webp', '.jpg'))
            z.write(p, name, compress_type=zipfile.ZIP_STORED if raw else zipfile.ZIP_DEFLATED)
print('wrote', out)
