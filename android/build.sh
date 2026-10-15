#!/bin/bash
# Build and sign "Xenogears Link X.X.apk" without Gradle.
# Usage: ./build.sh 1.99.0.1    (version name, up to four parts; version code below)
# Needs: aapt, zipalign, apksigner, javac, dalvik-exchange, android-23 platform jar; src/, res/, AndroidManifest.xml and keystore.jks beside this script;
#        the app's web files in ../app/www (index.html is copied in from ../app/index.html first).
set -e
cd "$(dirname "$0")"
unset JAVA_TOOL_OPTIONS
VER="$1"; [ -n "$VER" ] || { echo "usage: $0 <version, e.g. 1.23>"; exit 1; }
# versions are 1.99, then 1.99.0.1, 1.99.0.2 ... until 2.0 (Jack, 15 Oct 2026). Version code = A*1000000 + B*10000 + C*100 + D, so every
# build is higher than the last (1.99 -> 1990000, 1.99.0.1 -> 1990001, 2.0 -> 2000000; builds up to 1.99 used 10 + B).
IFS=. read -r VA VB VC VD <<< "$VER"; CODE=$(( 10#${VA:-0}*1000000 + 10#${VB:-0}*10000 + 10#${VC:-0}*100 + 10#${VD:-0} ))
OUT="Xenogears Link $VER.apk"
sed -i "s/var VERSION='[^']*'/var VERSION='$VER'/" ../app/index.html   # the start screen shows the version
cp ../app/index.html ../app/www/index.html
rm -rf assets/www && cp -r ../app/www assets/www
# The room maps and pictures come from the player's own disc (discbuild.js). Test builds still carry a built set (plan/, maps/,
# bundled.js); SHIP=1 ./build.sh X.X leaves them out for a build to share.
if [ "$SHIP" = "1" ]; then rm -rf assets/www/plan assets/www/maps assets/www/bundled.js; fi
# Java (MainActivity: WebView, RetroArch link, disc reading and the built-files folder; Link: the UDP reads)
rm -rf obj && mkdir obj
javac -nowarn -source 8 -target 8 -bootclasspath /usr/lib/android-sdk/platforms/android-23/android.jar -d obj src/com/dualscreen/xenogears/*.java 2>&1 | grep -v "warning\|Picked up\|^Note" || true
dalvik-exchange --dex --output=classes.dex obj && rm -rf obj
sed -i "s/versionCode=\"[0-9]*\"/versionCode=\"$CODE\"/; s/versionName=\"[^\"]*\"/versionName=\"$VER\"/" AndroidManifest.xml
# -0 webp: the room pictures are already compressed
aapt package -f -0 webp -M AndroidManifest.xml -S res -A assets -I /usr/lib/android-sdk/platforms/android-23/android.jar -F unsigned.apk
aapt add unsigned.apk classes.dex >/dev/null
zipalign -f 4 unsigned.apk aligned.apk
apksigner sign --ks keystore.jks --ks-pass env:XG_KS_PASS --key-pass env:XG_KS_PASS --out "$OUT" aligned.apk
rm -f unsigned.apk aligned.apk "$OUT.idsig"
apksigner verify "$OUT"
aapt dump badging "$OUT" | grep -E "^package|application-label:"
ls -la "$OUT"
