#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.4.8 - final JOBO/LPL 7451 column calibration and knob FAQ.
# Exact base: v0.4.7 with native Rolleiflex EV table and the complete v0.4.6 LPL scope.

bash combined/build_v047.sh
python3 combined/patch_v048_lpl_final.py | tee validation-v048-lpl-final-patch.txt

python3 - <<'PY'
from pathlib import Path
import re

p = Path('combined/src/main/AndroidManifest.xml')
s = p.read_text(encoding='utf-8')
s, n1 = re.subn(r'android:versionCode="[^"]+"', 'android:versionCode="39"', s, count=1)
s, n2 = re.subn(r'android:versionName="[^"]+"', 'android:versionName="0.4.8"', s, count=1)
if n1 != 1 or n2 != 1:
    raise SystemExit('v0.4.8 manifest version update failed')
p.write_text(s, encoding='utf-8')

g = Path('combined/build.gradle')
gs = g.read_text(encoding='utf-8')
gs, n3 = re.subn(r'(?m)^\s*versionCode\s+\d+\s*$', '        versionCode 39', gs, count=1)
gs, n4 = re.subn(r'(?m)^\s*versionName\s+[\'\"][^\'\"]+[\'\"]\s*$', "        versionName '0.4.8'", gs, count=1)
if n3 != 1 or n4 != 1:
    raise SystemExit('v0.4.8 Gradle version update failed')
g.write_text(gs, encoding='utf-8')
PY

rm -f combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.4.8.apk
gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.4.8.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.4.8.apk > certificate-v048.txt
"$AAPT" dump badging Darkroom-v0.4.8.apk > apk-badging-v048.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-v048.txt
grep -Fq "versionCode='39'" apk-badging-v048.txt
grep -Fq "versionName='0.4.8'" apk-badging-v048.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v048.txt
unzip -Z1 Darkroom-v0.4.8.apk > apk-listing-v048.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v048.txt

MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java
ENL=combined/src/main/java/it/darkroom/timer/EnlargementActivity.java
GEOMETRY=combined/src/main/java/it/darkroom/timer/Lpl7451Geometry.java
MAINT=combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java
JPEG=combined/src/main/java/it/darkroom/timer/JpegCardRenderer.java
MIGRATION=combined/src/main/java/it/darkroom/timer/Lpl7451Migration.java
SPLIT=combined/src/main/java/it/darkroom/timer/SplitGradePlan.java
ASSIST=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
MDC=combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java

# Final LPL geometry and measurement acceptance.
grep -Fq 'MEASURED_SCALE = 67.0' "$GEOMETRY"
grep -Fq 'MEASURED_NEGATIVE_TO_BASEBOARD_CM = 73.0' "$GEOMETRY"
grep -Fq 'EASEL_HEIGHT_CM = 0.6' "$GEOMETRY"
grep -Fq 'focalCm * (beta + 1.0 / beta + 2.0)' "$GEOMETRY"
grep -Fq 'columnCalibration=MEASURED_67_73_6MM' "$ENL"
grep -Fq 'scaleOffsetCm=5.40' "$ENL"
grep -Fq 'Scala colonna LPL %.1f' "$ENL"
grep -Fq 'enlargementMetaValue(meta, "columnScale")' "$MAIN"
grep -Fq 'append("scala LPL ")' "$MAIN"
grep -Fq 'β / Scala LPL' "$JPEG"
if grep -Fq 'columnCalibration=PENDING' "$ENL" || grep -Fq 'calibrazione fisica rinviata' "$ENL"; then
  echo 'Pending LPL calibration survived in final app source' >&2
  exit 1
fi

# Knob FAQ and maintenance acceptance.
grep -Fq 'Le manopole del modulo colore e del blocco colonna sono fragili' "$MAINT"
grep -Fq 'LPL 3281-282' "$MAINT"
grep -Fq 'LPL 3481-257' "$MAINT"
grep -Fq '6,00 da 6,35 mm' "$MAINT"
grep -Fq '30–35 mm' "$MAINT"
grep -Fq 'card.addView(section("MANOPOLE"' "$MAINT"

# Native EV table and cumulative app invariants remain present.
grep -Fq 'private static final String[][] EV_VALUES' "$MAINT"
grep -Fq 'private LinearLayout evTableView()' "$MAINT"
grep -Fq 'LinearLayout fixedColumn' "$MAINT"
grep -Fq 'HorizontalScrollView apertureScroller' "$MAINT"
grep -Fq 'EV_TABLE_QUESTION.equals(question)' "$MAINT"
if grep -Fq 'Typeface.MONOSPACE' "$MAINT" || grep -Fq '| Tempo | f/2,8 |' "$MAINT"; then
  echo 'ASCII EV table survived in v0.4.8' >&2
  exit 1
fi

