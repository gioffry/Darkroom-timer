#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.5.1 - 4x5 Sheet development in the film-development workflow.
# Exact base: v0.5.0 corrected large-format A/B chassis workflow.

bash combined/build_v050.sh
python3 combined/patch_v051_sheet_development.py | tee validation-v051-sheet-patch.txt

python3 - <<'PY'
from pathlib import Path
import re

p = Path('combined/src/main/AndroidManifest.xml')
s = p.read_text(encoding='utf-8')
s, n1 = re.subn(r'android:versionCode="[^"]+"', 'android:versionCode="42"', s, count=1)
s, n2 = re.subn(r'android:versionName="[^"]+"', 'android:versionName="0.5.1"', s, count=1)
if n1 != 1 or n2 != 1:
    raise SystemExit('v0.5.1 manifest version update failed')
p.write_text(s, encoding='utf-8')

g = Path('combined/build.gradle')
gs = g.read_text(encoding='utf-8')
gs, n3 = re.subn(r'(?m)^\s*versionCode\s+\d+\s*$', '        versionCode 42', gs, count=1)
gs, n4 = re.subn(r'(?m)^\s*versionName\s+[\'\"][^\'\"]+[\'\"]\s*$', "        versionName '0.5.1'", gs, count=1)
if n3 != 1 or n4 != 1:
    raise SystemExit('v0.5.1 Gradle version update failed')
g.write_text(gs, encoding='utf-8')
PY

rm -f combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.5.1.apk
gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.5.1.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.5.1.apk > certificate-v051.txt
"$AAPT" dump badging Darkroom-v0.5.1.apk > apk-badging-v051.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-v051.txt
grep -Fq "versionCode='42'" apk-badging-v051.txt
grep -Fq "versionName='0.5.1'" apk-badging-v051.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v051.txt
unzip -Z1 Darkroom-v0.5.1.apk > apk-listing-v051.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v051.txt

ASSIST=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
MDC=combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java
ENGINE=combined/src/main/java/it/darkroom/assistant/DevTimeEngine.java
LARGE=combined/src/main/java/it/darkroom/timer/largeformat/LargeFormatActivity.java
MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java
ENL=combined/src/main/java/it/darkroom/timer/EnlargementActivity.java

# 4x5 must be a real third development format backed by timesheet.
grep -Fq 'SELECT time35,time120,timesheet FROM times' "$MDC"
grep -Fq 'if (hasSheet) out.add("4x5")' "$MDC"
grep -Fq 'String raw = sheetFormat ? row.timeSheet' "$MDC"
grep -Fq 'if (sheetFormat) continue;' "$MDC"
grep -Fq 'MdcOfflineStore.lookup(' "$ASSIST"
grep -Fq 'NUMERO LASTRE 4×5' "$ASSIST"
grep -Fq 'return "4×5 / lastre"' "$ASSIST"
grep -Fq 'new Tank("JOBO 2520", 270, 2, 1, 6)' "$ASSIST"
grep -Fq 'JOBO 2520 + 2509N' "$ASSIST"
grep -Fq 'isSheetFormat(selectedFilm.format) ? t.maxSheet' "$ASSIST"
grep -Fq 'formatDisplay(result.format)' "$ASSIST"
grep -Fq 'film_used_units_v2_' "$ASSIST"
grep -Fq '4 lastre 4×5 ≈ 1 rullo 135-36 / 120' "$ASSIST"
grep -Fq '"4x5".equalsIgnoreCase(format) ? row.timeSheet' "$ENGINE"

# v0.5.0 large-format capture workflow must remain intact.
grep -Fq 'final Side a = new Side();' "$LARGE"
grep -Fq 'final Side b = new Side();' "$LARGE"
grep -Fq 'private static final String FILM_BRAND = "FOMAPAN";' "$LARGE"
grep -Fq 'Math.abs(selectedHighlight[0] - selectedShadow[0])' "$LARGE"
grep -Fq 'gap.setText("SCARTO: " + delta + " EV")' "$LARGE"

# Other cumulative invariants.
grep -q 'private static final String APP_VERSION = "0.13.11";' "$MAIN"
grep -Fq 'Math.round(ms / 500.0) * 500' "$ENL"
grep -Fq 'columnCalibration=MEASURED_67_73_6MM' "$ENL"

python3 - <<'PY' | tee validation-v051-source-db.txt
from pathlib import Path
import sqlite3

