#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.5.0 - corrected large-format A/B chassis workflow.
# Exact base: v0.4.9 large-format register.

bash combined/build_v049.sh

# Correct two source-guard literals in the patch file before execution.
python3 - <<'PY'
from pathlib import Path
p = Path('combined/patch_v050_large_format_sides.py')
s = p.read_text(encoding='utf-8')
s = s.replace("'chassisItem.number + \"A\"'", "'sideRow(item, item.a, \"A\")'")
s = s.replace("'chassisItem.number + \"B\"'", "'sideRow(item, item.b, \"B\")'")
p.write_text(s, encoding='utf-8')
PY
python3 combined/patch_v050_large_format_sides.py | tee validation-v050-large-format-patch.txt

python3 - <<'PY'
from pathlib import Path
import re

p = Path('combined/src/main/AndroidManifest.xml')
s = p.read_text(encoding='utf-8')
s, n1 = re.subn(r'android:versionCode="[^"]+"', 'android:versionCode="41"', s, count=1)
s, n2 = re.subn(r'android:versionName="[^"]+"', 'android:versionName="0.5.0"', s, count=1)
if n1 != 1 or n2 != 1:
    raise SystemExit('v0.5.0 manifest version update failed')
p.write_text(s, encoding='utf-8')

g = Path('combined/build.gradle')
gs = g.read_text(encoding='utf-8')
gs, n3 = re.subn(r'(?m)^\s*versionCode\s+\d+\s*$', '        versionCode 41', gs, count=1)
gs, n4 = re.subn(r'(?m)^\s*versionName\s+[\'\"][^\'\"]+[\'\"]\s*$', "        versionName '0.5.0'", gs, count=1)
if n3 != 1 or n4 != 1:
    raise SystemExit('v0.5.0 Gradle version update failed')
g.write_text(gs, encoding='utf-8')
PY

rm -f combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.5.0.apk
gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.5.0.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.5.0.apk > certificate-v050.txt
"$AAPT" dump badging Darkroom-v0.5.0.apk > apk-badging-v050.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-v050.txt
grep -Fq "versionCode='41'" apk-badging-v050.txt
grep -Fq "versionName='0.5.0'" apk-badging-v050.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v050.txt
unzip -Z1 Darkroom-v0.5.0.apk > apk-listing-v050.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v050.txt

HOME=combined/src/main/java/it/darkroom/timer/home/HomeActivity.java
LARGE=combined/src/main/java/it/darkroom/timer/largeformat/LargeFormatActivity.java
MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java
ENL=combined/src/main/java/it/darkroom/timer/EnlargementActivity.java

# Corrected Home label.
grep -Fq 'new HomeCard("GRANDE FORMATO", ICON_CHASSIS, false)' "$HOME"
if grep -Fq 'SCATTO GRANDE FORMATO' "$HOME"; then
  echo 'Old long Home label survived in v0.5.0' >&2
  exit 1
fi

# A/B model, Fomapan/ISO and vintage states.
grep -Fq 'final Side a = new Side();' "$LARGE"
grep -Fq 'final Side b = new Side();' "$LARGE"
grep -Fq 'sideRow(item, item.a, "A")' "$LARGE"
grep -Fq 'sideRow(item, item.b, "B")' "$LARGE"
grep -Fq 'private static final String FILM_BRAND = "FOMAPAN";' "$LARGE"
grep -Fq 'private static final int[] ISO_VALUES = {100, 200, 400};' "$LARGE"
grep -Fq 'EMPTY_COLOR = Color.rgb(108, 105, 98)' "$LARGE"
grep -Fq 'VIRGIN_COLOR = Color.rgb(109, 124, 94)' "$LARGE"
grep -Fq 'EXPOSED_COLOR = Color.rgb(151, 103, 66)' "$LARGE"
grep -Fq 'loadedFields.setVisibility(STATUS_EMPTY.equals(selectedStatus[0]) ? View.GONE : View.VISIBLE);' "$LARGE"
grep -Fq 'exposureFields.setVisibility(STATUS_EXPOSED.equals(selectedStatus[0]) ? View.VISIBLE : View.GONE);' "$LARGE"
grep -Fq 'side.iso = selectedIso[0];' "$LARGE"

