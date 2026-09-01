#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.5.2 - developer minimum volume + JOBO tank minimum volume.
# Exact base: v0.5.1 sheet-development workflow.

bash combined/build_v051.sh
python3 assistant/db/apply_developer_minimum_volumes_v052.py \
  combined/src/main/assets/mdc_full.sqlite \
  | tee validation-v052-minimum-volume-db.txt
python3 combined/patch_v052_chemistry_volume.py \
  | tee validation-v052-minimum-volume-source.txt

python3 - <<'PY'
from pathlib import Path
import re

manifest = Path('combined/src/main/AndroidManifest.xml')
text = manifest.read_text(encoding='utf-8')
text, count_code = re.subn(
    r'android:versionCode="[^"]+"', 'android:versionCode="43"', text, count=1
)
text, count_name = re.subn(
    r'android:versionName="[^"]+"', 'android:versionName="0.5.2"', text, count=1
)
if count_code != 1 or count_name != 1:
    raise SystemExit('v0.5.2 manifest version update failed')
manifest.write_text(text, encoding='utf-8')

gradle_file = Path('combined/build.gradle')
text = gradle_file.read_text(encoding='utf-8')
text, count_code = re.subn(
    r'(?m)^\s*versionCode\s+\d+\s*$', '        versionCode 43', text, count=1
)
text, count_name = re.subn(
    r'(?m)^\s*versionName\s+[\'\"][^\'\"]+[\'\"]\s*$',
    "        versionName '0.5.2'",
    text,
    count=1,
)
if count_code != 1 or count_name != 1:
    raise SystemExit('v0.5.2 Gradle version update failed')
gradle_file.write_text(text, encoding='utf-8')
PY

rm -f combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.5.2.apk
gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.5.2.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.5.2.apk > certificate-v052.txt
"$AAPT" dump badging Darkroom-v0.5.2.apk > apk-badging-v052.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-v052.txt
grep -Fq "versionCode='43'" apk-badging-v052.txt
grep -Fq "versionName='0.5.2'" apk-badging-v052.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v052.txt
unzip -Z1 Darkroom-v0.5.2.apk > apk-listing-v052.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v052.txt

ASSIST=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
MDC=combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java
grep -Fq 'new String[]{"1", "2", "4"}' "$ASSIST"
grep -Fq 'Math.max(tank.rotaryMl, Math.ceil(chemicalMinimumMl))' "$ASSIST"
grep -Fq 'Volume minimo chimico non verificato' "$ASSIST"
grep -Fq 'renderFilmCapacity(dev, stop, fix, workingVolumeMl)' "$ASSIST"
grep -Fq 'mdc_offline_darkroom_v052.sqlite' "$MDC"
grep -Fq 'static DeveloperMinimumVolume minimumWorkingVolume' "$MDC"

python3 - <<'PY' | tee validation-v052.txt
from pathlib import Path
import sqlite3

database = Path('combined/src/main/assets/mdc_full.sqlite')
connection = sqlite3.connect(database)
columns = {
    row[1] for row in connection.execute('PRAGMA table_info(developer_dilutions)')
}
required = {
    'min_working_ml_500cm2',
    'min_working_ml_4x5_1',
    'min_working_ml_4x5_2',
}
assert required <= columns, required - columns
assert connection.execute('PRAGMA user_version').fetchone()[0] == 4
assert connection.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
total = connection.execute('SELECT COUNT(*) FROM developer_dilutions').fetchone()[0]
verified = connection.execute(
    '''SELECT COUNT(*) FROM developer_dilutions
       WHERE min_working_ml_500cm2 IS NOT NULL
         AND min_working_ml_4x5_1 IS NOT NULL
         AND min_working_ml_4x5_2 IS NOT NULL'''
).fetchone()[0]
assert total == 781, total
assert verified == 11, verified

def values(developer, dilution):
    return connection.execute(
        '''SELECT min_working_ml_500cm2,min_working_ml_4x5_1,min_working_ml_4x5_2
           FROM developer_dilutions
           WHERE developer_norm=? AND dilution_norm=?''',
        (developer, dilution),
    ).fetchone()

assert values('foma universal', '1+3') == (340.0, 85.0, 170.0)
assert values('xt 3', '1+1') == (300.0, 75.0, 150.0)
assert values('rodinal', '1+50') == (255.0, 63.75, 127.5)
assert values('ilfotec lc29', '1+29') == (300.0, 75.0, 150.0)
connection.close()

print('release=Darkroom-v0.5.2')
print('versionName=0.5.2')
print('versionCode=43')
print('base_version=0.5.1')
print('developer_dilution_rows=' + str(total))
print('minimum_volume_verified_rows=' + str(verified))
print('minimum_volume_unknown_policy=BLOCK_NO_ESTIMATE')
print('working_volume_formula=MAX_CHEMICAL_MINIMUM_TANK_MINIMUM')
print('sheet_counts=1,2,4')
print('cpe2_limit_ml=600')
print('database_integrity=PASS')
PY

sha256sum Darkroom-v0.5.2.apk | tee Darkroom-v0.5.2.sha256