root = Path('combined/src/main/java/it/darkroom/assistant')
activity = (root / 'AssistantActivityV2.java').read_text(encoding='utf-8')
store = (root / 'MdcOfflineStore.java').read_text(encoding='utf-8')
engine = (root / 'DevTimeEngine.java').read_text(encoding='utf-8')

assert 'NUMERO LASTRE 4×5' in activity
assert '4×5 / lastre' in activity
assert 'JOBO 2520 + 2509N' in activity
assert 'maxSheet' in activity
assert 'MdcOfflineStore.lookup(' in activity
assert 'filmCapacityUnits(rolls, result.format)' in activity
assert 'SELECT time35,time120,timesheet FROM times' in store
assert 'if (hasSheet) out.add("4x5")' in store
assert 'if (sheetFormat) continue;' in store
assert '"4x5".equalsIgnoreCase(format) ? row.timeSheet' in engine

# Inspect the actual database bundled into this build, not only the importer source.
db = Path('combined/src/main/assets/mdc_full.sqlite')
assert db.exists(), db
con = sqlite3.connect(db)
cur = con.cursor()
assert cur.execute('pragma quick_check').fetchone()[0] == 'ok'
cols = [r[1] for r in cur.execute('pragma table_info(times)')]
assert 'time35' in cols and 'time120' in cols and 'timesheet' in cols

def valid_sheet_sql():
    return "timesheet IS NOT NULL AND trim(timesheet)<>'' AND trim(timesheet) NOT IN ('-','—','#','n/a','N/A')"

sheet_rows = cur.execute('SELECT count(*) FROM times WHERE ' + valid_sheet_sql()).fetchone()[0]
total_rows = cur.execute('SELECT count(*) FROM times').fetchone()[0]
assert total_rows >= 14000, total_rows
assert sheet_rows >= 5000, sheet_rows

foma_sheet = {}
for iso in (100, 200, 400):
    n = cur.execute(
        'SELECT count(*) FROM times WHERE lower(film) LIKE ? AND ' + valid_sheet_sql(),
        (f'%fomapan%{iso}%',)
    ).fetchone()[0]
    foma_sheet[iso] = n
assert foma_sheet[100] >= 150, foma_sheet
assert foma_sheet[200] >= 100, foma_sheet
assert foma_sheet[400] >= 150, foma_sheet

universal = cur.execute(
    '''SELECT film,iso,dilution,timesheet,temp FROM times
       WHERE lower(film) LIKE '%fomapan%'
         AND lower(developer) LIKE '%universal%'
         AND replace(replace(lower(dilution),':','+'),' ','')='1+3'
         AND timesheet IS NOT NULL AND trim(timesheet)<>''
       ORDER BY film,iso,temp'''
).fetchall()
assert len(universal) >= 3, universal
con.close()

print('release=Darkroom-v0.5.1')
print('versionName=0.5.1')
print('versionCode=42')
print('base_version=0.5.0')
print('development_formats=35,120,4x5')
print('sheet_primary_database_column=timesheet')
print('sheet_cross_format_fallback=DISABLED')
print('sheet_tank=JOBO_2520_PLUS_2509N')
print('sheet_capacity_per_tank=6')
print('sheet_rotary_volume_ml=270')
print('sheet_count_selector=1..6')
print('sheet_capacity_counter=ROLL_EQUIVALENT_BY_EMULSION_AREA')
print('mdc_total_rows=' + str(total_rows))
print('mdc_sheet_rows=' + str(sheet_rows))
print('fomapan_sheet_rows=' + ','.join(f'{k}:{v}' for k,v in foma_sheet.items()))
print('foma_universal_1+3_sheet_rows=' + str(len(universal)))
for row in universal[:12]:
    print('foma_universal_sheet=' + '|'.join(str(x) for x in row))
print('database_integrity=PASS')
print('v050_large_format_capture_preserved=PASS')
print('sonoff_final_step_seconds=0.5')
PY

python3 - <<'PY'
from pathlib import Path
parts = [
    Path('validation-v050.txt'),
    Path('validation-v051-sheet-patch.txt'),
    Path('validation-v051-source-db.txt'),
]
Path('validation-v051.txt').write_text(
    ''.join(p.read_text(encoding='utf-8') for p in parts),
    encoding='utf-8',
)
PY
sha256sum Darkroom-v0.5.1.apk | tee Darkroom-v0.5.1.sha256
