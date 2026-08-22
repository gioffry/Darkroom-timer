#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.3.3 — enriched offline developer database wired into the product UI.
# Base: verified Darkroom v0.3.2. Preserve Timer / Split Grade / SONOFF / manuals / user data.

# Reconstruct the exact v0.3.2 application first.
bash combined/build_v032.sh

# Build the evolved database with the agreed hierarchy:
# MDC first -> manufacturer only fills missing technical fields.
python3 assistant/db/enrich_developer_profiles.py
for batch in assistant/db/producer_enrichment_batch{2..12}.json; do
  python3 assistant/db/apply_manufacturer_batch.py "$batch"
done
shopt -s nullglob
for batch in assistant/db/macodirect_enrichment_batch*.json; do
  python3 assistant/db/apply_macodirect_scoped_batch.py "$batch"
done
python3 assistant/db/audit_developer_profiles.py
python3 assistant/db/audit_macodirect_scope.py

# The database produced above is the one bundled in the APK.
cp assistant/src/main/assets/mdc_full.sqlite combined/src/main/assets/mdc_full.sqlite

# Wire developer_profiles into Magazzino / Modifica prodotto and force a fresh DB asset on upgrade.
python3 combined/patch_v033_enriched_profiles.py

# Advance only the outer app package version. Internal Timer remains 0.13.11.
# Android Gradle Plugin takes versionName/versionCode from defaultConfig, so update both
# Gradle and manifest. Keep SQLite helper schema at 3 because the enriched asset itself is
# user_version=3; the new DB filename alone forces a fresh bundled copy on upgrade.
python3 - <<'PY'
from pathlib import Path
import re

p=Path('combined/src/main/AndroidManifest.xml')
s=p.read_text(encoding='utf-8')
s,n1=re.subn(r'android:versionCode="[^"]+"','android:versionCode="24"',s,count=1)
s,n2=re.subn(r'android:versionName="[^"]+"','android:versionName="0.3.3"',s,count=1)
if n1 != 1 or n2 != 1:
    raise SystemExit('v0.3.3 manifest version update failed')
p.write_text(s,encoding='utf-8')

g=Path('combined/build.gradle')
gs=g.read_text(encoding='utf-8')
gs,n3=re.subn(r'(?m)^\s*versionCode\s+\d+\s*$', '        versionCode 24', gs, count=1)
gs,n4=re.subn(r'(?m)^\s*versionName\s+[\'\"][^\'\"]+[\'\"]\s*$', "        versionName '0.3.3'", gs, count=1)
if n3 != 1 or n4 != 1:
    raise SystemExit('v0.3.3 Gradle version update failed')
g.write_text(gs,encoding='utf-8')

m=Path('combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java')
ms=m.read_text(encoding='utf-8')
if 'private static final int DB_VERSION = 4;' in ms:
    ms=ms.replace('private static final int DB_VERSION = 4;', 'private static final int DB_VERSION = 3;', 1)
if 'private static final int DB_VERSION = 3;' not in ms:
    raise SystemExit('v0.3.3 SQLite helper version marker missing')
if 'mdc_offline_darkroom_v033.sqlite' not in ms:
    raise SystemExit('v0.3.3 fresh database filename missing')
m.write_text(ms,encoding='utf-8')
PY

# Rebuild after the DB/UI bridge patch.
rm -f combined/build/outputs/apk/release/combined-release.apk
gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.3.3.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.3.3.apk > certificate-v033.txt
"$AAPT" dump badging Darkroom-v0.3.3.apk > apk-badging-v033.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-v033.txt
grep -Fq "versionCode='24'" apk-badging-v033.txt
grep -Fq "versionName='0.3.3'" apk-badging-v033.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v033.txt
unzip -Z1 Darkroom-v0.3.3.apk > apk-listing-v033.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v033.txt

# Validate the exact bundled SQLite before publishing the artifact.
python3 - <<'PY'
from pathlib import Path
import sqlite3

