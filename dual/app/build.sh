#!/bin/bash
# Builds "Xenogears Dual <version>.apk": javac -> dx -> aapt -> zipalign -> apksigner. No Gradle.
set -e
cd "$(dirname "$0")"
VER=$(grep -o 'versionName="[^"]*"' AndroidManifest.xml | cut -d'"' -f2)
AJAR=/usr/lib/android-sdk/platforms/android-23/android.jar
JDK=/usr/lib/jvm/java-17-openjdk-amd64/bin
rm -rf gen obj dex unsigned.apk aligned.apk
mkdir -p gen obj dex
aapt package -f -m -J gen -M AndroidManifest.xml -S res -I $AJAR
$JDK/javac --release 8 -nowarn -Xlint:-options -encoding UTF-8 -d obj -classpath $AJAR -sourcepath src:gen $(find src gen -name '*.java')
dalvik-exchange --dex --min-sdk-version=23 --output=dex/classes.dex obj
aapt package -f -M AndroidManifest.xml -S res -A assets -I $AJAR -F unsigned.apk
cp dex/classes.dex .
aapt add unsigned.apk classes.dex > /dev/null
rm classes.dex
( cd out && for f in lib/arm64-v8a/*.so; do aapt add -0 so ../unsigned.apk "$f" > /dev/null; done )
zipalign -f -p 4 unsigned.apk aligned.apk
: "${XG_DUAL_KS_PASS:?Set XG_DUAL_KS_PASS to your signing key password}"
mkdir -p signing
if [ ! -f signing/xenogears.jks ]; then
  keytool -genkeypair -keystore signing/xenogears.jks -alias xenogears -keyalg RSA -keysize 2048 -validity 10000 \
    -storepass "$XG_DUAL_KS_PASS" -keypass "$XG_DUAL_KS_PASS" -dname "CN=Xenogears, O=Jack" > /dev/null 2>&1
fi
apksigner sign --ks signing/xenogears.jks --ks-pass env:XG_DUAL_KS_PASS --key-pass env:XG_DUAL_KS_PASS --ks-key-alias xenogears \
  --out "Xenogears Dual $VER.apk" aligned.apk
rm -f unsigned.apk aligned.apk
apksigner verify "Xenogears Dual $VER.apk" && echo "Built Xenogears Dual $VER.apk"
