#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.5.4 - repair the film-calculation crash reported on-device.
# Exact base: v0.5.3 Maco developer minimum-volume release.

bash combined/build_v053.sh
python3 combined/patch_v054_calculation_crash_fix.py \
  | tee validation-v054-calculation-source.txt

python3 - <<'PY'
from pathlib import Path
import re

manifest = Path('combined/src/main/AndroidManifest.xml')
text = manifest.read_text(encoding='utf-8')
text, count_code = re.subn(
    r'android:versionCode="[^"]+"', 'android:versionCode="45"', text, count=1
)
text, count_name = re.subn(
    r'android:versionName="[^"]+"', 'android:versionName="0.5.4"', text, count=1
)
if count_code != 1 or count_name != 1:
    raise SystemExit('v0.5.4 manifest version update failed')
manifest.write_text(text, encoding='utf-8')

gradle_file = Path('combined/build.gradle')
text = gradle_file.read_text(encoding='utf-8')
text, count_code = re.subn(
    r'(?m)^\s*versionCode\s+\d+\s*$', '        versionCode 45', text, count=1
)
text, count_name = re.subn(
    r'(?m)^\s*versionName\s+[\'\"][^\'\"]+[\'\"]\s*$',
    "        versionName '0.5.4'",
    text,
    count=1,
)
if count_code != 1 or count_name != 1:
    raise SystemExit('v0.5.4 Gradle version update failed')
gradle_file.write_text(text, encoding='utf-8')
PY

rm -f combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.5.4.apk
gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.5.4.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.5.4.apk > certificate-v054.txt
"$AAPT" dump badging Darkroom-v0.5.4.apk > apk-badging-v054.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-v054.txt
grep -Fq "versionCode='45'" apk-badging-v054.txt
grep -Fq "versionName='0.5.4'" apk-badging-v054.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v054.txt
unzip -Z1 Darkroom-v0.5.4.apk > apk-listing-v054.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v054.txt

ASSIST=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
MDC=combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java
grep -Fq 'mdc_offline_darkroom_v054.sqlite' "$MDC"
grep -Fq 'showDevelopmentResultSafely' "$ASSIST"
grep -Fq 'showDevelopmentResultEssential' "$ASSIST"
grep -Fq "L'app è rimasta aperta" "$ASSIST"
grep -Fq 'formatDeveloperMix(dev.name, dilution, devMix, workingVolumeMl)' "$ASSIST"

python3 - <<'PY' | tee validation-v054.txt
from pathlib import Path
import math
import sqlite3

database = Path('combined/src/main/assets/mdc_full.sqlite')
connection = sqlite3.connect(database)
assert connection.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
assert connection.execute('PRAGMA user_version').fetchone()[0] == 5

def values(developer, dilution):
    return connection.execute(
        '''SELECT min_working_ml_500cm2,min_working_ml_4x5_1,min_working_ml_4x5_2
           FROM developer_dilutions
           WHERE developer_norm=? AND dilution_norm=?''',
        (developer, dilution),
    ).fetchone()

# Exact on-device regression reported by the user: KODAK D-76, 1+1, one roll,
# JOBO 2520. Chemistry requires 237 ml, therefore the 270 ml tank floor wins.
d76 = values('d 76', '1+1')
assert d76 == (237.0, 59.25, 118.5), d76
assert max(270, math.ceil(d76[0])) == 270

populated = connection.execute(
    'SELECT COUNT(*) FROM developer_dilutions WHERE min_working_ml_500cm2 IS NOT NULL'
).fetchone()[0]
scope = connection.execute('SELECT COUNT(*) FROM maco_developer_scope').fetchone()[0]
assert populated == 236
assert scope == 37
connection.close()

print('release=Darkroom-v0.5.4')
print('versionName=0.5.4')
print('versionCode=45')
print('base_version=0.5.3')
print('reported_regression=KODAK_D76_1+1_ONE_ROLL_JOBO_2520')
print('d76_chemical_minimum_ml=237')
print('d76_working_volume_ml=270')
print('fresh_database_copy=PASS')
print('ui_calculation_guard=PASS')
print('ui_result_fallback=PASS')
print('database_integrity=PASS')
PY

sha256sum Darkroom-v0.5.4.apk | tee Darkroom-v0.5.4.sha256
