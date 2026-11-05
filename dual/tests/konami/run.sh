#!/bin/bash
# compiles app/.../Konami.java with this test against android.jar (only its key constants, which javac inlines) and runs it
ROOT="$(cd "$(dirname "$(readlink -f "$0")")/../.." && pwd)"
O=$(mktemp -d)
/usr/lib/jvm/java-17-openjdk-amd64/bin/javac --release 8 -nowarn -Xlint:-options -d $O -classpath /usr/lib/android-sdk/platforms/android-23/android.jar \
  "$ROOT/app/src/com/jack/xenogears/Konami.java" "$ROOT/tests/konami/KonamiTest.java" && java -cp $O com.jack.xenogears.KonamiTest
r=$?; rm -rf $O; exit $r
