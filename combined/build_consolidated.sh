#!/usr/bin/env bash
set -euo pipefail

# Consolidated Darkroom v0.5.8 baseline.
# This script compiles the committed source exactly once. It must never call a
# historical build wrapper or download/regenerate the offline MDC snapshot.

START_SECONDS=$SECONDS
SOURCE_ROOT=combined/src
DATABASE="$SOURCE_ROOT/main/assets/mdc_full.sqlite"
MANIFEST="$SOURCE_ROOT/main/AndroidManifest.xml"

test -f "$DATABASE"
test -f "$SOURCE_ROOT/main/java/it/darkroom/assistant/MdcOfflineStore.java"
test -f "$SOURCE_ROOT/main/java/it/darkroom/assistant/AssistantActivityV2.java"

python3 - <<'PY' | tee validation-consolidated-v058-source.txt
from pathlib import Path
import re
import sqlite3

manifest = Path('combined/src/main/AndroidManifest.xml')
text = manifest.read_text(encoding='utf-8')
text, code_count = re.subn(
    r'android:versionCode="[^"]+"', 'android:versionCode="49"', text, count=1
)
text, name_count = re.subn(
    r'android:versionName="[^"]+"', 'android:versionName="0.5.8"', text, count=1
)
if code_count != 1 or name_count != 1:
    raise SystemExit('consolidated manifest version update failed')
manifest.write_text(text, encoding='utf-8')

gradle_file = Path('combined/build.gradle')
text = gradle_file.read_text(encoding='utf-8')
text, code_count = re.subn(
    r'(?m)^\s*versionCode\s+\d+\s*$', '        versionCode 49', text, count=1
)
text, name_count = re.subn(
    r'(?m)^\s*versionName\s+[\'\"][^\'\"]+[\'\"]\s*$',
    "        versionName '0.5.8'", text, count=1
)
if code_count != 1 or name_count != 1:
    raise SystemExit('consolidated Gradle version update failed')
gradle_file.write_text(text, encoding='utf-8')

db = sqlite3.connect('combined/src/main/assets/mdc_full.sqlite')
assert db.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
assert db.execute('SELECT COUNT(*) FROM times').fetchone()[0] == 14808
assert db.execute('SELECT COUNT(*) FROM maco_developer_scope').fetchone()[0] == 37
assert db.execute('SELECT COUNT(*) FROM developer_time_equivalents').fetchone()[0] == 39
assert db.execute(
    "SELECT COUNT(*) FROM developer_time_equivalents WHERE evidence_kind<>'AUDITED_DIRECT_ONE_HOP'"
).fetchone()[0] == 0

kentmere = db.execute(
    '''SELECT time35,time120,timesheet FROM times
       WHERE film_norm='kentmere 100' AND developer_norm='xtol'
         AND dilution_norm='1+1' AND iso=100 AND temp=20'''
).fetchone()
assert kentmere == ('10', '10', ''), kentmere

excel = db.execute(
    '''SELECT time35,time120,timesheet FROM times
       WHERE film_norm='fomapan 100' AND developer_norm='fomadon excel'
         AND dilution_norm='1+1' AND iso=100 AND temp=20'''
).fetchone()
assert excel == ('8-9', '8-9', '8-9'), excel
db.close()

store = Path(
    'combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java'
).read_text(encoding='utf-8')
activity = Path(
    'combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java'
).read_text(encoding='utf-8')
assert 'mdc_offline_darkroom_v058.sqlite' in store
assert 'if (exact != null) return exact;' in store
assert 'developer_time_equivalents' in store
assert 'MdcOfflineStore.lookup(' in activity
assert 'EQUIVALENZA CONTROLLATA' in activity
assert 'MdcOfflineStore.syncAsync' not in activity

print('baseline=Darkroom-v0.5.8')
print('versionCode=49')
print('historical_builds=ZERO')
print('mdc_network_downloads=ZERO')
print('gradle_assemblies_expected=ONE')
print('database_integrity=PASS')
print('offline_equivalence_regressions=PASS')
PY

rm -f combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.5.8.apk
gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.5.8.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.5.8.apk \
  > certificate-consolidated-v058.txt
"$AAPT" dump badging Darkroom-v0.5.8.apk > apk-badging-consolidated-v058.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-consolidated-v058.txt
grep -Fq "versionCode='49'" apk-badging-consolidated-v058.txt
grep -Fq "versionName='0.5.8'" apk-badging-consolidated-v058.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" \
  apk-badging-consolidated-v058.txt
unzip -Z1 Darkroom-v0.5.8.apk > apk-listing-consolidated-v058.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-consolidated-v058.txt

ELAPSED=$((SECONDS - START_SECONDS))
{
  echo 'consolidated_build=PASS'
  echo 'historical_builds=ZERO'
  echo 'mdc_network_downloads=ZERO'
  echo 'gradle_assemblies=ONE'
  echo "elapsed_seconds=$ELAPSED"
} | tee validation-consolidated-v058.txt

sha256sum Darkroom-v0.5.8.apk | tee Darkroom-v0.5.8.sha256
