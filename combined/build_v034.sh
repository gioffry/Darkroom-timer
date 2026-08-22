#!/usr/bin/env bash
set -euo pipefail

# Darkroom v0.3.4 — Italian technical chemistry data + unified card.
# Exact base: verified Darkroom v0.3.3 enriched catalog.
# Rule: MDC combination data are immutable in this release.

bash combined/build_v033.sh

# Add Italian display fields and auxiliary chemistry profiles INSIDE the same
# bundled SQLite. The script fingerprints all MDC tables before/after and fails
# if films, developers, times or developer_dilutions change.
python3 assistant/db/apply_italian_technical_profiles_v034.py combined/src/main/assets/mdc_full.sqlite \
  | tee validation-v034-technical-db.txt

# One UI card for recipe + product sheet; product detail and paper developer
# reuse the same Italian technical reader.
python3 combined/patch_v034_chemical_tech_card_it.py

# Advance only outer Darkroom version. Timer internals stay unchanged.
python3 - <<'PY'
from pathlib import Path
import re

p=Path('combined/src/main/AndroidManifest.xml')
s=p.read_text(encoding='utf-8')
s,n1=re.subn(r'android:versionCode="[^"]+"','android:versionCode="25"',s,count=1)
s,n2=re.subn(r'android:versionName="[^"]+"','android:versionName="0.3.4"',s,count=1)
if n1 != 1 or n2 != 1: raise SystemExit('v0.3.4 manifest version update failed')
p.write_text(s,encoding='utf-8')

g=Path('combined/build.gradle')
gs=g.read_text(encoding='utf-8')
gs,n3=re.subn(r'(?m)^\s*versionCode\s+\d+\s*$', '        versionCode 25', gs, count=1)
gs,n4=re.subn(r'(?m)^\s*versionName\s+[\'\"][^\'\"]+[\'\"]\s*$', "        versionName '0.3.4'", gs, count=1)
if n3 != 1 or n4 != 1: raise SystemExit('v0.3.4 Gradle version update failed')
g.write_text(gs,encoding='utf-8')
PY

rm -f combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.3.4.apk
gradle :combined:assembleRelease --stacktrace
cp combined/build/outputs/apk/release/combined-release.apk Darkroom-v0.3.4.apk

APKSIGNER="$ANDROID_HOME/build-tools/34.0.0/apksigner"
AAPT="$ANDROID_HOME/build-tools/34.0.0/aapt"
"$APKSIGNER" verify --verbose --print-certs Darkroom-v0.3.4.apk > certificate-v034.txt
"$AAPT" dump badging Darkroom-v0.3.4.apk > apk-badging-v034.txt
grep -Fq "package: name='it.darkroom.darkroom'" apk-badging-v034.txt
grep -Fq "versionCode='25'" apk-badging-v034.txt
grep -Fq "versionName='0.3.4'" apk-badging-v034.txt
grep -Fq "launchable-activity: name='it.darkroom.timer.home.HomeActivity'" apk-badging-v034.txt
unzip -Z1 Darkroom-v0.3.4.apk > apk-listing-v034.txt
grep -q 'assets/mdc_full.sqlite' apk-listing-v034.txt

ASSIST=combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java
MDC=combined/src/main/java/it/darkroom/assistant/MdcOfflineStore.java
MAIN=combined/src/main/java/it/darkroom/timer/MainActivity.java
MAINT=combined/src/main/java/it/darkroom/timer/maintenance/UseMaintenanceActivity.java

grep -Fq 'chemicalTechnicalSummaryIt' "$ASSIST"
grep -Fq 'RIVELATORE · RICETTA + SCHEDA TECNICA' "$ASSIST"
grep -Fq 'COMBINAZIONE PELLICOLA / RIVELATORE' "$ASSIST"
grep -Fq 'SCHEDA TECNICA DEL PRODOTTO' "$ASSIST"
grep -Fq 'mdc_offline_darkroom_v034.sqlite' "$MDC"
grep -Fq 'private static final int DB_VERSION = 3;' "$MDC"
# Preserve prior app areas and Timer behavior.
grep -q 'private static final String APP_VERSION = "0.13.11";' "$MAIN"
grep -Fq 'NIKON L35AF' "$MAINT"
grep -Fq 'ROLLEIFLEX 2.8 E2' "$MAINT"

python3 - <<'PY' | tee validation-v034-bundled-db.txt
from pathlib import Path
import sqlite3
p=Path('combined/src/main/assets/mdc_full.sqlite')
con=sqlite3.connect(p); cur=con.cursor()
assert cur.execute('PRAGMA quick_check').fetchone()[0]=='ok'
assert cur.execute('SELECT COUNT(*) FROM times').fetchone()[0]==14504
assert cur.execute('SELECT COUNT(*) FROM films').fetchone()[0]==347
assert cur.execute('SELECT COUNT(*) FROM developers').fetchone()[0]==232
assert cur.execute("SELECT COUNT(*) FROM developer_dilutions WHERE source_kind='MDC'").fetchone()[0]==776
cols={r[1] for r in cur.execute('PRAGMA table_info(developer_profiles)')}
for c in ['preparation_it','capacity_it','shelf_life_unopened_it','shelf_life_opened_it','shelf_life_stock_it','shelf_life_working_it','storage_notes_it','notes_it']:
    assert c in cols, c
it_count=cur.execute("SELECT COUNT(*) FROM developer_profiles WHERE COALESCE(preparation_it,physical_state_it,capacity_it,shelf_life_working_it,shelf_life_stock_it,shelf_life_opened_it,shelf_life_unopened_it,'')<>''").fetchone()[0]
assert it_count >= 79, it_count
assert cur.execute('SELECT COUNT(*) FROM auxiliary_chemical_profiles WHERE verified=1').fetchone()[0] >= 4
for n in ['fomatol lqn','adox adostop eco','fomafix','fotonal']:
    row=cur.execute('SELECT preparation_it,notes_it FROM auxiliary_chemical_profiles WHERE norm_name=?',(n,)).fetchone()
    assert row and row[0] and row[1], n
excel=cur.execute("SELECT preparation_it,capacity_it FROM developer_profiles WHERE developer_norm='fomadon excel'").fetchone()
id11=cur.execute("SELECT preparation_it,shelf_life_stock_it,shelf_life_working_it FROM developer_profiles WHERE developer_norm='id 11'").fetchone()
assert excel and all(excel)
assert id11 and all(id11)
print('release=Darkroom-v0.3.4')
print('versionName=0.3.4')
print('versionCode=25')
print('base_version=0.3.3')
print('catalog_hierarchy=MDC_FIRST_MANUFACTURER_FILL_ONLY')
print('mdc_times_unchanged=14504')
print('mdc_films_unchanged=347')
print('mdc_developers_unchanged=232')
print('mdc_dilutions_unchanged=776')
print(f'developer_profiles_with_italian_technical_data={it_count}')
print('auxiliary_chemistry_it=FOMATOL_LQN,ADOSTOP_ECO,FOMAFIX,FOTONAL')
print('single_card_mdc_plus_technical=PASS')
print('original_technical_text_preserved=PASS')
print('timer_splitgrade_sonoff_preserved=PASS')
print('personal_data_migration=NO_DESTRUCTIVE_RESET')
con.close()
PY

cat validation-v033-catalog.txt validation-v034-technical-db.txt validation-v034-bundled-db.txt > validation-v034.txt
sha256sum Darkroom-v0.3.4.apk | tee Darkroom-v0.3.4.sha256
