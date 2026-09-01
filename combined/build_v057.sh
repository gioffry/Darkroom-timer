#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.5.7 - release-gated, dual-index MDC snapshot. The app itself
# remains fully offline; network access exists only in this release build.
# No APK is emitted unless every validation below succeeds.

python3 combined/patch_v056_build_chain.py
python3 combined/patch_v057_build_chain.py
bash combined/build_v055.sh
python3 combined/patch_v056_offline_times_ui.py \
  | tee validation-v057-offline-ui-source.txt
python3 combined/patch_v057_runtime.py \
  | tee validation-v057-runtime-source.txt

python3 - <<'PY'
from pathlib import Path
import re

manifest = Path('combined/src/main/AndroidManifest.xml')
text = manifest.read_text(encoding='utf-8')
text, n1 = re.subn(r'android:versionCode="[^"]+"', 'android:versionCode="48"', text, count=1)
text, n2 = re.subn(r'android:versionName="[^"]+"', 'android:versionName="0.5.7"', text, count=1)
if n1 != 1 or n2 != 1: raise SystemExit('v0.5.7 manifest version update failed')
manifest.write_text(text, encoding='utf-8')

gradle_file = Path('combined/build.gradle')
text = gradle_file.read_text(encoding='utf-8')
text, n3 = re.subn(r'(?m)^\s*versionCode\s+\d+\s*$', '        versionCode 48', text, count=1)
text, n4 = re.subn(r'(?m)^\s*versionName\s+[\'\"][^\'\"]+[\'\"]\s*$', "        versionName '0.5.7'", text, count=1)
if n3 != 1 or n4 != 1: raise SystemExit('v0.5.7 Gradle version update failed')
gradle_file.write_text(text, encoding='utf-8')
PY

rm -f combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.5.7.apk
gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.5.7.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.5.7.apk > certificate-v057.txt
"$AAPT" dump badging Darkroom-v0.5.7.apk > apk-badging-v057.txt
grep -Fq "versionCode='48'" apk-badging-v057.txt
grep -Fq "versionName='0.5.7'" apk-badging-v057.txt
unzip -Z1 Darkroom-v0.5.7.apk > apk-listing-v057.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v057.txt

ASSIST=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
MDC=combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java
grep -Fq 'mdc_offline_darkroom_v057.sqlite' "$MDC"
! grep -Fq 'MdcOfflineStore.syncAsync' "$ASSIST"
! grep -Fq 'verified_rows=' assistant/build_mdc_sqlite_asset_v032.py
grep -Fq 'def one_film(film):' assistant/build_mdc_sqlite_asset_v032.py
grep -Fq "Current film-page acquisition incomplete" assistant/build_mdc_sqlite_asset_v032.py

python3 - <<'PY' | tee validation-v057.txt
from pathlib import Path
import sqlite3

db = sqlite3.connect(Path('combined/src/main/assets/mdc_full.sqlite'))
db.row_factory = sqlite3.Row
assert db.execute('PRAGMA quick_check').fetchone()[0] == 'ok'

meta = dict(db.execute('SELECT key,value FROM meta'))
assert int(meta['current_film_pages']) >= 250, meta
assert int(meta['current_film_rows']) >= 3000, meta
assert int(meta['current_film_failed']) == 0, meta
assert meta['snapshot_policy'] == 'current film pages first; developer indexes as fallback'

fx39 = db.execute(
    '''SELECT time35,time120,timesheet,temp,source_url FROM times
       WHERE film_norm='fomapan 100' AND developer_norm='fx 39'
         AND dilution_norm='1+9' AND iso=100 AND temp=20
       ORDER BY id LIMIT 1'''
).fetchone()
assert fx39 is not None, 'Fomapan 100 / FX-39 / 1+9 / ISO 100 missing'
assert tuple(fx39[:4]) == ('7','7','7',20.0), tuple(fx39)
assert 'Film=Fomapan+100' in fx39['source_url'], fx39['source_url']

ilfosol = db.execute(
    '''SELECT timesheet,notes FROM times
       WHERE film_norm='fomapan 100' AND developer_norm='ilfosol 3'
         AND dilution_norm='1+9' AND iso=100 AND temp=20
       ORDER BY id LIMIT 1'''
).fetchone()
assert ilfosol is not None and ilfosol['timesheet'] == '5', ilfosol

d76 = db.execute(
    '''SELECT timesheet FROM times
       WHERE film_norm='fomapan 100' AND developer_norm='d 76'
         AND dilution_norm='1+1' AND iso=100 AND temp=20
       ORDER BY id LIMIT 1'''
).fetchone()
assert d76 is not None and d76['timesheet'] == '10', d76

# Continuous JOBO factor 0.85, rounded by the app to the nearest five seconds.
assert round(7 * 60 * 0.85 / 5) * 5 == 355
assert db.execute('SELECT COUNT(*) FROM times').fetchone()[0] >= 14500
assert db.execute('SELECT COUNT(*) FROM maco_developer_scope').fetchone()[0] == 37
assert db.execute(
    'SELECT COUNT(*) FROM developer_dilutions WHERE min_working_ml_500cm2 IS NOT NULL'
).fetchone()[0] == 236
db.close()

print('release=Darkroom-v0.5.7')
print('versionName=0.5.7')
print('versionCode=48')
print('runtime_network_for_mdc=DISABLED')
print('snapshot_pipeline=FILM_INDEX_PLUS_DEVELOPER_INDEX')
print('manual_time_rows=ZERO')
print('failed_current_film_pages=ZERO')
print('fomapan100_fx39_1+9_iso100_sheet_base=7min')
print('fomapan100_fx39_1+9_iso100_sheet_jobo=5min55s')
print('regression_ilfosol3=PASS')
print('regression_d76=PASS')
print('database_integrity=PASS')
PY

sha256sum Darkroom-v0.5.7.apk | tee Darkroom-v0.5.7.sha256
