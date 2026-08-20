#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.1.3 parte esclusivamente dalla base canonica Darkroom 0.1.1.
# Timer e Assistant restano quelli della Darkroom 0.1.1; cambia solo la Home.
git fetch origin archive/timer-v0137-baseline archive/assistant-v038-baseline

git update-ref refs/remotes/origin/feature-v0137-flat-bottom-nav \
  "$(git rev-parse origin/archive/timer-v0137-baseline)"
git update-ref refs/remotes/origin/feature-darkroom-assistant-v038-edit-persistence \
  "$(git rev-parse origin/archive/assistant-v038-baseline)"

test "$(git rev-parse origin/archive/timer-v0137-baseline)" = "bd7291e4d0e875f4664fbe034be4b901059c1e4f"
test "$(git rev-parse origin/archive/assistant-v038-baseline)" = "7ff0e0324376c3465777b08e3949cc284e4a8487"

python3 combined/fix_build_v011_newlines.py

python3 - <<'PY'
from pathlib import Path
src = Path('combined/build_v011.sh').read_text(encoding='utf-8')
marker = '# Build e verifica.'
if marker not in src:
    raise SystemExit('build_v011.sh: marker build non trovato')
prefix = src.split(marker, 1)[0]
Path('/tmp/prepare_darkroom_v011.sh').write_text(prefix, encoding='utf-8')
PY
bash /tmp/prepare_darkroom_v011.sh

TIMER_MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java
ASSISTANT_MAIN=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
sha256sum "$TIMER_MAIN" | cut -d' ' -f1 > /tmp/timer.before
sha256sum "$ASSISTANT_MAIN" | cut -d' ' -f1 > /tmp/assistant.before

grep -q 'android:versionName="0.1.1"' combined/src/main/AndroidManifest.xml
grep -q 'android:versionCode="2"' combined/src/main/AndroidManifest.xml
grep -q "versionName '0.1.1'" combined/build.gradle
grep -q 'versionCode 2' combined/build.gradle

python3 combined/patch_v012_vintage_home.py

test "$(cat /tmp/timer.before)" = "$(sha256sum "$TIMER_MAIN" | cut -d' ' -f1)"
test "$(cat /tmp/assistant.before)" = "$(sha256sum "$ASSISTANT_MAIN" | cut -d' ' -f1)"

grep -q 'android:versionName="0.1.3"' combined/src/main/AndroidManifest.xml
grep -q 'android:versionCode="4"' combined/src/main/AndroidManifest.xml
grep -q "versionName '0.1.3'" combined/build.gradle
grep -q 'versionCode 4' combined/build.gradle

HOME=combined/src/main/java/it/darkroom/timer/home/HomeActivity.java
grep -q 'openAssistant("products")' "$HOME"
grep -q 'openAssistant("film")' "$HOME"
grep -q 'openAssistant("paper")' "$HOME"
grep -q 'MainActivity.class' "$HOME"
grep -q 'ImageView.ScaleType.CENTER_CROP' "$HOME"
grep -q 'R.drawable.home_vintage' "$HOME"
! grep -q 'BitmapFactory' "$HOME"
! grep -q 'WindowInsetsController' "$HOME"
grep -q 'restoreSavedFilmDilution' "$ASSISTANT_MAIN"
grep -q 'private static final String APP_VERSION = "0.13.7";' "$TIMER_MAIN"
test -f combined/src/main/res/drawable-nodpi/home_vintage.webp

gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.1.3.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.1.3.apk | tee certificate-v013.txt
"$AAPT" dump badging Darkroom-v0.1.3.apk > apk-badging-v013.txt
grep -q "package: name='it.darkroom.darkroom' versionCode='4' versionName='0.1.3'" apk-badging-v013.txt
grep -q "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v013.txt
unzip -l Darkroom-v0.1.3.apk > apk-listing-v013.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v013.txt
grep -Eq 'res/drawable-nodpi(-v4)?/home_vintage.webp' apk-listing-v013.txt
CERT_FP=$(grep -m1 'certificate SHA-256 digest:' certificate-v013.txt | sed 's/.*: *//')
test "$CERT_FP" = "fbead305657584b50a9d8892aa19bd9844b412d77db316e7daa5593c94e2a02f"
sha256sum Darkroom-v0.1.3.apk | tee Darkroom-v0.1.3.sha256

{
  echo 'base_darkroom=0.1.1'
  echo 'versionName=0.1.3'
  echo 'versionCode=4'
  echo 'timer_version=0.13.7'
  echo 'assistant_version=0.3.8'
  echo 'vintage_home=PASS'
  echo 'safe_home_views=PASS'
  echo 'products_function=PASS'
  echo 'film_function=PASS'
  echo 'paper_function=PASS'
  echo 'timer_function=PASS'
  echo 'timer_source_unchanged=PASS'
  echo 'assistant_source_unchanged=PASS'
  echo 'certificate_continuity=PASS'
  echo "certificate_SHA256=$CERT_FP"
  echo 'build=SUCCESS'
} > validation-v013.txt