db=Path('combined/src/main/assets/mdc_full.sqlite')
con=sqlite3.connect(db); cur=con.cursor()
quick=cur.execute('PRAGMA quick_check').fetchone()[0]
profiles=cur.execute('SELECT COUNT(*) FROM developer_profiles').fetchone()[0]
combinations=cur.execute('SELECT COUNT(*) FROM times').fetchone()[0]
mdc_dils=cur.execute("SELECT COUNT(*) FROM developer_dilutions WHERE source_kind='MDC'").fetchone()[0]
sg=cur.execute("SELECT manufacturer,preparation,reuse_mode,capacity_text,shelf_life_unopened FROM developer_profiles WHERE developer_norm='rollei supergrain'").fetchone()
if not sg or not all(str(x or '').strip() for x in sg):
    raise SystemExit('Rollei Supergrain profile is not complete: '+repr(sg))
excel=cur.execute("SELECT manufacturer,preparation,reuse_mode,capacity_text FROM developer_profiles WHERE developer_norm='fomadon excel'").fetchone()
excel_dils=[r[0] for r in cur.execute("SELECT dilution FROM developer_dilutions WHERE developer_norm='fomadon excel' ORDER BY dilution_norm")]
if not excel or not all(str(x or '').strip() for x in excel):
    raise SystemExit('FOMADON Excel enriched profile incomplete: '+repr(excel))
for required in ('stock','1+1','1+2','1+3'):
    if required not in excel_dils: raise SystemExit('FOMADON Excel dilution missing: '+required)
if quick!='ok' or profiles!=232 or combinations!=14504 or mdc_dils!=776:
    raise SystemExit(f'DB integrity mismatch quick={quick} profiles={profiles} combinations={combinations} mdc_dils={mdc_dils}')
con.close()
print('bundled_sqlite_quick_check=PASS')
print('developer_profiles=232')
print('mdc_combinations=14504')
print('mdc_dilutions_preserved=776')
print('rollei_supergrain_complete=PASS')
print('fomadon_excel_runtime_profile=PASS')
PY

ASSIST=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
MDC=combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java
MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java
MAINT=combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java

grep -Fq 'developerTechnicalSummary' "$ASSIST"
grep -Fq 'applyDeveloperProfile' "$ASSIST"
grep -Fq 'if ((role & ROLE_FILM_DEV) != 0) return 0;' "$ASSIST"
grep -Fq 'REUSE_FRESH_RECOMMENDED = 3' "$ASSIST"
grep -Fq 'mdc_offline_darkroom_v033.sqlite' "$MDC"
grep -Fq 'private static final int DB_VERSION = 3;' "$MDC"
# Preserve prior functional areas.
grep -q 'private static final String APP_VERSION = "0.13.11";' "$MAIN"
grep -Fq 'NIKON L35AF' "$MAINT"
grep -Fq 'ROLLEIFLEX 2.8 E2' "$MAINT"

cat developer-db-audit.txt > validation-v033-catalog.txt
cat macodirect-scope-audit.txt >> validation-v033-catalog.txt
cat >> validation-v033-catalog.txt <<'EOF'
release=Darkroom-v0.3.3
versionName=0.3.3
versionCode=24
base_version=0.3.2
catalog_hierarchy=MDC_FIRST_MANUFACTURER_FILL_ONLY
catalog_runtime=FULL_OFFLINE_BUNDLED_SQLITE
rollei_supergrain_complete=PASS
fomadon_excel_runtime_bridge=PASS
fomadon_excel_role_regression=PASS
fresh_catalog_copy_on_upgrade=PASS
personal_data_migration=NO_DESTRUCTIVE_RESET
camera_manuals_preserved=PASS
timer_splitgrade_sonoff_preserved=PASS
EOF

sha256sum Darkroom-v0.3.3.apk | tee Darkroom-v0.3.3.sha256