# Native zone selection and automatic gap.
grep -Fq 'sectionTitle("ZONE ANSEL ADAMS")' "$LARGE"
grep -Fq 'label("OMBRA"' "$LARGE"
grep -Fq 'label("LUCE"' "$LARGE"
grep -Fq 'Math.abs(selectedHighlight[0] - selectedShadow[0])' "$LARGE"
grep -Fq 'gap.setText("SCARTO: " + delta + " EV")' "$LARGE"
grep -Fq 'o.put("zoneGapEv", zoneGap(side));' "$LARGE"
if grep -Fq 'Zone Ansel Adams · es.' "$LARGE"; then
  echo 'Old textual Ansel Adams field survived in v0.5.0' >&2
  exit 1
fi

# ADESSO layout fix and v0.4.9 data migration.
grep -Fq 'View dateSpacer = new View(this);' "$LARGE"
grep -Fq 'exposureFields.addView(dateSpacer, lp(-1, dp(15)));' "$LARGE"
grep -Fq 'KEY_DATA_V1 = "chassis_json_v1"' "$LARGE"
grep -Fq 'KEY_DATA_V2 = "chassis_json_v2"' "$LARGE"
grep -Fq 'old chassis data becomes side A' "$LARGE"

# Unwanted fields remain absent.
if grep -Eq 'Obiettivo|Filtro|Soffietto|field\("Pellicola"' "$LARGE"; then
  echo 'Unwanted large-format field survived in v0.5.0' >&2
  exit 1
fi

# Cumulative release invariants.
grep -q 'private static final String APP_VERSION = "0.13.11";' "$MAIN"
grep -Fq 'Math.round(ms / 500.0) * 500' "$ENL"
grep -Fq 'columnCalibration=MEASURED_67_73_6MM' "$ENL"
grep -Fq 'setLogFilter("4x5")' "$MAIN"

python3 - <<'PY' | tee validation-v050-source.txt
from pathlib import Path

root = Path('combined/src/main/java/it/darkroom/timer')
home = (root / 'home/HomeActivity.java').read_text(encoding='utf-8')
large = (root / 'largeformat/LargeFormatActivity.java').read_text(encoding='utf-8')

assert 'GRANDE FORMATO' in home
assert 'SCATTO GRANDE FORMATO' not in home
assert 'final Side a = new Side();' in large
assert 'final Side b = new Side();' in large
assert 'FOMAPAN' in large
assert 'ISO_VALUES = {100, 200, 400}' in large
assert 'Color.rgb(108, 105, 98)' in large
assert 'Color.rgb(109, 124, 94)' in large
assert 'Color.rgb(151, 103, 66)' in large
assert 'Math.abs(selectedHighlight[0] - selectedShadow[0])' in large
assert 'SCARTO: ' in large
assert 'zoneGapEv' in large
assert 'View dateSpacer = new View(this);' in large
assert 'chassis_json_v2' in large and 'chassis_json_v1' in large
for forbidden in ('Obiettivo', 'Filtro', 'Soffietto', 'Zone Ansel Adams · es.'):
    assert forbidden not in large, forbidden

print('release=Darkroom-v0.5.0')
print('versionName=0.5.0')
print('versionCode=41')
print('base_version=0.4.9')
print('home_label=GRANDE_FORMATO')
print('chassis_sides=A_AND_B_INDEPENDENT')
print('states=EMPTY,UNEXPOSED,EXPOSED')
print('state_palette=VINTAGE_STONE,SAGE,AMBER_LEATHER')
print('film_brand=FOMAPAN_FIXED')
print('virgin_iso_selector=100,200,400')
print('zone_selector=0_TO_X_NATIVE_BUTTONS')
print('zone_gap=ABS_HIGHLIGHT_MINUS_SHADOW_EV')
print('adesso_overlap_fix=PASS')
print('v049_migration=OLD_DATA_TO_SIDE_A')
print('sonoff_final_step_seconds=0.5')
PY

python3 - <<'PY'
from pathlib import Path
parts = [
    Path('validation-v049.txt'),
    Path('validation-v050-large-format-patch.txt'),
    Path('validation-v050-source.txt'),
]
Path('validation-v050.txt').write_text(
    ''.join(p.read_text(encoding='utf-8') for p in parts),
    encoding='utf-8',
)
PY
sha256sum Darkroom-v0.5.0.apk | tee Darkroom-v0.5.0.sha256
