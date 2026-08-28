#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.4.7 - native, mobile-friendly Rolleiflex EV table.
# Exact base: v0.4.6 JOBO/LPL 7451 release candidate. All Timer, SONOFF,
# enlargement, Split Grade, EV/Zone content and maintenance functions survive.

bash combined/build_v046.sh
python3 combined/patch_v047_native_ev_table.py | tee validation-v047-native-ev-table.txt

python3 - <<'PY'
from pathlib import Path
import re

p = Path('combined/src/main/AndroidManifest.xml')
s = p.read_text(encoding='utf-8')
s, n1 = re.subn(r'android:versionCode="[^"]+"', 'android:versionCode="38"', s, count=1)
s, n2 = re.subn(r'android:versionName="[^"]+"', 'android:versionName="0.4.7"', s, count=1)
if n1 != 1 or n2 != 1:
    raise SystemExit('v0.4.7 manifest version update failed')
p.write_text(s, encoding='utf-8')

g = Path('combined/build.gradle')
gs = g.read_text(encoding='utf-8')
gs, n3 = re.subn(r'(?m)^\s*versionCode\s+\d+\s*$', '        versionCode 38', gs, count=1)
gs, n4 = re.subn(r'(?m)^\s*versionName\s+[\'\"][^\'\"]+[\'\"]\s*$', "        versionName '0.4.7'", gs, count=1)
if n3 != 1 or n4 != 1:
    raise SystemExit('v0.4.7 Gradle version update failed')
g.write_text(gs, encoding='utf-8')
PY

rm -f combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.4.7.apk
gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.4.7.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.4.7.apk > certificate-v047.txt
"$AAPT" dump badging Darkroom-v0.4.7.apk > apk-badging-v047.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-v047.txt
grep -Fq "versionCode='38'" apk-badging-v047.txt
grep -Fq "versionName='0.4.7'" apk-badging-v047.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v047.txt
unzip -Z1 Darkroom-v0.4.7.apk > apk-listing-v047.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v047.txt

MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java
ENL=combined/src/main/java/it/darkroom/timer/EnlargementActivity.java
MAINT=combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java
MIGRATION=combined/src/main/java/it/darkroom/timer/Lpl7451Migration.java
SPLIT=combined/src/main/java/it/darkroom/timer/SplitGradePlan.java
ASSIST=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
MDC=combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java

# Native EV table acceptance.
grep -Fq 'private static final String[][] EV_VALUES' "$MAINT"
grep -Fq 'private LinearLayout evTableView()' "$MAINT"
grep -Fq 'LinearLayout fixedColumn' "$MAINT"
grep -Fq 'HorizontalScrollView apertureScroller' "$MAINT"
grep -Fq 'VALORI EV · scorri i diaframmi  →' "$MAINT"
grep -Fq '★  Rolleiflex 2.8 E2' "$MAINT"
grep -Fq '●  Rolleiflex 3.5 Tessar MX' "$MAINT"
grep -Fq 'EV_TABLE_QUESTION.equals(question)' "$MAINT"
if grep -Fq 'Typeface.MONOSPACE' "$MAINT" || grep -Fq '| Tempo | f/2,8 |' "$MAINT"; then
  echo 'ASCII EV table survived in final app source' >&2
  exit 1
fi

# v0.4.6 LPL scope and operational invariants remain present.
grep -Fq 'static final String LPL_MODEL = "LPL7451"' "$ENL"
grep -Fq '"35", "66", "45"' "$ENL"
grep -Fq 'Math.pow((c.beta+1)/(b1+1),2)' "$ENL"
grep -Fq 'Math.round(ms / 500.0) * 500' "$ENL"
grep -Fq 'columnCalibration=PENDING' "$ENL"
grep -Fq 'setLogFilter("4x5")' "$MAIN"
grep -Fq '"Y60 / M0", "Y30 / M0", "Y0 / M10", "Y0 / M40", "Y0 / M90", "Y0 / M130"' "$MAIN"
grep -Fq 'public int hardMagenta = 130;' "$SPLIT"
grep -Fq 'lpl7451MigrationV046Done' "$MIGRATION"
grep -Fq '1y67xUwISxjz8f4-QFmBUOquabVezXq4A' "$MAINT"
grep -Fq 'Come posso usare il Sistema Zonale con il Minolta Auto Meter III F?' "$MAINT"
grep -q 'private static final String APP_VERSION = "0.13.11";' "$MAIN"
grep -Fq 'DURATA STOCK · BOTTIGLIA PIENA' "$ASSIST"
grep -Fq 'mdc_offline_darkroom_v037.sqlite' "$MDC"

python3 - <<'PY' | tee validation-v047-source.txt
from pathlib import Path
import re
import sqlite3

root = Path('combined/src/main/java/it/darkroom/timer')
maint = (root / 'maintenance/UseMaintenanceActivity.java').read_text(encoding='utf-8')
main = (root / 'MainActivity.java').read_text(encoding='utf-8')
enl = (root / 'EnlargementActivity.java').read_text(encoding='utf-8')

def java_strings(block):
    return re.findall(r'"(?:\\.|[^"\\])*"', block)

def array_body(name):
    marker = 'private static final String[] ' + name + ' = {'
    start = maint.index(marker)
    body_start = maint.index('{', start) + 1
    end = maint.index('\n    };', body_start)
    return maint[body_start:end]

assert len(java_strings(array_body('Q_MINOLTA'))) == 12
assert len(java_strings(array_body('A_MINOLTA'))) == 12
assert len(java_strings(array_body('Q_ZONE'))) == 11
assert len(java_strings(array_body('A_ZONE'))) == 11
assert maint.count('private LinearLayout evTableView()') == 1
assert 'Typeface.MONOSPACE' not in maint
assert '| Tempo | f/2,8 |' not in maint
assert len(re.findall(r'^\s*\{"(?:[^"\\]|\\.)*"(?:,\s*"(?:[^"\\]|\\.)*"){7}\},?$', maint, re.MULTILINE)) >= 15
assert main.count('setLogFilter("4x5")') == 1
assert 'b2c(' not in enl and 'paperPlane' not in enl

db = Path('combined/src/main/assets/mdc_full.sqlite')
con = sqlite3.connect(db)
cur = con.cursor()
assert cur.execute('pragma quick_check').fetchone()[0] == 'ok'
assert cur.execute('select count(*) from times').fetchone()[0] == 14504
assert cur.execute('select count(*) from films').fetchone()[0] == 347
assert cur.execute('select count(*) from developers').fetchone()[0] == 232
assert cur.execute("select count(*) from developer_dilutions where source_kind='MDC'").fetchone()[0] == 776
con.close()

print('release=Darkroom-v0.4.7')
print('versionName=0.4.7')
print('versionCode=38')
print('base_version=0.4.6')
print('ev_table_renderer=NATIVE_ANDROID_GRID')
print('fixed_time_column=PASS')
print('horizontal_aperture_scroll=PASS')
print('ascii_table_removed=PASS')
print('enlarger=JOBO/LPL_7451_ONLY')
print('ev_zone_work_preserved=PASS')
print('sonoff_final_step_seconds=0.5')
print('physical_column_calibration=DEFERRED')
print('mdc_times_unchanged=14504')
print('mdc_films_unchanged=347')
print('mdc_developers_unchanged=232')
print('mdc_dilutions_unchanged=776')
PY

cat validation-v046.txt validation-v047-native-ev-table.txt validation-v047-source.txt > validation-v047.txt
sha256sum Darkroom-v0.4.7.apk | tee Darkroom-v0.4.7.sha256
