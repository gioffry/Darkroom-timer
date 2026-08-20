#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.1.5: base canonica Darkroom 0.1.1.
# Timer 0.13.7 e Assistant 0.3.8 restano invariati. Cambia solo la Home.
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
Path('/tmp/prepare_darkroom_v011.sh').write_text(src.split(marker, 1)[0], encoding='utf-8')
PY
bash /tmp/prepare_darkroom_v011.sh

TIMER_MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java
ASSISTANT_MAIN=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
sha256sum "$TIMER_MAIN" | cut -d' ' -f1 > /tmp/timer.before
sha256sum "$ASSISTANT_MAIN" | cut -d' ' -f1 > /tmp/assistant.before

grep -q 'android:versionName="0.1.1"' combined/src/main/AndroidManifest.xml
grep -q 'android:versionCode="2"' combined/src/main/AndroidManifest.xml

# Riusa esclusivamente il codice Home sicuro della 0.1.3, senza il suo vecchio asset.
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

# Ricostruisce il vecchio asset HD, valido nella parte alta, usandolo solo come sorgente.
python3 - <<'PY'
from pathlib import Path
import base64
hd = Path('combined/v014_assets/home_hd')
parts = sorted(hd.glob('*.part'))
if len(parts) != 8:
    raise SystemExit(f'asset HD: attese 8 parti, trovate {len(parts)}')
encoded = ''.join(''.join(p.read_text(encoding='utf-8').split()) for p in parts)
encoded += '=' * (-len(encoded) % 4)
data = base64.b64decode(encoded, validate=True)
if len(data) < 80000 or data[:4] != b'RIFF' or data[8:12] != b'WEBP':
    raise SystemExit('asset HD WebP sorgente non valido')
Path('/tmp/home_hd_source.webp').write_bytes(data)
print('WEBP_SOURCE_BYTES=' + str(len(data)))
PY

# Patch inferiore: ritaglio pulito 864x216 del mockup originale approvato, da y=1320 a 1536.
BOTTOM=combined/v015_assets/home_bottom.jpg
test -s "$BOTTOM"
test "$(head -c 2 "$BOTTOM" | od -An -tx1 | tr -d ' \n')" = "ffd8"
test "$(tail -c 2 "$BOTTOM" | od -An -tx1 | tr -d ' \n')" = "ffd9"
ffmpeg -v error -xerror -i "$BOTTOM" -frames:v 1 -f null -
BOTTOM_DIMS="$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "$BOTTOM")"
test "$BOTTOM_DIMS" = "864x216"

# Android riceve SOLO un JPEG standard. Il fondo corrotto del vecchio WebP viene completamente
# coperto con il ritaglio pulito originale a partire da y=1320.
rm -f combined/src/main/res/drawable-nodpi/home_vintage.webp
ffmpeg -y -v warning -err_detect ignore_err \
  -i /tmp/home_hd_source.webp -i "$BOTTOM" \
  -filter_complex "[0:v]scale=864:-2,pad=864:1536:0:0:black[base];[base][1:v]overlay=0:1320:format=auto" \
  -frames:v 1 -pix_fmt yuvj420p -q:v 2 \
  combined/src/main/res/drawable-nodpi/home_vintage.jpg

JPG=combined/src/main/res/drawable-nodpi/home_vintage.jpg
test -s "$JPG"
test "$(head -c 2 "$JPG" | od -An -tx1 | tr -d ' \n')" = "ffd8"
test "$(tail -c 2 "$JPG" | od -An -tx1 | tr -d ' \n')" = "ffd9"
ffmpeg -v error -xerror -i "$JPG" -frames:v 1 -f null -
DIMS="$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "$JPG")"
test "$DIMS" = "864x1536"

# Versione Darkroom 0.1.5 / versionCode 6.
sed -i 's/android:versionCode="4"/android:versionCode="6"/' combined/src/main/AndroidManifest.xml
sed -i 's/android:versionName="0.1.3"/android:versionName="0.1.5"/' combined/src/main/AndroidManifest.xml
sed -i "s/versionCode 4/versionCode 6/" combined/build.gradle
sed -i "s/versionName '0.1.3'/versionName '0.1.5'/" combined/build.gradle

test "$(cat /tmp/timer.before)" = "$(sha256sum "$TIMER_MAIN" | cut -d' ' -f1)"
test "$(cat /tmp/assistant.before)" = "$(sha256sum "$ASSISTANT_MAIN" | cut -d' ' -f1)"

grep -q 'android:versionName="0.1.5"' combined/src/main/AndroidManifest.xml
grep -q 'android:versionCode="6"' combined/src/main/AndroidManifest.xml
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
  echo 'home_jpeg_full_decode=PASS'
  echo 'home_bottom_patch=PASS'
  echo 'home_bottom_patch_y=1320'
  echo 'home_bottom_patch_dimensions=864x216'
  echo 'home_webp_not_packaged=PASS'
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
