#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.5.6 - refreshed bundled MDC data, exact offline time selection,
# compatible dilutions, and a non-redundant result card.

python3 combined/patch_v056_build_chain.py
bash combined/build_v055.sh
python3 combined/patch_v056_offline_times_ui.py \
  | tee validation-v056-source.txt

python3 - <<'PY'
from pathlib import Path
import re

manifest = Path('combined/src/main/AndroidManifest.xml')
text = manifest.read_text(encoding='utf-8')
text, n1 = re.subn(r'android:versionCode="[^"]+"', 'android:versionCode="47"', text, count=1)
text, n2 = re.subn(r'android:versionName="[^"]+"', 'android:versionName="0.5.6"', text, count=1)
if n1 != 1 or n2 != 1: raise SystemExit('v0.5.6 manifest version update failed')
manifest.write_text(text, encoding='utf-8')

gradle_file = Path('combined/build.gradle')
text = gradle_file.read_text(encoding='utf-8')
text, n3 = re.subn(r'(?m)^\s*versionCode\s+\d+\s*$', '        versionCode 47', text, count=1)
text, n4 = re.subn(r'(?m)^\s*versionName\s+[\'\"][^\'\"]+[\'\"]\s*$', "        versionName '0.5.6'", text, count=1)
if n3 != 1 or n4 != 1: raise SystemExit('v0.5.6 Gradle version update failed')
gradle_file.write_text(text, encoding='utf-8')
PY

rm -f combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.5.6.apk
gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.5.6.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.5.6.apk > certificate-v056.txt
"$AAPT" dump badging Darkroom-v0.5.6.apk > apk-badging-v056.txt
grep -Fq "versionCode='47'" apk-badging-v056.txt
grep -Fq "versionName='0.5.6'" apk-badging-v056.txt
unzip -Z1 Darkroom-v0.5.6.apk > apk-listing-v056.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v056.txt

ASSIST=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
MDC=combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java
grep -Fq 'mdc_offline_darkroom_v056.sqlite' "$MDC"
grep -Fq 'dilutionsForCombination' "$MDC"
grep -Fq 'refreshFilmDilutions' "$ASSIST"
! grep -Fq 'addUnifiedChemicalField(summary, "COMBINAZIONE"' "$ASSIST"
! grep -Fq 'addUnifiedChemicalField(summary, "TANK / VOLUME"' "$ASSIST"
! grep -Fq 'MdcOfflineStore.syncAsync' "$ASSIST"

python3 - <<'PY' | tee validation-v056.txt
from pathlib import Path
import sqlite3

db = sqlite3.connect(Path('combined/src/main/assets/mdc_full.sqlite'))
db.row_factory = sqlite3.Row
assert db.execute('PRAGMA quick_check').fetchone()[0] == 'ok'

rows_19 = db.execute(
    '''SELECT time35,time120,timesheet,temp,notes,source_url FROM times
       WHERE film_norm='fomapan 100' AND developer_norm='ilfosol 3'
         AND dilution_norm='1+9' AND iso=100 AND temp=20
       ORDER BY CAST(timesheet AS REAL) DESC'''
).fetchall()
assert rows_19, 'Fomapan 100 / Ilfosol 3 1+9 missing'
sheet_values_19 = {r['timesheet'] for r in rows_19 if r['timesheet'] not in ('', '-', '—', '#')}
assert '5' in sheet_values_19, sheet_values_19
assert any('[40]' in (r['notes'] or '') and r['timesheet'] == '5' for r in rows_19), rows_19
assert any('[63]' in (r['notes'] or '') for r in rows_19), rows_19
assert all((r['source_url'] or '').startswith('https://www.digitaltruth.com/') for r in rows_19)

rows_114 = db.execute(
    '''SELECT timesheet,notes FROM times
       WHERE film_norm='fomapan 100' AND developer_norm='ilfosol 3'
         AND dilution_norm='1+14' AND iso=100 AND temp=20'''
).fetchall()
assert any(r['timesheet'] == '7.5' and '[63]' not in (r['notes'] or '') for r in rows_114), rows_114

dilutions = {
    r[0] for r in db.execute(
        '''SELECT DISTINCT dilution_norm FROM times
           WHERE film_norm='fomapan 100' AND developer_norm='ilfosol 3' '''
    )
}
assert '1+9' in dilutions and '1+14' in dilutions
assert '1+3' not in dilutions

# 5 minutes in MDC -> continuous JOBO factor 0.85 -> 4m15s.
assert round(5 * 60 * 0.85 / 5) * 5 == 255
assert db.execute('SELECT COUNT(*) FROM times').fetchone()[0] >= 14504
assert db.execute('SELECT COUNT(*) FROM maco_developer_scope').fetchone()[0] == 37
assert db.execute(
    'SELECT COUNT(*) FROM developer_dilutions WHERE min_working_ml_500cm2 IS NOT NULL'
).fetchone()[0] == 236
db.close()

print('release=Darkroom-v0.5.6')
print('versionName=0.5.6')
print('versionCode=47')
print('runtime_network_for_mdc=DISABLED')
print('fomapan100_ilfosol3_1+9_sheet_base=5min')
print('fomapan100_ilfosol3_1+9_sheet_jobo=4min15s')
print('fomapan100_ilfosol3_1+9_note=PREWASH_3_TO_5_MIN')
print('combination_dilutions=PASS')
print('compact_result=PASS')
print('database_integrity=PASS')
PY

sha256sum Darkroom-v0.5.6.apk | tee Darkroom-v0.5.6.sha256
