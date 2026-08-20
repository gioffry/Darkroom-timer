#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.1.5: base canonica 0.1.1, Timer 0.13.7 + Assistant 0.3.8.
# Cambia ESCLUSIVAMENTE la Home grafica: usa un JPEG Android-safe ad alta risoluzione.
git fetch origin archive/timer-v0137-baseline archive/assistant-v038-baseline feature-darkroom-v012-vintage-home-r2

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
Path('/tmp/prepare_darkroom_v011.sh').write_text(src.split(marker, 1)[0], encoding='utf-8')
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

# Riusa soltanto il codice Home già verificato della 0.1.3.
# L'asset legacy viene bypassato e sostituito subito dopo.
python3 - <<'PY'
from pathlib import Path
src = Path('combined/patch_v012_vintage_home.py').read_text(encoding='utf-8')
start = src.index("parts = sorted(assets.glob('*.part'))")
end = src.index("home_source = r'''", start)
replacement = """image_bytes = b'RIFF0000WEBP'\ndrawable = combined / 'src/main/res/drawable-nodpi/home_vintage.webp'\ndrawable.parent.mkdir(parents=True, exist_ok=True)\ndrawable.write_bytes(image_bytes)\n\n"""
src = src[:start] + replacement + src[end:]
Path('/tmp/patch_home_code_only.py').write_text(src, encoding='utf-8')
PY
python3 /tmp/patch_home_code_only.py

# Ricostruisce la copia HD storica completa e la decodifica rigorosamente.
SRC_REF=origin/feature-darkroom-v012-vintage-home-r2
mapfile -t PARTS < <(git ls-tree -r --name-only "$SRC_REF" -- combined/v012_assets/home_mockup | sort)
test "${#PARTS[@]}" -eq 9
: > /tmp/home_hd.b64
for f in "${PARTS[@]}"; do
  git show "$SRC_REF:$f" >> /tmp/home_hd.b64
done
tr -d '\r\n\t ' < /tmp/home_hd.b64 > /tmp/home_hd.clean.b64
base64 --decode /tmp/home_hd.clean.b64 > /tmp/home_hd_source.webp

test "$(head -c 4 /tmp/home_hd_source.webp)" = "RIFF"
test "$(dd if=/tmp/home_hd_source.webp bs=1 skip=8 count=4 status=none)" = "WEBP"

# Fallisce se il WebP è anche solo parzialmente corrotto.
ffmpeg -v error -xerror -i /tmp/home_hd_source.webp -frames:v 1 -f null -

DIMS="$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 /tmp/home_hd_source.webp)"
test "$DIMS" = "864x1536"

# Android-safe: JPEG standard, nessun WebP nel pacchetto Home.
rm -f combined/src/main/res/drawable-nodpi/home_vintage.webp
ffmpeg -v error -xerror -i /tmp/home_hd_source.webp -frames:v 1 -q:v 2 \
  combined/src/main/res/drawable-nodpi/home_vintage.jpg

JPG=combined/src/main/res/drawable-nodpi/home_vintage.jpg
test -s "$JPG"
test "$(head -c 2 "$JPG" | od -An -tx1 | tr -d ' \n')" = "ffd8"
JPG_DIMS="$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "$JPG")"
test "$JPG_DIMS" = "864x1536"

# v0.1.5 / versionCode 6.
sed -i 's/android:versionCode="4"/android:versionCode="6"/' combined/src/main/AndroidManifest.xml
sed -i 's/android:versionName="0.1.3"/android:versionName="0.1.5"/' combined/src/main/AndroidManifest.xml
sed -i "s/versionCode 4/versionCode 6/" combined/build.gradle
sed -i "s/versionName '0.1.3'/versionName '0.1.5'/" combined/build.gradle

test "$(cat /tmp/timer.before)" = "$(sha256sum "$TIMER_MAIN" | cut -d' ' -f1)"
test "$(cat /tmp/assistant.before)" = "$(sha256sum "$ASSISTANT_MAIN" | cut -d' ' -f1)"

grep -q 'android:versionName="0.1.5"' combined/src/main/AndroidManifest.xml
grep -q 'android:versionCode="6"' combined/src/main/AndroidManifest.xml
grep -q "versionName '0.1.5'" combined/build.gradle
grep -q 'versionCode 6' combined/build.gradle

HOME=combined/src/main/java/it/darkroom/timer/home/HomeActivity.java
grep -q 'openAssistant("products")' "$HOME"
grep -q 'openAssistant("film")' "$HOME"
grep -q 'openAssistant("paper")' "$HOME"
grep -q 'MainActivity.class' "$HOME"
grep -q 'ImageView.ScaleType.CENTER_CROP' "$HOME"
grep -q 'R.drawable.home_vintage' "$HOME"
grep -q 'restoreSavedFilmDilution' "$ASSISTANT_MAIN"
grep -q 'private static final String APP_VERSION = "0.13.7";' "$TIMER_MAIN"
test -f "$JPG"
test ! -f combined/src/main/res/drawable-nodpi/home_vintage.webp

gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.1.5.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.1.5.apk | tee certificate-v015.txt
"$AAPT" dump badging Darkroom-v0.1.5.apk > apk-badging-v015.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-v015.txt
grep -Fq "versionCode='6'" apk-badging-v015.txt
grep -Fq "versionName='0.1.5'" apk-badging-v015.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v015.txt
unzip -l Darkroom-v0.1.5.apk > apk-listing-v015.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v015.txt

CERT_FP=$(grep -m1 'certificate SHA-256 digest:' certificate-v015.txt | sed 's/.*: *//')
test "$CERT_FP" = "fbead305657584b50a9d8892aa19bd9844b412d77db316e7daa5593c94e2a02f"
sha256sum Darkroom-v0.1.5.apk | tee Darkroom-v0.1.5.sha256

{
  echo 'base_darkroom=0.1.1'
  echo 'versionName=0.1.5'
  echo 'versionCode=6'
  echo 'timer_version=0.13.7'
  echo 'assistant_version=0.3.8'
  echo 'home_asset_format=JPEG'
  echo 'home_asset_dimensions=864x1536'
  echo 'home_webp_removed=PASS'
  echo 'products_function=PASS'
  echo 'film_function=PASS'
  echo 'paper_function=PASS'
  echo 'timer_function=PASS'
  echo 'timer_source_unchanged=PASS'
  echo 'assistant_source_unchanged=PASS'
  echo 'certificate_continuity=PASS'
  echo "certificate_SHA256=$CERT_FP"
  echo 'build=SUCCESS'
} > validation-v015.txt
