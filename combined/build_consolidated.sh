#!/usr/bin/env bash
set -euo pipefail

# Consolidated Darkroom v0.6.0 build.
# Starts from the committed verified v0.5.8 source checkpoint, applies the tested
# v0.5.9 contact-sheet functionality and then the v0.6.0 layout/preset refinement.
# One Gradle assembly only; no historical wrapper and no MDC network regeneration.

START_SECONDS=$SECONDS
SOURCE_ROOT=combined/src
DATABASE="$SOURCE_ROOT/main/assets/mdc_full.sqlite"
MANIFEST="$SOURCE_ROOT/main/AndroidManifest.xml"

test -f "$DATABASE"
test -f "$SOURCE_ROOT/main/java/it/darkroom/timer/MainActivity.java"
test -f "$SOURCE_ROOT/main/java/it/darkroom/timer/SonoffArmService.java"
test -f "$SOURCE_ROOT/main/java/it/darkroom/assistant/MdcOfflineStore.java"
test -f "$SOURCE_ROOT/main/java/it/darkroom/assistant/AssistantActivityV2.java"

python3 combined/patch_v059_contact_sheet.py | tee validation-v059-contact-source.txt
python3 combined/patch_v060_contact_layout.py | tee validation-v060-contact-layout-source.txt

python3 - <<'PY' | tee validation-consolidated-v060-source.txt
from pathlib import Path
import re
import sqlite3

manifest = Path('combined/src/main/AndroidManifest.xml')
text = manifest.read_text(encoding='utf-8')
text, code_count = re.subn(
    r'android:versionCode="[^"]+"', 'android:versionCode="51"', text, count=1
)
text, name_count = re.subn(
    r'android:versionName="[^"]+"', 'android:versionName="0.6.0"', text, count=1
)
if code_count != 1 or name_count != 1:
    raise SystemExit('v0.6.0 manifest version update failed')
manifest.write_text(text, encoding='utf-8')

gradle_file = Path('combined/build.gradle')
text = gradle_file.read_text(encoding='utf-8')
text, code_count = re.subn(
    r'(?m)^\s*versionCode\s+\d+\s*$', '        versionCode 51', text, count=1
)
text, name_count = re.subn(
    r'(?m)^\s*versionName\s+[\'\"][^\'\"]+[\'\"]\s*$',
    "        versionName '0.6.0'", text, count=1
)
if code_count != 1 or name_count != 1:
    raise SystemExit('v0.6.0 Gradle version update failed')
gradle_file.write_text(text, encoding='utf-8')

db = sqlite3.connect('combined/src/main/assets/mdc_full.sqlite')
assert db.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
assert db.execute('SELECT COUNT(*) FROM times').fetchone()[0] == 14808
assert db.execute('SELECT COUNT(*) FROM maco_developer_scope').fetchone()[0] == 37
assert db.execute('SELECT COUNT(*) FROM developer_time_equivalents').fetchone()[0] == 39
assert db.execute(
    "SELECT COUNT(*) FROM developer_time_equivalents WHERE evidence_kind<>'AUDITED_DIRECT_ONE_HOP'"
).fetchone()[0] == 0

good = db.execute(
    '''SELECT time35,time120,timesheet FROM times
       WHERE film_norm='kentmere 100' AND developer_norm='xtol'
         AND dilution_norm='1+1' AND iso=100 AND temp=20'''
).fetchone()
assert good == ('10', '10', ''), good
db.close()

main = Path('combined/src/main/java/it/darkroom/timer/MainActivity.java').read_text(encoding='utf-8')
service = Path('combined/src/main/java/it/darkroom/timer/SonoffArmService.java').read_text(encoding='utf-8')
assert 'APP_VERSION = "0.13.13"' in main
assert 'compactButton("PROVINO SINGOLO")' in main
assert 'compactButton("PROVINO SPLIT GRADE")' in main
assert 'compactButton("IMPOSTA INGRANDIMENTO")' in main
assert 'compactButton("PROVINO A CONTATTO 35 mm")' in main
assert 'compactButton("PROVINO STAMPA")' not in main
assert main.index('compactButton("PROVINO SINGOLO")') < main.index('compactButton("IMPOSTA INGRANDIMENTO")') < main.index('compactButton("PROVINO A CONTATTO 35 mm")')
assert 'ISO/EI' not in main
assert ' · EI ' not in main
assert 'editField("ISO — es. 125"' in main
assert 'Colonna LPL — predefinito 57' in main
assert 'Diaframma — predefinito f/8' in main
assert 'Contrasto — predefinito Y0 / M10' in main
assert 'String setupLine()' in main
assert '.putInt("iso_" + preset.id, preset.iso)' in main
assert 'contact35_presets' in main
assert '+  NUOVO PRESET' in main
assert 'SALVA PRESET' in main
assert 'contact35CycleActive' in main
assert 'EXTRA_COUNT, 1' in main
assert 'EXTRA_CONTACT_SHEET_35' in main
assert 'EXTRA_CONTACT_SHEET_35 = "contact_sheet_35"' in service
assert 'count = contactSheet35 ? 1 : Math.max(2, Math.min(20' in service

store = Path('combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java').read_text(encoding='utf-8')
activity = Path('combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java').read_text(encoding='utf-8')
assert 'mdc_offline_darkroom_v058.sqlite' in store
assert 'if (exact != null) return exact;' in store
assert 'developer_time_equivalents' in store
assert 'EQUIVALENZA CONTROLLATA' in activity
assert 'MdcOfflineStore.syncAsync' not in activity

print('release=Darkroom-v0.6.0')
print('versionCode=51')
print('timer_internal=0.13.13')
print('historical_builds=ZERO')
print('mdc_network_downloads=ZERO')
print('gradle_assemblies_expected=ONE')
print('provino_hierarchy=SINGLE_SPLIT_THEN_ENLARGEMENT_THEN_CONTACT')
print('contact35_iso_only=PASS')
print('contact35_editable_column_aperture_contrast=PASS')
print('contact35_presets_persistent=PASS')
print('contact35_single_sonoff_exposure=PASS')
print('database_integrity=PASS')
print('offline_equivalence_regressions=PASS')
PY

rm -f combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.6.0.apk
gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.6.0.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.6.0.apk > certificate-v060.txt
"$AAPT" dump badging Darkroom-v0.6.0.apk > apk-badging-v060.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-v060.txt
grep -Fq "versionCode='51'" apk-badging-v060.txt
grep -Fq "versionName='0.6.0'" apk-badging-v060.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v060.txt
unzip -Z1 Darkroom-v0.6.0.apk > apk-listing-v060.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v060.txt

ELAPSED=$((SECONDS - START_SECONDS))
{
  echo 'consolidated_build=PASS'
  echo 'release=Darkroom-v0.6.0'
  echo 'historical_builds=ZERO'
  echo 'mdc_network_downloads=ZERO'
  echo 'gradle_assemblies=ONE'
  echo "elapsed_seconds=$ELAPSED"
} | tee validation-consolidated-v060.txt

sha256sum Darkroom-v0.6.0.apk | tee Darkroom-v0.6.0.sha256
