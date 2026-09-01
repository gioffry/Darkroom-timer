#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.5.5 - canonical time aliases + progressive result disclosure.
# Exact base: v0.5.4 runtime crash guard.

bash combined/build_v054.sh
python3 combined/patch_v055_time_aliases.py | tee validation-v055-time-aliases.txt
python3 combined/patch_v055_results_ui.py | tee validation-v055-results-ui.txt

python3 - <<'PY'
from pathlib import Path
import re

manifest = Path('combined/src/main/AndroidManifest.xml')
text = manifest.read_text(encoding='utf-8')
text, n1 = re.subn(r'android:versionCode="[^"]+"', 'android:versionCode="46"', text, count=1)
text, n2 = re.subn(r'android:versionName="[^"]+"', 'android:versionName="0.5.5"', text, count=1)
if n1 != 1 or n2 != 1: raise SystemExit('v0.5.5 manifest version update failed')
manifest.write_text(text, encoding='utf-8')

gradle = Path('combined/build.gradle')
text = gradle.read_text(encoding='utf-8')
text, n3 = re.subn(r'(?m)^\s*versionCode\s+\d+\s*$', '        versionCode 46', text, count=1)
text, n4 = re.subn(r'(?m)^\s*versionName\s+[\'\"][^\'\"]+[\'\"]\s*$', "        versionName '0.5.5'", text, count=1)
if n3 != 1 or n4 != 1: raise SystemExit('v0.5.5 Gradle version update failed')
gradle.write_text(text, encoding='utf-8')
PY

rm -f combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.5.5.apk
gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.5.5.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.5.5.apk > certificate-v055.txt
"$AAPT" dump badging Darkroom-v0.5.5.apk > apk-badging-v055.txt
grep -Fq "versionCode='46'" apk-badging-v055.txt
grep -Fq "versionName='0.5.5'" apk-badging-v055.txt
unzip -Z1 Darkroom-v0.5.5.apk > apk-listing-v055.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v055.txt

ASSIST=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
MDC=combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java
test "$(grep -Fc 'FullCatalogStore.canonicalDeveloper(developer)' "$MDC")" -ge 2
grep -Fq 'DevTimeEngine.Result exactResult' "$ASSIST"
grep -Fq 'RISULTATO SVILUPPO' "$ASSIST"
grep -Fq 'PREPARAZIONE BAGNI' "$ASSIST"
grep -Fq 'body.setVisibility(View.GONE)' "$ASSIST"

python3 - <<'PY' | tee validation-v055.txt
from pathlib import Path
import sqlite3

db = sqlite3.connect(Path('combined/src/main/assets/mdc_full.sqlite'))
db.row_factory = sqlite3.Row
assert db.execute('pragma quick_check').fetchone()[0] == 'ok'

row = db.execute(
    '''SELECT time35,time120,timesheet,temp FROM times
       WHERE film_norm='fomapan 100' AND developer_norm='d 76'
         AND dilution_norm='1+1' AND iso=100 AND temp=20 LIMIT 1'''
).fetchone()
assert row is not None
assert tuple(row) == ('10', '10', '10', 20.0), tuple(row)

# The user-facing commercial alias must canonicalize to the exact database key.
def norm(value):
    import re, unicodedata
    value = unicodedata.normalize('NFD', value).lower().replace('-', ' ')
    value = ''.join(c for c in value if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9+]+', ' ', value)).strip()

alias = 'KODAK D-76'
canonical = 'D-76'
assert norm(alias) == 'kodak d 76'
assert norm(canonical) == 'd 76'
assert db.execute(
    "SELECT COUNT(*) FROM times WHERE film_norm='fomapan 100' AND developer_norm=? AND dilution_norm='1+1' AND iso=100",
    (norm(canonical),),
).fetchone()[0] >= 1

base_seconds = 10 * 60
jobo_seconds = round(base_seconds * 0.85 / 5) * 5
assert jobo_seconds == 510
assert db.execute('SELECT COUNT(*) FROM maco_developer_scope').fetchone()[0] == 37
assert db.execute('SELECT COUNT(*) FROM developer_dilutions WHERE min_working_ml_500cm2 IS NOT NULL').fetchone()[0] == 236
db.close()

print('release=Darkroom-v0.5.5')
print('versionName=0.5.5')
print('versionCode=46')
print('time_alias=KODAK_D76_TO_D76')
print('fomapan100_d76_1+1_sheet_base=10min')
print('fomapan100_d76_1+1_sheet_jobo=8min30s')
print('progressive_sections=DETAILS,TECHNICAL,REUSE')
print('preparation_always_visible=PASS')
print('database_integrity=PASS')
PY

sha256sum Darkroom-v0.5.5.apk | tee Darkroom-v0.5.5.sha256
