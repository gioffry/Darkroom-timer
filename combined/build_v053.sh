#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.5.3 - Maco Direct developer scope and complete minimum volumes.
# Exact base: v0.5.2 chemistry-volume workflow.

bash combined/build_v052.sh
python3 assistant/db/generate_maco_minimum_volumes_v053.py \
  combined/src/main/assets/mdc_full.sqlite \
  --output generated-v053-maco-minimum-volumes.json \
  | tee validation-v053-maco-generation.txt
python3 assistant/db/apply_developer_minimum_volumes_v053.py \
  combined/src/main/assets/mdc_full.sqlite \
  --records generated-v053-maco-minimum-volumes.json \
  | tee validation-v053-maco-database.txt
python3 combined/patch_v053_maco_minimum_volumes.py \
  | tee validation-v053-maco-source.txt

python3 - <<'PY'
from pathlib import Path
import re

manifest = Path('combined/src/main/AndroidManifest.xml')
text = manifest.read_text(encoding='utf-8')
text, count_code = re.subn(
    r'android:versionCode="[^"]+"', 'android:versionCode="44"', text, count=1
)
text, count_name = re.subn(
    r'android:versionName="[^"]+"', 'android:versionName="0.5.3"', text, count=1
)
if count_code != 1 or count_name != 1:
    raise SystemExit('v0.5.3 manifest version update failed')
manifest.write_text(text, encoding='utf-8')

gradle_file = Path('combined/build.gradle')
text = gradle_file.read_text(encoding='utf-8')
text, count_code = re.subn(
    r'(?m)^\s*versionCode\s+\d+\s*$', '        versionCode 44', text, count=1
)
text, count_name = re.subn(
    r'(?m)^\s*versionName\s+[\'\"][^\'\"]+[\'\"]\s*$',
    "        versionName '0.5.3'",
    text,
    count=1,
)
if count_code != 1 or count_name != 1:
    raise SystemExit('v0.5.3 Gradle version update failed')
gradle_file.write_text(text, encoding='utf-8')
PY

rm -f combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.5.3.apk
gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.5.3.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.5.3.apk > certificate-v053.txt
"$AAPT" dump badging Darkroom-v0.5.3.apk > apk-badging-v053.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-v053.txt
grep -Fq "versionCode='44'" apk-badging-v053.txt
grep -Fq "versionName='0.5.3'" apk-badging-v053.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v053.txt
unzip -Z1 Darkroom-v0.5.3.apk > apk-listing-v053.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v053.txt

ASSIST=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
MDC=combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java
grep -Fq 'Math.max(tank.rotaryMl, Math.ceil(chemicalMinimumMl))' "$ASSIST"
grep -Fq 'normalizedMixDilution' "$ASSIST"
grep -Fq 'formatDeveloperMix' "$ASSIST"
grep -Fq 'Parte A ' "$ASSIST"
grep -Fq 'FONTE / CRITERIO VOLUME' "$ASSIST"
grep -Fq 'mdc_offline_darkroom_v053.sqlite' "$MDC"
grep -Fq 's.evidence_kind' "$MDC"

python3 - <<'PY' | tee validation-v053.txt
from pathlib import Path
import json
import math
import sqlite3

database = Path('combined/src/main/assets/mdc_full.sqlite')
records_path = Path('generated-v053-maco-minimum-volumes.json')
payload = json.loads(records_path.read_text(encoding='utf-8'))
connection = sqlite3.connect(database)

assert connection.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
assert connection.execute('PRAGMA user_version').fetchone()[0] == 5
columns = {row[1] for row in connection.execute('PRAGMA table_info(developer_dilutions)')}
assert {'min_working_ml_500cm2','min_working_ml_4x5_1','min_working_ml_4x5_2'} <= columns
source_columns = {
    row[1] for row in connection.execute('PRAGMA table_info(developer_minimum_volume_sources)')
}
assert 'evidence_kind' in source_columns

total = connection.execute('SELECT COUNT(*) FROM developer_dilutions').fetchone()[0]
populated = connection.execute(
    '''SELECT COUNT(*) FROM developer_dilutions
       WHERE min_working_ml_500cm2 IS NOT NULL
         AND min_working_ml_4x5_1 IS NOT NULL
         AND min_working_ml_4x5_2 IS NOT NULL'''
).fetchone()[0]
scope = connection.execute('SELECT COUNT(*) FROM maco_developer_scope').fetchone()[0]
manufacturer = connection.execute(
    """SELECT COUNT(*) FROM developer_minimum_volume_sources
       WHERE evidence_kind<>'CONSERVATIVE_OPERATIONAL'"""
).fetchone()[0]
operational = connection.execute(
    """SELECT COUNT(*) FROM developer_minimum_volume_sources
       WHERE evidence_kind='CONSERVATIVE_OPERATIONAL'"""
).fetchone()[0]
assert total == 781, total
assert populated == 236, populated
assert scope == 37, scope
assert manufacturer == 206, manufacturer
assert operational == 30, operational
assert len(payload['scope']) == scope
assert len(payload['records']) == populated

def values(developer, dilution):
    return connection.execute(
        '''SELECT min_working_ml_500cm2,min_working_ml_4x5_1,min_working_ml_4x5_2
           FROM developer_dilutions
           WHERE developer_norm=? AND dilution_norm=?''',
        (developer, dilution),
    ).fetchone()

def near(actual, expected):
    assert actual is not None
    assert all(abs(a-b) < 0.00001 for a,b in zip(actual, expected)), (actual, expected)

near(values('foma universal', '1+3'), (333.333333, 83.333333, 166.666667))
near(values('xt 3', '1+1'), (300.0, 75.0, 150.0))
near(values('moersch eco', '2+1+50'), (265.0, 66.25, 132.5))
near(values('jobo alpha', '1+1+18'), (120.0, 30.0, 60.0))
near(values('rodinal', '1+50'), (255.0, 63.75, 127.5))
near(values('hc 110', 'b'), (200.0, 50.0, 100.0))
assert values('123 pyro', '1+100') == (None, None, None)

# The app applies the tank floor after selecting the load-specific chemistry value.
assert max(270, math.ceil(values('foma universal', '1+3')[0])) == 334
assert max(270, math.ceil(values('foma universal', '1+3')[1])) == 270
assert max(270, math.ceil(values('foma universal', '1+3')[2])) == 270
assert max(270, math.ceil(values('xt 3', '1+1')[0])) == 300

for minimum_500, one_sheet, two_sheets in connection.execute(
    '''SELECT min_working_ml_500cm2,min_working_ml_4x5_1,min_working_ml_4x5_2
       FROM developer_dilutions WHERE min_working_ml_500cm2 IS NOT NULL'''
):
    assert abs(one_sheet * 4 - minimum_500) < 0.00001
    assert abs(two_sheets * 2 - minimum_500) < 0.00001

connection.close()
print('release=Darkroom-v0.5.3')
print('versionName=0.5.3')
print('versionCode=44')
print('base_version=0.5.2')
print('maco_scope_checked_at=2026-09-01')
print('maco_scope_developers=' + str(scope))
print('minimum_volume_populated_rows=' + str(populated))
print('manufacturer_evidence_rows=' + str(manufacturer))
print('conservative_operational_rows=' + str(operational))
print('outside_maco_scope_policy=BLOCK')
print('working_volume_formula=MAX_CHEMICAL_MINIMUM_TANK_MINIMUM')
print('multi_component_dilutions=SUPPORTED')
print('database_integrity=PASS')
PY

sha256sum Darkroom-v0.5.3.apk | tee Darkroom-v0.5.3.sha256