grep -Fq 'static final String LPL_MODEL = "LPL7451"' "$ENL"
grep -Fq '"35", "66", "45"' "$ENL"
grep -Fq 'Math.pow((c.beta+1)/(b1+1),2)' "$ENL"
grep -Fq 'Math.round(ms / 500.0) * 500' "$ENL"
grep -Fq 'setLogFilter("4x5")' "$MAIN"
grep -Fq '"Y60 / M0", "Y30 / M0", "Y0 / M10", "Y0 / M40", "Y0 / M90", "Y0 / M130"' "$MAIN"
grep -Fq 'public int hardMagenta = 130;' "$SPLIT"
grep -Fq 'lpl7451MigrationV046Done' "$MIGRATION"
grep -Fq '1y67xUwISxjz8f4-QFmBUOquabVezXq4A' "$MAINT"
grep -Fq 'Come posso usare il Sistema Zonale con il Minolta Auto Meter III F?' "$MAINT"
grep -q 'private static final String APP_VERSION = "0.13.11";' "$MAIN"
grep -Fq 'DURATA STOCK · BOTTIGLIA PIENA' "$ASSIST"
grep -Fq 'mdc_offline_darkroom_v037.sqlite' "$MDC"

python3 - <<'PY' | tee validation-v048-source.txt
from pathlib import Path
import math
import re
import sqlite3

root = Path('combined/src/main/java/it/darkroom/timer')
maint = (root / 'maintenance/UseMaintenanceActivity.java').read_text(encoding='utf-8')
main = (root / 'MainActivity.java').read_text(encoding='utf-8')
enl = (root / 'EnlargementActivity.java').read_text(encoding='utf-8')
geometry = (root / 'Lpl7451Geometry.java').read_text(encoding='utf-8')

def java_strings(block):
    return re.findall(r'"(?:\\.|[^"\\])*"', block)

def array_body(name):
    marker = 'private static final String[] ' + name + ' = {'
    start = maint.index(marker)
    body_start = maint.index('{', start) + 1
    end = maint.index('\n    };', body_start)
    return maint[body_start:end]

assert len(java_strings(array_body('Q_LPL7451'))) == 11
assert len(java_strings(array_body('A_LPL7451'))) == 11
assert len(java_strings(array_body('Q_MINOLTA'))) == 12
assert len(java_strings(array_body('A_MINOLTA'))) == 12
assert len(java_strings(array_body('Q_ZONE'))) == 11
assert len(java_strings(array_body('A_ZONE'))) == 11
assert maint.count('private LinearLayout evTableView()') == 1
assert 'Typeface.MONOSPACE' not in maint
assert '| Tempo | f/2,8 |' not in maint
assert 'columnCalibration=PENDING' not in enl
assert 'MEASURED_67_73_6MM' in enl
assert 'SCALE_TO_PAPER_OFFSET_CM' in geometry
assert main.count('setLogFilter("4x5")') == 1
assert 'b2c(' not in enl and 'paperPlane' not in enl

measured_scale = 67.0
negative_to_baseboard = 73.0
easel_height = 0.6
mechanical_offset = negative_to_baseboard - measured_scale
paper_offset = mechanical_offset - easel_height
paper_distance = negative_to_baseboard - easel_height
assert abs(mechanical_offset - 6.0) < 1e-9
assert abs(paper_offset - 5.4) < 1e-9
assert abs(paper_distance - 72.4) < 1e-9
assert abs((paper_distance - paper_offset) - measured_scale) < 1e-9
for lens_mm in (50, 75, 150):
    focal_cm = lens_mm / 10.0
    sum_beta_inverse = paper_distance / focal_cm - 2.0
    discriminant = sum_beta_inverse * sum_beta_inverse - 4.0
    assert discriminant >= 0.0
    beta = (sum_beta_inverse + math.sqrt(discriminant)) / 2.0
    reconstructed_distance = focal_cm * (beta + 1.0 / beta + 2.0)
    assert abs((reconstructed_distance - paper_offset) - measured_scale) < 1e-9

db = Path('combined/src/main/assets/mdc_full.sqlite')
con = sqlite3.connect(db)
cur = con.cursor()
assert cur.execute('pragma quick_check').fetchone()[0] == 'ok'
assert cur.execute('select count(*) from times').fetchone()[0] == 14504
assert cur.execute('select count(*) from films').fetchone()[0] == 347
assert cur.execute('select count(*) from developers').fetchone()[0] == 232
assert cur.execute("select count(*) from developer_dilutions where source_kind='MDC'").fetchone()[0] == 776
con.close()

print('release=Darkroom-v0.4.8')
print('versionName=0.4.8')
print('versionCode=39')
print('base_version=0.4.7')
print('enlarger=JOBO/LPL_7451_ONLY')
print('mechanical_offset_cm=6.0')
print('easel_height_mm=6.0')
print('scale_to_paper_offset_cm=5.4')
print('calibration_round_trip=67.0')
print('lenses_50_75_150_round_trip=PASS')
print('lpl_knob_faq=PASS')
print('ev_table_renderer=NATIVE_ANDROID_GRID')
print('ev_zone_work_preserved=PASS')
print('split_grade_structure_preserved=PASS')
print('sonoff_final_step_seconds=0.5')
print('mdc_times_unchanged=14504')
print('mdc_films_unchanged=347')
print('mdc_developers_unchanged=232')
print('mdc_dilutions_unchanged=776')
PY

python3 - <<'PY'
from pathlib import Path
parts = [
    Path('validation-v047.txt'),
    Path('validation-v048-lpl-final-patch.txt'),
    Path('validation-v048-source.txt'),
]
Path('validation-v048.txt').write_text(
    ''.join(p.read_text(encoding='utf-8') for p in parts),
    encoding='utf-8',
)
PY
sha256sum Darkroom-v0.4.8.apk | tee Darkroom-v0.4.8.sha256
