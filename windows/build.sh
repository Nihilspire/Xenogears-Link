#!/bin/bash
# Build "Xenogears Link X.X.exe" (portable Windows app) from the Android app's page. Usage: ./build.sh 1.61
# Needs node 18+, npm i (electron-builder, resedit, png-to-ico, @electron/asar), and network to GitHub (Electron + NSIS downloads).
set -e
cd "$(dirname "$0")"
VER="$1"; [ -n "$VER" ] || { echo "usage: $0 <version>"; exit 1; }
# up to four parts (1.99.0.1); electron-builder wants three, so A.B.C.D -> A.B.(C*1000+D): 1.99.0.1 -> 1.99.1, 1.99 -> 1.99.0
IFS=. read -r VA VB VC VD <<< "$VER"; SEMVER="$((10#${VA:-0})).$((10#${VB:-0})).$(( 10#${VC:-0}*1000 + 10#${VD:-0} ))"
EV=33.2.1
rm -rf app/www && cp -r ../app/www app/www && cp ../app/index.html app/www/index.html
if [ "$SHIP" = "1" ]; then rm -rf app/www/plan app/www/maps app/www/bundled.js; fi   # shared builds: maps come from the player's disc (discbuild.js)
sed -i "s/^var VERSION='[^']*';/var VERSION='$VER';/" app/www/index.html
cp icon256.png app/icon.png
sed -i "s/\"version\": \"[^\"]*\"/\"version\": \"$SEMVER\"/" app/package.json
ZIP=cache/electron-v$EV-win32-x64.zip; mkdir -p cache
[ -f "$ZIP" ] || curl -sL -o "$ZIP" https://github.com/electron/electron/releases/download/v$EV/electron-v$EV-win32-x64.zip
rm -rf dist && mkdir -p dist/win-unpacked && (cd dist/win-unpacked && unzip -q ../../$ZIP)
rm -f dist/win-unpacked/resources/default_app.asar
mv dist/win-unpacked/electron.exe "dist/win-unpacked/Xenogears Link.exe"
npx asar pack app dist/win-unpacked/resources/app.asar
node seticon.js "dist/win-unpacked/Xenogears Link.exe" app/icon.png "$VER"
cp app/icon.ico app/icon.ico 2>/dev/null || true
npx electron-builder --win portable --x64 --prepackaged "$PWD/dist/win-unpacked" --projectDir app --config ../builder.json -c.extraMetadata.version="$SEMVER" -c.portable.artifactName="Xenogears Link $VER.exe"
(cd dist && rm -f "Xenogears Link $VER (folder).zip" && mv win-unpacked "Xenogears Link" && zip -qr "Xenogears Link $VER (folder).zip" "Xenogears Link" && mv "Xenogears Link" win-unpacked)
ls -la dist/*.exe dist/*.zip
