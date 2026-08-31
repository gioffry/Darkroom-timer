#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.4.9 - large-format chassis and exposed-sheet register.
# Exact base: v0.4.8 final JOBO/LPL 7451 calibration.

bash combined/build_v048.sh
python3 combined/patch_v049_large_format.py | tee validation-v049-large-format-patch.txt

python3 - <<'PY'
from pathlib import Path
import re

p = Path('combined/src/main/AndroidManifest.xml')
s = p.read_text(encoding='utf-8')
s, n1 = re.subn(r'android:versionCode="[^"]+"', 'android:versionCode="40"', s, count=1)
s, n2 = re.subn(r'android:versionName="[^"]+"', 'android:versionName="0.4.9"', s, count=1)
if n1 != 1 or n2 != 1:
    raise SystemExit('v0.4.9 manifest version update failed')
p.write_text(s, encoding='utf-8')

g = Path('combined/build.gradle')
gs = g.read_text(encoding='utf-8')
gs, n3 = re.subn(r'(?m)^\s*versionCode\s+\d+\s*$', '        versionCode 40', gs, count=1)
gs, n4 = re.subn(r'(?m)^\s*versionName\s+[\'\"][^\'\"]+[\'\"]\s*$', "        versionName '0.4.9'", gs, count=1)
if n3 != 1 or n4 != 1:
    raise SystemExit('v0.4.9 Gradle version update failed')
g.write_text(gs, encoding='utf-8')
PY

rm -f combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.4.9.apk
gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.4.9.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.4.9.apk > certificate-v049.txt
"$AAPT" dump badging Darkroom-v0.4.9.apk > apk-badging-v049.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-v049.txt
grep -Fq "versionCode='40'" apk-badging-v049.txt
grep -Fq "versionName='0.4.9'" apk-badging-v049.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v049.txt
unzip -Z1 Darkroom-v0.4.9.apk > apk-listing-v049.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v049.txt

HOME=combined/src/main/java/it/darkroom/timer/home/HomeActivity.java
LARGE=combined/src/main/java/it/darkroom/timer/largeformat/LargeFormatActivity.java
MANIFEST=combined/src/main/AndroidManifest.xml
MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java
ENL=combined/src/main/java/it/darkroom/timer/EnlargementActivity.java

# New large-format flow.
grep -Fq 'HomeCard largeFormat = new HomeCard("SCATTO GRANDE FORMATO", ICON_CHASSIS, false);' "$HOME"
grep -Fq 'startActivity(new Intent(this, LargeFormatActivity.class))' "$HOME"
grep -Fq 'private static final int ICON_CHASSIS = 6;' "$HOME"
grep -Fq 'Lpl7451Migration.run(this);' "$HOME"
grep -Fq 'private static final String STATUS_EMPTY = "EMPTY";' "$LARGE"
grep -Fq 'private static final String STATUS_UNEXPOSED = "UNEXPOSED";' "$LARGE"
grep -Fq 'private static final String STATUS_EXPOSED = "EXPOSED";' "$LARGE"
grep -Fq 'field("Pellicola"' "$LARGE"
grep -Fq 'field("ISO"' "$LARGE"
grep -Fq 'field("Tempo"' "$LARGE"
grep -Fq 'field("Diaframma"' "$LARGE"
grep -Fq 'field("Zone Ansel Adams' "$LARGE"
grep -Fq 'field("Data e ora scatto"' "$LARGE"
grep -Fq 'chassis_json_v1' "$LARGE"
grep -Fq 'item.clearExposure();' "$LARGE"
grep -Fq 'dd/MM/yyyy HH:mm' "$LARGE"
grep -Fq 'it.darkroom.timer.largeformat.LargeFormatActivity' "$MANIFEST"
if grep -Eq 'Obiettivo|Filtro|Soffietto' "$LARGE"; then
  echo 'Unwanted large-format field survived in v0.4.9' >&2
  exit 1
fi

# Cumulative release invariants.
grep -q 'private static final String APP_VERSION = "0.13.11";' "$MAIN"
grep -Fq 'Math.round(ms / 500.0) * 500' "$ENL"
grep -Fq 'columnCalibration=MEASURED_67_73_6MM' "$ENL"
grep -Fq 'setLogFilter("4x5")' "$MAIN"

python3 - <<'PY' | tee validation-v049-source.txt
from pathlib import Path

root = Path('combined/src/main/java/it/darkroom/timer')
home = (root / 'home/HomeActivity.java').read_text(encoding='utf-8')
large = (root / 'largeformat/LargeFormatActivity.java').read_text(encoding='utf-8')
manifest = Path('combined/src/main/AndroidManifest.xml').read_text(encoding='utf-8')

assert home.count('SCATTO GRANDE FORMATO') == 2
assert home.count('LargeFormatActivity.class') == 1
assert home.count('ICON_CHASSIS') >= 3
assert manifest.count('it.darkroom.timer.largeformat.LargeFormatActivity') == 1

for marker in [
    'STATUS_EMPTY = "EMPTY"',
    'STATUS_UNEXPOSED = "UNEXPOSED"',
    'STATUS_EXPOSED = "EXPOSED"',
    '"Pellicola"', '"ISO"', '"Tempo"', '"Diaframma"',
    '"Zone Ansel Adams', '"Data e ora scatto"',
    'chassis_json_v1', 'SharedPreferences.Editor',
    'item.clearExposure()', 'dd/MM/yyyy HH:mm',
    'PIENO · VERGINE', 'PIENO · ESPOSTO', 'VUOTO'
]:
    assert marker in large, marker
for forbidden in ('Obiettivo', 'Filtro', 'Soffietto'):
    assert forbidden not in large, forbidden

print('release=Darkroom-v0.4.9')
print('versionName=0.4.9')
print('versionCode=40')
print('base_version=0.4.8')
print('feature=LARGE_FORMAT_CHASSIS_REGISTER')
print('states=EMPTY,UNEXPOSED,EXPOSED')
print('exposed_fields=FILM,ISO,SHUTTER,APERTURE,ZONES,SHOT_DATETIME')
print('persistence=SHARED_PREFERENCES_JSON')
print('exposure_data_cleared_when_not_exposed=PASS')
print('objective_filter_bellows_fields=ABSENT')
print('lpl_migration_preserved=PASS')
print('sonoff_final_step_seconds=0.5')
PY

python3 - <<'PY'
from pathlib import Path
parts = [
    Path('validation-v048.txt'),
    Path('validation-v049-large-format-patch.txt'),
    Path('validation-v049-source.txt'),
]
Path('validation-v049.txt').write_text(
    ''.join(p.read_text(encoding='utf-8') for p in parts),
    encoding='utf-8',
)
PY
sha256sum Darkroom-v0.4.9.apk | tee Darkroom-v0.4.9.sha256
